from __future__ import annotations
import re
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    if re.search(r"\$where\b", text):
        findings.append(RuleFinding("security", "high", 25, "$where can be unsafe and slow."))
    if re.search(r"db\.[^.]+\.find\s*\(\s*\{\s*\}\s*\)", text):
        findings.append(RuleFinding("security", "medium", 10, "Unfiltered find() queries can leak too much data or scan large collections."))
    return findings
