from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class RuleFinding:
    rule: str
    severity: str
    score_impact: int
    message: str
    line: int | None = None

@dataclass
class AnalyzerResult:
    language: str
    file_path: str
    analyzer_name: str
    score: int
    findings: list[RuleFinding] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict:
        return {
            "language": self.language,
            "file_path": self.file_path,
            "analyzer_name": self.analyzer_name,
            "score": self.score,
            "findings": [finding.__dict__ for finding in self.findings],
            "metrics": self.metrics,
        }
