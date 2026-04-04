from __future__ import annotations
import re
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    if re.search(r"<img\b[^>]*>", text, re.I) and not re.search(r"alt\s*=", text, re.I):
        findings.append(RuleFinding("style", "medium", 6, "React images should include alt text."))
    return findings
