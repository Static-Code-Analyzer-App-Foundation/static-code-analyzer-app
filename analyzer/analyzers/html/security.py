from __future__ import annotations
import re
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    if re.search(r"<script[^>]*>\s*[^<]*document\.write", text, re.I | re.S):
        findings.append(RuleFinding("security", "high", 22, "document.write can create XSS risk."))
    if re.search(r"on\w+\s*=", text, re.I):
        findings.append(RuleFinding("security", "medium", 10, "Inline event handlers are harder to secure and audit."))
    if re.search(r"href\s*=\s*['\"]javascript:", text, re.I):
        findings.append(RuleFinding("security", "high", 20, "javascript: URLs can introduce XSS or unsafe navigation."))
    return findings

