from nepso import CutAndPrint, Printable, Text
from handlers.webhook_body_handler import WebhookBodyHandler
from util import pad_newlines, print_timestamp


class LinearHandler(WebhookBodyHandler):
    def generatePrintables(self, message: dict) -> list[Printable] | None:
        action = message.get("action", "")
        data = message.get("data", {})
        assignee = data.get("assignee", {}).get("name")
        was_reassigned = action == "update" and "assigneeId" in message.get(
            "updatedFrom", {}
        )
        was_created = action == "create"
        should_process = (was_reassigned or was_created) and assignee is not None
        if not should_process:
            return None
        author = message.get("actor", {}).get("name", "(no author)")
        created_at = data.get("createdAt", "")
        created_at_pretty = (
            print_timestamp(created_at) if created_at else "(no timestamp)"
        )
        title = data.get("title", "(no title)")
        estimate = data.get("estimate", 0)
        estimate_pretty = estimate if estimate else "[?]"
        description = data.get("description", "(no description)")
        identifier = data.get("identifier", "(no identifier)")
        text = f"{identifier} :: assigned to {assignee} :: {estimate_pretty} point(s)\n{title}\n---\nCreated by {author} at {created_at_pretty}\n---\n{description}"
        return [Text(pad_newlines(text, 8)), CutAndPrint()]
