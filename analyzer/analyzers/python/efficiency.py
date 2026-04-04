from __future__ import annotations
import re
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    patterns = [
        (r"for\s+\w+\s+in\s+range\([^)]+\):\s*(?:\n|.){0,120}?for\s+\w+\s+in\s+range", "Nested loops may create quadratic cost.", 12),
        (r"\w+\s*=\s*\w+\s*\+\s*\[", "List concatenation in a loop can be slow; prefer append/extend.", 10),
        (r"\btime\.sleep\s*\(", "Sleep calls can block execution and reduce throughput.", 5),
        (r"\bopen\s*\(", "Repeated file opening can be expensive when used in hot paths.", 5),
    ]
    for pattern, message, impact in patterns:
        for _ in re.finditer(pattern, text):
            findings.append(RuleFinding("efficiency", "medium", impact, message))
    return findings
