from nepso import CutAndPrint, Printable, Text
from handlers.webhook_body_handler import WebhookBodyHandler
from util import HR_STRAIGHT, pad_newlines, print_timestamp, strip_markdown_links


class PagerDutyHandler(WebhookBodyHandler):
    def generatePrintables(self, message: dict) -> list[Printable] | None:
        event = message.get("event", {})
        occurred_at = event.get("occurred_at", "")
        occurred_at_pretty = (
            print_timestamp(occurred_at) if occurred_at else "(no timestamp)"
        )
        message_body = strip_markdown_links(event.get("data", {}).get("message", ""))
        text = f"HELIUM BACKEND ALERT\nTriggered at {occurred_at_pretty}\n{HR_STRAIGHT}\n{message_body}\n"
        return [
            Text(pad_newlines(text, 8)),
            CutAndPrint(),
        ]
