from __future__ import annotations

import re
from ...rules import RuleFinding

_DANGEROUS_WHERE = re.compile(r"\$where\b", re.IGNORECASE)
_EMPTY_FIND = re.compile(r"\.(?:find|findOne|findMany)\s*\(\s*\{\s*\}\s*\)", re.IGNORECASE | re.DOTALL)
_EMPTY_DELETE = re.compile(r"\.(?:deleteOne|deleteMany|remove|removeOne)\s*\(\s*\{\s*\}\s*\)", re.IGNORECASE | re.DOTALL)
_EMPTY_UPDATE = re.compile(r"\.(?:updateOne|updateMany|replaceOne|update)\s*\(\s*\{\s*\}\s*,", re.IGNORECASE | re.DOTALL)
_RAW_EVAL = re.compile(r"\b(?:eval|Function|new\s+Function)\s*\(", re.IGNORECASE)
_REGEX_FROM_INPUT = re.compile(
    r"\$regex\b.{0,120}\b(?:req|request|body|query|params|input|user|data|payload)\b",
    re.IGNORECASE | re.DOTALL,
)
_STRING_INTERPOLATION_IN_QUERY = re.compile(r"(\+\s*[\w.]+\s*\+|f['\"]|format\s*\()", re.IGNORECASE)


def _add(findings: list[RuleFinding], severity: str, score: int, message: str) -> None:
    findings.append(RuleFinding("security", severity, score, message))


def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    if _DANGEROUS_WHERE.search(text):
        _add(
            findings,
            "high",
            25,
            "$where can be unsafe and slow. Replace it with structured predicates.",
        )

    if _EMPTY_FIND.search(text):
        _add(
            findings,
            "medium",
            10,
            "Unfiltered find() query can expose too much data or scan large collections.",
        )

    if _EMPTY_DELETE.search(text):
        _add(
            findings,
            "high",
            22,
            "Destructive operation appears to target an empty filter. That is a serious data-loss risk.",
        )

    if _EMPTY_UPDATE.search(text):
        _add(
            findings,
            "high",
            20,
            "Update operation appears to use an empty filter. That can modify far more data than intended.",
        )

    if _RAW_EVAL.search(text):
        _add(
            findings,
            "high",
            24,
            "Dynamic code execution detected. That is a major security risk in query-adjacent code.",
        )

    # Best-effort scan for regex built from request-like input.
    if _REGEX_FROM_INPUT.search(text):
        _add(
            findings,
            "medium",
            12,
            "Regex appears to be built from user-controlled input. Sanitize or escape it before use.",
        )

    # Very rough signal for query string concatenation.
    if _STRING_INTERPOLATION_IN_QUERY.search(text) and ("find(" in text or "aggregate(" in text or "$where" in text):
        _add(
            findings,
            "medium",
            11,
            "String interpolation or concatenation appears near query logic. That can invite injection bugs.",
        )

    return findings
