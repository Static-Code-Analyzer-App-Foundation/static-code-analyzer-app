from __future__ import annotations
import re
from ...rules import RuleFinding

_SCRIPT_RE = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.I | re.S)
_STYLE_BLOCK_RE = re.compile(r"<style\b[^>]*>.*?</style>", re.I | re.S)
_STYLE_ATTR_RE = re.compile(r'\sstyle\s*=\s*(["\'])(.*?)\1', re.I | re.S)
_TARGET_BLANK_RE = re.compile(r'<a\b[^>]*target\s*=\s*["\']_blank["\'][^>]*>', re.I)
_HREF_RE = re.compile(r'<a\b[^>]*href\s*=\s*["\']([^"\']+)["\'][^>]*>', re.I)
_SECRET_RE = re.compile(
    r'(?i)\b(?:api[_-]?key|secret|token|bearer|password|passwd|private[_-]?key|client[_-]?secret)\b'
    r'[^<>\n]{0,80}(?:["\'][A-Za-z0-9_\-./=]{16,}["\']|:[^<>\n]{8,})'
)
_AWS_KEY_RE = re.compile(r'\bAKIA[0-9A-Z]{16}\b')
_GENERIC_TOKEN_RE = re.compile(r'\b[A-Za-z0-9+/]{32,}={0,2}\b')
_FORM_RE = re.compile(r'<form\b[^>]*>(.*?)</form>', re.I | re.S)
_INPUT_RE = re.compile(r'<(input|textarea|select|button)\b([^>]*)>', re.I | re.S)
_REL_NOOPENER_RE = re.compile(r'\brel\s*=\s*["\'][^"\']*\bnoopener\b[^"\']*["\']', re.I)

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    if re.search(r'\b(?:innerHTML|outerHTML|insertAdjacentHTML|document\.write)\b', text, re.I):
        findings.append(RuleFinding("security", "high", 24, "Unsafe DOM insertion can create XSS risk, especially with user-controlled data."))

    if re.search(r'\b(?:innerHTML|outerHTML|insertAdjacentHTML)\s*=\s*[^;\n]*(?:location\.|searchParams\.get|document\.cookie|localStorage\.|sessionStorage\.|\.value\b|prompt\s*\()', text, re.I):
        findings.append(RuleFinding("security", "high", 24, "User-controlled input appears to flow into DOM insertion without escaping or sanitization."))

    if _SCRIPT_RE.search(text) or _STYLE_BLOCK_RE.search(text) or _STYLE_ATTR_RE.search(text):
        findings.append(RuleFinding("security", "medium", 10, "Inline scripts or styles make a strong CSP much harder to adopt."))

    secret_hits = []
    if _SECRET_RE.search(text):
        secret_hits.append("possible secret/token label")
    if _AWS_KEY_RE.search(text):
        secret_hits.append("AWS access key pattern")
    if _GENERIC_TOKEN_RE.search(text) and re.search(r'(?i)\b(?:secret|token|key|bearer)\b', text):
        secret_hits.append("token-like value")
    if secret_hits:
        findings.append(RuleFinding("security", "high", 24, f"Possible sensitive data detected: {', '.join(secret_hits[:3])}."))

    for href in _HREF_RE.findall(text):
        href_l = href.lower()
        if href_l.startswith(("javascript:", "data:text/html", "vbscript:")):
            findings.append(RuleFinding("security", "high", 20, "Unsafe href value can trigger script execution or dangerous navigation."))
            break
        if re.search(r'[?&](?:redirect|returnurl|next|url|return|target)=', href_l):
            findings.append(RuleFinding("security", "medium", 8, "Possible open-redirect style link parameter detected."))
            break

    if _TARGET_BLANK_RE.search(text) and not _REL_NOOPENER_RE.search(text):
        findings.append(RuleFinding("security", "medium", 10, 'Links using target="_blank" should include rel="noopener noreferrer".'))

    for attrs, _body in _SCRIPT_RE.findall(text):
        src_match = re.search(r'\bsrc\s*=\s*["\']([^"\']+)["\']', attrs, re.I)
        if src_match:
            src = src_match.group(1)
            if re.match(r'(?i)https?://', src) and "integrity=" not in attrs.lower():
                findings.append(RuleFinding("security", "medium", 10, "External script is missing integrity metadata or trust control."))
                break

    for form_body in _FORM_RE.findall(text):
        inputs = list(_INPUT_RE.finditer(form_body))
        if not inputs:
            continue
        has_validation = any(re.search(r'\b(?:required|pattern|minlength|maxlength|type\s*=\s*["\'](?:email|url|number|tel|password)["\'])', m.group(2), re.I) for m in inputs)
        if not has_validation:
            findings.append(RuleFinding("security", "low", 6, "Form inputs have little visible client-side validation. Do not rely on frontend checks alone."))
            break

    return findings
