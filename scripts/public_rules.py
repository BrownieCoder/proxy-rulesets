"""Read only the repository-owned config/rules.yaml template, not general YAML.

The accepted block mapping/list grammar is deliberately small and fail-closed.
Rule kinds, fields, targets and first-match precedence remain semantic checks in
the existing validators; this module establishes the actual string sequence.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path


def parse_routing_rules(text: str) -> list[str]:
    """Require one literal top-level rules key and a nonempty block string list."""
    text = text.replace("\r\n", "\n")
    if any(char != "\n" and (unicodedata.category(char).startswith("C")
                              or unicodedata.category(char) in {"Zl", "Zp"})
           for char in text):
        raise ValueError("Public config/rules.yaml forbids tabs and control characters")
    rules: list[str] = []
    seen_header = False
    indentation: str | None = None

    def invalid(number: int, reason: str) -> ValueError:
        return ValueError(f"Public config/rules.yaml line {number}: {reason}")

    for number, raw in enumerate(text.split("\n"), 1):
        if not raw.strip(" ") or raw.lstrip(" ").startswith("#"):
            continue
        if raw.rstrip(" ") == "rules:":
            if seen_header:
                raise invalid(number, "require exactly one top-level rules key")
            seen_header = True
            continue
        entry = re.fullmatch(r"( *)- (\S(?:.*\S)?) *", raw)
        if not seen_header or entry is None:
            raise invalid(number, "expected one rules mapping with block scalar entries")
        if indentation is None:
            indentation = entry[1]
        elif entry[1] != indentation:
            raise invalid(number, "inconsistent rules sequence indentation")
        value = entry[2]
        if value[0] in {"'", '"'}:
            quote = value[0]
            if len(value) < 2 or value[-1] != quote:
                raise invalid(number, "unbalanced rule scalar quotes")
            value = value[1:-1]
            if not value or quote in value or "\\" in value:
                raise invalid(number, "expected a nonempty literal quoted string without escapes")
        else:
            # Comma-separated routing literals cannot acquire YAML implicit
            # bool/null/number types. Bare uppercase rule kinds are kept so the
            # existing semantic gate, not this structural reader, reports them.
            if (re.fullmatch(r"[A-Z][A-Z0-9-]*(?:,.*)?", value) is None
                    or value in {"TRUE", "FALSE", "YES", "NO", "ON", "OFF", "NULL"}
                    or any(char in value for char in "'\"\\#[]{}")
                    or re.search(r":(?: |$)", value)):
                raise invalid(number, "expected a literal routing string, without inline YAML syntax")
        if any(field != field.strip(" ") for field in value.split(",")):
            raise invalid(number, "routing fields must not have leading or trailing ASCII spaces")
        rules.append(value)
    if not seen_header or not rules:
        raise ValueError("Public config/rules.yaml requires one rules key and a nonempty string list")
    return rules


def read_routing_rules(path: Path) -> list[str]:
    """Read a public routing template explicitly as UTF-8."""
    return parse_routing_rules(path.read_text(encoding="utf-8"))
