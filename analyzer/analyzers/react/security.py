from __future__ import annotations
import re
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    if re.search(r"dangerouslySetInnerHTML", text):
        findings.append(RuleFinding("security", "high", 25, "dangerouslySetInnerHTML can expose XSS risk."))
    if re.search(r"eval\s*\(", text):
        findings.append(RuleFinding("security", "high", 20, "eval is unsafe in React code as well."))
    return findings
