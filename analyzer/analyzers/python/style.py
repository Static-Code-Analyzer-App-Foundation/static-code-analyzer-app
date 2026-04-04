from __future__ import annotations
import re
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    for line in text.splitlines():
        if len(line) > 88:
            findings.append(RuleFinding("style", "low", 2, "Line exceeds 88 characters."))
            break
    if re.search(r"\bimport\s+\*", text):
        findings.append(RuleFinding("style", "medium", 8, "Wildcard imports reduce clarity and can cause namespace collisions."))
    return findings
