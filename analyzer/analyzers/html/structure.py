from __future__ import annotations
import re
from collections import Counter
from ...rules import RuleFinding

_VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "source", "track", "wbr", "param"
}

_BLOCK_TAGS = {
    "address", "article", "aside", "blockquote", "body", "canvas", "dd",
    "div", "dl", "dt", "fieldset", "figcaption", "figure", "footer", "form",
    "h1", "h2", "h3", "h4", "h5", "h6", "header", "main", "nav", "ol", "p",
    "pre", "section", "table", "ul", "li"
}

_SEMANTIC_TAGS = {
    "header", "main", "nav", "section", "article", "aside", "footer",
    "form", "button", "label", "figure", "figcaption"
}

_INVALID_P_CHILDREN = {"div", "section", "article", "header", "footer", "main", "nav", "aside", "form", "ul", "ol", "table"}

_TOKEN_RE = re.compile(r"<!--.*?-->|<!DOCTYPE[^>]*>|<[^>]+>|[^<]+", re.I | re.S)
_TAG_RE = re.compile(r"<\s*(/)?\s*([a-zA-Z][\w:-]*)\b([^>]*)>", re.S)
_ID_RE = re.compile(r'\bid\s*=\s*["\']([^"\']+)["\']', re.I)
_META_CHARSET_RE = re.compile(r'<meta\b[^>]*charset\s*=', re.I)
_META_VIEWPORT_RE = re.compile(r'<meta\b[^>]*name\s*=\s*["\']viewport["\']', re.I)
_TITLE_RE = re.compile(r'<title\b[^>]*>.*?</title>', re.I | re.S)
_META_DESCRIPTION_RE = re.compile(r'<meta\b[^>]*name\s*=\s*["\']description["\']', re.I)
_EVENT_HANDLER_RE = re.compile(r'\son\w+\s*=\s*["\']', re.I)
_URL_RE = re.compile(r'https?://[^\s"\'>)]+', re.I)
_TEMPLATE_MARKERS = re.compile(r"\{\{.*?\}\}|\$\{.*?\}|<%.*?%>", re.S)

def _max_div_depth(text: str) -> int:
    depth = 0
    max_depth = 0
    for match in _TOKEN_RE.finditer(text):
        token = match.group(0)
        t = token.strip()
        if not t.startswith("<") or t.startswith("<!--") or t.startswith("<!"):
            continue
        m = _TAG_RE.match(t)
        if not m:
            continue
        closing, name = m.group(1), m.group(2).lower()
        self_closing = t.endswith("/>") or name in _VOID_TAGS

        if closing:
            if name == "div" and depth > 0:
                depth -= 1
            continue

        if name == "div":
            depth += 1
            max_depth = max(max_depth, depth)

        if self_closing:
            continue
    return max_depth

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    stack: list[str] = []
    for match in _TOKEN_RE.finditer(text):
        token = match.group(0)
        stripped = token.strip()
        if not stripped.startswith("<") or stripped.startswith("<!--") or stripped.startswith("<!"):
            continue
        m = _TAG_RE.match(stripped)
        if not m:
            continue
        closing, tag = m.group(1), m.group(2).lower()
        is_self_closing = stripped.endswith("/>") or tag in _VOID_TAGS

        if closing:
            if stack and stack[-1] == tag:
                stack.pop()
            elif tag in stack:
                findings.append(RuleFinding("structure", "medium", 10, f"Tag <{tag}> closes out of order or invalid nesting is likely present."))
                while stack and stack[-1] != tag:
                    stack.pop()
                if stack and stack[-1] == tag:
                    stack.pop()
            else:
                findings.append(RuleFinding("structure", "medium", 10, f"Unexpected closing tag </{tag}> found."))
            continue

        if stack and stack[-1] == "p" and tag in _INVALID_P_CHILDREN:
            findings.append(RuleFinding("structure", "medium", 10, f"Invalid child <{tag}> inside <p> can break layout and semantics."))

        if tag not in _VOID_TAGS and not is_self_closing:
            stack.append(tag)

    if stack:
        findings.append(RuleFinding("structure", "high", 14, f"Unclosed tags detected: {', '.join(stack[-3:])}."))

    ids = _ID_RE.findall(text)
    duplicate_ids = [item for item, count in Counter(ids).items() if count > 1]
    if duplicate_ids:
        findings.append(RuleFinding("structure", "high", 18, f"Duplicate id values found: {', '.join(duplicate_ids[:3])}."))

    max_div_depth = _max_div_depth(text)
    if max_div_depth >= 6:
        findings.append(RuleFinding("structure", "medium", 8, f"Deep div nesting detected (depth {max_div_depth}). This usually signals layout soup."))

    div_count = len(re.findall(r"<div\b", text, re.I))
    span_count = len(re.findall(r"<span\b", text, re.I))
    semantic_count = sum(len(re.findall(rf"<{tag}\b", text, re.I)) for tag in _SEMANTIC_TAGS)
    if (div_count + span_count) >= 18 and semantic_count <= 2:
        findings.append(RuleFinding("structure", "medium", 8, "Markup relies heavily on generic div/span tags instead of semantic structure."))

    html_tag = re.search(r"<html\b[^>]*>", text, re.I)
    if html_tag and not re.search(r"<html\b[^>]*\blang\s*=", html_tag.group(0), re.I):
        findings.append(RuleFinding("structure", "medium", 8, "HTML root should declare a lang attribute."))
    if not _META_CHARSET_RE.search(text):
        findings.append(RuleFinding("structure", "medium", 8, "Missing meta charset declaration."))
    if not _META_VIEWPORT_RE.search(text):
        findings.append(RuleFinding("structure", "medium", 8, "Missing viewport meta tag for responsive layout support."))
    if not _TITLE_RE.search(text):
        findings.append(RuleFinding("structure", "high", 14, "Missing <title> element."))
    if len(text) > 300 and not _META_DESCRIPTION_RE.search(text):
        findings.append(RuleFinding("structure", "low", 4, "Meta description is missing on a non-trivial page."))

    if _EVENT_HANDLER_RE.search(text):
        findings.append(RuleFinding("structure", "medium", 10, "Inline event handlers keep behavior inside markup and are hard to maintain."))

    urls = _URL_RE.findall(text)
    repeated_urls = [u for u, count in Counter(urls).items() if count >= 3]
    if repeated_urls:
        findings.append(RuleFinding("structure", "low", 4, "Repeated hardcoded URLs suggest duplicated content instead of reuse."))

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    template_markers = bool(_TEMPLATE_MARKERS.search(text))
    if lines and not template_markers:
        repeated_lines = [line for line, count in Counter(lines).items() if count >= 4 and len(line) > 12]
        if repeated_lines:
            findings.append(RuleFinding("structure", "low", 4, "Repeated hardcoded blocks appear throughout the page."))

    return findings
