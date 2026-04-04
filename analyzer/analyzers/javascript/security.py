from __future__ import annotations
import re
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    checks = [
        (r"\beval\s*\(", 25, "eval can execute arbitrary code."),
        (r"new Function\s*\(", 25, "new Function can execute arbitrary code."),
        (r"document\.write\s*\(", 15, "document.write is unsafe and brittle."),
        (r"innerHTML\s*=", 20, "innerHTML assignments can create XSS risk."),
    ]
    for pattern, impact, msg in checks:
        for _ in re.finditer(pattern, text):
            findings.append(RuleFinding("security", "high" if impact >= 20 else "medium", impact, msg))
    return findings
