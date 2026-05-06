from __future__ import annotations

import re
from pathlib import Path

from ...rules import RuleFinding

PROMISE_CALL_RE = re.compile(
    r"\b(?:fetch|axios(?:\.[A-Za-z_$][\w$]*)?|Promise\.(?:all|allSettled|race|any)|new\s+Promise)\s*\("
)

MUTATION_RE = re.compile(r"(?:\+\+|--|\+=|-=|\*=|/=|%=)")


def analyze(path: Path, text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    lines = text.splitlines()

    if re.search(r"\.\s*forEach\s*\(\s*async\b", text):
        findings.append(
            RuleFinding(
                "async",
                "medium",
                10,
                "Array.forEach with an async callback will not wait for the promises to finish.",
            )
        )

    if re.search(r"\.\s*map\s*\(\s*async\b", text) and "Promise.all" not in text:
        findings.append(
            RuleFinding(
                "async",
                "medium",
                9,
                "Async map results are usually meant to be awaited with Promise.all.",
            )
        )

    if re.search(r"\.\s*(?:filter|reduce)\s*\(\s*async\b", text):
        findings.append(
            RuleFinding(
                "async",
                "medium",
                8,
                "Async callbacks inside filter/reduce are often a logic bug.",
            )
        )

    if re.search(r"\bset(?:Timeout|Interval)\s*\(\s*async\b", text):
        findings.append(
            RuleFinding(
                "async",
                "low",
                4,
                "Async timer callbacks can hide rejected promises unless they are handled explicitly.",
            )
        )

    for lineno, line in enumerate(lines, 1):
        if PROMISE_CALL_RE.search(line):
            if not re.search(r"\bawait\b", line) and not re.search(r"\breturn\b", line):
                if ".then(" not in line and ".catch(" not in line and ".finally(" not in line:
                    findings.append(
                        RuleFinding(
                            "async",
                            "medium",
                            9,
                            f"Promise-like call on line {lineno} may be missing await or return.",
                        )
                    )
                    break

    for m in re.finditer(r"\.then\s*\(", text):
        window = text[m.start() : m.start() + 350]
        if ".catch(" not in window and ".finally(" not in window:
            findings.append(
                RuleFinding(
                    "async",
                    "medium",
                    10,
                    "Promise chain appears to be missing a catch handler; rejections may go unhandled.",
                )
            )
            break

    if re.search(r"\bPromise\.all\s*\(", text) and re.search(r"(?:\+\+|--|\+=|-=|\*=|/=|%=)", text):
        findings.append(
            RuleFinding(
                "async",
                "medium",
                8,
                "Concurrent async work combined with shared mutations can create race conditions.",
            )
        )

    if re.search(r"\b(?:await\s+fetch|fetch\s*\()",
        text,
    ) and re.search(r"(\btry\s*\{[\s\S]{0,200}\bfetch\s*\()|(\bfetch\s*\([\s\S]{0,200}\}\s*catch\s*\{)", text):
        pass

    return findings
