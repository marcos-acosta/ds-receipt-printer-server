from datetime import datetime
from zoneinfo import ZoneInfo


def print_timestamp(iso: str) -> str:
    return (
        datetime.fromisoformat(iso)
        .astimezone(ZoneInfo("America/New_York"))
        .strftime("%B %d, %Y, %I:%M %p")
    )


def pad_newlines(text: str, target_lines: int) -> str:
    return text + "\n" * max(0, target_lines - 1 - text.count("\n"))
