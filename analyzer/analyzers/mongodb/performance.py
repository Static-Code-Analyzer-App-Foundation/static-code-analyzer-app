from __future__ import annotations

import re
from ...rules import RuleFinding

# Precompiled patterns for speed
_AGGREGATE_PIPELINE = re.compile(r"aggregate\s*\(\s*\[", re.IGNORECASE | re.DOTALL)
_FIND_CALL = re.compile(r"\bfind(?:One|Many)?\s*\(", re.IGNORECASE)
_LIMIT_CALL = re.compile(r"\.limit\s*\(", re.IGNORECASE)
_SORT_CALL = re.compile(r"\.sort\s*\(", re.IGNORECASE)
_SKIP_CALL = re.compile(r"\.skip\s*\(", re.IGNORECASE)
_MATCH_STAGE = re.compile(r"\$match\b", re.IGNORECASE)
_HEAVY_STAGE = re.compile(
    r"\$(?:sort|group|lookup|unwind|facet|bucket|bucketAuto|graphLookup|setWindowFields)\b",
    re.IGNORECASE,
)
_INDEX_HINT = re.compile(
    r"\b(?:createIndex|create_index|ensureIndex|ensure_index|index(?:es)?)\b",
    re.IGNORECASE,
)
_REGEX_STAGE = re.compile(r"\$regex\b", re.IGNORECASE)
_LEADING_WILDCARD = re.compile(r"\.\*\S*|\^\.\*|\$regex\s*:\s*['\"][^'\"]*\.\*", re.IGNORECASE)


def _add(findings: list[RuleFinding], severity: str, score: int, message: str) -> None:
    findings.append(RuleFinding("performance", severity, score, message))


def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    line_count = text.count("\n") + (1 if text else 0)

    has_aggregate = bool(_AGGREGATE_PIPELINE.search(text))
    has_find = bool(_FIND_CALL.search(text))
    has_limit = bool(_LIMIT_CALL.search(text))
    has_sort = bool(_SORT_CALL.search(text))
    has_skip = bool(_SKIP_CALL.search(text))
    has_match = bool(_MATCH_STAGE.search(text))
    has_heavy_stage = bool(_HEAVY_STAGE.search(text))
    has_index_hint = bool(_INDEX_HINT.search(text))
    has_regex = bool(_REGEX_STAGE.search(text))
    has_leading_wildcard = bool(_LEADING_WILDCARD.search(text))

    # Aggregation without early filtering usually burns CPU and memory.
    if has_aggregate and has_heavy_stage and not has_match:
        _add(
            findings,
            "medium",
            8,
            "Aggregation pipeline has heavy stages but no visible $match filter. Filter early to cut work.",
        )

    # Sorts should usually be index-backed.
    if has_sort and not has_index_hint:
        _add(
            findings,
            "medium",
            7,
            "Sort logic has no obvious index support. Unindexed sorts get expensive fast.",
        )

    # Reads without limit can silently become expensive.
    if has_find and not has_limit:
        _add(
            findings,
            "low",
            4,
            "find() appears without limit(). Bound reads when possible to reduce work and response size.",
        )

    # Skip without limit tends to waste more and more time as offsets grow.
    if has_skip and not has_limit:
        _add(
            findings,
            "medium",
            6,
            "skip() appears without limit(). Large-offset paging is usually inefficient.",
        )

    # Regex patterns with leading wildcards are common performance traps.
    if has_regex and has_leading_wildcard:
        _add(
            findings,
            "high",
            9,
            "Regex pattern appears to use a leading wildcard or broad match. That can trigger collection scans.",
        )

    # Query-heavy code with no indexing signal deserves a stronger warning.
    if (has_find or has_aggregate) and not has_index_hint:
        _add(
            findings,
            "low",
            3,
            "No indexing signal found near query logic. Repeated scans may become a bottleneck.",
        )

    # Large files are harder to optimize and review.
    if line_count > 200:
        severity = "medium" if line_count <= 500 else "high"
        score = 3 + min(line_count // 100, 7)
        _add(
            findings,
            severity,
            score,
            f"Large file detected ({line_count} lines). Split query logic before it becomes maintenance debt.",
        )

    return findings
