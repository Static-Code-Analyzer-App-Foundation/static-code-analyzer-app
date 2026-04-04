from __future__ import annotations
from collections import Counter
from .rules import RuleFinding
from .utils import clamp, line_count

def score_from_findings(base: int, findings: list[RuleFinding]) -> int:
    score = base
    for finding in findings:
        score -= finding.score_impact
    return clamp(score)

def file_metrics(text: str) -> dict:
    lines = text.splitlines()
    non_empty = [line for line in lines if line.strip()]
    avg_len = sum(len(line) for line in lines) / len(lines) if lines else 0
    return {
        "lines": line_count(text),
        "non_empty_lines": len(non_empty),
        "avg_line_length": round(avg_len, 2),
        "todo_count": text.lower().count("todo"),
    }
