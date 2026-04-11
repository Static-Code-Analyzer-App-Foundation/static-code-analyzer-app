# Static Code Analyzer

A Flask-based web application for static code analysis. Upload ZIP files containing source code to get comprehensive analysis across multiple languages, with detailed scores and PDF reports.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+

### Installation (Cross-Platform)

**Windows (PowerShell/cmd):**
```cmd
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

**Linux/macOS:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run the App
```bash
python app.py
```
Open http://127.0.0.1:5000

## ✨ Features

- ZIP file upload and secure extraction
- Multi-language detection (Python, JS, HTML, CSS, React, MongoDB)
- Rule-based static analysis per language
- Aggregated scoring system (0-100%)
- Interactive results dashboard
- PDF report generation and download
- Local data persistence

## 📚 Supported Languages & Analysis Categories

| Language | Categories |
|----------|------------|
| Python | Correctness, Efficiency, Maintenance, Security, Style |
| JavaScript | Efficiency, Maintenance, Security, Style |
| HTML | Accessibility, Maintenance, Performance, Security |
| CSS | Maintenance, Performance, Security, Style |
| React | Maintenance, Performance, Security, Style |
| MongoDB | Maintenance, Performance, Security, Style |

## 🏗️ Architecture

1. **Upload & Extract**: ZIP → local workspace
2. **Language Routing**: Extension/content → analyzer
3. **Rule Execution**: Language-specific rule modules
4. **Scoring**: Penalty accumulation → final score
5. **Results**: Merged table + detailed findings
6. **Export**: PDF generation

## 📁 Project Structure

```
static-code-analyzer-app/
├── app.py                 # Flask app
├── analyzer/              # Core analysis engine
│   ├── analyzers/         # Language analyzers
│   │   ├── css/
│   │   ├── html/
│   │   ├── javascript/
│   │   ├── mongodb/
│   │   ├── python/
│   │   └── react/
│   ├── base.py, utils.py  # Shared logic
│   └── webapp.py          # Web integration
├── templates/             # Jinja2 templates
│   ├── base.html
│   ├── index.html
│   └── result.html
├── static/                # CSS/JS
│   ├── css/style.css
│   └── js/main.js
├── data/                  # Persistent data
├── uploads/               # User uploads
├── reports/               # Generated PDFs
├── requirements.txt       # Dependencies
└── README.md
```

## 🔧 Development

Modify rules in `analyzer/analyzers/[lang]/` modules.
Add new languages by creating `analyzer/analyzers/[newlang]/`.


