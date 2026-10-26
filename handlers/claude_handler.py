from nepso import CutAndPrint, Printable, Text
from handlers.webhook_body_handler import WebhookBodyHandler
from util import HR_WAVY, pad_newlines, print_timestamp
from datetime import datetime


class ClaudeHandler(WebhookBodyHandler):
    def generatePrintables(self, message: dict) -> list[Printable] | None:
        text = message.get("text", None) or message.get("message", None)
        on_behalf_of = message.get("claude", {}).get("on_behalf_of", None)
        if not text:
            return None
        now_datestring = str(datetime.now())
        byline = f"Printed by Claude at {print_timestamp(now_datestring)}"
        if on_behalf_of:
            byline = byline + f" on behalf of {on_behalf_of}"
        full_message = f"\n{byline}\n{HR_WAVY}\n{text}"
        return [Text(pad_newlines(full_message, 8)), CutAndPrint()]
