from __future__ import annotations
from pathlib import Path
from .utils import extract_language_from_path, safe_read_text
from .analyzers.python.python_analyzer import PythonAnalyzer
from .analyzers.html.html_analyzer import HTMLAnalyzer
from .analyzers.css.css_analyzer import CSSAnalyzer
from .analyzers.javascript.javascript_analyzer import JavaScriptAnalyzer
from .analyzers.react.react_analyzer import ReactAnalyzer
from .analyzers.mongodb.mongodb_analyzer import MongoDBAnalyzer

ANALYZERS = {
    "python": PythonAnalyzer(),
    "html": HTMLAnalyzer(),
    "css": CSSAnalyzer(),
    "javascript": JavaScriptAnalyzer(),
    "react": ReactAnalyzer(),
    "mongodb": MongoDBAnalyzer(),
}

def detect_language(path: Path) -> str | None:
    text = safe_read_text(path)
    return extract_language_from_path(path, text)

def get_analyzer(language: str):
    return ANALYZERS.get(language)
