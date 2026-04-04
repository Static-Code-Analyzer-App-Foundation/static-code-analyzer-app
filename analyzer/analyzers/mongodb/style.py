from __future__ import annotations
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    if "TODO" in text:
        findings.append(RuleFinding("style", "low", 2, "Resolve TODO markers in query files."))
    return findings
