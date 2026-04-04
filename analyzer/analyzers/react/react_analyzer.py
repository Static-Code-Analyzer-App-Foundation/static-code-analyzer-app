from __future__ import annotations
from pathlib import Path
from ...base import BaseAnalyzer
from ...common import file_metrics, score_from_findings
from ...rules import AnalyzerResult
from ...utils import normalize_path
from . import security, performance, maintenance, style

class ReactAnalyzer(BaseAnalyzer):
    language = "react"

    def analyze(self, path: Path, text: str) -> AnalyzerResult:
        findings = []
        findings.extend(security.analyze(text))
        findings.extend(performance.analyze(text))
        findings.extend(maintenance.analyze(text))
        findings.extend(style.analyze(text))
        score = score_from_findings(100, findings)
        metrics = file_metrics(text)
        return AnalyzerResult(self.language, normalize_path(path), "react_analyzer", score, findings, metrics)
