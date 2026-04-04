from __future__ import annotations
import re
from collections import Counter
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    if len(text.splitlines()) > 300:
        findings.append(RuleFinding("maintenance", "medium", 8, "Very large CSS files become harder to maintain."))
    props = re.findall(r"\b([a-z-]+)\s*:\s*[^;]+;", text, re.I)
    repeated = [prop for prop, count in Counter(props).items() if count > 8]
    if repeated:
        findings.append(RuleFinding("maintenance", "low", 4, f"Repeated properties detected: {', '.join(sorted(repeated)[:3])}."))
    if re.search(r"#[^\s{]+\s+#[^\s{]+\s+#[^\s{]+", text):
        findings.append(RuleFinding("maintenance", "medium", 8, "Deep selector chains reduce maintainability."))
    return findings
