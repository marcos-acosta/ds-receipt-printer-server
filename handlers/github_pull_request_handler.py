from nepso import CutAndPrint, Printable, Text
from handlers.webhook_body_handler import WebhookBodyHandler
from util import HR_WAVY, print_timestamp
import re


class GitHubPullRequestHandler(WebhookBodyHandler):
    def generatePrintables(self, message: dict) -> list[Printable] | None:
        action = message.get("action", "")
        if action != "review_requested" or "requested_reviewer" not in message:
            return None
        number = message.get("number", "???")
        pr = message.get("pull_request", {})
        title = pr.get("title", "(no title)")
        sender = pr.get("user", {}).get("login", "(no sender)")
        body_raw = pr.get("body", "(no body)")
        body = re.sub(r"[\n\r]+", "\n", body_raw)
        requested_reviewer = message.get("requested_reviewer", {}).get(
            "login", "(no requested reviewer)"
        )
        head = pr.get("head", {})
        branch = head.get("ref", "(no branch name)")
        repo_name = head.get("repo", {}).get("full_name", "(no repo name)")
        created_at = pr.get("created_at", "")
        created_at_pretty = (
            print_timestamp(created_at) if created_at else "(no timestamp)"
        )
        message_text = f"\n\n\nPull request #{number} opened by {sender}\n{repo_name} / {branch}\n{title}\n\nCreated at {created_at_pretty}\nReview requested from {requested_reviewer}\n{HR_WAVY}\n{body}"
        return [Text(message_text), CutAndPrint()]
