import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image, PageBreak,
)


def dataframe_to_table_data(df):
    data = [list(df.columns)]
    for _, row in df.iterrows():
        data.append(list(row))
    return data


def styled_table(df, col_widths=None):
    data = dataframe_to_table_data(df)
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#1565C0")),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    return table


def alert_table(rows, col_widths=None):
    """Two-column key-value table for metrics."""
    table = Table(rows, colWidths=col_widths or [4.0*inch, 2.0*inch], repeatRows=0)
    table.setStyle(TableStyle([
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("ALIGN",         (0, 0), (0, -1), "LEFT"),
        ("ALIGN",         (1, 0), (1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
        ("ROWBACKGROUNDS",(0, 0), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    return table


def add_figure_if_exists(story, title, path, styles,
                          width=6.5*inch, height=3.8*inch):
    if os.path.exists(path):
        story.append(Paragraph(title, styles["Heading3"]))
        story.append(Spacer(1, 0.08*inch))
        story.append(Image(path, width=width, height=height))
        story.append(Spacer(1, 0.2*inch))


def _flag_color(value, threshold, invert=False):
    """Return red for bad, green for good."""
    if value is None:
        return colors.HexColor("#94A3B8")
    if invert:
        return colors.HexColor("#EF4444") if value < threshold else colors.HexColor("#10B981")
    return colors.HexColor("#EF4444") if value > threshold else colors.HexColor("#10B981")


def build_pdf_report(results, figure_dir, output_pdf,
                     summary_text=None, insights=None):
    os.makedirs(os.path.dirname(output_pdf), exist_ok=True)

    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=letter,
        rightMargin=50, leftMargin=50,
        topMargin=50,   bottomMargin=50
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="SectionTitle",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#1565C0"),
        spaceAfter=8, spaceBefore=12,
        borderPad=4
    ))
    styles.add(ParagraphStyle(
        name="SubTitle",
        parent=styles["Heading3"],
        textColor=colors.HexColor("#475569"),
        spaceAfter=6, spaceBefore=8,
        fontSize=10
    ))
    styles.add(ParagraphStyle(
        name="BodySmall",
        parent=styles["BodyText"],
        fontSize=9, leading=13
    ))
    styles.add(ParagraphStyle(
        name="AlertRed",
        parent=styles["BodyText"],
        textColor=colors.HexColor("#C62828"),
        fontSize=9, fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        name="AlertGreen",
        parent=styles["BodyText"],
        textColor=colors.HexColor("#2E7D32"),
        fontSize=9, fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        name="Caption",
        parent=styles["BodyText"],
        fontSize=8, textColor=colors.HexColor("#64748B"),
        leading=11
    ))

    story = []

    # ?? Title page ????????????????????????????????????????????????????????????
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(
        "Cervical Cytology-Histology Correlation",
        styles["Title"]
    ))
    story.append(Paragraph(
        "Quality Assurance Report",
        styles["Title"]
    ))
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph(
        "Automated pipeline per ASC Birdsong Guideline 2017 | CAP CYP.06600",
        styles["BodySmall"]
    ))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        f"Total Cases Analyzed: {results.get('total_cases', 0)}",
        styles["BodyText"]
    ))
    story.append(Spacer(1, 0.3*inch))

    # Executive summary
    story.append(Paragraph("Executive Summary", styles["SectionTitle"]))
    exec_text = summary_text or (
        f"A total of {results.get('total_cases')} cytology-histology pairs were analyzed "
        f"using an automated deterministic QA pipeline aligned with the American Society "
        f"of Cytopathology (ASC) Birdsong Guideline 2017 and CAP checklist requirement "
        f"CYP.06600. This report presents concordance distribution, HSIL-focused metrics, "
        f"intergrade follow-up rates, discrepancy bucket analysis, and key quality signals."
    )
    story.append(Paragraph(exec_text, styles["BodySmall"]))
    story.append(Spacer(1, 0.2*inch))

    # CAP alert box
    major_rate = results.get("concordance_percentages", {}).get("major_discordant", 0)
    hsil_pv    = results.get("hsil_pv_plus", 0) or 0
    pv_flag    = results.get("hsil_pv_interpretation", "")

    if major_rate > 10:
        story.append(Paragraph(
            f"CAP ALERT: Major discordance rate of {major_rate:.1f}% exceeds the "
            f"CAP benchmark of less than 10%. Corrective action documentation "
            f"required per CYP.06600.",
            styles["AlertRed"]
        ))
    else:
        story.append(Paragraph(
            f"CAP STATUS: Major discordance rate of {major_rate:.1f}% is within "
            f"the CAP benchmark of less than 10%.",
            styles["AlertGreen"]
        ))

    story.append(Spacer(1, 0.1*inch))

    if hsil_pv < 60 and hsil_pv > 0:
        story.append(Paragraph(
            f"PV+ ALERT: HSIL positive predictive value of {hsil_pv:.1f}% falls "
            f"below the CAP target of 60%.",
            styles["AlertRed"]
        ))
    elif hsil_pv > 95:
        story.append(Paragraph(
            f"PV+ FLAG: HSIL PV+ of {hsil_pv:.1f}% is unusually high. "
            f"Per Birdsong, this may indicate an excessive cytology undercall rate.",
            styles["AlertRed"]
        ))

    story.append(PageBreak())

    # ?? Section 1: Concordance Summary ???????????????????????????????????????
    story.append(Paragraph("Section 1 ? Concordance Summary", styles["SectionTitle"]))
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

    # Agreement within one grade ? Birdsong Section 5
    within_one     = results.get("agreement_within_one_grade", 0)
    within_one_pct = results.get("agreement_within_one_pct", 0)
    total          = results.get("total_cases", 1)

    story.append(Paragraph("Agreement Within One Grade (Birdsong Section 5)", styles["SubTitle"]))
    story.append(Paragraph(
        "Percentage of pairs with exact agreement or minor disagreement only. "
        "Per Birdsong, this metric is of educational interest.",
        styles["Caption"]
    ))
    story.append(Spacer(1, 0.08*inch))

    within_rows = [
        ["Metric", "Count", "Percentage"],
        ["Agreement within one grade", str(within_one), f"{within_one_pct:.1f}%"],
        ["Exact agreement only",
         str(results.get("concordance_counts", {}).get("concordant", 0)),
         f"{results.get('concordance_percentages', {}).get('concordant', 0):.1f}%"],
        ["Major discordance (outside one grade)",
         str(results.get("concordance_counts", {}).get("major_discordant", 0)),
         f"{results.get('concordance_percentages', {}).get('major_discordant', 0):.1f}%"],
    ]
    story.append(alert_table(within_rows, col_widths=[3.5*inch, 1.2*inch, 1.2*inch]))
    story.append(Spacer(1, 0.25*inch))

    # ?? Section 2: CAP Discrepancy Buckets ???????????????????????????????????
    story.append(Paragraph("Section 2 ? Discrepancy Bucket Summary", styles["SectionTitle"]))
    story.append(Paragraph(
        "CAP-style discrepancy classification per Birdsong Figure 1 and Figure 3.",
        styles["Caption"]
    ))
    story.append(Spacer(1, 0.1*inch))
    story.append(styled_table(
        results["bucket_table"],
        col_widths=[2.5*inch, 1.5*inch, 1.5*inch]
    ))
    story.append(Spacer(1, 0.25*inch))

    # ?? Section 3: HSIL-Focused Metrics (Birdsong Section 7) ?????????????????
    story.append(Paragraph(
        "Section 3 ? HSIL-Focused Metrics (Birdsong Section 7)",
        styles["SectionTitle"]
    ))
    story.append(Paragraph(
        "The five statistical calculations required by Birdsong Section 7 "
        "and the ASC Clinical Practice Committee.",
        styles["Caption"]
    ))
    story.append(Spacer(1, 0.1*inch))
    story.append(styled_table(
        results["hsil_pv_table"],
        col_widths=[4.5*inch, 1.5*inch]
    ))
    story.append(Spacer(1, 0.15*inch))

    # PV+ interpretation
    story.append(Paragraph("PV+ Interpretation (Birdsong Section 7a)", styles["SubTitle"]))
    pv_style = "AlertRed" if (hsil_pv < 60 or hsil_pv > 95) else "AlertGreen"
    story.append(Paragraph(pv_flag, styles[pv_style]))
    story.append(Spacer(1, 0.1*inch))

    # Extended PV+ including ASC-H and AGC-NEO
    ext_pv     = results.get("extended_pv_plus")
    total_hg   = results.get("total_high_grade_paps", 0)
    hg_to_hsil = results.get("high_grade_to_hsil", 0)

    story.append(Paragraph(
        "Extended PV+ ? High-Grade Cytology Group (HSIL + ASC-H + AGC-NEO)",
        styles["SubTitle"]
    ))
    story.append(Paragraph(
        "Per Birdsong Figure 1, HSIL, ASC-H, and AGC-NEO are grouped together "
        "for concordance assessment. The extended PV+ reflects combined performance.",
        styles["Caption"]
    ))
    story.append(Spacer(1, 0.08*inch))

    ext_rows = [
        ["Metric", "Value"],
        ["Total high-grade Pap tests (HSIL + ASC-H + AGC-NEO)", str(total_hg)],
        ["High-grade Pap tests with HSIL+ histology", str(hg_to_hsil)],
        ["Extended PV+", f"{ext_pv:.1f}%" if ext_pv is not None else "N/A"],
    ]
    story.append(alert_table(ext_rows, col_widths=[4.5*inch, 1.5*inch]))
    story.append(Spacer(1, 0.25*inch))

    # ?? Section 4: Intergrade Follow-Up Rates (Birdsong Section 8) ???????????
    story.append(Paragraph(
        "Section 4 ? Intergrade Follow-Up Rates (Birdsong Section 8)",
        styles["SectionTitle"]
    ))
    story.append(Paragraph(
        "Per Birdsong Section 8: review of HSIL histology rates following "
        "ASC-US, ASC-H, and LSIL cytologic interpretations to identify "
        "systematic undercall patterns.",
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
            "Elevated HSIL+ follow-up rates in ASC-US or LSIL categories "
            "may indicate systematic cytologic undercalling requiring "
            "targeted slide review per Birdsong Section 8.",
            styles["Caption"]
        ))
    else:
        story.append(Paragraph("Insufficient data for intergrade analysis.", styles["BodySmall"]))
    story.append(Spacer(1, 0.25*inch))

    # ?? Section 5: Key Quality Signals ???????????????????????????????????????
    story.append(Paragraph("Section 5 ? Key Quality Signals", styles["SectionTitle"]))

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
            "?", "?"
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
            "?", "?"
        ],
        [
            "HSIL PV+",
            f"{key_signals.get('hsil_pv_plus', 0):.1f}%",
            "> 60%",
            "LOW" if key_signals.get("pv_below_cap_target") else "OK"
        ],
        [
            "Extended PV+ (HSIL+ASC-H+AGC-NEO)",
            f"{key_signals.get('extended_pv_plus', 0) or 0:.1f}%",
            "> 60%", "?"
        ],
        [
            "Agreement within one grade",
            f"{key_signals.get('agreement_within_one_grade', 0):.1f}%",
            "?", "?"
        ],
        [
            "Major false negative count",
            str(int(key_signals.get("major_fn_count", 0))),
            "Minimize", "REVIEW" if key_signals.get("major_fn_count", 0) > 0 else "OK"
        ],
    ]

    signal_table = Table(
        signal_rows,
        colWidths=[2.8*inch, 1.2*inch, 1.2*inch, 1.0*inch],
        repeatRows=1
    )
    signal_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#1565C0")),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8.5),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("ALIGN",         (0, 0), (0, -1),  "LEFT"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ]))

    # Color EXCEEDS and LOW cells red
    for i, row in enumerate(signal_rows[1:], start=1):
        status = row[3]
        if status in ("EXCEEDS", "LOW", "REVIEW"):
            signal_table.setStyle(TableStyle([
                ("TEXTCOLOR",  (3, i), (3, i), colors.HexColor("#C62828")),
                ("FONTNAME",   (3, i), (3, i), "Helvetica-Bold"),
                ("BACKGROUND", (3, i), (3, i), colors.HexColor("#FFEBEE")),
            ]))
        elif status == "OK":
            signal_table.setStyle(TableStyle([
                ("TEXTCOLOR",  (3, i), (3, i), colors.HexColor("#2E7D32")),
                ("FONTNAME",   (3, i), (3, i), "Helvetica-Bold"),
                ("BACKGROUND", (3, i), (3, i), colors.HexColor("#E8F5E9")),
            ]))

    story.append(signal_table)
    story.append(PageBreak())

    # ?? Section 6: Figures ???????????????????????????????????????????????????
    story.append(Paragraph("Section 6 ? Visualizations", styles["SectionTitle"]))

    add_figure_if_exists(
        story, "Figure 1 ? Concordance Distribution",
        os.path.join(figure_dir, "concordance_bar.png"), styles
    )
    add_figure_if_exists(
        story, "Figure 2 ? Cytology-Histology Correlation Buckets",
        os.path.join(figure_dir, "discrepancy_buckets.png"), styles
    )
    add_figure_if_exists(
        story, "Figure 3 ? HSIL Correlation Metrics",
        os.path.join(figure_dir, "hsil_metrics.png"), styles
    )
    add_figure_if_exists(
        story, "Figure 4 ? Cytology vs Histology Confusion Matrix",
        os.path.join(figure_dir, "confusion_matrix.png"), styles,
        width=6.7*inch, height=4.2*inch
    )
    add_figure_if_exists(
        story, "Figure 5 ? Summary Dashboard",
        os.path.join(figure_dir, "summary_dashboard.png"), styles,
        width=6.7*inch, height=4.5*inch
    )

    story.append(PageBreak())

    # ?? Section 7: AI Clinical Commentary ????????????????????????????????????
    if insights:
        story.append(Paragraph("Section 7 ? AI Clinical Commentary", styles["SectionTitle"]))
        story.append(Paragraph(
            "The following commentary was generated by a locally-hosted AI language "
            "model based on the QA metrics above. It should be reviewed by a qualified "
            "pathologist before use in official documentation.",
            styles["Caption"]
        ))
        story.append(Spacer(1, 0.15*inch))
        clean = insights.replace("\n\n", "<br/><br/>").replace("\n", " ")
        story.append(Paragraph(clean, styles["BodySmall"]))
        story.append(Spacer(1, 0.2*inch))
        story.append(PageBreak())

    # ?? Section 8: Limitations ???????????????????????????????????????????????
    story.append(Paragraph("Section 8 ? Limitations", styles["SectionTitle"]))
    story.append(Paragraph("""
This report is generated by an automated deterministic cytology-histology
correlation pipeline. Classification rules are derived from the ASC Clinical
Practice Committee Birdsong Guideline (2017) and applied deterministically
to all pairs. The following limitations apply:
    """.strip(), styles["BodySmall"]))
    story.append(Spacer(1, 0.1*inch))

    limitations = [
        "Verification bias: CHC datasets are subject to verification bias due "
        "to selective histologic follow-up. Results should not be interpreted "
        "as measures of screening sensitivity or specificity.",

        "Observed discrepancies should be interpreted within the context of "
        "laboratory QA review rather than as direct indicators of diagnostic error.",

        "LLM normalization: Free-text diagnosis normalization was performed by "
        "a locally-hosted large language model. Normalized terms were validated "
        "against a controlled vocabulary. Residual normalization errors may affect "
        "a small number of cases.",

        "Pairing logic: Cases were paired by patient identifier and date window. "
        "Complex scenarios including multiple biopsies, multiple Pap tests, and "
        "delayed follow-up may result in suboptimal pairing in a minority of cases.",

        "Root cause classification: This pipeline classifies discordance type and "
        "direction but does not perform root cause analysis (sampling error, "
        "screening error, interpretive error). Manual review of major discordant "
        "cases is required per Birdsong Section 8.",
    ]

    for i, lim in enumerate(limitations, 1):
        story.append(Paragraph(f"{i}. {lim}", styles["BodySmall"]))
        story.append(Spacer(1, 0.08*inch))

    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(
        "Reference: Birdsong GG, Walker JW. Gynecologic Cytology-Histology "
        "Correlation Guideline. ASC Bulletin. 2017;LIV(2):VIII-XIII.",
        styles["Caption"]
    ))

    doc.build(story)
