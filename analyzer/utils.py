from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

from .config import SUPPORTED_EXTENSIONS


_REACT_IMPORT_RE = re.compile(
    r"""
    ^\s*(?:import\s+.*\bfrom\s+['"]react['"]
        |import\s+['"]react['"]
        |(?:const|let|var)\s+.*=\s*require\(['"]react['"]\))
    """,
    re.MULTILINE | re.VERBOSE,
)

_REACT_RUNTIME_RE = re.compile(
    r"\b(?:jsx|jsxs|jsxDEV|Fragment)\b|\b(?:React\.createElement|createRoot|hydrateRoot)\b"
)
_REACT_HOOK_RE = re.compile(
    r"\buse(?:State|Effect|Memo|Callback|Ref|Reducer|Context|LayoutEffect|ImperativeHandle|Transition|DeferredValue|Id)\b"
)
_JSX_FRAGMENT_RE = re.compile(r"<>|</>")
_JSX_TAG_RE = re.compile(r"<([A-Za-z][A-Za-z0-9_]*)\b[^>]*?>")


def _strip_strings_and_comments(text: str) -> str:
    pattern = re.compile(
        r"""
        //.*?$                         |  # line comments
        /\*.*?\*/                      |  # block comments
        '(?:\\.|[^'\\])*'              |  # single-quoted strings
        "(?:\\.|[^"\\])*"              |  # double-quoted strings
        `(?:\\.|[^`\\])*`                 # template literals
        """,
        re.DOTALL | re.MULTILINE | re.VERBOSE,
    )
    return pattern.sub(" ", text)


def _looks_like_react(text: str) -> bool:
    if not text:
        return False

    cleaned = _strip_strings_and_comments(text)

    if _REACT_IMPORT_RE.search(cleaned):
        return True
    if _REACT_RUNTIME_RE.search(cleaned):
        return True
    if _REACT_HOOK_RE.search(cleaned):
        return True
    if _JSX_FRAGMENT_RE.search(cleaned):
        return True

    tag_hits = _JSX_TAG_RE.findall(cleaned)
    if len(tag_hits) >= 2:
        return True

    if tag_hits and re.search(r"\breturn\s*\(", cleaned):
        return True

    return False


def safe_read_text(path: Path, limit: int = 500_000) -> str:
    try:
        data = path.read_bytes()
    except OSError:
        return ""
    data = data[:limit]
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def line_count(text: str) -> int:
    return text.count("\n") + (1 if text and not text.endswith("\n") else 0)


def clamp(value: float, min_value: float = 0, max_value: float = 100) -> int:
    return int(max(min_value, min(max_value, round(value))))


def normalize_path(path: Path) -> str:
    return str(path).replace(os.sep, "/")


def extract_language_from_path(path: Path, text: str = "") -> str | None:
    ext = path.suffix.lower()
    if ext not in (".py", ".html", ".htm", ".css", ".js", ".jsx", ".mjs", ".mongo", ".mongodb", ".json"):
        return None

    lang = SUPPORTED_EXTENSIONS.get(ext)

    if ext == ".jsx":
        return "react"

    if ext == ".js":
        return "react" if _looks_like_react(text) else "javascript"

    if lang == "mongodb" and ext == ".json":
        if any(
            k in text
            for k in ("$match", "$group", "db.", "collection", "aggregate", "find(", "insertOne", "updateOne", "createIndex")
        ):
            return "mongodb"
        return None

    return lang
