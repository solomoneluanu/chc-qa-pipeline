import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
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
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FBFF")]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def add_figure_if_exists(story, title, path, styles, width=6.5 * inch, height=3.8 * inch):
    if os.path.exists(path):
        story.append(Paragraph(title, styles["Heading3"]))
        story.append(Spacer(1, 0.08 * inch))
        story.append(Image(path, width=width, height=height))
        story.append(Spacer(1, 0.2 * inch))


def build_pdf_report(results, figure_dir, output_pdf, summary_text=None):
    os.makedirs(os.path.dirname(output_pdf), exist_ok=True)

    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=letter,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="SectionTitle",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#1F4E79"),
        spaceAfter=8,
        spaceBefore=10
    ))
    styles.add(ParagraphStyle(
        name="BodySmall",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14
    ))

    story = []

    # -------------------------
    # Title Page
    # -------------------------
    story.append(Paragraph("Cervical Cytology-Histology Correlation QA Report", styles["Title"]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Automated rule-based quality assurance analysis", styles["BodyText"]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(f"Total Cases: {results.get('total_cases')}", styles["BodyText"]))
    story.append(Spacer(1, 0.35 * inch))

    if summary_text:
        story.append(Paragraph("Executive Summary", styles["SectionTitle"]))
        for block in summary_text.split("\n\n"):
            if block.strip():
                story.append(Paragraph(block.replace("\n", "<br/>"), styles["BodySmall"]))
                story.append(Spacer(1, 0.12 * inch))
    else:
        story.append(Paragraph("Executive Summary", styles["SectionTitle"]))
        fallback_summary = (
            f"A total of {results.get('total_cases')} cases were analyzed using a deterministic "
            f"cytology-histology correlation pipeline. Concordance, discordance subtype distribution, "
            f"HSIL-related follow-up metrics, and figure-based summaries are provided in this report."
        )
        story.append(Paragraph(fallback_summary, styles["BodySmall"]))

    story.append(PageBreak())

    # -------------------------
    # Summary Tables
    # -------------------------
    story.append(Paragraph("Concordance Summary", styles["SectionTitle"]))
    story.append(styled_table(results["concordance_table"], col_widths=[2.8 * inch, 1.2 * inch, 1.2 * inch]))
    story.append(Spacer(1, 0.25 * inch))


    story.append(Paragraph("HSIL-Focused Metrics", styles["SectionTitle"]))
    story.append(styled_table(results["hsil_pv_table"], col_widths=[4.8 * inch, 1.0 * inch]))
    story.append(Spacer(1, 0.25 * inch))

    if "bucket_table" in results:
        story.append(Paragraph("Discrepancy Bucket Summary", styles["SectionTitle"]))
        story.append(styled_table(results["bucket_table"], col_widths=[2.0 * inch, 1.2 * inch, 1.2 * inch]))
        story.append(Spacer(1, 0.25 * inch))

    # -------------------------
    # Key Quality Signals
    # -------------------------
    story.append(Paragraph("Key Quality Signals", styles["SectionTitle"]))

    signals = [
        f"Major discordance rate: {results['concordance_percentages'].get('major_discordant', 0)}%",
        f"Minor discordance rate: {results['concordance_percentages'].get('minor_discordant', 0)}%",
        f"Undercall proportion: {results['direction_percentages'].get('undercall', 0)}%",
        f"Overcall proportion: {results['direction_percentages'].get('overcall', 0)}%",
        f"HSIL PV+: {results.get('hsil_pv_plus', 0)}%",
    ]

    for s in signals:
        story.append(Paragraph(f"- {s}", styles["BodySmall"]))
        story.append(Spacer(1, 0.08 * inch))

    story.append(PageBreak())

    # -------------------------
    # Figures
    # -------------------------
    story.append(Paragraph("Figures", styles["SectionTitle"]))

    add_figure_if_exists(
        story,
        "Concordance Distribution",
        os.path.join(figure_dir, "concordance_bar.png"),
        styles
    )


    add_figure_if_exists(
        story,
        "Cytology-Histology Correlation Buckets",
        os.path.join(figure_dir, "discrepancy_buckets.png"),
        styles
    )

    add_figure_if_exists(
        story,
        "HSIL Correlation Metrics",
        os.path.join(figure_dir, "hsil_metrics.png"),
        styles
    )

    add_figure_if_exists(
        story,
        "Confusion Matrix",
        os.path.join(figure_dir, "confusion_matrix.png"),
        styles,
        width=6.7 * inch,
        height=4.2 * inch
    )

    story.append(PageBreak())

    # -------------------------
    # Limitations
    # -------------------------
    story.append(Paragraph("Limitations", styles["SectionTitle"]))

    limitations_text = """
    This report is based on deterministic cytology-histology correlation using rule-based classification.
    Routine CHC datasets are subject to verification bias due to selective histologic follow-up.
    Accordingly, these results should not be interpreted as measures of screening sensitivity or specificity.
    Observed discrepancies should be interpreted within the context of laboratory QA review rather than as direct indicators of diagnostic error.
    """

    story.append(Paragraph(limitations_text.strip().replace("\n", "<br/>"), styles["BodySmall"]))

    doc.build(story)
