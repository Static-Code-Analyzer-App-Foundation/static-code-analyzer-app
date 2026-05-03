from __future__ import annotations

import re
from ...rules import RuleFinding


def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    if len(re.findall(r"\buseState\s*\(", text)) > 8:
        findings.append(
            RuleFinding(
                "maintenance",
                "medium",
                8,
                "Too many local states may indicate component sprawl.",
            )
        )

    if re.search(r"\bdocument\.(querySelector|getElementById|getElementsByClassName|getElementsByTagName)\b", text):
        findings.append(
            RuleFinding(
                "maintenance",
                "medium",
                8,
                "Direct DOM access fights React's model.",
            )
        )

    if len(text.splitlines()) > 450:
        findings.append(
            RuleFinding(
                "maintenance",
                "medium",
                8,
                "Very large React components are hard to maintain.",
            )
        )

    if re.search(r"\buseEffect\s*\(", text) and re.search(r"\buseState\s*\(", text) and len(re.findall(r"\buseEffect\s*\(", text)) > 5:
        findings.append(
            RuleFinding(
                "maintenance",
                "low",
                5,
                "This component has many effects and states together. Consider splitting responsibilities.",
            )
        )

    return findings
