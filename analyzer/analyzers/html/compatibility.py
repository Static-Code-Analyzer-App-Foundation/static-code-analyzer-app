from __future__ import annotations
import re
from ...rules import RuleFinding

_MODERN_JS_RE = [
    (re.compile(r'\?\.'), "Optional chaining may not be supported on older targets."),
    (re.compile(r'\?\?'), "Nullish coalescing may not be supported on older targets."),
    (re.compile(r'\b(?:fetch|Promise\.allSettled|queueMicrotask|IntersectionObserver|ResizeObserver|AbortController|crypto\.randomUUID|structuredClone|at)\b'), "Modern JavaScript APIs were detected and may need fallbacks."),
    (re.compile(r'\btype\s*=\s*["\']module["\']', re.I), "ES modules require modern browser support."),
]

_MODERN_CSS_RE = [
    (re.compile(r':has\('), ":has() is still not safe to assume across all target browsers."),
    (re.compile(r'\bclamp\s*\('), "clamp() may need fallback handling for older browsers."),
    (re.compile(r'\bbackdrop-filter\b', re.I), "backdrop-filter can be inconsistent across browsers."),
    (re.compile(r'\baspect-ratio\b', re.I), "aspect-ratio may need fallback layout rules."),
    (re.compile(r'\bscroll-snap-type\b', re.I), "scroll-snap behavior can vary across engines and needs testing."),
]

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    for pattern, message in _MODERN_JS_RE:
        if pattern.search(text):
            findings.append(RuleFinding("compatibility", "low", 4, message))

    css_text = "\n".join(re.findall(r"<style\b[^>]*>(.*?)</style>", text, re.I | re.S))
    css_text += "\n" + "\n".join(m.group(2) for m in re.finditer(r'\sstyle\s*=\s*(["\'])(.*?)\1', text, re.I | re.S))
    for pattern, message in _MODERN_CSS_RE:
        if pattern.search(css_text):
            findings.append(RuleFinding("compatibility", "low", 4, message))

    if re.search(r'\bposition\s*:\s*sticky\b', css_text, re.I):
        findings.append(RuleFinding("compatibility", "low", 4, "Sticky positioning should be tested carefully across target browsers."))

    if re.search(r'100vh', css_text, re.I):
        findings.append(RuleFinding("compatibility", "low", 4, "100vh can behave differently on mobile browser chrome; test carefully."))

    if re.search(r'-(webkit|moz|ms)-', css_text, re.I):
        findings.append(RuleFinding("compatibility", "low", 4, "Vendor-prefixed CSS is present; verify standard fallbacks exist."))

    return findings
