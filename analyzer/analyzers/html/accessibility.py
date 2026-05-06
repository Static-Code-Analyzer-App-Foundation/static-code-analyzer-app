from __future__ import annotations
import re
from ...rules import RuleFinding

_INPUT_RE = re.compile(r'<(input|textarea|select)\b([^>]*)>', re.I | re.S)
_ALT_RE = re.compile(r'<img\b[^>]*\balt\s*=\s*["\']([^"\']*)["\']', re.I)
_IMG_RE = re.compile(r'<img\b[^>]*>', re.I)
_INTERACTIVE_BAD_RE = re.compile(r'<(div|span)\b[^>]*\bon\w+\s*=\s*["\'][^"\']+["\'][^>]*>', re.I)
_ROLE_BUTTON_RE = re.compile(r'\brole\s*=\s*["\']button["\']', re.I)
_KEYHANDLER_RE = re.compile(r'\bon(?:keydown|keyup|keypress)\s*=', re.I)
_ARIA_RE = re.compile(r'\baria-[\w-]+\s*=', re.I)
_FOCUS_STYLE_RE = re.compile(r':focus(?:-visible)?\b', re.I)

def _labels_for_ids(text: str) -> set[str]:
    ids = set()
    for m in re.finditer(r'<label\b[^>]*\bfor\s*=\s*["\']([^"\']+)["\']', text, re.I):
        ids.add(m.group(1))
    return ids

def _element_id(attrs: str) -> str | None:
    m = re.search(r'\bid\s*=\s*["\']([^"\']+)["\']', attrs, re.I)
    return m.group(1) if m else None

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    imgs = _IMG_RE.findall(text)
    if imgs:
        for tag in imgs:
            alt = _ALT_RE.search(tag)
            if alt is None or not alt.group(1).strip():
                findings.append(RuleFinding("accessibility", "high", 16, "Image tag missing meaningful alt text."))
                break

    label_for_ids = _labels_for_ids(text)
    for tag_name, attrs in _INPUT_RE.findall(text):
        if tag_name.lower() == "input" and re.search(r'\btype\s*=\s*["\'](?:hidden|submit|button|reset|image)["\']', attrs, re.I):
            continue
        element_id = _element_id(attrs or "")
        has_aria = re.search(r'\b(?:aria-label|aria-labelledby)\s*=', attrs, re.I) is not None
        has_placeholder = re.search(r'\bplaceholder\s*=', attrs, re.I) is not None
        if not has_aria and not (element_id and element_id in label_for_ids) and not has_placeholder:
            findings.append(RuleFinding("accessibility", "high", 16, f"<{tag_name}> appears to lack an accessible label."))
            break

    if _INTERACTIVE_BAD_RE.search(text):
        findings.append(RuleFinding("accessibility", "medium", 10, "Clickable div/span patterns hurt keyboard and screen-reader support."))
    if _INTERACTIVE_BAD_RE.search(text) and not _KEYHANDLER_RE.search(text) and not _ROLE_BUTTON_RE.search(text):
        findings.append(RuleFinding("accessibility", "medium", 10, "JS-only interactions on generic elements need keyboard support and proper roles."))

    if _ARIA_RE.search(text) and not re.search(r'\b(role|aria-label|aria-labelledby|aria-describedby)\s*=', text, re.I):
        findings.append(RuleFinding("accessibility", "low", 4, "ARIA attributes are present, but usable labeling/role context is weak."))

    if re.search(r'<button\b|<a\b|<input\b|<select\b|<textarea\b', text, re.I) and _FOCUS_STYLE_RE.search(text) is None:
        findings.append(RuleFinding("accessibility", "low", 4, "No focus-visible styling was detected for interactive elements."))

    if re.search(r'<div\b[^>]*\bonclick\s*=', text, re.I) and not re.search(r'\brole\s*=\s*["\']button["\']', text, re.I):
        findings.append(RuleFinding("accessibility", "medium", 10, "Use a real <button> instead of a clickable <div>."))

    return findings
