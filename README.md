# Static Code Analyzer

Run with:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
# 🛡️ Static Code Analyzer App

A local web app that lets you upload a ZIP file of source code, extracts it safely, analyzes supported files with language-specific rule sets, and shows the results in a clean dashboard with PDF export.

---

## ✨ What it does

- 📦 Upload a ZIP file containing code
- 🗂️ Extract the project into a local workspace
- 🧭 Route files by language/extension
- 🔍 Run language-specific analyzers
- 📊 Show results in a table with scores
- 📄 Export the report as PDF
- 💾 Store analysis data locally

---

## 🧠 Supported Languages

- Python
- JavaScript
- HTML
- CSS
- React
- MongoDB-related code and config files

---

## 🏗️ How it works

1. User uploads a ZIP file.
2. The app extracts it into a local folder.
3. Files are detected by extension.
4. Each language goes to its own analyzer pipeline.
5. Each analyzer runs its own rule modules.
6. Scores are collected and merged.
7. Results appear on the result page.
8. The user can download a PDF report.

---

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
change successfully by saiff