from __future__ import annotations
import re
from ...rules import RuleFinding

def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    if re.search(r"def\s+\w+\s*\([^\)]*=\s*\[[^\]]*\]", text):
        findings.append(RuleFinding("correctness", "high", 18, "Mutable list default argument can cause shared-state bugs."))
    if re.search(r"def\s+\w+\s*\([^\)]*=\s*\{[^\}]*\}", text):
        findings.append(RuleFinding("correctness", "high", 18, "Mutable dict default argument can cause shared-state bugs."))
    if "try:" in text and "except" in text and re.search(r"except\s+\w+\s+as\s+\w+:", text) is None:
        findings.append(RuleFinding("correctness", "medium", 8, "Exception handling should preserve useful error context."))
    if re.search(r"assert\s+.+", text):
        findings.append(RuleFinding("correctness", "low", 4, "assert is not a runtime validation strategy."))
    return findings
