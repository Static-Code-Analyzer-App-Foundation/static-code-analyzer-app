from __future__ import annotations
import re
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    if re.search(r"<img\b", text, re.I) and re.search(r"loading\s*=\s*['\"]lazy['\"]", text, re.I) is None:
        findings.append(RuleFinding("performance", "low", 3, "Consider lazy-loading images for better page performance."))
    if re.search(r"style\s*=\s*['\"]", text, re.I):
        findings.append(RuleFinding("performance", "low", 4, "Inline style attributes make caching and reuse less efficient."))
    return findings
