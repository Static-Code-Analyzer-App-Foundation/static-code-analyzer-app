from __future__ import annotations
import hashlib
import os
import re
from pathlib import Path

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

    from .config import SUPPORTED_EXTENSIONS
    lang = SUPPORTED_EXTENSIONS.get(ext)

    if lang == "javascript" and ("import React" in text or "from 'react'" in text or 'from "react"' in text or "<" in text and ">" in text):
        return "react"
    if lang == "mongodb" and ext == ".json":
        if any(k in text for k in ("$match", "$group", "db.", "collection", "aggregate", "find(", "insertOne", "updateOne", "createIndex")):
            return "mongodb"
        return None
    return lang
