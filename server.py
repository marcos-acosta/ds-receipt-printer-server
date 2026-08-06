#!/usr/bin/env python3
"""Web server that prints the body of each POST request."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs
import os

from nepso import Printer, TcpTransport

from handlers.linear_handler import LinearHandler
from handlers.pagerduty_handler import PagerDutyHandler
from handlers.webhook_body_handler import WebhookBodyHandler

PORT = 8082
PRINTER_IP = os.environ.get("PRINTER_IP", "10.51.46.125")

LINEAR_USER_AGENT_SUBSTRING = "Linear"
PAGERDUTY_USER_AGENT_SUBSTRING = "PagerDuty"


def parse_body(body, content_type) -> str | None:
    """Make a dictionary from the request body.

    Returns the raw text if the body is not a known format.
    """
    if not body:
        return {}

    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        # The body is not text. Give the raw bytes.
        return None

    media_type = content_type.split(";")[0].strip().lower()

    if media_type == "application/x-www-form-urlencoded":
        # Each key can occur more than one time. Keep only the first value.
        return {key: values[0] for key, values in parse_qs(text).items()}

    if media_type == "application/json" or media_type.endswith("+json"):
        return json.loads(text)

    # The sender gave no usable type. Try JSON, then give the text.
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


class WebhookRequestHandler(BaseHTTPRequestHandler):
    printer: Printer = Printer(TcpTransport(PRINTER_IP), throttle_ms=200)
    handlers: dict[str, WebhookBodyHandler] = {
        LINEAR_USER_AGENT_SUBSTRING: LinearHandler(printer=printer),
        PAGERDUTY_USER_AGENT_SUBSTRING: PagerDutyHandler(printer=printer),
    }

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        headers = {k: v for k, v in self.headers.items()}

        user_agent = headers.get("User-Agent", "")
        data = parse_body(body, self.headers.get("Content-Type", ""))
        if data is not None:
            self.handle_data(data, user_agent)

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", "3")
        self.end_headers()
        self.wfile.write(b"OK\n")

    def handle_data(self, data: dict, user_agent: str):
        for user_agent_substring, handler in self.handlers.items():
            if user_agent_substring in user_agent:
                handler.handle(data)
                return
        self.log(f"Couldn't find handler for user agent {user_agent}")

    def log_message(self, format, *args):
        # Do not write the default request log. It hides the body output.
        pass

    def log(self, message: str):
        print(f"[Request handler] {message}")


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
