from __future__ import annotations
import re
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    if re.search(r"aggregate\s*\(\s*\[", text) and "$match" not in text:
        findings.append(RuleFinding("performance", "medium", 8, "Aggregation pipelines should usually filter early with $match."))
    if re.search(r"find\s*\([^\)]*\)\s*\.sort\s*\(", text):
        findings.append(RuleFinding("performance", "low", 4, "Sort operations should be supported by indexes where possible."))
    if "find(" in text and ".limit(" not in text:
        findings.append(RuleFinding("performance", "low", 4, "Consider limit() for bounded reads when appropriate."))
    return findings
