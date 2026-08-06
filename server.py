#!/usr/bin/env python3
"""Web server that prints the contents of webhook POST requests."""

import json
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import TracebackType
from urllib.parse import parse_qs
import os

from dotenv import load_dotenv
from nepso import Printer, TcpTransport

from handlers.linear_handler import LinearHandler
from handlers.pagerduty_handler import PagerDutyHandler
from handlers.webhook_body_handler import WebhookBodyHandler
from util import read_secrets, signature_matches

load_dotenv()

PORT = 8082
PRINTER_IP = os.environ.get("PRINTER_IP", "10.51.46.125")

LINEAR_USER_AGENT_SUBSTRING = "Linear"
PAGERDUTY_USER_AGENT_SUBSTRING = "PagerDuty"


class SerializedPrinter(Printer):
    """A Printer that gives one thread at a time the connection.

    Each request runs in its own thread, and the printer accepts a single
    connection. Without this, two receipts interleave on one socket.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._lock = threading.Lock()

    def __enter__(self) -> Printer:
        self._lock.acquire()
        try:
            return super().__enter__()
        except BaseException:
            self._lock.release()
            raise

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        try:
            super().__exit__(exc_type, exc, tb)
        finally:
            self._lock.release()


@dataclass(frozen=True)
class WebhookSource:
    user_agent_substring: str
    signature_header: str
    secrets: list[str] = field(repr=False)
    handler: WebhookBodyHandler

    @property
    def header_key(self) -> str:
        return self.signature_header.lower()

    def matches(self, user_agent: str) -> bool:
        return self.user_agent_substring in user_agent

    def is_signed(self, body: bytes, headers: dict[str, str]) -> bool:
        return signature_matches(body, headers.get(self.header_key, ""), self.secrets)


def parse_body(body, content_type) -> dict | None:
    if not body:
        return {}

    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        return None

    media_type = content_type.split(";")[0].strip().lower()

    if media_type == "application/x-www-form-urlencoded":
        return {key: values[0] for key, values in parse_qs(text).items()}

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


class WebhookRequestHandler(BaseHTTPRequestHandler):
    printer: Printer = SerializedPrinter(TcpTransport(PRINTER_IP), throttle_ms=200)
    sources: list[WebhookSource] = [
        WebhookSource(
            user_agent_substring=LINEAR_USER_AGENT_SUBSTRING,
            signature_header="Linear-Signature",
            secrets=read_secrets("LINEAR_WEBHOOK_SECRET"),
            handler=LinearHandler(printer=printer),
        ),
        WebhookSource(
            user_agent_substring=PAGERDUTY_USER_AGENT_SUBSTRING,
            signature_header="X-PagerDuty-Signature",
            secrets=read_secrets(
                "PAGERDUTY_HIGH_PRIORITY_SECRET",
                "PAGERDUTY_LOW_PRIORITY_SECRET",
            ),
            handler=PagerDutyHandler(printer=printer),
        ),
    ]

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        # The signature covers the raw bytes, so verify before parse_body.
        body = self.rfile.read(length) if length else b""
        headers = {name.lower(): value for name, value in self.headers.items()}
        user_agent = headers.get("user-agent", "")

        source = next((s for s in self.sources if s.matches(user_agent)), None)
        if source is None:
            self.log(f"Couldn't find handler for user agent {user_agent}")
            self.respond(404, "no handler\n")
            return

        if not source.is_signed(body, headers):
            self.log(f"Rejected an unsigned or badly signed {user_agent} request")
            self.respond(401, "bad signature\n")
            return

        data = parse_body(body, headers.get("content-type", ""))
        if data is None:
            self.log(f"Couldn't parse the body of a {user_agent} request")
            self.respond(400, "bad body\n")
            return

        source.handler.handle(data)
        self.respond(200, "OK\n")

    def respond(self, code: int, text: str):
        payload = text.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log(self, message: str):
        print(f"[Request handler] {message}", flush=True)


def main():
    server = ThreadingHTTPServer(("", PORT), WebhookRequestHandler)
    print(f"Listening on port {PORT}. Press Ctrl+C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
