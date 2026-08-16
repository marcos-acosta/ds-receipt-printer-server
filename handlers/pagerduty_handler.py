from nepso import CutAndPrint, Printable, Text
from handlers.webhook_body_handler import WebhookBodyHandler
from util import HR_STRAIGHT, pad_newlines, print_timestamp, strip_markdown_links


class PagerDutyHandler(WebhookBodyHandler):
    def generatePrintables(self, message: dict) -> list[Printable] | None:
        print(message, flush=True)
        event = message.get("event", {})
        data = event.get("data", {})
        title = data.get("title", "(no title)")
        assignees = data.get("assignees", [])
        assignee = (
            assignees[0].get("summary", "[?]") if len(assignees) else "(no assignee)"
        )
        urgency = data.get("urgency", "(no urgency)")
        service = data.get("service", {}).get("summary", "(no service)")
        occurred_at = event.get("occurred_at", "")
        occurred_at_pretty = (
            print_timestamp(occurred_at) if occurred_at else "(no timestamp)"
        )
        text = f"PAGERDUTY ALERT // {service}\n{title}\n{HR_STRAIGHT}\nTriggered at {occurred_at_pretty}\nAssigned to {assignee}\nUrgency: {urgency}"
        return [
            Text(pad_newlines(text, 8)),
            CutAndPrint(),
        ]
