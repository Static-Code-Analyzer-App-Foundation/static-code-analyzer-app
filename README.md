````markdown
# 🚀 Static Code Analyzer

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Framework-Flask-black)
![License](https://img.shields.io/badge/Status-Active-success)
![Platform](https://img.shields.io/badge/Platform-Web-orange)

A powerful multi-language static code analysis platform built with Flask.

Analyze source code, detect vulnerabilities, evaluate code quality, generate weighted scores, and export professional PDF reports — all from a web browser.

</div>

---

# 📖 Overview

Static Code Analyzer is a lightweight yet powerful web-based application designed to automate source code quality analysis across multiple programming languages.

The platform allows users to upload a ZIP archive containing source code files. The system securely extracts the archive, detects supported programming languages, applies rule-based analysis, calculates weighted quality scores, and generates a professional PDF report containing detailed findings.

Unlike traditional static analysis tools that require complex setup and local installation, this application is fully browser-based and beginner-friendly.

The project was developed to provide an accessible, scalable, and easy-to-use solution for:

- Students
- Beginner developers
- Freelancers
- Small development teams
- Academic projects

---

# 🌐 Live Demo

<div align="center">

| Platform | URL |
|---|---|
| PythonAnywhere | https://mohammedsaifalsabah.pythonanywhere.com |

</div>

---

# ✨ Key Features

## 🔍 Multi-Language Static Analysis
Analyze source code across multiple programming languages within a single uploaded archive.

## 📦 Secure ZIP Upload & Extraction
Safely validates and extracts uploaded ZIP files into isolated workspaces.

## ⚡ Intelligent Language Detection
Detects programming languages using both extension matching and content-based heuristics.

## 🧠 Rule-Based Analysis Engine
Identifies:
- Security vulnerabilities
- Maintainability issues
- Performance bottlenecks
- Accessibility problems
- Coding style violations

## 📊 Weighted Scoring System
Generates meaningful category-wise and overall project quality scores.

## 📄 Professional PDF Report Generation
Creates downloadable PDF reports containing:
- Analysis summary
- File-wise findings
- Category scores
- Detailed issue breakdowns

## 🖥 Clean Dashboard Interface
Provides a simple and intuitive analysis results dashboard.

## 🌍 Cross-Platform Compatibility
Runs on:
- Windows
- Linux
- macOS

## ☁️ Cloud Deployment Support
Successfully deployed on PythonAnywhere free-tier hosting.

---

# 🌍 Supported Languages

| Language | Support |
|---|---|
| Python | ✅ |
| JavaScript | ✅ |
| HTML | ✅ |
| CSS | ✅ |
| React | ✅ |
| MongoDB Configuration Files | ✅ |

---

# 📊 Analysis Categories

| Language | Categories |
|---|---|
| Python | Correctness, Efficiency, Maintenance, Security, Style |
| JavaScript | Efficiency, Maintenance, Security, Style |
| HTML | Accessibility, Maintenance, Performance, Security |
| CSS | Maintenance, Performance, Security, Style |
| React | Maintenance, Performance, Security, Style |
| MongoDB | Maintenance, Performance, Security, Style |

---

# 🏗 System Workflow

```text
+-------------------+
| Upload ZIP File   |
+-------------------+
          |
          v
+-------------------+
| File Validation   |
+-------------------+
          |
          v
+-------------------+
| ZIP Extraction    |
+-------------------+
          |
          v
+-------------------+
| Language Detection|
+-------------------+
          |
          v
+-------------------+
| Rule-Based Engine |
+-------------------+
          |
          v
+-------------------+
| Score Generation  |
+-------------------+
          |
          v
+-------------------+
| PDF Report Output |
+-------------------+
````

---

# 🏛 System Architecture

```text
+------------------------------------------------+
|                Web Interface Layer             |
| (Upload, Dashboard, Visualization)             |
+------------------------------------------------+
                     |
                     v
+------------------------------------------------+
|               Analysis Engine                  |
| Detection | Rule Processing | Scoring          |
+------------------------------------------------+
                     |
                     v
+------------------------------------------------+
|                 Storage Layer                  |
| Uploads | Reports | Extracted Files            |
+------------------------------------------------+
```

---

# ⚙️ Technology Stack

| Technology     | Purpose                   |
| -------------- | ------------------------- |
| Python 3.10    | Core Programming Language |
| Flask          | Backend Web Framework     |
| Jinja2         | Frontend Templating       |
| ReportLab      | PDF Report Generation     |
| Gunicorn       | Production WSGI Server    |
| PythonAnywhere | Deployment Platform       |

---

# 🛠 Requirements

Before running the project locally, ensure the following are installed:

* Python 3.8 or higher
* pip
* Git
* ZIP archive containing source code files

---

# ⚙️ Installation Guide

## 1️⃣ Clone the Repository

```bash
git clone https://github.com/Static-Code-Analyzer-App-Foundation/static-code-analyzer-app.git

cd static-code-analyzer-app
```

---

## 2️⃣ Create Virtual Environment

### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Windows (CMD)

```cmd
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Run Setup Script

### Linux / macOS / WSL / Git Bash

```bash
bash run.sh
```

### Native Windows

Use:

* Git Bash
* WSL

Or manually execute the setup commands from `run.sh`.

---

# ▶️ Run the Application

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

---

# 🔍 How the Analyzer Works

## Step 1 — Upload Source Code

The user uploads a ZIP archive containing project source files.

## Step 2 — Secure Extraction

The system validates and securely extracts the archive.

## Step 3 — Language Detection

Files are identified using:

* File extensions
* Content heuristics
* Syntax patterns

## Step 4 — Rule Processing

Files are routed to language-specific analyzers.

## Step 5 — Scoring

Violations contribute weighted penalties to category scores.

## Step 6 — Report Generation

Results are displayed in the dashboard and exported as a PDF report.

---

# 📂 Project Structure

```text
static-code-analyzer-app/
│
├── app.py
├── run.sh
├── requirements.txt
├── Procfile
├── .env.example
│
├── analyzer/
│   ├── base.py
│   ├── utils.py
│   ├── webapp.py
│   │
│   └── analyzers/
│       ├── python/
│       ├── javascript/
│       ├── html/
│       ├── css/
│       ├── react/
│       └── mongodb/
│
├── templates/
│   ├── base.html
│   ├── index.html
│   └── result.html
│
├── static/
│   ├── css/
│   └── js/
│
├── uploads/
├── extracted/
├── reports/
└── data/
```

---

# ☁️ Deployment

The application is deployed using PythonAnywhere.

### Deployment Process

1. Create PythonAnywhere account
2. Clone repository
3. Create virtual environment
4. Install dependencies
5. Configure Flask application
6. Configure WSGI file
7. Reload application

---

# 📤 Output Features

The system provides:

* Per-file analysis reports
* Category-wise scoring
* Security findings
* Performance warnings
* Style recommendations
* Final project score
* Downloadable PDF reports

---

# 🧑‍💻 Development Guide

## Add New Rules

Edit:

```text
analyzer/analyzers/[language]/
```

## Add New Language Support

1. Create analyzer module
2. Define rules
3. Implement scoring logic
4. Register analyzer in routing system

---

# 📈 Advantages

* Beginner-friendly
* Browser-based accessibility
* Lightweight architecture
* Multi-language support
* No installation required
* Professional report generation
* Fast analysis workflow

---

# ⚠️ Current Limitations

* Limited language support
* No GitHub integration
* No real-time collaboration
* Rule-based analysis only
* Limited scalability on free hosting

---

# 🚀 Future Improvements

Planned enhancements include:

* AI-powered code analysis
* Machine learning integration
* GitHub/GitLab integration
* CI/CD pipeline support
* Docker deployment
* User authentication system
* Cloud storage integration
* Additional programming language support

---

# 🐛 Troubleshooting

## `run.sh` not working on Windows

Use:

* Git Bash
* WSL

Or manually run setup commands.

---

## ZIP Upload Fails

Ensure:

* The file is `.zip`
* The archive is not corrupted
* Source files are readable

---

## Application Does Not Start

Verify:

* Virtual environment is activated
* Dependencies are installed
* Python 3.8+ is installed

---

# 📄 License

This project is intended for educational and academic purposes.

Add your preferred license here if needed.

---

# 👤 Author

## Mohammed Saif Al Sabah

Static Code Analyzer Project
Department of Computer Science and Engineering

---

# ⭐ Final Note

Static Code Analyzer demonstrates that a modern, browser-based, multi-language static analysis platform can be built using lightweight technologies while remaining accessible, scalable, and practical for real-world use.

The project establishes a strong foundation for future expansion into a more advanced and enterprise-level code quality platform.

```
```
