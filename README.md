 Static Code Analyzer

Run with:
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
python app.py
```
# 🛡️ Static Code Analyzer App

A local web app that lets you upload a ZIP file of source code, extracts it safely, analyzes supported files with language-specific rule sets, and shows the results in a clean dashboard with PDF export.
### Run the App
```bash
python app.py
```
Open http://127.0.0.1:5000

---
## ✨ Features

## ✨ What it does
- ZIP file upload and secure extraction
- Multi-language detection (Python, JS, HTML, CSS, React, MongoDB)
- Rule-based static analysis per language
- Aggregated scoring system (0-100%)
- Interactive results dashboard
- PDF report generation and download
- Local data persistence

- 📦 Upload a ZIP file containing code
- 🗂️ Extract the project into a local workspace
- 🧭 Route files by language/extension
- 🔍 Run language-specific analyzers
- 📊 Show results in a table with scores
- 📄 Export the report as PDF
- 💾 Store analysis data locally
## 📚 Supported Languages & Analysis Categories

---
| Language | Categories |
|----------|------------|
| Python | Correctness, Efficiency, Maintenance, Security, Style |
| JavaScript | Efficiency, Maintenance, Security, Style |
| HTML | Accessibility, Maintenance, Performance, Security |
| CSS | Maintenance, Performance, Security, Style |
| React | Maintenance, Performance, Security, Style |
| MongoDB | Maintenance, Performance, Security, Style |

## 🧠 Supported Languages
## 🏗️ Architecture

- Python
- JavaScript
- HTML
- CSS
- React
- MongoDB-related code and config files
1. **Upload & Extract**: ZIP → local workspace
2. **Language Routing**: Extension/content → analyzer
3. **Rule Execution**: Language-specific rule modules
4. **Scoring**: Penalty accumulation → final score
5. **Results**: Merged table + detailed findings
6. **Export**: PDF generation

---
## 📁 Project Structure

## 🏗️ How it works
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

1. User uploads a ZIP file.
2. The app extracts it into a local folder.
3. Files are detected by extension.
4. Each language goes to its own analyzer pipeline.
5. Each analyzer runs its own rule modules.
6. Scores are collected and merged.
7. Results appear on the result page.
8. The user can download a PDF report.
## 🔧 Development

---
Modify rules in `analyzer/analyzers/[lang]/` modules.
Add new languages by creating `analyzer/analyzers/[newlang]/`.

## 📁 Project Structure

```text
app.py
analyzer/
├── analyzers/
│   ├── python/
│   ├── html/
│   ├── css/
│   ├── javascript/
│   ├── react/
│   └── mongodb/
templates/
static/
data/
uploads/
extracted/
reports//
