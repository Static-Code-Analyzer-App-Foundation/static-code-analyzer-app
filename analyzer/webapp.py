from __future__ import annotations
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from .config import TEMPLATE_DIR, STATIC_DIR, REPORT_DIR
from .db import init_db
from .engine import save_upload, extract_zip, register_upload, index_and_analyze, load_job_results, summarize_results
from .pdf_report import build_pdf_report

def create_app() -> Flask:
    init_db()
    app = Flask(__name__, template_folder=str(TEMPLATE_DIR), static_folder=str(STATIC_DIR))
    app.secret_key = "replace-this-secret"
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    @app.route("/", methods=["GET"])
    def index():
        return render_template("index.html")

    @app.route("/analyze", methods=["POST"])
    def analyze():
        if "zip_file" not in request.files:
            flash("No file part found.")
            return redirect(url_for("index"))

        file = request.files["zip_file"]
        if not file.filename:
            flash("Please choose a ZIP file.")
            return redirect(url_for("index"))

        if not file.filename.lower().endswith(".zip"):
            flash("Only ZIP uploads are supported.")
            return redirect(url_for("index"))

        job_id, zip_path = save_upload(file)
        extracted_path = extract_zip(zip_path, job_id)
        register_upload(job_id, file.filename, zip_path, extracted_path)
        index_and_analyze(job_id, extracted_path)
        return redirect(url_for("result", job_id=job_id))

    @app.route("/result/<job_id>", methods=["GET"])
    def result(job_id: str):
        results = load_job_results(job_id)
        summary = summarize_results(results)
        return render_template("result.html", job_id=job_id, results=results, summary=summary)

    @app.route("/report/<job_id>.pdf", methods=["GET"])
    def report(job_id: str):
        results = load_job_results(job_id)
        summary = summarize_results(results)
        pdf_path = build_pdf_report(job_id, results, summary)
        return send_file(pdf_path, as_attachment=True, download_name=f"static-code-analyzer-{job_id}.pdf")

    return app
