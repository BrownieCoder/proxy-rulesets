"""Fail-closed syntax guard for new project-owned select-group templates.

This is deliberately not a general YAML parser. Every non-comment line must
belong to the supported type/proxies block grammar; complex/escaped keys,
anchors, tags, merge keys, flow mappings and unknown fields are rejected.
Existing application validators are not changed by importing this module.
"""
from __future__ import annotations

import re

_KEY = re.compile(r'''^    (type|proxies|'type'|'proxies'|"type"|"proxies")[ \t]*:(?:[ \t]+(.*)|[ \t]*)$''')
_SELECT = re.compile(r'''^(?:select|'select'|"select")(?:[ \t]+\#.*)?[ \t]*$''')
_MEMBER = re.compile(r'''^      - (?:DIRECT|REJECT(?:-DROP)?|PASS|"[^"\\\x00-\x1f]+")(?:[ \t]+\#.*)?[ \t]*$''')


def validate_select_group(block: str, error: str) -> None:
    """Validate a group's body after its canonical name line, without parsing private input."""
    seen: set[str] = set()
    in_proxies = False
    proxy_count = 0
    for number, line in enumerate(block.splitlines(), 1):
        if not line.strip(' ') or line.lstrip(' ').startswith('#'):
            continue
        key = _KEY.fullmatch(line)
        if key is not None:
            name = key[1].strip("'\"")
            value = key[2] or ''
            if name in seen:
                raise ValueError(f'{error}; duplicate {name} declaration')
            seen.add(name)
            in_proxies = name == 'proxies'
            if name == 'type' and _SELECT.fullmatch(value) is None:
                raise ValueError(f'{error}; expected a literal select type')
            if name == 'proxies' and value.strip():
                raise ValueError(f'{error}; proxies must use the simple block-list form')
        elif in_proxies and _MEMBER.fullmatch(line) is not None:
            proxy_count += 1
        else:
            raise ValueError(f'{error}; unsupported group YAML syntax on body line {number}')
    if seen != {'type', 'proxies'} or proxy_count == 0:
        raise ValueError(f'{error}; require one type, one proxies block and proxy members')
