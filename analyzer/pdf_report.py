from __future__ import annotations
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from .config import REPORT_DIR

def build_pdf_report(job_id: str, results: list[dict], summary: dict) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = REPORT_DIR / f"{job_id}.pdf"

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, rightMargin=12*mm, leftMargin=12*mm, topMargin=12*mm, bottomMargin=12*mm)

    story = [
        Paragraph("Static Code Analyzer Report", styles["Title"]),
        Spacer(1, 6),
        Paragraph(f"Job ID: {job_id}", styles["Normal"]),
        Spacer(1, 10),
    ]

    summary_data = [["Language", "Files", "Average Score"]]
    for lang, data in sorted(summary.items()):
        summary_data.append([lang, str(data["count"]), f'{data["average_score"]}%'])

    summary_table = Table(summary_data, repeatRows=1)
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [Paragraph("Summary", styles["Heading2"]), summary_table, Spacer(1, 12)]

    detail_data = [["File", "Language", "Analyzer", "Score"]]
    for row in results:
        detail_data.append([row["file_name"], row["language"], row["analyzer_name"], f'{row["score"]}%'])
    detail_table = Table(detail_data, repeatRows=1, colWidths=[85*mm, 30*mm, 45*mm, 20*mm])
    detail_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [Paragraph("File Results", styles["Heading2"]), detail_table]

    doc.build(story)
    return pdf_path
