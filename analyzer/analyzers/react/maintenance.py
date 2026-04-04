from __future__ import annotations
import re
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    if len(re.findall(r"useState\s*\(", text)) > 8:
        findings.append(RuleFinding("maintenance", "medium", 8, "Too many local states may indicate component sprawl."))
    if re.search(r"document\.querySelector|getElementById", text):
        findings.append(RuleFinding("maintenance", "medium", 8, "Direct DOM access fights React's model."))
    if len(text.splitlines()) > 450:
        findings.append(RuleFinding("maintenance", "medium", 8, "Very large React components are hard to maintain."))
    return findings
