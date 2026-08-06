import hashlib
import hmac
import os
from collections.abc import Sequence
from datetime import datetime
from zoneinfo import ZoneInfo
import re

PRINTER_CHAR_WIDTH = 48
HR_WAVY = "~" * PRINTER_CHAR_WIDTH
HR_STRAIGHT = "-" * PRINTER_CHAR_WIDTH

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


def pad_newlines(text: str, target_lines: int) -> str:
    return text + "\n" * max(0, target_lines - 1 - text.count("\n"))
