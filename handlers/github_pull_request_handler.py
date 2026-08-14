from nepso import CutAndPrint, Printable, Text
from handlers.webhook_body_handler import WebhookBodyHandler
from util import pad_newlines


class GitHubPullRequestHandler(WebhookBodyHandler):
    def generatePrintables(self, message: dict) -> list[Printable] | None:
        print(message, flush=True)
        return [
            Text(pad_newlines("GitHub pull request made- check logs for body", 8)),
            CutAndPrint(),
        ]
