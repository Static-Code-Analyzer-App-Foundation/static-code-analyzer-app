from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

from .config import REPORT_DIR


def build_pdf_report(job_id: str, results: list[dict], summary: dict) -> Path:
    """
    Build a polished PDF report for static code analysis results.

    Expected result row keys:
        - file_name
        - language
        - analyzer_name
        - score
    """

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = REPORT_DIR / f"{job_id}.pdf"

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "SubtitleCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#475569"),
        spaceAfter=10,
    )

    section_style = ParagraphStyle(
        "SectionCustom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        leading=15,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=8,
        spaceAfter=6,
    )

    normal_style = ParagraphStyle(
        "NormalCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1f2937"),
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.white,
        alignment=TA_LEFT,
    )

    cell_style = ParagraphStyle(
        "Cell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=10,
        textColor=colors.HexColor("#111827"),
    )

    def para(text: Any, style: ParagraphStyle = cell_style) -> Paragraph:
        safe_text = "" if text is None else str(text)
        return Paragraph(safe_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), style)

    def score_color(score: float) -> colors.Color:
        if score >= 85:
            return colors.HexColor("#166534")  # green
        if score >= 70:
            return colors.HexColor("#a16207")  # amber
        return colors.HexColor("#b91c1c")      # red

    def _build_page(canvas, doc):
        canvas.saveState()

        # Top line
        canvas.setStrokeColor(colors.HexColor("#cbd5e1"))
        canvas.setLineWidth(0.6)
        canvas.line(doc.leftMargin, A4[1] - 10 * mm, A4[0] - doc.rightMargin, A4[1] - 10 * mm)

        # Header
        canvas.setFont("Helvetica-Bold", 9)
        canvas.setFillColor(colors.HexColor("#334155"))
        canvas.drawString(doc.leftMargin, A4[1] - 7.5 * mm, "Static Code Analyzer Report")

        # Footer
        canvas.setStrokeColor(colors.HexColor("#e2e8f0"))
        canvas.line(doc.leftMargin, 12 * mm, A4[0] - doc.rightMargin, 12 * mm)

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(doc.leftMargin, 8.2 * mm, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        canvas.drawRightString(A4[0] - doc.rightMargin, 8.2 * mm, f"Page {canvas.getPageNumber()}")

        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="Static Code Analyzer Report",
        author="Static Code Analyzer",
        subject="Static code analysis results",
        creator="Static Code Analyzer",
    )

    story: list[Any] = []

    # Title block
    story.append(Paragraph("Static Code Analyzer Report", title_style))
    story.append(Paragraph(f"Job ID: <b>{job_id}</b>", subtitle_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
    story.append(Spacer(1, 6))

    # Quick stats
    total_files = len(results)
    languages = len(summary)
    avg_score = round(
        sum(float(row.get("score", 0) or 0) for row in results) / total_files, 1
    ) if total_files else 0.0

    stats_data = [
        [
            para("Total Files", table_header_style),
            para("Languages", table_header_style),
            para("Average Score", table_header_style),
        ],
        [
            para(total_files, normal_style),
            para(languages, normal_style),
            para(f"{avg_score}%", normal_style),
        ],
    ]

    stats_table = Table(stats_data, colWidths=[55 * mm, 55 * mm, 55 * mm])
    stats_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.HexColor("#e2e8f0")]),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.extend([stats_table, Spacer(1, 10)])

    # Summary section
    story.append(Paragraph("Language Summary", section_style))

    summary_data = [
        [
            para("Language", table_header_style),
            para("Files", table_header_style),
            para("Average Score", table_header_style),
        ]
    ]

    for lang, data in sorted(summary.items(), key=lambda x: str(x[0]).lower()):
        count = data.get("count", 0)
        average_score = data.get("average_score", 0)
        summary_data.append([
            para(lang, cell_style),
            para(count, cell_style),
            para(f"{average_score}%", cell_style),
        ])

    summary_table = Table(summary_data, colWidths=[80 * mm, 35 * mm, 45 * mm], repeatRows=1)
    summary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ])
    )
    story.extend([summary_table, Spacer(1, 12)])

    # Details section
    story.append(Paragraph("File Results", section_style))
    story.append(Paragraph(
        "Each row shows the file analyzed, the detected language, the analyzer used, and the final score.",
        normal_style
    ))
    story.append(Spacer(1, 6))

    detail_data = [
        [
            para("File", table_header_style),
            para("Language", table_header_style),
            para("Analyzer", table_header_style),
            para("Score", table_header_style),
        ]
    ]

    for row in results:
        file_name = row.get("file_name", "")
        language = row.get("language", "")
        analyzer_name = row.get("analyzer_name", "")
        score = float(row.get("score", 0) or 0)

        detail_data.append([
            para(file_name, cell_style),
            para(language, cell_style),
            para(analyzer_name, cell_style),
            para(f"{score}%", cell_style),
        ])

    detail_table = Table(
        detail_data,
        repeatRows=1,
        colWidths=[78 * mm, 28 * mm, 48 * mm, 18 * mm],
    )

    table_style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("FONTSIZE", (0, 0), (-1, -1), 8.4),
    ]

    # Highlight score cells by quality
    for i, row in enumerate(results, start=1):
        score = float(row.get("score", 0) or 0)
        table_style_commands.append(
            ("TEXTCOLOR", (3, i), (3, i), score_color(score))
        )
        table_style_commands.append(
            ("FONTNAME", (3, i), (3, i), "Helvetica-Bold")
        )

    detail_table.setStyle(TableStyle(table_style_commands))
    story.append(detail_table)

    if not results:
        story.append(Spacer(1, 12))
        story.append(Paragraph("No file results were generated for this job.", normal_style))

    doc.build(story, onFirstPage=_build_page, onLaterPages=_build_page)
    return pdf_path
