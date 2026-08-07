from nepso import CutAndPrint, Printable, Text
from handlers.webhook_body_handler import WebhookBodyHandler
from util import HR_WAVY, pad_newlines, print_timestamp, strip_markdown_links


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
        description = strip_markdown_links(data.get("description", "(no description)"))
        identifier = data.get("identifier", "(no identifier)")
        text = f"\n\n\n{identifier}\n{title}\n{HR_WAVY}\nEstimate: {estimate_pretty} point(s)\nAssigned to {assignee}\nCreated by {author}\nCreated at {created_at_pretty}\n{HR_WAVY}\n{description}\n\n\n\n"
        return [Text(pad_newlines(text, 8)), CutAndPrint()]
