from __future__ import annotations

import re

from ...rules import RuleFinding


def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    if re.search(r"\bfor\s*\([^\)]*;[^\)]*;[^\)]*\)\s*\{[\s\S]{0,220}?\bfor\s*\(", text):
        findings.append(
            RuleFinding(
                "efficiency",
                "medium",
                10,
                "Nested loops may be costly on large data sets.",
            )
        )

    if re.search(r"\bwhile\s*\(", text) and re.search(r"\bfor\s*\(", text):
        if re.search(r"\bwhile\s*\([\s\S]{0,220}?\bfor\s*\(", text):
            findings.append(
                RuleFinding(
                    "efficiency",
                    "medium",
                    10,
                    "Nested loop structures can become expensive fast.",
                )
            )

    if re.search(r"\bsetInterval\s*\(", text):
        findings.append(
            RuleFinding(
                "efficiency",
                "low",
                4,
                "Ensure timers are cleared to avoid leaks and runaway background work.",
            )
        )

    if "setInterval(" in text and "clearInterval(" not in text:
        findings.append(
            RuleFinding(
                "efficiency",
                "medium",
                7,
                "setInterval is used without a visible clearInterval cleanup.",
            )
        )

    if re.search(r"JSON\.parse\s*\(\s*JSON\.stringify\s*\(", text, re.S):
        findings.append(
            RuleFinding(
                "efficiency",
                "low",
                4,
                "Deep cloning through JSON stringify/parse is expensive and lossy.",
            )
        )

    if re.search(r"\bnew\s+(?:Object|Array)\s*\(", text):
        findings.append(
            RuleFinding(
                "efficiency",
                "low",
                3,
                "new Object/new Array are rarely needed and can be replaced with literals.",
            )
        )

    if re.search(r"\b(?:for|while)\b[\s\S]{0,260}\b(?:querySelector|getElementById|getElementsBy|createElement)\(", text):
        findings.append(
            RuleFinding(
                "efficiency",
                "medium",
                8,
                "DOM queries inside loops can become expensive; cache repeated lookups.",
            )
        )

    if re.search(r"\baddEventListener\s*\(", text) and "removeEventListener(" not in text:
        findings.append(
            RuleFinding(
                "efficiency",
                "medium",
                8,
                "Event listeners are added without a visible cleanup path.",
            )
        )

    return findings
