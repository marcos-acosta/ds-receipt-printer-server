import hashlib
import hmac
import os
from collections.abc import Sequence
from datetime import datetime
from zoneinfo import ZoneInfo
import re
from collections import OrderedDict

PRINTER_CHAR_WIDTH = 48
HR_WAVY = "~" * PRINTER_CHAR_WIDTH
HR_STRAIGHT = "-" * PRINTER_CHAR_WIDTH


class BoundedDict(OrderedDict):
    def __init__(self, *args, maxsize=128, **kwargs):
        self.maxsize = maxsize
        super().__init__(*args, **kwargs)
        self._evict()

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._evict()

    def _evict(self):
        while len(self) > self.maxsize:
            self.popitem(last=False)


_MD_LINK = re.compile(
    r"""
    (?<!!)                                      # do not touch images
    \[([^\[\]]*)\]                              # the display text
    \(\s*
        (?:<[^<>]*>|[^()\s]*)                   # the target, bare or in < >
        (?:\s+(?:"[^"]*"|'[^']*'|\([^()]*\)))?  # an optional title
    \s*\)
    """,
    re.VERBOSE,
)


def strip_markdown_links(text: str) -> str:
    return _MD_LINK.sub(r"\1", text)


def read_secrets(*variables: str) -> list[str]:
    secrets = []
    for variable in variables:
        secret = os.environ.get(variable, "").strip()
        if not secret:
            raise RuntimeError(
                f"{variable} is not set. Put it in the .env file before you start the server."
            )
        secrets.append(secret)
    return secrets


def parse_signatures(header_value: str) -> list[str]:
    """Read a bare digest or a list such as "v1=<hex>,v1=<hex>"."""
    signatures = []
    for part in header_value.split(","):
        part = part.strip()
        if not part:
            continue
        _, _, digest = part.rpartition("=")
        signatures.append(digest.lower())
    return signatures


def expected_digests(body: bytes, secrets: Sequence[str]) -> list[str]:
    return [
        hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        for secret in secrets
    ]


def signature_matches(body: bytes, header_value: str, secrets: Sequence[str]) -> bool:
    given = parse_signatures(header_value)
    if not given:
        return False

    expected = expected_digests(body, secrets)
    return any(
        hmac.compare_digest(candidate, digest)
        for digest in given
        for candidate in expected
    )


def print_timestamp(iso: str) -> str:
    return (
        datetime.fromisoformat(iso)
        .astimezone(ZoneInfo("America/New_York"))
        .strftime("%B %d, %Y, %I:%M %p")
    )


def print_timestamp_epoch(ts: float) -> str:
    return (
        datetime.fromtimestamp(ts)
        .astimezone(ZoneInfo("America/New_York"))
        .strftime("%B %d, %Y, %I:%M %p")
    )


def pad_newlines(text: str, target_lines: int) -> str:
    return text + "\n" * max(0, target_lines - 1 - text.count("\n"))


def hard_wrap(text: str, width: int) -> list[str]:
    """Break text into lines of at most `width` characters.

    Existing newlines start a new line. Words are not kept whole.
    """
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        lines.extend(paragraph[i : i + width] for i in range(0, len(paragraph), width))
    return lines


def truncate_to_lines(
    text: str, max_lines: int, width: int = PRINTER_CHAR_WIDTH, ellipsis: str = "..."
) -> str:
    """Cut text so that it occupies at most `max_lines` lines of `width` characters.

    The ellipsis replaces the tail of the last line, so the result never goes
    over the budget.
    """
    if max_lines <= 0 or width <= 0:
        return ""

    lines = hard_wrap(text, width)
    if len(lines) <= max_lines:
        return "\n".join(lines)

    kept = lines[:max_lines]
    if len(ellipsis) >= width:
        kept[-1] = ellipsis[:width]
    else:
        kept[-1] = kept[-1][: width - len(ellipsis)].rstrip() + ellipsis
    return "\n".join(kept)
