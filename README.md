# Static Code Analyzer

A Flask-based web application for static code analysis. Upload a ZIP file containing source code, and the app will securely extract it, analyze supported files across multiple languages, generate scores, and produce a PDF report.

## Features

* ZIP file upload and secure extraction
* Multi-language detection and routing
* Rule-based static analysis
* Language-specific scoring system
* Clean results dashboard
* PDF report generation and download
* Local data persistence
* Cross-platform support for Windows, macOS, and Linux

## Supported Languages

* Python
* JavaScript
* HTML
* CSS
* React
* MongoDB-related files and configuration

## Analysis Categories

| Language   | Categories                                            |
| ---------- | ----------------------------------------------------- |
| Python     | Correctness, Efficiency, Maintenance, Security, Style |
| JavaScript | Efficiency, Maintenance, Security, Style              |
| HTML       | Accessibility, Maintenance, Performance, Security     |
| CSS        | Maintenance, Performance, Security, Style             |
| React      | Maintenance, Performance, Security, Style             |
| MongoDB    | Maintenance, Performance, Security, Style             |

## Requirements

* Python 3.8 or higher
* pip
* A ZIP archive containing source code

## Installation

### 1) Clone the repository

```bash
git clone <your-repo-url>
cd static-code-analyzer-app
```

### 2) Create and activate a virtual environment

#### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\activate
```

#### Windows (cmd)

```cmd
python -m venv .venv
.venv\Scripts\activate
```

#### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4) Run the setup script

After installing dependencies, run the setup script to install any additional tools, prepare databases, and complete the initial setup.

#### macOS / Linux / WSL / Git Bash

```bash
bash run.sh
```

#### Windows native

`run.sh` is a shell script, so on native Windows you should do one of the following:

* Run it in Git Bash
* Run it in WSL
* Or manually execute the same setup steps listed inside `run.sh`

## Run the Application

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## How It Works

1. Upload a ZIP file containing source code.
2. The app extracts the archive into a safe local workspace.
3. Files are detected by extension and content.
4. Each file is routed to the correct language analyzer.
5. Rule checks are applied based on language-specific logic.
6. Results are aggregated into a score.
7. Findings are displayed in the dashboard.
8. A PDF report can be generated and downloaded.

## Project Structure

```text
static-code-analyzer-app/
├── app.py
├── run.sh
├── analyzer/
│   ├── analyzers/
│   │   ├── css/
│   │   ├── html/
│   │   ├── javascript/
│   │   ├── mongodb/
│   │   ├── python/
│   │   └── react/
│   ├── base.py
│   ├── utils.py
│   └── webapp.py
├── templates/
│   ├── base.html
│   ├── index.html
│   └── result.html
├── static/
│   ├── css/
│   └── js/
├── data/
├── uploads/
├── extracted/
├── reports/
├── requirements.txt
└── README.md
```

## Development

To add or modify rules, edit the relevant module inside:

```text
analyzer/analyzers/[language]/
```

To add a new language:

1. Create a new analyzer folder.
2. Add its rule set and scoring logic.
3. Register it in the analyzer routing system.

## Output

The application provides:

* Per-file analysis results
* Category-wise scoring
* Detailed findings
* Final aggregated score
* PDF export

## Troubleshooting

### `run.sh` does not work on Windows

Use Git Bash or WSL, or manually run the setup commands inside the script.

### ZIP file upload fails

Make sure the uploaded file is a valid `.zip` archive and contains readable source files.

### App does not start

Confirm that:

* The virtual environment is activated
* Dependencies are installed
* Python 3.8+ is being used

## License

Add your license here if needed.

## Author

Add your name or project team here.
