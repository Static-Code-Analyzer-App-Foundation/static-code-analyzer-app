from __future__ import annotations
import re
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    if re.search(r"for\s*\([^\)]*;[^\)]*;[^\)]*\)\s*\{[\s\S]{0,160}?for\s*\(", text):
        findings.append(RuleFinding("efficiency", "medium", 10, "Nested loops may be costly on large data sets."))
    if re.search(r"setInterval\s*\(", text):
        findings.append(RuleFinding("efficiency", "low", 4, "Ensure timers are cleaned up to avoid leaks."))
    if re.search(r"JSON\.parse\(.*JSON\.stringify\(", text, re.S):
        findings.append(RuleFinding("efficiency", "low", 4, "Deep cloning via stringify/parse is expensive."))
    return findings
