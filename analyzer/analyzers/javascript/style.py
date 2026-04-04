from __future__ import annotations
import re
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    if re.search(r"function\s*\(", text):
        findings.append(RuleFinding("style", "low", 2, "Prefer named functions for readability when possible."))
    if "TODO" in text:
        findings.append(RuleFinding("style", "low", 2, "Resolve TODO markers or track them externally."))
    return findings
