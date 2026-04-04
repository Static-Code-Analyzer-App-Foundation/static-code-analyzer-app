from __future__ import annotations
import re
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    if re.search(r"\.map\s*\([^\)]*=>\s*<[^>]+\s+key\s*=\s*\{\s*index\s*\}", text, re.S):
        findings.append(RuleFinding("performance", "medium", 10, "Index as key can cause inefficient reconciliation."))
    if re.search(r"useEffect\s*\([^\)]*\)", text, re.S) and re.search(r"\[\s*\]", text):
        findings.append(RuleFinding("performance", "low", 4, "Check if useEffect should really run only once."))
    return findings
