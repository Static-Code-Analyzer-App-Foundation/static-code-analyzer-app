from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from ...rules import RuleFinding


@dataclass(frozen=True)
class _Issue:
    severity: str
    score: int
    message: str


_QUERY_HINTS = (
    "find(",
    "find_one(",
    "findMany(",
    "aggregate(",
    "update(",
    "update_one(",
    "update_many(",
    "delete(",
    "delete_one(",
    "delete_many(",
    ".find(",
    ".aggregate(",
    ".update(",
    ".delete(",
)

_INDEX_HINTS = (
    "createIndex(",
    "create_index(",
    "ensureIndex(",
    "ensure_index(",
    "indexes",
    "index(",
)

_MONGO_STAGE_HINTS = (
    "$match",
    "$group",
    "$sort",
    "$lookup",
    "$unwind",
    "$project",
    "$addFields",
    "$set",
    "$limit",
    "$skip",
    "$facet",
    "$count",
    "$replaceRoot",
    "$replaceWith",
    "$bucket",
    "$bucketAuto",
    "$graphLookup",
    "$setWindowFields",
)

_MAINTENANCE_MARKERS = (
    "TODO",
    "FIXME",
    "HACK",
    "XXX",
    "TEMP",
    "temporary",
    "workaround",
    "compatibility",
)


def _count_matches(text: str, needles: Iterable[str]) -> int:
    return sum(text.count(n) for n in needles)


def _find_long_lines(text: str, threshold: int = 120) -> int:
    return sum(1 for line in text.splitlines() if len(line.rstrip("\n")) > threshold)


def _find_magic_numbers(text: str) -> int:
    """
    Counts numeric literals that often make queries harder to maintain.
    This is intentionally noisy but useful for review.
    """
    patterns = [
        r"(?<![\w.])\d{3,}(?![\w.])",      # 100, 200, 1000...
        r"(?<![\w.])\d+\.\d+(?![\w.])",    # 1.5, 2.75...
        r"(?<![\w.])\d+\s*ms\b",           # 500 ms
        r"(?<![\w.])\d+\s*s\b",            # 5 s
    ]
    return sum(len(re.findall(p, text, flags=re.IGNORECASE)) for p in patterns)


def _has_query_shape(text: str) -> bool:
    lower = text.lower()
    return any(h.lower() in lower for h in _QUERY_HINTS)


def _has_indexing_signals(text: str) -> bool:
    lower = text.lower()
    return any(h.lower() in lower for h in _INDEX_HINTS)


def _mongo_pipeline_stage_count(text: str) -> int:
    return sum(text.count(stage) for stage in _MONGO_STAGE_HINTS)


def _score_issue(*, base: int, bonus: int = 0, penalty: int = 0) -> int:
    return max(1, base + bonus + penalty)


def analyze(text: str) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    lower = text.lower()

    lines = text.splitlines()
    line_count = len(lines)
    char_count = len(text)

    query_present = _has_query_shape(text)
    index_present = _has_indexing_signals(text)
    stage_count = _mongo_pipeline_stage_count(text)
    long_line_count = _find_long_lines(text)
    magic_number_count = _find_magic_numbers(text)

    # 1) Missing indexing around query-heavy code.
    if query_present and not index_present:
        findings.append(
            RuleFinding(
                "maintenance",
                "high",
                9,
                "Query-heavy code with no obvious indexing path. This will age badly as data grows.",
            )
        )

    # 2) Large aggregation pipelines are hard to maintain.
    if stage_count >= 4:
        severity = "high" if stage_count >= 8 else "medium"
        score = _score_issue(base=6, bonus=min(stage_count, 4))
        findings.append(
            RuleFinding(
                "maintenance",
                severity,
                score,
                f"Aggregation pipeline is complex ({stage_count} stage hints). Break it into smaller, named steps.",
            )
        )

    # 3) Large files are harder to review and refactor.
    if line_count > 200:
        severity = "medium" if line_count <= 500 else "high"
        score = _score_issue(base=3, bonus=min(line_count // 100, 7))
        findings.append(
            RuleFinding(
                "maintenance",
                severity,
                score,
                f"Large file ({line_count} lines) reduces readability and increases refactor risk.",
            )
        )

    # 4) Long lines usually mean dense, brittle logic.
    if long_line_count >= 5:
        severity = "medium" if long_line_count < 15 else "high"
        score = _score_issue(base=4, bonus=min(long_line_count // 3, 5))
        findings.append(
            RuleFinding(
                "maintenance",
                severity,
                score,
                f"Found {long_line_count} long lines. The code is harder to scan and maintain.",
            )
        )

    # 5) Magic numbers make query behavior unclear.
    if magic_number_count >= 3:
        severity = "low" if magic_number_count < 8 else "medium"
        score = _score_issue(base=2, bonus=min(magic_number_count // 2, 5))
        findings.append(
            RuleFinding(
                "maintenance",
                severity,
                score,
                f"Multiple hardcoded numeric literals ({magic_number_count}) reduce intent clarity.",
            )
        )

    # 6) Repeated query patterns suggest duplicated logic.
    repeated_query_ops = sum(
        text.count(op) for op in ("find(", "aggregate(", "update(", "delete(", ".find(", ".aggregate(")
    )
    if repeated_query_ops >= 6:
        severity = "medium" if repeated_query_ops < 12 else "high"
        score = _score_issue(base=5, bonus=min(repeated_query_ops // 3, 4))
        findings.append(
            RuleFinding(
                "maintenance",
                severity,
                score,
                "Repeated query operations suggest duplicated data-access logic. Extract shared helpers.",
            )
        )

    # 7) Query intent without projection often becomes bloated over time.
    projection_signals = ("project(", ".only(", ".values(", ".select(", "$project")
    if query_present and not any(sig in text for sig in projection_signals):
        findings.append(
            RuleFinding(
                "maintenance",
                "low",
                3,
                "No projection/filtering hint found near queries. Returning too much data can make code noisy and fragile.",
            )
        )

    # 8) Deep nesting / heavy branching makes maintenance worse.
    branch_score = lower.count("if ") + lower.count("elif ") + lower.count("else:") + lower.count("switch") + lower.count("case ")
    if branch_score >= 12:
        severity = "medium" if branch_score < 25 else "high"
        score = _score_issue(base=4, bonus=min(branch_score // 4, 6))
        findings.append(
            RuleFinding(
                "maintenance",
                severity,
                score,
                f"High branching density detected ({branch_score} branch markers). Consider smaller functions.",
            )
        )

    # 9) TODO/FIXME markers are explicit maintenance debt.
    marker_hits = sum(text.count(marker) for marker in _MAINTENANCE_MARKERS)
    if marker_hits:
        severity = "low" if marker_hits < 4 else "medium"
        score = _score_issue(base=2, bonus=min(marker_hits, 6))
        findings.append(
            RuleFinding(
                "maintenance",
                severity,
                score,
                f"Maintenance markers found ({marker_hits}). Track and eliminate them before the code fossilizes.",
            )
        )

    # 10) If file is query-heavy and huge, prioritize maintenance risk.
    if query_present and line_count > 300 and char_count > 12000:
        findings.append(
            RuleFinding(
                "maintenance",
                "high",
                10,
                "This is a large, query-heavy file with elevated maintenance risk. Split domain logic, query building, and validation.",
            )
        )

    # 11) Comments can be useful, but comment spam around query code can hide complexity.
    comment_lines = sum(1 for line in lines if line.strip().startswith(("#", "//", "/*", "*")))
    if comment_lines > 40 and line_count > 0 and (comment_lines / line_count) > 0.25:
        findings.append(
            RuleFinding(
                "maintenance",
                "low",
                2,
                "Comment density is high. Too many comments can indicate the code is doing too much.",
            )
        )

    # 12) If there are query hints but no clear structure markers, flag for refactor.
    structure_markers = (
        "def ",
        "class ",
        "async def ",
        "try:",
        "except ",
        "with ",
    )
    if query_present and not any(m in text for m in structure_markers):
        findings.append(
            RuleFinding(
                "maintenance",
                "low",
                2,
                "Query logic appears unstructured. Wrapping it in explicit helpers will make future changes safer.",
            )
        )

    return findings
