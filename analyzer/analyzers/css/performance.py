from __future__ import annotations
import re
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    if re.search(r"\*\s*\{", text):
        findings.append(RuleFinding("performance", "low", 4, "Universal selector can be expensive on large pages."))
    if re.search(r"box-shadow\s*:[^;]+,[^;]+,[^;]+", text, re.I):
        findings.append(RuleFinding("performance", "low", 3, "Heavy shadow stacking can hurt rendering performance."))
    return findings
