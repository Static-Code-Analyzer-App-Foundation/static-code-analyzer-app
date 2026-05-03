from __future__ import annotations

from pathlib import Path

from ...base import BaseAnalyzer
from ...common import file_metrics, score_from_findings
from ...rules import AnalyzerResult
from ...utils import normalize_path
from . import accessibility, hooks, lifecycle, maintenance, performance, props, security, state, style


class ReactAnalyzer(BaseAnalyzer):
    language = "react"

    def analyze(self, path: Path, text: str) -> AnalyzerResult:
        findings = []

        for module in (
            hooks,
            state,
            props,
            lifecycle,
            security,
            performance,
            maintenance,
            accessibility,
            style,
        ):
            findings.extend(module.analyze(text))

        score = score_from_findings(100, findings)
        metrics = file_metrics(text)

        return AnalyzerResult(
            self.language,
            normalize_path(path),
            "react_analyzer",
            score,
            findings,
            metrics,
        )
