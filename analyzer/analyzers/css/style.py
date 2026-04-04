from __future__ import annotations
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    if "\t" in text:
        findings.append(RuleFinding("style", "low", 2, "Tabs in CSS can create inconsistent indentation."))
    if text.count("{") != text.count("}"):
        findings.append(RuleFinding("style", "high", 15, "Unbalanced braces suggest broken CSS syntax."))
    return findings
