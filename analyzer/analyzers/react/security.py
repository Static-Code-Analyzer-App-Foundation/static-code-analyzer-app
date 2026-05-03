from __future__ import annotations

import re
from ...rules import RuleFinding


def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    if re.search(r"\bdangerouslySetInnerHTML\b", text):
        findings.append(
            RuleFinding(
                "security",
                "high",
                25,
                "dangerouslySetInnerHTML can expose XSS risk.",
            )
        )

    if re.search(r"(?<![\w$])(?:innerHTML|outerHTML)\s*=", text):
        findings.append(
            RuleFinding(
                "security",
                "high",
                22,
                "Direct HTML injection through innerHTML/outerHTML is unsafe.",
            )
        )

    if re.search(r"\bdocument\.write\s*\(", text):
        findings.append(
            RuleFinding(
                "security",
                "high",
                18,
                "document.write is unsafe in modern React apps.",
            )
        )

    if re.search(r"\beval\s*\(", text) or re.search(r"\bnew\s+Function\s*\(", text):
        findings.append(
            RuleFinding(
                "security",
                "high",
                20,
                "Dynamic code execution is unsafe here.",
            )
        )

    return findings
