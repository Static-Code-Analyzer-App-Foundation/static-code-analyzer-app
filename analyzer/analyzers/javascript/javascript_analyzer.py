from __future__ import annotations

from pathlib import Path

from ...base import BaseAnalyzer
from ...common import file_metrics, score_from_findings
from ...rules import AnalyzerResult
from ...utils import normalize_path
from . import async_checks, correctness, dependencies, efficiency, maintenance, security, style


class JavaScriptAnalyzer(BaseAnalyzer):
    language = "javascript"

    def analyze(self, path: Path, text: str) -> AnalyzerResult:
        findings = []

        findings.extend(correctness.analyze(path, text))
        findings.extend(async_checks.analyze(path, text))
        findings.extend(security.analyze(text))
        findings.extend(efficiency.analyze(text))
        findings.extend(maintenance.analyze(text))
        findings.extend(dependencies.analyze(path, text))
        findings.extend(style.analyze(text))

        score = score_from_findings(100, findings)
        metrics = file_metrics(text)
        return AnalyzerResult(
            self.language,
            normalize_path(path),
            "javascript_analyzer",
            score,
            findings,
            metrics,
        )
