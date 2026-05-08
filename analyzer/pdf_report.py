from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
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
    KeepTogether,
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
        - details (optional)
            - metrics (dict, optional)
            - findings (list[dict], optional)
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
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "SubtitleCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#475569"),
        spaceAfter=2,
    )

    section_style = ParagraphStyle(
        "SectionCustom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=6,
        spaceAfter=6,
    )

    small_section_style = ParagraphStyle(
        "SmallSectionCustom",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=4,
        spaceAfter=4,
    )

    body_style = ParagraphStyle(
        "BodyCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1f2937"),
    )

    muted_style = ParagraphStyle(
        "MutedCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#64748b"),
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=10.5,
        textColor=colors.white,
        alignment=TA_LEFT,
    )

    center_header_style = ParagraphStyle(
        "CenterHeader",
        parent=table_header_style,
        alignment=TA_CENTER,
    )

    cell_style = ParagraphStyle(
        "Cell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.4,
        leading=10.2,
        textColor=colors.HexColor("#111827"),
    )

    cell_center_style = ParagraphStyle(
        "CellCenter",
        parent=cell_style,
        alignment=TA_CENTER,
    )

    cell_right_style = ParagraphStyle(
        "CellRight",
        parent=cell_style,
        alignment=TA_RIGHT,
    )

    def para(text: Any, style: ParagraphStyle = cell_style) -> Paragraph:
        safe_text = "" if text is None else escape(str(text))
        return Paragraph(safe_text, style)

    def clean_score(value: Any) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    def score_color(score: float) -> colors.Color:
        if score >= 85:
            return colors.HexColor("#166534")
        if score >= 70:
            return colors.HexColor("#a16207")
        if score >= 50:
            return colors.HexColor("#c2410c")
        return colors.HexColor("#b91c1c")

    def score_band(score: float) -> str:
        if score >= 85:
            return "Good"
        if score >= 70:
            return "Fair"
        if score >= 50:
            return "Weak"
        return "Poor"

    def severity_band(severity: Any) -> tuple[str, colors.Color]:
        sev = str(severity or "").strip().lower()
        if sev in {"critical", "high"}:
            return sev.title(), colors.HexColor("#b91c1c")
        if sev == "medium":
            return "Medium", colors.HexColor("#c2410c")
        if sev == "low":
            return "Low", colors.HexColor("#a16207")
        if sev:
            return sev.title(), colors.HexColor("#334155")
        return "Info", colors.HexColor("#475569")

    def table_style(header_bg: str = "#1e293b", row_alt: str = "#f8fafc") -> TableStyle:
        return TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_bg)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(row_alt)]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ])

    def _build_page(canvas, doc):
        canvas.saveState()

        page_w, page_h = doc.pagesize

        canvas.setStrokeColor(colors.HexColor("#cbd5e1"))
        canvas.setLineWidth(0.6)
        canvas.line(doc.leftMargin, page_h - 10 * mm, page_w - doc.rightMargin, page_h - 10 * mm)

        canvas.setFont("Helvetica-Bold", 9)
        canvas.setFillColor(colors.HexColor("#334155"))
        canvas.drawString(doc.leftMargin, page_h - 7.7 * mm, "Static Code Analyzer Report")

        canvas.setStrokeColor(colors.HexColor("#e2e8f0"))
        canvas.line(doc.leftMargin, 12 * mm, page_w - doc.rightMargin, 12 * mm)

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(doc.leftMargin, 8.2 * mm, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        canvas.drawRightString(page_w - doc.rightMargin, 8.2 * mm, f"Page {canvas.getPageNumber()}")

        canvas.restoreState()

    total_files = len(results)
    total_languages = len(summary)

    total_findings = 0
    total_score = 0.0
    scored_files = 0

    for row in results:
        score = clean_score(row.get("score", 0))
        total_score += score
        scored_files += 1

        details = row.get("details") or {}
        findings = details.get("findings") if isinstance(details, dict) else []
        if isinstance(findings, list):
            total_findings += len(findings)

    avg_score = round(total_score / scored_files, 1) if scored_files else 0.0

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
    story.append(Paragraph(f"Job ID: <b>{escape(job_id)}</b>", subtitle_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
    story.append(Spacer(1, 6))

    # Overview cards
    overview_data = [
        [
            para("Total Files", center_header_style),
            para("Languages", center_header_style),
            para("Average Score", center_header_style),
            para("Findings", center_header_style),
        ],
        [
            para(total_files, cell_center_style),
            para(total_languages, cell_center_style),
            para(f"{avg_score}%", cell_center_style),
            para(total_findings, cell_center_style),
        ],
    ]
    overview_table = Table(overview_data, colWidths=[43 * mm, 43 * mm, 43 * mm, 43 * mm])
    overview_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.HexColor("#e2e8f0")]),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.extend([overview_table, Spacer(1, 10)])

    # Guidance block
    story.append(Paragraph("Report Notes", section_style))
    story.append(Paragraph(
        "Scores are grouped as Good (85+), Fair (70-84), Weak (50-69), and Poor (below 50). "
        "Findings are listed per file so the report stays actionable.",
        body_style,
    ))
    story.append(Spacer(1, 8))

    # Language summary
    story.append(Paragraph("Language Summary", section_style))

    summary_data = [[
        para("Language", table_header_style),
        para("Files", center_header_style),
        para("Average Score", center_header_style),
    ]]

    if summary:
        for lang, data in sorted(summary.items(), key=lambda x: str(x[0]).lower()):
            count = data.get("count", 0) if isinstance(data, dict) else 0
            average_score = data.get("average_score", 0) if isinstance(data, dict) else 0
            summary_data.append([
                para(lang, cell_style),
                para(count, cell_center_style),
                para(f"{average_score}%", cell_center_style),
            ])
    else:
        summary_data.append([
            para("No analyzable language detected", cell_style),
            para("-", cell_center_style),
            para("-", cell_center_style),
        ])

    summary_table = Table(summary_data, colWidths=[90 * mm, 35 * mm, 45 * mm], repeatRows=1)
    summary_table.setStyle(table_style(header_bg="#0f172a"))
    story.extend([summary_table, Spacer(1, 12)])

    # File-level table
    story.append(Paragraph("File Results", section_style))
    story.append(Paragraph(
        "This section gives a compact view of every analyzed file and its final score.",
        body_style,
    ))
    story.append(Spacer(1, 5))

    detail_data = [[
        para("File", table_header_style),
        para("Language", center_header_style),
        para("Analyzer", center_header_style),
        para("Score", center_header_style),
        para("Band", center_header_style),
    ]]

    for row in results:
        file_name = row.get("file_name", "")
        language = row.get("language", "")
        analyzer_name = row.get("analyzer_name", "")
        score = clean_score(row.get("score", 0))

        detail_data.append([
            para(file_name, cell_style),
            para(language, cell_center_style),
            para(analyzer_name, cell_center_style),
            para(f"{score}%", cell_center_style),
            para(score_band(score), cell_center_style),
        ])

    if len(detail_data) == 1:
        detail_data.append([
            para("No file results were generated for this job.", cell_style),
            para("-", cell_center_style),
            para("-", cell_center_style),
            para("-", cell_center_style),
            para("-", cell_center_style),
        ])

    detail_table = Table(
        detail_data,
        repeatRows=1,
        colWidths=[64 * mm, 27 * mm, 44 * mm, 18 * mm, 24 * mm],
    )

    detail_style_commands = table_style(header_bg="#1e293b")
    detail_style_commands.add("ALIGN", (1, 1), (-1, -1), "CENTER")
    detail_style_commands.add("FONTNAME", (3, 1), (3, -1), "Helvetica-Bold")
    detail_style_commands.add("TEXTCOLOR", (3, 1), (3, -1), colors.HexColor("#0f172a"))

    for i, row in enumerate(results, start=1):
        score = clean_score(row.get("score", 0))
        detail_style_commands.add("TEXTCOLOR", (3, i), (3, i), score_color(score))

    detail_table.setStyle(detail_style_commands)
    story.append(detail_table)

    # Detailed per-file findings
    if results:
        story.append(PageBreak())
        story.append(Paragraph("Per-File Analysis", section_style))
        story.append(Paragraph(
            "Each file below includes its score, key metrics, and all findings returned by the analyzers.",
            body_style,
        ))
        story.append(Spacer(1, 8))

        for idx, row in enumerate(results, start=1):
            file_name = row.get("file_name", "Unknown file")
            language = row.get("language", "Unknown")
            analyzer_name = row.get("analyzer_name", "Unknown analyzer")
            score = clean_score(row.get("score", 0))
            details = row.get("details") or {}
            metrics = details.get("metrics") if isinstance(details, dict) else {}
            findings = details.get("findings") if isinstance(details, dict) else []

            block: list[Any] = []

            header_tbl = Table(
                [[
                    para(f"{idx}. {file_name}", ParagraphStyle(
                        "FileTitle",
                        parent=body_style,
                        fontName="Helvetica-Bold",
                        fontSize=10.5,
                        leading=13,
                        textColor=colors.HexColor("#0f172a"),
                    )),
                    para(f"{score}% ({score_band(score)})", ParagraphStyle(
                        "ScoreBadge",
                        parent=body_style,
                        fontName="Helvetica-Bold",
                        fontSize=10,
                        leading=12,
                        alignment=TA_RIGHT,
                        textColor=score_color(score),
                    )),
                ]],
                colWidths=[150 * mm, 35 * mm],
            )
            header_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ]))
            block.append(header_tbl)
            block.append(Spacer(1, 5))

            meta_tbl = Table(
                [
                    [para("Language", table_header_style), para(language, cell_style)],
                    [para("Analyzer", table_header_style), para(analyzer_name, cell_style)],
                    [para("Findings", table_header_style), para(len(findings) if isinstance(findings, list) else 0, cell_style)],
                ],
                colWidths=[35 * mm, 150 * mm],
            )
            meta_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#1e293b")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            block.append(meta_tbl)
            block.append(Spacer(1, 5))

            metric_rows = [[para("Metric", table_header_style), para("Value", center_header_style)]]
            if isinstance(metrics, dict) and metrics:
                for key, value in metrics.items():
                    metric_rows.append([para(key, cell_style), para(value, cell_center_style)])
            else:
                metric_rows.append([para("No metrics returned", cell_style), para("-", cell_center_style)])

            metric_tbl = Table(metric_rows, colWidths=[70 * mm, 115 * mm], repeatRows=1)
            metric_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            block.append(Paragraph("Metrics", small_section_style))
            block.append(metric_tbl)
            block.append(Spacer(1, 5))

            block.append(Paragraph("Findings", small_section_style))
            if isinstance(findings, list) and findings:
                finding_rows = [[
                    para("Severity", table_header_style),
                    para("Rule", center_header_style),
                    para("Message", center_header_style),
                    para("Impact", center_header_style),
                ]]

                for finding in findings:
                    severity_label, sev_color = severity_band(finding.get("severity"))
                    rule = finding.get("rule", "Unknown rule")
                    message = finding.get("message", "")
                    impact = finding.get("score_impact", 0)

                    finding_rows.append([
                        Paragraph(
                            f'<font color="{sev_color.hexval()}"><b>{escape(severity_label)}</b></font>',
                            cell_style,
                        ),
                        para(rule, cell_style),
                        para(message, cell_style),
                        para(f"-{impact}", cell_center_style),
                    ])

                findings_tbl = Table(
                    finding_rows,
                    colWidths=[28 * mm, 42 * mm, 96 * mm, 19 * mm],
                    repeatRows=1,
                )
                findings_tbl.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#cbd5e1")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (3, 1), (3, -1), "CENTER"),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]))
                block.append(findings_tbl)
            else:
                block.append(Paragraph("No findings recorded for this file.", muted_style))

            story.append(KeepTogether(block))
            story.append(Spacer(1, 10))

    doc.build(story, onFirstPage=_build_page, onLaterPages=_build_page)
    return pdf_path
