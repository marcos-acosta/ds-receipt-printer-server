from nepso import CutAndPrint, Printable, Text
from handlers.webhook_body_handler import WebhookBodyHandler
from util import pad_newlines, print_timestamp


class PagerDutyHandler(WebhookBodyHandler):
    def generatePrintables(self, message: dict) -> list[Printable] | None:
        event = message.get("event", {})
        occurred_at = event.get("occurred_at", "")
        occurred_at_pretty = (
            print_timestamp(occurred_at) if occurred_at else "(no timestamp)"
        )
        message_body = event.get("data", {}).get("message", "")
        text = f"HELIUM BACKEND ALERT :: {occurred_at_pretty}\n---\n{message_body}"
        return [
            Text(pad_newlines(text, 8)),
            CutAndPrint(),
        ]
