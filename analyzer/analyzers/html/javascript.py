from __future__ import annotations
import re
from collections import Counter
from ...rules import RuleFinding

_SCRIPT_RE = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.I | re.S)
_QUERY_RE = re.compile(r'\b(?:document\.querySelectorAll?|getElementById|getElementsByClassName|getElementsByTagName)\s*\(')
_ADD_LISTENER_RE = re.compile(r'\.addEventListener\s*\(')
_GLOBAL_ASSIGN_RE = re.compile(r'\b(?:window|globalThis|self)\s*\.\s*([A-Za-z_$][\w$]*)\s*=')
_INNER_HTML_RE = re.compile(r'\b(?:innerHTML|outerHTML|insertAdjacentHTML|document\.write)\b')
_FETCH_RE = re.compile(r'\bfetch\s*\(')
_ASYNC_FN_RE = re.compile(r'\basync\s+function\b|\basync\s*\(')
_TRY_RE = re.compile(r'\btry\s*\{')
_CATCH_RE = re.compile(r'\bcatch\b')

def _script_bodies(text: str) -> list[str]:
    return [body for _attrs, body in _SCRIPT_RE.findall(text)]

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    scripts = _script_bodies(text)
    if not scripts:
        return findings

    script_text = "\n".join(scripts)
    script_blocks = len(scripts)
    script_size = len(script_text)

    if script_blocks >= 2 or script_size > 3000:
        findings.append(RuleFinding("script", "medium", 8, "Inline scripts are large enough to deserve real module boundaries."))

    query_count = len(_QUERY_RE.findall(script_text))
    listener_count = len(_ADD_LISTENER_RE.findall(script_text))
    if query_count >= 8 and listener_count >= 4:
        findings.append(RuleFinding("script", "medium", 8, "DOM querying and listener wiring are scattered instead of being centralized."))

    globals_found = _GLOBAL_ASSIGN_RE.findall(script_text)
    if globals_found:
        findings.append(RuleFinding("script", "medium", 8, f"Global state is leaking onto the page: {', '.join(sorted(set(globals_found))[:3])}."))

    lines = [line.strip() for line in script_text.splitlines() if line.strip()]
    repeated_lines = [line for line, count in Counter(lines).items() if count >= 4 and len(line) > 20]
    if repeated_lines:
        findings.append(RuleFinding("script", "low", 4, "Repeated JavaScript statements suggest missing helper functions."))

    if query_count >= 4 and re.search(r'\.(?:style|classList|dataset)\b', script_text):
        findings.append(RuleFinding("script", "low", 4, "JavaScript is tightly coupled to specific markup and presentation details."))

    dom_vars = re.findall(r'\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:document\.querySelector(?:All)?|document\.getElementById|document\.getElementsByClassName|document\.getElementsByTagName)\s*\(', script_text)
    for var_name in dom_vars[:8]:
        used = re.search(rf'\b{re.escape(var_name)}\s*\.\s*(?:addEventListener|classList|style|value|textContent|innerHTML|setAttribute)\b', script_text) is not None
        has_guard = re.search(rf'\bif\s*\(\s*{re.escape(var_name)}\s*\)', script_text) is not None
        if used and not has_guard:
            findings.append(RuleFinding("script", "medium", 10, f"Possible missing null check before using '{var_name}'."))
            break

    if _INNER_HTML_RE.search(script_text):
        findings.append(RuleFinding("security", "high", 22, "Unsafe DOM insertion detected through innerHTML/document.write/insertAdjacentHTML."))

    if re.search(r'\bXMLHttpRequest\s*\([^)]*,\s*false\s*\)', script_text) or re.search(r'\bwhile\s*\(\s*true\s*\)', script_text):
        findings.append(RuleFinding("performance", "high", 16, "Synchronous or endless blocking logic can freeze the UI."))

    if re.search(r'\b(for|while)\s*\(', script_text) and query_count >= 2 and re.search(r'\bgetBoundingClientRect|offsetWidth|offsetHeight|clientWidth|clientHeight\b', script_text):
        findings.append(RuleFinding("performance", "medium", 8, "DOM reads inside loops can trigger unnecessary reflow/repaint work."))

    if (_FETCH_RE.search(script_text) or _ASYNC_FN_RE.search(script_text)) and _CATCH_RE.search(script_text) is None and _TRY_RE.search(script_text) is None:
        findings.append(RuleFinding("maintenance", "medium", 8, "Async logic lacks visible error handling around fetch/parsing/event flow."))

    if script_blocks and script_size > 1000 and re.search(r'<head\b', text, re.I) and re.search(r'<script\b(?![^>]*\bdefer\b)(?![^>]*\basync\b)(?![^>]*\btype\s*=\s*["\']module["\'])', text, re.I):
        findings.append(RuleFinding("performance", "medium", 8, "Large blocking scripts appear to run before the DOM is ready."))

    if listener_count >= 8 and re.search(r'\bquerySelectorAll\s*\(', script_text):
        findings.append(RuleFinding("performance", "low", 4, "Many individual event listeners could likely be replaced by delegation."))

    return findings
