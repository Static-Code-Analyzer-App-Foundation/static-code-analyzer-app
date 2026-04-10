from __future__ import annotations

import re
from ...rules import RuleFinding

_TODO_MARKERS = re.compile(r"\b(?:TODO|FIXME|HACK|XXX|TEMP)\b")
_TABS = re.compile(r"\t")
_TRAILING_SPACE = re.compile(r"[ \t]+$", re.MULTILINE)
_LONG_LINE = re.compile(r"^.{121,}$", re.MULTILINE)
_COMMENTED_OUT_CODE = re.compile(
    r"^\s*#\s*(?:if|for|while|def|class|return|import|from|try|except|with|else|elif|switch|case)\b",
    re.MULTILINE,
)
_EXCESS_BLANK_LINES = re.compile(r"\n{4,}")


def _add(findings: list[RuleFinding], severity: str, score: int, message: str) -> None:
    findings.append(RuleFinding("style", severity, score, message))


def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    todo_count = len(_TODO_MARKERS.findall(text))
    tab_count = len(_TABS.findall(text))
    trailing_space_count = len(_TRAILING_SPACE.findall(text))
    long_line_count = len(_LONG_LINE.findall(text))
    commented_code_count = len(_COMMENTED_OUT_CODE.findall(text))
    excess_blank_runs = len(_EXCESS_BLANK_LINES.findall(text))

    if todo_count:
        severity = "low" if todo_count < 4 else "medium"
        score = 2 + min(todo_count, 6)
        _add(
            findings,
            severity,
            score,
            f"Found {todo_count} TODO-style marker(s). Clean them up before the code spreads.",
        )

    if tab_count:
        severity = "low" if tab_count < 10 else "medium"
        score = 2 + min(tab_count // 2, 6)
        _add(
            findings,
            severity,
            score,
            f"Tabs detected ({tab_count}). Keep indentation consistent for cleaner reviews.",
        )

    if trailing_space_count:
        severity = "low" if trailing_space_count < 5 else "medium"
        score = 2 + min(trailing_space_count // 2, 5)
        _add(
            findings,
            severity,
            score,
            f"Trailing whitespace found on {trailing_space_count} line(s). It adds noise to diffs.",
        )

    if long_line_count:
        severity = "low" if long_line_count < 8 else "medium"
        score = 3 + min(long_line_count // 2, 6)
        _add(
            findings,
            severity,
            score,
            f"{long_line_count} long line(s) detected. Break dense statements for readability.",
        )

    if commented_code_count:
        severity = "low" if commented_code_count < 3 else "medium"
        score = 2 + min(commented_code_count, 5)
        _add(
            findings,
            severity,
            score,
            f"Commented-out code found ({commented_code_count} line(s)). Remove dead code instead of parking it.",
        )

    if excess_blank_runs:
        _add(
            findings,
            "low",
            2,
            "Excessive blank-line runs detected. Tighten spacing so the file stays easier to scan.",
        )

    return findings
