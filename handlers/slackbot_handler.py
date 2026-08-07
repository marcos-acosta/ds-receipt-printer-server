from nepso import CutAndPrint, Image, Printable, Text
from handlers.webhook_body_handler import WebhookBodyHandler
from util import HR_WAVY, pad_newlines, print_timestamp_epoch
import base64
import os
import re
import tempfile


def unlink_slack_text(text):
    """Replace Slack link markup with its label, so URLs stay off the receipt."""
    text = re.sub(r"<(https?://[^|>]+)\|([^>]+)>", r"\2", text)
    return re.sub(r"<(https?://[^|>]+)>", r"\1", text)


def write_temp_image(encoded: str) -> str:
    """Put a base64 image on disk and give back the path.

    nepso reads the file at print time, so the file must stay until the print
    ends. SlackbotHandler.cleanup() removes it.
    """
    content = base64.b64decode(encoded, validate=True)
    with tempfile.NamedTemporaryFile(prefix="slack-image-", delete=False) as tmp:
        tmp.write(content)
        return tmp.name


class SlackbotHandler(WebhookBodyHandler):
    def generatePrintables(self, message: dict) -> list[Printable] | None:
        sender = message.get("sender", "(unknown)")
        timestamp_epoch_ms = float(message.get("timestamp", None))
        message_text = message.get("text", "")
        images = message.get("images", [])
        sent_at_pretty = (
            print_timestamp_epoch(timestamp_epoch_ms)
            if timestamp_epoch_ms
            else "(no timestamp)"
        )
        message_text_pretty = unlink_slack_text(message_text)
        # Nothing to print
        if not message_text_pretty and len(images) == 0:
            return None

        header = f"Message from {sender}\nSent at {sent_at_pretty}\n{HR_WAVY}"
        printables: list[Printable] = [Text(header)]

        if message_text_pretty:
            formatted_text = (
                pad_newlines(message_text_pretty, 4)
                if len(images) == 0
                else message_text_pretty
            )
            printables.append(Text(formatted_text))

        # Print the first image only. More than one fills the paper too fast.
        if images:
            if len(images) > 1:
                print(f"[Slackbot handler] Ignoring {len(images) - 1} extra image(s)")
            try:
                printables.extend([Text("\n"), Image(write_temp_image(images[0]))])
            except Exception as e:
                print(f"[Slackbot handler] Could not prepare the image: {e}")

        printables.extend([Text("\n"), CutAndPrint()])
        return printables

    def cleanup(self, printables: list[Printable]) -> None:
        for item in printables:
            if not isinstance(item, Image):
                continue
            try:
                os.unlink(item.path)
            except OSError as e:
                print(f"[Slackbot handler] Could not remove {item.path}: {e}")
