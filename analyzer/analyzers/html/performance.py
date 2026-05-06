from __future__ import annotations
import re
from ...rules import RuleFinding

_SCRIPT_RE = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.I | re.S)
_STYLE_RE = re.compile(r"<style\b[^>]*>(.*?)</style>", re.I | re.S)
_DATA_URI_RE = re.compile(r'data:[^"\']+;base64,[A-Za-z0-9+/=]{200,}', re.I)
_DOM_QUERY_RE = re.compile(r'\b(?:querySelectorAll?|getElementById|getElementsByClassName|getElementsByTagName)\s*\(')
_LOOP_RE = re.compile(r'\b(for|while)\s*\(')
_LISTENER_RE = re.compile(r'\.addEventListener\s*\(')
_LAYOUT_READ_RE = re.compile(r'\b(?:offsetWidth|offsetHeight|clientWidth|clientHeight|getBoundingClientRect|scrollWidth|scrollHeight)\b')
_LAYOUT_WRITE_RE = re.compile(r'\b(?:style\.[A-Za-z_$][\w$]*\s*=|classList\.(?:add|remove|toggle))')
_DEFERLESS_SCRIPT_RE = re.compile(r'<script\b(?![^>]*\bdefer\b)(?![^>]*\basync\b)(?![^>]*\btype\s*=\s*["\']module["\'])[^>]*src\s*=\s*["\'][^"\']+["\'][^>]*>', re.I)
_HEAD_SCRIPT_RE = re.compile(r'<head\b.*?<script\b', re.I | re.S)

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    scripts = _SCRIPT_RE.findall(text)
    styles = _STYLE_RE.findall(text)
    script_text = "\n".join(body for _attrs, body in scripts)
    style_text = "\n".join(styles)

    if _DATA_URI_RE.search(text):
        findings.append(RuleFinding("performance", "medium", 8, "Large base64 assets are embedded directly in the page."))

    if len(script_text) > 2000:
        findings.append(RuleFinding("performance", "medium", 8, "Large inline JavaScript increases initial load cost."))

    if len(style_text) > 2000:
        findings.append(RuleFinding("performance", "medium", 8, "Large inline CSS increases initial load cost."))

    if _DOM_QUERY_RE.findall(script_text) and _LOOP_RE.search(script_text):
        findings.append(RuleFinding("performance", "medium", 8, "DOM queries inside loops can create unnecessary work and reflows."))

    if len(_LISTENER_RE.findall(script_text)) >= 8:
        findings.append(RuleFinding("performance", "low", 4, "Many per-element listeners may be better handled with delegation."))

    if _LAYOUT_READ_RE.search(script_text) and _LAYOUT_WRITE_RE.search(script_text):
        findings.append(RuleFinding("performance", "medium", 8, "Mixed layout reads and writes can trigger repeated reflow/repaint cycles."))

    if _HEAD_SCRIPT_RE.search(text) and _DEFERLESS_SCRIPT_RE.search(text):
        findings.append(RuleFinding("performance", "medium", 8, "Render-blocking scripts are present in the document head."))

    if re.search(r'<img\b[^>]*>', text, re.I) and re.search(r'\bloading\s*=\s*["\']lazy["\']', text, re.I) is None and len(re.findall(r'<img\b', text, re.I)) >= 3:
        findings.append(RuleFinding("performance", "low", 4, "Consider lazy-loading images to reduce initial page cost."))

    return findings
