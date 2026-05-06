from __future__ import annotations

import re

from ...rules import RuleFinding


def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    if re.search(r"\bfunction\s*\(", text):
        findings.append(
            RuleFinding(
                "style",
                "low",
                2,
                "Prefer named functions for readability when possible.",
            )
        )

    if "TODO" in text:
        findings.append(
            RuleFinding(
                "style",
                "low",
                1,
                "Track TODOs deliberately so they do not get lost.",
            )
        )

    return findings
