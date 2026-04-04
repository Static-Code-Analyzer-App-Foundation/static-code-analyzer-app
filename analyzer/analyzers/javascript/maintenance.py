from __future__ import annotations
import re
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    if "console.log(" in text:
        findings.append(RuleFinding("maintenance", "low", 3, "Remove debug console.log calls before release."))
    if re.search(r"\bvar\b", text):
        findings.append(RuleFinding("maintenance", "medium", 8, "Prefer let/const over var."))
    if re.search(r"==(?!=)", text) and "===" not in text:
        findings.append(RuleFinding("maintenance", "low", 3, "Use strict equality for predictable behavior."))
    if len(text.splitlines()) > 350:
        findings.append(RuleFinding("maintenance", "medium", 8, "Very large JS files are harder to maintain."))
    return findings
