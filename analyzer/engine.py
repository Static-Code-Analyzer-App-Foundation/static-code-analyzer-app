from __future__ import annotations
import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .config import EXTRACT_DIR, UPLOAD_DIR
from .db import get_conn
from .dispatcher import detect_language, get_analyzer
from .utils import safe_read_text, sha256_file, normalize_path

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def generate_job_id() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S") + "_" + os.urandom(3).hex()

def save_upload(file_storage) -> tuple[str, Path]:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = file_storage.filename or "upload.zip"
    job_id = generate_job_id()
    zip_path = UPLOAD_DIR / f"{job_id}_{filename}"
    file_storage.save(zip_path)
    return job_id, zip_path

def extract_zip(zip_path: Path, job_id: str) -> Path:
    target = EXTRACT_DIR / job_id
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            normalized = Path(member.filename)
            if normalized.is_absolute() or ".." in normalized.parts:
                continue
            zf.extract(member, target)
    return target

def register_upload(job_id: str, original_name: str, zip_path: Path, extracted_path: Path) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO uploads (job_id, original_name, zip_path, extracted_path, created_at) VALUES (?, ?, ?, ?, ?)",
            (job_id, original_name, str(zip_path), str(extracted_path), utc_now()),
        )

def index_and_analyze(job_id: str, root: Path) -> list:
    results = []
    with get_conn() as conn:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            lang = detect_language(path)
            if not lang:
                continue
            text = safe_read_text(path)
            analyzer = get_analyzer(lang)
            if not analyzer:
                continue
            sha = sha256_file(path)
            conn.execute(
                "INSERT INTO files (job_id, relative_path, absolute_path, language, sha256, size_bytes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (job_id, str(path.relative_to(root)), str(path), lang, sha, path.stat().st_size, utc_now()),
            )
            result = analyzer.analyze(path, text)
            results.append(result)
            conn.execute(
                "INSERT INTO analyses (job_id, file_path, language, analyzer_name, score, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (job_id, normalize_path(path), lang, result.analyzer_name, result.score, json.dumps(result.to_json(), ensure_ascii=False), utc_now()),
            )
    return results

def load_job_results(job_id: str) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT f.relative_path, f.language, a.analyzer_name, a.score, a.details_json
            FROM files f
            JOIN analyses a ON f.job_id = a.job_id AND f.absolute_path = a.file_path
            WHERE f.job_id = ?
            ORDER BY f.relative_path ASC
            """,
            (job_id,),
        ).fetchall()

    merged = []
    for row in rows:
        merged.append({
            "file_name": row["relative_path"],
            "language": row["language"],
            "analyzer_name": row["analyzer_name"],
            "score": row["score"],
            "details": json.loads(row["details_json"]),
        })
    return merged

def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {}
    for item in results:
        lang = item["language"]
        summary.setdefault(lang, {"count": 0, "total": 0, "files": []})
        summary[lang]["count"] += 1
        summary[lang]["total"] += item["score"]
        summary[lang]["files"].append(item)
    for lang, data in summary.items():
        data["average_score"] = round(data["total"] / data["count"], 2) if data["count"] else 0
    return summary
