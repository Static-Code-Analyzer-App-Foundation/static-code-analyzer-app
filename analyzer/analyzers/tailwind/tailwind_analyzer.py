from __future__ import annotations

from pathlib import Path

from ...base import BaseAnalyzer
from ...common import file_metrics, score_from_findings
from ...rules import AnalyzerResult
from ...utils import normalize_path
from ..css import tailwind as tailwind_rules


class TailwindAnalyzer(BaseAnalyzer):
    language = "tailwind"

    def analyze(self, path: Path, text: str) -> AnalyzerResult:
        findings = tailwind_rules.analyze(text, path)
        score = score_from_findings(100, findings)
        metrics = file_metrics(text)
        return AnalyzerResult(self.language, normalize_path(path), "tailwind_analyzer", score, findings, metrics)
