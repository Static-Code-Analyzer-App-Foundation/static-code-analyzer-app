# 🚀 Static Code Analyzer

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Framework-Flask-black)
![Status](https://img.shields.io/badge/Status-Active-success)
![Platform](https://img.shields.io/badge/Platform-Web-orange)

### Multi-Language Static Code Analysis Platform

Analyze source code, detect vulnerabilities, calculate weighted quality scores, and generate professional PDF reports directly from your browser.

</div>

---

# 📚 Table of Contents

- [Overview](#-overview)
- [Live Demo](#-live-demo)
- [Key Features](#-key-features)
- [Supported Languages](#-supported-languages)
- [Analysis Categories](#-analysis-categories)
- [System Workflow](#-system-workflow)
- [System Architecture](#-system-architecture)
- [Technology Stack](#️-technology-stack)
- [Requirements](#-requirements)
- [Installation Guide](#️-installation-guide)
- [Run the Application](#️-run-the-application)
- [How the Analyzer Works](#-how-the-analyzer-works)
- [Project Structure](#-project-structure)
- [Deployment](#️-deployment)
- [Output Features](#-output-features)
- [Development Guide](#-development-guide)
- [Advantages](#-advantages)
- [Current Limitations](#️-current-limitations)
- [Future Improvements](#-future-improvements)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)
- [Author](#-author)

---

# 📖 Overview

Static Code Analyzer is a lightweight yet powerful web-based application designed to automate source code quality analysis across multiple programming languages.

The system allows users to upload a ZIP archive containing source code files. The application securely extracts the archive, detects supported programming languages, applies rule-based analysis, calculates weighted quality scores, and generates professional PDF reports containing detailed findings.

Unlike traditional static analysis tools that often require complex local setup and configuration, this platform is fully browser-based, beginner-friendly, and easy to use.

### Target Users

- Students
- Beginner Developers
- Freelancers
- Small Development Teams
- Academic & Research Projects

---

# 🌐 Live Demo

<div align="center">

| Platform | URL |
|----------|-----|
| PythonAnywhere | https://mohammedsaifalsabah.pythonanywhere.com |

</div>

---

# ✨ Key Features

### 🔍 Multi-Language Static Analysis
Analyze multiple programming languages within a single uploaded archive.

### 📦 Secure ZIP Upload & Extraction
Safely validates and extracts uploaded ZIP files into isolated workspaces.

### ⚡ Intelligent Language Detection
Uses:
- File extension matching
- Content-based heuristics
- Syntax pattern recognition

### 🧠 Rule-Based Analysis Engine
Detects:
- Security vulnerabilities
- Maintainability issues
- Performance bottlenecks
- Accessibility problems
- Coding style violations

### 📊 Weighted Scoring System
Generates:
- Category-wise scores
- File-wise scores
- Final aggregated project score

### 📄 PDF Report Generation
Creates professional downloadable reports including:
- Analysis summary
- Detailed findings
- Rule violations
- Recommendations

### 🖥 Interactive Dashboard
Displays structured analysis results through a clean user interface.

### ☁️ Cloud Deployment Ready
Successfully deployed on PythonAnywhere free-tier hosting.

---

# 🌍 Supported Languages

| Language | Support |
|----------|----------|
| Python | ✅ |
| JavaScript | ✅ |
| HTML | ✅ |
| CSS | ✅ |
| React | ✅ |
| MongoDB Configuration Files | ✅ |

---

# 📊 Analysis Categories

| Language | Categories |
|----------|-------------|
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
| Secure Extraction |
+-------------------+
          |
          v
+-------------------+
| Language Detection|
+-------------------+
          |
          v
+-------------------+
| Rule Processing   |
+-------------------+
          |
          v
+-------------------+
| Score Calculation |
+-------------------+
          |
          v
+-------------------+
| PDF Report Output |
+-------------------+
```

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

| Technology | Purpose |
|------------|---------|
| Python 3.10 | Core Programming Language |
| Flask | Backend Web Framework |
| Jinja2 | Frontend Templating |
| ReportLab | PDF Report Generation |
| Gunicorn | Production WSGI Server |
| PythonAnywhere | Deployment Platform |

---

# 🛠 Requirements

Before running the project locally, ensure the following are installed:

- Python 3.8 or higher
- pip
- Git
- ZIP archive containing source code files

---

# ⚙️ Installation Guide

## 1️⃣ Clone the Repository

```bash
git clone https://github.com/Static-Code-Analyzer-App-Foundation/static-code-analyzer-app.git

cd static-code-analyzer-app
```

---

## 2️⃣ Create a Virtual Environment

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
- Git Bash
- WSL

Or manually execute the setup commands inside `run.sh`.

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

## Step 2 — Validation & Secure Extraction
The system validates and securely extracts the archive.

## Step 3 — Language Detection
Files are identified using:
- File extensions
- Content heuristics
- Syntax patterns

## Step 4 — Rule Processing
Files are routed to language-specific analyzers.

## Step 5 — Score Calculation
Violations contribute weighted penalties to overall scores.

## Step 6 — Report Generation
Results are displayed in the dashboard and exported as PDF reports.

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

## Deployment Steps

1. Create a PythonAnywhere account
2. Clone the repository
3. Create a virtual environment
4. Install dependencies
5. Configure the Flask application
6. Configure the WSGI file
7. Reload the application

---

# 📤 Output Features

The application generates:

- Per-file analysis reports
- Category-wise scoring
- Security findings
- Performance warnings
- Style recommendations
- Final aggregated score
- Downloadable PDF reports

---

# 🧑‍💻 Development Guide

## Add New Rules

Edit files inside:

```text
analyzer/analyzers/[language]/
```

## Add New Language Support

1. Create analyzer module
2. Define rule sets
3. Implement scoring logic
4. Register analyzer in routing system

---

# 📈 Advantages

- Beginner-friendly
- Browser-based accessibility
- Lightweight architecture
- Multi-language support
- No installation required
- Professional report generation
- Fast analysis workflow

---

# ⚠️ Current Limitations

- Limited language support
- No GitHub integration
- No real-time collaboration
- Rule-based analysis only
- Limited scalability on free hosting

---

# 🚀 Future Improvements

Planned enhancements include:

- AI-powered code analysis
- Machine learning integration
- GitHub/GitLab integration
- CI/CD pipeline support
- Docker deployment
- User authentication system
- Cloud storage integration
- Additional language support

---

# 🐛 Troubleshooting

## `run.sh` Not Working on Windows

Use:
- Git Bash
- WSL

Or manually execute setup commands.

---

## ZIP Upload Fails

Ensure:
- The file is `.zip`
- The archive is valid
- Source files are readable

---

## Application Does Not Start

Verify:
- Virtual environment is activated
- Dependencies are installed
- Python 3.8+ is installed

---

# 📄 License

This project is intended for educational and academic purposes.

You may add your preferred license here.

---

# 👤 Author

<div align="center">

| Name | Role |
|------|------|
| Mahir Ahmed | Project Manager |
| Mohammed Saif Al Sabah | Backend Developer |
| Maruf | Team Member |
| Sindid | Team Member |

</div>
---



# ⭐ Final Note

Static Code Analyzer demonstrates that a modern, browser-based, and multi-language static analysis platform can be developed using lightweight technologies while remaining accessible, scalable, and practical for real-world use.

The project establishes a strong foundation for future expansion into a more advanced enterprise-level code quality platform.
