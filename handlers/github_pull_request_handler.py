from nepso import CutAndPrint, Printable, Text
from handlers.webhook_body_handler import WebhookBodyHandler
from util import HR_WAVY, print_timestamp


class GitHubPullRequestHandler(WebhookBodyHandler):
    def generatePrintables(self, message: dict) -> list[Printable] | None:
        action = message.get("action", "")
        if action != "review_requested":
            return None
        number = message.get("number", "???")
        pr = message.get("pull_request", {})
        title = pr.get("title", "(no title)")
        sender = pr.get("user", {}).get("login", "(no sender)")
        body = pr.get("body", "(no body)")
        requested_reviewers = pr.get("requested_reviewers", [])
        reviewer_names = (
            ", ".join([r.get("login", "(no name)") for r in requested_reviewers])
            if requested_reviewers
            else "(no requested reviewers)"
        )
        head = pr.get("head", {})
        branch = head.get("ref", "(no branch name)")
        repo_name = head.get("repo", {}).get("full name", "(no repo name)")
        created_at = pr.get("created_at", "")
        created_at_pretty = (
            print_timestamp(created_at) if created_at else "(no timestamp)"
        )
        message_text = f"""
        Pull request #{number} opened by {sender}
        {repo_name} / {branch}
        {title}

        Created at {created_at_pretty}       
        Review requested from: {reviewer_names}
        {HR_WAVY}
        {body}
        """.strip()
        return [Text("\n\n\n" + message_text), CutAndPrint()]
