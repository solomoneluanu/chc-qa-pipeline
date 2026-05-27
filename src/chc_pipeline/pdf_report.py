import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image, PageBreak,
    HRFlowable, KeepTogether
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime


def dataframe_to_table_data(df):
    data = [list(df.columns)]
    for _, row in df.iterrows():
        data.append([str(v) if v is not None else "-" for v in row])
    return data


def styled_table(df, col_widths=None):
    data = dataframe_to_table_data(df)
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#1565C0")),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  9),
        ("FONTSIZE",      (0, 1), (-1, -1), 8.5),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("ALIGN",         (0, 1), (0, -1),  "LEFT"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [
            colors.white,
            colors.HexColor("#F0F7FF")
        ]),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("LINEBELOW",     (0, 0), (-1, 0),  1.5, colors.HexColor("#1565C0")),
    ]))
    return table


def kv_table(rows, col_widths=None):
    table = Table(rows, colWidths=col_widths or [4.2*inch, 1.8*inch])
    table.setStyle(TableStyle([
        ("FONTSIZE",      (0, 0), (-1, -1), 8.5),
        ("FONTNAME",      (0, 0), (0, -1),  "Helvetica"),
        ("FONTNAME",      (1, 0), (1, -1),  "Helvetica-Bold"),
        ("ALIGN",         (0, 0), (0, -1),  "LEFT"),
        ("ALIGN",         (1, 0), (1, -1),  "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
        ("ROWBACKGROUNDS",(0, 0), (-1, -1), [
            colors.white,
            colors.HexColor("#F8FAFC")
        ]),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
    ]))
    return table


def add_figure_if_exists(story, title, path, styles,
                          width=6.5*inch, height=3.8*inch):
    if os.path.exists(path):
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(title, styles["FigureTitle"]))
        story.append(Spacer(1, 0.06*inch))
        story.append(Image(path, width=width, height=height))
        story.append(Spacer(1, 0.25*inch))


def section_header(title, styles):
    return [
        HRFlowable(
            width="100%", thickness=2,
            color=colors.HexColor("#1565C0"),
            spaceAfter=4
        ),
        Paragraph(title, styles["SectionTitle"]),
        Spacer(1, 0.08*inch),
    ]


def build_pdf_report(results, figure_dir, output_pdf,
                     summary_text=None, insights=None):
    os.makedirs(os.path.dirname(output_pdf), exist_ok=True)

    # Page with header and footer
    def on_page(canvas, doc):
        canvas.saveState()

        # Header bar
        canvas.setFillColor(colors.HexColor("#1565C0"))
        canvas.rect(0, letter[1] - 28, letter[0], 28, fill=1, stroke=0)

        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(colors.white)
        canvas.drawString(50, letter[1] - 18,
            "CHC-QA Pipeline | Cytology-Histology Correlation Report")
        canvas.drawRightString(letter[0] - 50, letter[1] - 18,
            f"CAP CYP.06600 | ASC Birdsong Guideline 2017")

        # Footer bar
        canvas.setFillColor(colors.HexColor("#F1F5F9"))
        canvas.rect(0, 0, letter[0], 24, fill=1, stroke=0)

        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawString(50, 8,
            f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')} | "
            f"github.com/solomoneluanu/chc-qa-pipeline")
        canvas.drawRightString(letter[0] - 50, 8,
            f"Page {doc.page}")

        canvas.restoreState()

    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=letter,
        rightMargin=50, leftMargin=50,
        topMargin=55,   bottomMargin=40,
        onFirstPage=on_page,
        onLaterPages=on_page
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        textColor=colors.HexColor("#0D47A1"),
        fontSize=22,
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        name="ReportSubtitle",
        parent=styles["Normal"],
        textColor=colors.HexColor("#475569"),
        fontSize=11,
        spaceAfter=4,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="SectionTitle",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#1565C0"),
        spaceAfter=6,
        spaceBefore=4,
        fontSize=12,
        fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        name="SubTitle",
        parent=styles["Heading3"],
        textColor=colors.HexColor("#334155"),
        spaceAfter=5,
        spaceBefore=8,
        fontSize=10,
        fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        name="BodySmall",
        parent=styles["BodyText"],
        fontSize=9,
        leading=14,
        textColor=colors.HexColor("#1E293B")
    ))
    styles.add(ParagraphStyle(
        name="Caption",
        parent=styles["BodyText"],
        fontSize=8,
        textColor=colors.HexColor("#64748B"),
        leading=11,
        spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name="AlertRed",
        parent=styles["BodyText"],
        textColor=colors.HexColor("#B91C1C"),
        fontSize=9,
        fontName="Helvetica-Bold",
        leading=14
    ))
    styles.add(ParagraphStyle(
        name="AlertGreen",
        parent=styles["BodyText"],
        textColor=colors.HexColor("#15803D"),
        fontSize=9,
        fontName="Helvetica-Bold",
        leading=14
    ))
    styles.add(ParagraphStyle(
        name="AlertOrange",
        parent=styles["BodyText"],
        textColor=colors.HexColor("#C2410C"),
        fontSize=9,
        fontName="Helvetica-Bold",
        leading=14
    ))
    styles.add(ParagraphStyle(
        name="FigureTitle",
        parent=styles["Normal"],
        textColor=colors.HexColor("#475569"),
        fontSize=9,
        fontName="Helvetica-Bold",
        spaceAfter=2
    ))

    story = []

    # ?? Cover Page ????????????????????????????????????????????????????????????
    story.append(Spacer(1, 0.5*inch))

    # Blue header banner
    cover_data = [[
        Paragraph(
            "CERVICAL CYTOLOGY-HISTOLOGY CORRELATION<br/>QUALITY ASSURANCE REPORT",
            ParagraphStyle(
                "CoverTitle",
                parent=styles["Normal"],
                textColor=colors.white,
                fontSize=18,
                fontName="Helvetica-Bold",
                alignment=TA_CENTER,
                leading=26
            )
        )
    ]]
    cover_table = Table(cover_data, colWidths=[6.5*inch])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1565C0")),
        ("TOPPADDING",    (0, 0), (-1, -1), 24),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 24),
        ("LEFTPADDING",   (0, 0), (-1, -1), 20),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 20),
        ("ROUNDEDCORNERS", [8]),
    ]))
    story.append(cover_table)
    story.append(Spacer(1, 0.25*inch))

    # Guideline reference
    story.append(Paragraph(
        "Per ASC Clinical Practice Committee Birdsong Guideline 2017",
        styles["ReportSubtitle"]
    ))
    story.append(Paragraph(
        "CAP Accreditation Checklist Requirement CYP.06600",
        styles["ReportSubtitle"]
    ))
    story.append(Spacer(1, 0.4*inch))

    # Summary stats box
    total      = results.get("total_cases", 0)
    concordant = results.get("concordance_counts", {}).get("concordant", 0)
    major      = results.get("concordance_counts", {}).get("major_discordant", 0)
    minor      = results.get("concordance_counts", {}).get("minor_discordant", 0)
    major_rate = results.get("concordance_percentages", {}).get("major_discordant", 0)
    hsil_pv    = results.get("hsil_pv_plus", 0) or 0
    pv_flag    = results.get("hsil_pv_interpretation", "")
    major_fn   = results.get("major_fn_count", 0)

    summary_data = [
        [
            Paragraph("Total Cases", styles["Caption"]),
            Paragraph("Concordant", styles["Caption"]),
            Paragraph("Major Discordant", styles["Caption"]),
            Paragraph("HSIL PV+", styles["Caption"]),
        ],
        [
            Paragraph(f"<b>{total}</b>",
                ParagraphStyle("SN", parent=styles["Normal"],
                    fontSize=22, fontName="Helvetica-Bold",
                    textColor=colors.HexColor("#1565C0"),
                    alignment=TA_CENTER)),
            Paragraph(f"<b>{concordant}</b>",
                ParagraphStyle("SN", parent=styles["Normal"],
                    fontSize=22, fontName="Helvetica-Bold",
                    textColor=colors.HexColor("#15803D"),
                    alignment=TA_CENTER)),
            Paragraph(f"<b>{major}</b>",
                ParagraphStyle("SN", parent=styles["Normal"],
                    fontSize=22, fontName="Helvetica-Bold",
                    textColor=colors.HexColor("#B91C1C"),
                    alignment=TA_CENTER)),
            Paragraph(f"<b>{hsil_pv:.1f}%</b>",
                ParagraphStyle("SN", parent=styles["Normal"],
                    fontSize=22, fontName="Helvetica-Bold",
                    textColor=colors.HexColor("#B91C1C") if hsil_pv < 60
                              else colors.HexColor("#15803D"),
                    alignment=TA_CENTER)),
        ],
        [
            Paragraph("cases analyzed", styles["Caption"]),
            Paragraph(f"{concordant/total*100:.1f}%" if total > 0 else "-",
                ParagraphStyle("SP", parent=styles["Normal"],
                    fontSize=10, textColor=colors.HexColor("#15803D"),
                    alignment=TA_CENTER, fontName="Helvetica-Bold")),
            Paragraph(f"{major_rate:.1f}%",
                ParagraphStyle("SP", parent=styles["Normal"],
                    fontSize=10, textColor=colors.HexColor("#B91C1C"),
                    alignment=TA_CENTER, fontName="Helvetica-Bold")),
            Paragraph("Target: >60%", styles["Caption"]),
        ]
    ]

    summary_table = Table(
        summary_data,
        colWidths=[1.6*inch]*4
    )
    summary_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX",           (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ("LINEAFTER",     (0, 0), (2, -1),  0.5, colors.HexColor("#CBD5E1")),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))

    # CAP status alerts
    if major_rate > 10:
        alert_data = [[Paragraph(
            f"CAP ALERT: Major discordance rate of {major_rate:.1f}% exceeds the "
            f"CAP benchmark of less than 10%. Corrective action documentation "
            f"required per CYP.06600.",
            ParagraphStyle("AT", parent=styles["Normal"],
                textColor=colors.HexColor("#B91C1C"),
                fontSize=9, fontName="Helvetica-Bold", leading=14)
        )]]
        alert_bg = colors.HexColor("#FEF2F2")
        alert_border = colors.HexColor("#FCA5A5")
    else:
        alert_data = [[Paragraph(
            f"CAP STATUS: Major discordance rate of {major_rate:.1f}% is within "
            f"the CAP benchmark of less than 10%.",
            ParagraphStyle("AT", parent=styles["Normal"],
                textColor=colors.HexColor("#15803D"),
                fontSize=9, fontName="Helvetica-Bold", leading=14)
        )]]
        alert_bg = colors.HexColor("#F0FDF4")
        alert_border = colors.HexColor("#86EFAC")

    alert_table_obj = Table(alert_data, colWidths=[6.5*inch])
    alert_table_obj.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), alert_bg),
        ("BOX",           (0, 0), (-1, -1), 1.5, alert_border),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
    ]))
    story.append(alert_table_obj)
    story.append(Spacer(1, 0.1*inch))

    if hsil_pv > 0 and hsil_pv < 60:
        pv_data = [[Paragraph(
            f"PV+ ALERT: HSIL positive predictive value of {hsil_pv:.1f}% falls "
            f"below the CAP target of 60%. Review HSIL overcall rate.",
            ParagraphStyle("AT", parent=styles["Normal"],
                textColor=colors.HexColor("#B91C1C"),
                fontSize=9, fontName="Helvetica-Bold", leading=14)
        )]]
        pv_tbl = Table(pv_data, colWidths=[6.5*inch])
        pv_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#FEF2F2")),
            ("BOX",           (0, 0), (-1, -1), 1.5, colors.HexColor("#FCA5A5")),
            ("TOPPADDING",    (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ]))
        story.append(pv_tbl)
        story.append(Spacer(1, 0.1*inch))

    if major_fn > 0:
        fn_data = [[Paragraph(
            f"MAJOR FALSE NEGATIVES: {int(major_fn)} major undercall cases identified. "
            f"All require mandatory slide review per Birdsong Section 8.",
            ParagraphStyle("AT", parent=styles["Normal"],
                textColor=colors.HexColor("#B91C1C"),
                fontSize=9, fontName="Helvetica-Bold", leading=14)
        )]]
        fn_tbl = Table(fn_data, colWidths=[6.5*inch])
        fn_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#FFF7ED")),
            ("BOX",           (0, 0), (-1, -1), 1.5, colors.HexColor("#FDBA74")),
            ("TOPPADDING",    (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ]))
        story.append(fn_tbl)

    story.append(Spacer(1, 0.3*inch))

    # Executive summary
    story.extend(section_header("Executive Summary", styles))
    exec_text = summary_text or (
        f"A total of {results.get('total_cases')} cytology-histology pairs were analyzed "
        f"using an automated deterministic QA pipeline aligned with the American Society "
        f"of Cytopathology (ASC) Birdsong Guideline 2017 and CAP checklist requirement "
        f"CYP.06600. Classification rules were derived directly from Birdsong Figure 1. "
        f"This report presents concordance distribution, HSIL-focused metrics, "
        f"intergrade follow-up rates per Birdsong Section 8, discrepancy bucket analysis "
        f"per Figure 3, and key quality signals with CAP benchmark comparisons."
    )
    story.append(Paragraph(exec_text, styles["BodySmall"]))
    story.append(PageBreak())

    # ?? Section 1: Concordance Summary ???????????????????????????????????????
    story.extend(section_header("Section 1 - Concordance Summary", styles))
    story.append(Paragraph(
        "Classification of all cytology-histology pairs per ASC Birdsong concordance definitions.",
        styles["Caption"]
    ))
    story.append(Spacer(1, 0.1*inch))
    story.append(styled_table(
        results["concordance_table"],
        col_widths=[3.0*inch, 1.5*inch, 1.5*inch]
    ))
    story.append(Spacer(1, 0.2*inch))

    # Agreement within one grade
    within_one     = results.get("agreement_within_one_grade", 0)
    within_one_pct = results.get("agreement_within_one_pct", 0)

    story.append(Paragraph(
        "Agreement Within One Grade (Birdsong Section 5)",
        styles["SubTitle"]
    ))
    story.append(Paragraph(
        "Percentage of pairs with exact agreement or minor disagreement only. "
        "Per Birdsong, this metric is of educational interest but not statistically "
        "meaningful due to verification bias.",
        styles["Caption"]
    ))
    story.append(Spacer(1, 0.08*inch))

    within_rows = [
        ["Metric", "Count", "Percentage"],
        ["Agreement within one grade (concordant + minor)", str(within_one), f"{within_one_pct:.1f}%"],
        ["Exact agreement only",
         str(results.get("concordance_counts", {}).get("concordant", 0)),
         f"{results.get('concordance_percentages', {}).get('concordant', 0):.1f}%"],
        ["Major discordance (outside one grade)",
         str(results.get("concordance_counts", {}).get("major_discordant", 0)),
         f"{results.get('concordance_percentages', {}).get('major_discordant', 0):.1f}%"],
    ]
    story.append(kv_table(within_rows, col_widths=[3.5*inch, 1.2*inch, 1.2*inch]))
    story.append(Spacer(1, 0.25*inch))

    # ?? Section 2: Discrepancy Buckets ????????????????????????????????????????
    story.extend(section_header("Section 2 - Discrepancy Bucket Summary", styles))
    story.append(Paragraph(
        "CAP-style discrepancy classification per Birdsong Figure 1 and Figure 3. "
        "Undercall = cytology less severe than histology. "
        "Overcall = cytology more severe than histology.",
        styles["Caption"]
    ))
    story.append(Spacer(1, 0.1*inch))
    story.append(styled_table(
        results["bucket_table"],
        col_widths=[2.5*inch, 1.5*inch, 1.5*inch]
    ))
    story.append(Spacer(1, 0.25*inch))

    # ?? Section 3: HSIL Metrics ???????????????????????????????????????????????
    story.extend(section_header(
        "Section 3 - HSIL-Focused Metrics (Birdsong Section 7)",
        styles
    ))
    story.append(Paragraph(
        "The five statistical calculations required by Birdsong Section 7 "
        "and the ASC Clinical Practice Committee. These are the primary "
        "performance metrics for cytopathology quality assurance.",
        styles["Caption"]
    ))
    story.append(Spacer(1, 0.1*inch))
    story.append(styled_table(
        results["hsil_pv_table"],
        col_widths=[4.5*inch, 1.5*inch]
    ))
    story.append(Spacer(1, 0.15*inch))

    # PV+ interpretation
    story.append(Paragraph(
        "PV+ Interpretation (Birdsong Section 7a)",
        styles["SubTitle"]
    ))
    pv_style = "AlertRed" if (hsil_pv < 60 or hsil_pv > 95) else "AlertGreen"
    story.append(Paragraph(pv_flag, styles[pv_style]))
    story.append(Spacer(1, 0.15*inch))

    # Extended PV+
    ext_pv     = results.get("extended_pv_plus")
    total_hg   = results.get("total_high_grade_paps", 0)
    hg_to_hsil = results.get("high_grade_to_hsil", 0)

    story.append(Paragraph(
        "Extended PV+ - High-Grade Cytology Group (HSIL + ASC-H + AGC-NEO)",
        styles["SubTitle"]
    ))
    story.append(Paragraph(
        "Per Birdsong Figure 1, HSIL, ASC-H, and AGC-NEO cytology diagnoses are "
        "grouped together for concordance assessment. The extended PV+ reflects "
        "combined performance of the entire high-grade cytology group.",
        styles["Caption"]
    ))
    story.append(Spacer(1, 0.08*inch))

    ext_rows = [
        ["Metric", "Value"],
        ["Total high-grade Pap tests (HSIL + ASC-H + AGC-NEO)", str(total_hg)],
        ["High-grade Pap tests with HSIL+ histology", str(hg_to_hsil)],
        ["Extended PV+", f"{ext_pv:.1f}%" if ext_pv is not None else "N/A"],
    ]
    story.append(kv_table(ext_rows, col_widths=[4.5*inch, 1.5*inch]))
    story.append(Spacer(1, 0.25*inch))

    # ?? Section 4: Intergrade Follow-Up ???????????????????????????????????????
    story.extend(section_header(
        "Section 4 - Intergrade Follow-Up Rates (Birdsong Section 8)",
        styles
    ))
    story.append(Paragraph(
        "Per Birdsong Section 8: careful review of rates of HSIL histology following "
        "cytologic interpretations of ASC-US, ASC-H, and LSIL might reveal opportunities "
        "for improvement. Elevated rates may indicate systematic cytologic undercalling.",
        styles["Caption"]
    ))
    story.append(Spacer(1, 0.1*inch))

    intergrade = results.get("intergrade_table")
    if intergrade is not None and len(intergrade) > 0:
        story.append(styled_table(
            intergrade,
            col_widths=[2.0*inch, 1.5*inch, 1.5*inch, 1.5*inch]
        ))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(
            "Clinical interpretation: ASC-US to HSIL+ rates above 15-20% or "
            "LSIL to HSIL+ rates above 20-25% may indicate undercalling patterns "
            "requiring targeted educational slide review.",
            styles["Caption"]
        ))
    else:
        story.append(Paragraph(
            "Insufficient data for intergrade analysis.",
            styles["BodySmall"]
        ))
    story.append(Spacer(1, 0.25*inch))

    # ?? Section 5: Key Quality Signals ????????????????????????????????????????
    story.extend(section_header("Section 5 - Key Quality Signals", styles))
    story.append(Paragraph(
        "Summary of key performance indicators with CAP benchmark comparisons. "
        "Status reflects comparison against published CAP and ASC thresholds.",
        styles["Caption"]
    ))
    story.append(Spacer(1, 0.1*inch))

    key_signals = results.get("key_signals", {})
    signal_rows = [
        ["Quality Signal", "Value", "CAP Threshold", "Status"],
        [
            "Major discordance rate",
            f"{key_signals.get('major_discordance_rate', 0):.1f}%",
            "< 10%",
            "EXCEEDS" if key_signals.get("major_disc_exceeds_cap") else "OK"
        ],
        [
            "Minor discordance rate",
            f"{key_signals.get('minor_discordance_rate', 0):.1f}%",
            "No threshold", "-"
        ],
        [
            "Undercall proportion",
            f"{key_signals.get('undercall_proportion', 0):.1f}%",
            "< 15%",
            "EXCEEDS" if key_signals.get("undercall_proportion", 0) > 15 else "OK"
        ],
        [
            "Overcall proportion",
            f"{key_signals.get('overcall_proportion', 0):.1f}%",
            "No threshold", "-"
        ],
        [
            "HSIL PV+ (positive predictive value)",
            f"{key_signals.get('hsil_pv_plus', 0) or 0:.1f}%",
            "> 60%",
            "LOW" if key_signals.get("pv_below_cap_target") else "OK"
        ],
        [
            "Extended PV+ (HSIL + ASC-H + AGC-NEO)",
            f"{key_signals.get('extended_pv_plus', 0) or 0:.1f}%",
            "> 60%",
            "LOW" if (key_signals.get('extended_pv_plus') or 0) < 60 else "OK"
        ],
        [
            "Agreement within one grade",
            f"{key_signals.get('agreement_within_one_grade', 0):.1f}%",
            "Educational interest", "-"
        ],
        [
            "Major false negative count",
            str(int(key_signals.get("major_fn_count", 0))),
            "Minimize",
            "REVIEW" if key_signals.get("major_fn_count", 0) > 0 else "OK"
        ],
    ]

    signal_table = Table(
        signal_rows,
        colWidths=[2.8*inch, 1.2*inch, 1.3*inch, 1.0*inch],
        repeatRows=1
    )
    signal_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#1565C0")),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8.5),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("ALIGN",         (0, 1), (0, -1),  "LEFT"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [
            colors.white, colors.HexColor("#F0F7FF")
        ]),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("LINEBELOW",     (0, 0), (-1, 0),  1.5, colors.HexColor("#1565C0")),
    ]))

    for i, row in enumerate(signal_rows[1:], start=1):
        status = row[3]
        if status in ("EXCEEDS", "LOW", "REVIEW"):
            signal_table.setStyle(TableStyle([
                ("TEXTCOLOR",  (3, i), (3, i), colors.HexColor("#B91C1C")),
                ("FONTNAME",   (3, i), (3, i), "Helvetica-Bold"),
                ("BACKGROUND", (3, i), (3, i), colors.HexColor("#FEF2F2")),
            ]))
        elif status == "OK":
            signal_table.setStyle(TableStyle([
                ("TEXTCOLOR",  (3, i), (3, i), colors.HexColor("#15803D")),
                ("FONTNAME",   (3, i), (3, i), "Helvetica-Bold"),
                ("BACKGROUND", (3, i), (3, i), colors.HexColor("#F0FDF4")),
            ]))

    story.append(signal_table)
    story.append(PageBreak())

    # ?? Section 6: Figures ????????????????????????????????????????????????????
    story.extend(section_header("Section 6 - Visualizations", styles))
    story.append(Paragraph(
        "All figures generated by the CHC-QA Pipeline per ASC Birdsong Guideline 2017.",
        styles["Caption"]
    ))

    add_figure_if_exists(
        story, "Figure 1 - Concordance Distribution",
        os.path.join(figure_dir, "concordance_bar.png"), styles
    )
    add_figure_if_exists(
        story, "Figure 2 - Cytology-Histology Correlation Buckets",
        os.path.join(figure_dir, "discrepancy_buckets.png"), styles
    )
    add_figure_if_exists(
        story, "Figure 3 - HSIL Correlation Metrics",
        os.path.join(figure_dir, "hsil_metrics.png"), styles
    )
    add_figure_if_exists(
        story, "Figure 4 - Cytology vs Histology Confusion Matrix",
        os.path.join(figure_dir, "confusion_matrix.png"), styles,
        width=6.7*inch, height=4.2*inch
    )
    add_figure_if_exists(
        story, "Figure 5 - Summary Dashboard",
        os.path.join(figure_dir, "summary_dashboard.png"), styles,
        width=6.7*inch, height=4.5*inch
    )

    story.append(PageBreak())

    # ?? Section 7: AI Clinical Commentary ????????????????????????????????????
    if insights:
        story.extend(section_header(
            "Section 7 - AI Clinical Commentary", styles
        ))
        story.append(Paragraph(
            "The following commentary was generated by a locally-hosted AI language "
            "model based on the QA metrics above. This commentary should be reviewed "
            "by a qualified cytopathologist before use in official documentation.",
            styles["Caption"]
        ))
        story.append(Spacer(1, 0.15*inch))
        clean = insights.replace("\n\n", "<br/><br/>").replace("\n", " ")
        story.append(Paragraph(clean, styles["BodySmall"]))
        story.append(Spacer(1, 0.2*inch))
        story.append(PageBreak())

    # ?? Section 8: Limitations ????????????????????????????????????????????????
    story.extend(section_header("Section 8 - Limitations", styles))
    story.append(Paragraph(
        "This report is generated by an automated deterministic cytology-histology "
        "correlation pipeline. The following limitations apply and should be considered "
        "when interpreting results.",
        styles["BodySmall"]
    ))
    story.append(Spacer(1, 0.1*inch))

    limitations = [
        ("Verification bias",
         "CHC datasets are subject to verification bias due to selective histologic "
         "follow-up. Results should not be interpreted as measures of screening "
         "sensitivity or specificity."),
        ("Clinical context",
         "Observed discrepancies should be interpreted within the context of laboratory "
         "QA review rather than as direct indicators of diagnostic error."),
        ("LLM normalization",
         "Free-text diagnosis normalization was performed by a locally-hosted large "
         "language model. Normalized terms were validated against a controlled vocabulary. "
         "Residual normalization errors may affect a small number of cases."),
        ("Pairing logic",
         "Cases were paired by patient identifier and date window. Complex scenarios "
         "including multiple biopsies, multiple Pap tests, and delayed follow-up may "
         "result in suboptimal pairing in a minority of cases."),
        ("Root cause classification",
         "This pipeline classifies discordance type and direction but does not perform "
         "root cause analysis (sampling error, screening error, interpretive error). "
         "Manual review of major discordant cases is required per Birdsong Section 8."),
    ]

    for i, (title, text) in enumerate(limitations, 1):
        lim_data = [[
            Paragraph(f"{i}.", styles["BodySmall"]),
            Paragraph(f"<b>{title}:</b> {text}", styles["BodySmall"])
        ]]
        lim_tbl = Table(lim_data, colWidths=[0.3*inch, 6.2*inch])
        lim_tbl.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(lim_tbl)
        story.append(Spacer(1, 0.06*inch))

    story.append(Spacer(1, 0.3*inch))

    # Reference box
    ref_data = [[Paragraph(
        "Reference: Birdsong GG, Walker JW. Gynecologic Cytology-Histology Correlation "
        "Guideline. ASC Bulletin. 2017;LIV(2):VIII-XIII. | "
        "CAP Checklist Requirement CYP.06600 | "
        "Generated by CHC-QA Pipeline (github.com/solomoneluanu/chc-qa-pipeline)",
        ParagraphStyle("Ref", parent=styles["Normal"],
            fontSize=7.5, textColor=colors.HexColor("#64748B"),
            leading=11)
    )]]
    ref_tbl = Table(ref_data, colWidths=[6.5*inch])
    ref_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
    ]))
    story.append(ref_tbl)

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
