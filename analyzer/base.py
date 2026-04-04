from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from .rules import AnalyzerResult

class BaseAnalyzer(ABC):
    language = "unknown"

    @abstractmethod
    def analyze(self, path: Path, text: str) -> AnalyzerResult:
        raise NotImplementedError
