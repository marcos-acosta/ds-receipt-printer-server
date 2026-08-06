from nepso import CutAndPrint, Printable, Text
from handlers.webhook_body_handler import WebhookBodyHandler
from util import pad_newlines, print_timestamp


class PlaintextHandler(WebhookBodyHandler):
    def generatePrintables(self, message: dict) -> list[Printable] | None:
        text = message.get("text", None)
        if not text:
            return None
        return [Text(pad_newlines(text, 8)), CutAndPrint()]
