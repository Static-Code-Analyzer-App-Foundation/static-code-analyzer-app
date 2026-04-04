from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
EXTRACT_DIR = BASE_DIR / "extracted"
REPORT_DIR = BASE_DIR / "reports"
TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
DB_PATH = DATA_DIR / "analyzer.db"

SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".js": "javascript",
    ".jsx": "react",
    ".mjs": "javascript",
    ".mongo": "mongodb",
    ".mongodb": "mongodb",
    ".json": "mongodb",
}
