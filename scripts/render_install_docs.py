"""Render the small, authored Markdown subset used by install guides; stdlib only."""
from __future__ import annotations
import html
import posixpath
import re
from urllib.parse import urlsplit


def heading_id(text: str) -> str:
    return re.sub(r'[^\w\- ]', '', text.lower()).replace(' ', '-')


def render(text: str, path: str, generated_pages: set[str]) -> str:
    """Fail closed on unsupported blocks instead of hiding guide content."""
    def destination(target: str) -> str:
        if urlsplit(target).scheme or target.startswith('#'):
            return target
        parts = target.split('#', 1)
        local = posixpath.normpath(posixpath.join(posixpath.dirname(path), parts[0]))
        suffix = ('#' + parts[1]) if len(parts) == 2 else ''
        if local in {'README.md', 'README.en.md'}:
            return posixpath.relpath('install/index.html', posixpath.dirname(path))
        if local in generated_pages:
            return parts[0][:-3] + '.html' + suffix
        if local.endswith('.md'):
            return 'https://github.com/BrownieCoder/proxy-rulesets/blob/main/' + local + suffix
        return target

    def inline(value: str) -> str:
        result = []
        pattern = r'(`[^`]+`|\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\))'
        for token in re.split(pattern, value):
            if token.startswith('`') and token.endswith('`'):
                result.append('<code>' + html.escape(token[1:-1]) + '</code>')
            elif token.startswith('**') and token.endswith('**'):
                result.append('<strong>' + html.escape(token[2:-2]) + '</strong>')
            elif token.startswith('[') and re.fullmatch(r'\[([^\]]+)\]\(([^)]+)\)', token):
                match = re.fullmatch(r'\[([^\]]+)\]\(([^)]+)\)', token)
                result.append('<a href="' + html.escape(destination(match[2]), quote=True) + '">' + html.escape(match[1]) + '</a>')
            else:
                result.append(html.escape(token))
        return ''.join(result)

    blocks = []
    paragraph = []
    code = None
    list_type = None

    def flush():
        if paragraph:
            blocks.append('<p>' + inline(' '.join(paragraph)) + '</p>')
            paragraph.clear()

    def close_list():
        nonlocal list_type
        if list_type:
            blocks.append('</' + list_type + '>')
            list_type = None

    for line in text.splitlines():
        if line.startswith('```'):
            flush(); close_list()
            if code is None:
                code = []
            else:
                blocks.append('<pre><code>' + html.escape('\n'.join(code)) + '</code></pre>')
                code = None
            continue
        if code is not None:
            code.append(line)
            continue
        if line.startswith('<!--'):
            continue
        if not line.strip():
            flush(); close_list(); continue
        heading = re.match(r'^(#{1,6}) (.+)$', line)
        item = re.match(r'^(\d+\. |\- )(.+)$', line)
        if heading:
            flush(); close_list()
            level, title = len(heading[1]), heading[2]
            blocks.append(f'<h{level} id="{heading_id(title)}">{inline(title)}</h{level}>')
        elif item:
            flush()
            desired = 'ul' if item[1] == '- ' else 'ol'
            if list_type != desired:
                close_list(); blocks.append('<' + desired + '>'); list_type = desired
            blocks.append('<li>' + inline(item[2]) + '</li>')
        else:
            if line.startswith(('|', '>')):
                raise ValueError(f'Unsupported guide block in {path}: {line[:30]}')
            close_list(); paragraph.append(line)
    if code is not None:
        raise ValueError('Unclosed guide code block')
    flush(); close_list()
    title = next((l[2:] for l in text.splitlines() if l.startswith('# ')), '安装教程')
    home = posixpath.relpath('install/index.html', posixpath.dirname(path))
    return f'''<!doctype html>
<!-- Generated from {path}; do not edit. -->
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · Proxy Rulesets</title>
<style>body{{margin:0;background:#f6f7f2;color:#1c3029;font:17px/1.8 system-ui,-apple-system,sans-serif}}main{{max-width:850px;margin:auto;padding:32px 22px 80px}}a{{color:#146846;overflow-wrap:anywhere}}h1{{font-size:2rem;line-height:1.3}}h2{{margin-top:2.2em;border-top:1px solid #ccd7ce;padding-top:1em}}pre{{overflow:auto;background:#e8eee7;padding:18px;border-radius:8px;font-size:14px}}code{{background:#e8eee7;overflow-wrap:anywhere}}li{{margin:10px 0}}:focus-visible{{outline:3px solid #b66c20;outline-offset:4px}}header{{font-size:14px;margin-bottom:32px}}</style></head>
<body><main><header><a href="{home}">← 返回安装中心</a></header>{''.join(blocks)}</main></body></html>\n'''
