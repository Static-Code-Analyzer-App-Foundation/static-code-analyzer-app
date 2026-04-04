from __future__ import annotations
import re
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    if re.search(r"expression\s*\(", text, re.I):
        findings.append(RuleFinding("security", "high", 20, "CSS expression() is unsafe and obsolete."))
    if re.search(r"url\s*\(\s*['\"]?javascript:", text, re.I):
        findings.append(RuleFinding("security", "high", 20, "javascript: URLs inside CSS are unsafe."))
    if "!important" in text:
        findings.append(RuleFinding("security", "medium", 6, "Overuse of !important can create hard-to-control style overrides."))
    return findings
