from __future__ import annotations
import re
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    if "find(" in text or "aggregate(" in text:
        if "createIndex(" not in text:
            findings.append(RuleFinding("maintenance", "medium", 8, "Indexing intent is unclear; performance may degrade over time."))
    if len(text.splitlines()) > 200:
        findings.append(RuleFinding("maintenance", "low", 3, "Large query files are harder to review and maintain."))
    return findings
