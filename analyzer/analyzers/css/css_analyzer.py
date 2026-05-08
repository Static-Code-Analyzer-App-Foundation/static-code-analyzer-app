from __future__ import annotations

from collections import Counter
from pathlib import Path

from ...base import BaseAnalyzer
from ...common import file_metrics, score_from_findings
from ...rules import AnalyzerResult
from ...utils import normalize_path
from . import maintenance, performance, security, style

try:
    from . import tailwind
except Exception:  # pragma: no cover
    tailwind = None


def _dedupe_findings(findings):
    seen = set()
    result = []
    for f in findings:
        key = (
            getattr(f, "category", None),
            getattr(f, "severity", None),
            getattr(f, "points", None),
            getattr(f, "message", None),
            getattr(f, "line", None),
            getattr(f, "snippet", None),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(f)
    return result


class CSSAnalyzer(BaseAnalyzer):
    language = "css"

    def analyze(self, path: Path, text: str) -> AnalyzerResult:
        findings = []

        findings.extend(style.analyze(text))
        findings.extend(security.analyze(text))
        findings.extend(performance.analyze(text))
        findings.extend(maintenance.analyze(text))

        if tailwind is not None:
            findings.extend(tailwind.analyze(text, path))

        findings = _dedupe_findings(findings)
        score = score_from_findings(100, findings)

        metrics = file_metrics(text)
        if isinstance(metrics, dict):
            severity_counts = Counter(getattr(f, "severity", "info") for f in findings)
            category_counts = Counter(getattr(f, "category", "unknown") for f in findings)
            metrics = {
                **metrics,
                "finding_count": len(findings),
                "severity_counts": dict(severity_counts),
                "category_counts": dict(category_counts),
            }

        return AnalyzerResult(self.language, normalize_path(path), "css_analyzer", score, findings, metrics)
