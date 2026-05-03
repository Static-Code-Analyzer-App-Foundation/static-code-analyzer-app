from __future__ import annotations

import re
from ...rules import RuleFinding


def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    if re.search(r"\bconsole\.log\s*\(", text):
        findings.append(
            RuleFinding(
                "style",
                "low",
                3,
                "console.log left in production code.",
            )
        )

    # nested ternaries
    ternary_like_lines = 0
    for line in text.splitlines():
        if "?" in line and ":" in line and (line.count("?") >= 2 or re.search(r"\?.*\?.*", line)):
            ternary_like_lines += 1
    if ternary_like_lines > 0:
        findings.append(
            RuleFinding(
                "style",
                "low",
                4,
                "Nested ternary logic hurts readability.",
            )
        )

    # inline style overuse
    if len(re.findall(r"\bstyle\s*=\s*\{\s*\{", text)) > 3:
        findings.append(
            RuleFinding(
                "style",
                "low",
                4,
                "Heavy inline styling makes JSX harder to maintain.",
            )
        )

    # long lines
    if any(len(line) > 160 for line in text.splitlines()):
        findings.append(
            RuleFinding(
                "style",
                "low",
                3,
                "Some lines are very long. Split them for readability.",
            )
        )

    return findings
