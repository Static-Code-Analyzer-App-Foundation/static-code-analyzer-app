from __future__ import annotations
import re
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    if len(text.splitlines()) > 400:
        findings.append(RuleFinding("maintenance", "medium", 8, "Large Python files are harder to maintain."))
    for match in re.finditer(r"^\s*def\s+(\w+)\s*\([^\)]*\):", text, re.MULTILINE):
        name = match.group(1)
        if re.search(r"[A-Z-]", name):
            findings.append(RuleFinding("maintenance", "low", 6, f"Function name '{name}' is not snake_case."))
    if "print(" in text:
        findings.append(RuleFinding("maintenance", "low", 4, "Debug print statements should be removed or logged properly."))
    if re.search(r"^\s*except\s*:\s*$", text, re.MULTILINE):
        findings.append(RuleFinding("maintenance", "medium", 10, "Bare except blocks make debugging and recovery harder."))
    return findings
