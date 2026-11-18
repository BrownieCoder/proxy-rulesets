"""Strict stdlib model reader for the public policy template, not general YAML."""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

GroupValue = str | bool | int | list[str]
STRING_FIELDS = {'name', 'type', 'exclude-type', 'url', 'filter', 'empty-fallback'}
BOOL_FIELDS = {'include-all', 'lazy'}
INT_FIELDS = {'interval', 'timeout', 'tolerance', 'expected-status'}
FIELDS = STRING_FIELDS | BOOL_FIELDS | INT_FIELDS | {'proxies'}
_MAPPING = re.compile(r'''([a-z][a-z0-9-]*|'[a-z][a-z0-9-]*'|"[a-z][a-z0-9-]*") *:(?: +(.*)| *)''')
_PLAIN = re.compile(r'[A-Za-z_][A-Za-z0-9_.#-]*')
_INTEGER = re.compile(r'-?(?:0|[1-9][0-9]*)')


def parse_policy_group_model(text: str) -> list[dict[str, GroupValue]]:
    """Read one nonempty mapping list at canonical 2/4/6-space block levels."""
    text = text.replace('\r\n', '\n')
    if any(char != '\n' and (unicodedata.category(char).startswith('C')
                              or unicodedata.category(char) in {'Zl', 'Zp'})
           for char in text):
        raise ValueError('Public config/proxy-groups.yaml forbids tabs and control characters')
    groups: list[dict[str, GroupValue]] = []
    names: set[str] = set()
    current: dict[str, GroupValue] | None = None
    active_field: str | None = None
    seen_root = False

    def error(number: int, reason: str) -> ValueError:
        return ValueError(f'Public config/proxy-groups.yaml line {number}: {reason}')

    def uncomment(value: str, number: int) -> str:
        quote = None
        for index, char in enumerate(value):
            if quote is not None:
                if char == quote:
                    quote = None
            elif char in {'"', "'"}:
                quote = char
            elif char == '#' and (index == 0 or value[index - 1] == ' '):
                return value[:index].rstrip(' ')
        if quote is not None:
            raise error(number, 'unbalanced scalar quotes')
        return value.rstrip(' ')

    def mapping(value: str, number: int) -> tuple[str, str]:
        match = _MAPPING.fullmatch(value)
        if match is None:
            raise error(number, 'expected a literal mapping key with a separated value')
        return match[1].strip("'\""), uncomment(match[2] or '', number)

    def literal(value: str, number: int) -> str | int | bool:
        if not value:
            raise error(number, 'null or missing scalar value is unsupported')
        if value[0] in {'"', "'"}:
            quote = value[0]
            if len(value) < 2 or value[-1] != quote or quote in value[1:-1] or '\\' in value:
                raise error(number, 'expected an unescaped whole quoted literal')
            return value[1:-1]  # YAML preserves spaces inside the quotes.
        if value in {'true', 'false'}:
            return value == 'true'
        if _INTEGER.fullmatch(value):
            return int(value)
        if (value.endswith(':') or value.lower() in {'true', 'false', 'yes', 'no', 'on', 'off', 'null'}
                or not (_PLAIN.fullmatch(value)
                        or re.fullmatch(r'''https?://[^\s'"\\\[\]{}]+''', value))):
            raise error(number, 'unsupported scalar syntax or implicit YAML type')
        return value

    def string(value: str, number: int) -> str:
        result = literal(value, number)
        if not isinstance(result, str) or not result:
            raise error(number, 'expected a nonempty literal string')
        return result

    def finish(number: int) -> None:
        if current is None:
            return
        if 'name' not in current:
            raise error(number, 'group mapping requires one name string')
        name = current['name']
        if name in names:
            raise error(number, f'defines duplicate group: {name}')
        if 'proxies' in current and not current['proxies']:
            raise error(number, 'proxies must be a nonempty block string list, not null')
        names.add(name)
        groups.append(current)

    def field(value: str, number: int) -> None:
        nonlocal active_field
        # Called only after creating a group or checking that one exists.
        assert current is not None
        key, raw_value = mapping(value, number)
        if key not in FIELDS:
            raise error(number, f'unsupported group field: {key}')
        if key in current:
            raise error(number, f'duplicate group field: {key}')
        active_field = key
        if key == 'proxies':
            if raw_value:
                raise error(number, 'proxies requires a block string list, not a scalar or flow value')
            current[key] = []
        elif key in STRING_FIELDS:
            current[key] = string(raw_value, number)
        else:
            result = literal(raw_value, number)
            expected = bool if key in BOOL_FIELDS else int
            if type(result) is not expected:
                raise error(number, f'{key} requires a literal {expected.__name__} value')
            current[key] = result

    for number, raw in enumerate(text.split('\n'), 1):
        if not raw.strip(' ') or raw.lstrip(' ').startswith('#'):
            continue
        if not raw.startswith(' '):
            key, value = mapping(raw, number)
            if key != 'proxy-groups' or value:
                raise error(number, 'require only the proxy-groups block-list root')
            if seen_root:
                raise error(number, 'require exactly one proxy-groups root')
            seen_root = True
            continue
        if not seen_root:
            raise error(number, 'group entries must follow the proxy-groups root')
        if raw.startswith('  - '):
            finish(number)
            current = {}
            active_field = None
            field(raw[4:], number)
        elif raw.startswith('      - '):
            if current is None or active_field != 'proxies':
                raise error(number, 'proxy member must be inside its group proxies list')
            current['proxies'].append(string(uncomment(raw[8:], number), number))
        elif raw.startswith('    ') and not raw.startswith('     '):
            if current is None:
                raise error(number, 'group fields require a preceding mapping-list entry')
            field(raw[4:], number)
        else:
            raise error(number, 'unsupported group/list nesting or indentation')
    finish(len(text.split('\n')))
    if not seen_root or not groups:
        raise ValueError('Public config/proxy-groups.yaml requires one root and a nonempty group mapping list')
    return groups


def read_policy_group_model(path: Path) -> list[dict[str, GroupValue]]:
    """Read only a public project template, explicitly as UTF-8."""
    return parse_policy_group_model(path.read_text(encoding='utf-8'))
