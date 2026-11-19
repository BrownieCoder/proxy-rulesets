"""Check raw YAML payload characters without parsing or normalizing the text."""
from __future__ import annotations

import re


# YAML 1.2.2 section 5.1, production [1] c-printable. Check the complete
# source before splitlines/strip/comment filtering can hide a forbidden byte.
FORBIDDEN_CHARACTER = re.compile(
    r"[^\x09\x0A\x0D\x20-\x7E\x85\xA0-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]"
)


def validate_yaml_characters(text: str) -> None:
    """Reject raw characters outside YAML's printable set; preserve legal text."""
    match = FORBIDDEN_CHARACTER.search(text)
    if match is not None:
        raise ValueError(
            f"YAML payload contains a forbidden raw character U+{ord(match[0]):04X} "
            f"at character {match.start() + 1}"
        )
