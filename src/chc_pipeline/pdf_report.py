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


def build_pdf_report(results, summary_text, figure_dir, output_pdf):
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

    # Title page
    story.append(Paragraph("Cervical Cytology-Histology Correlation QA Report", styles["Title"]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Automated rule-based QA analysis with LLM-assisted summary", styles["BodyText"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(f"Total Cases: {results.get('total_cases')}", styles["BodyText"]))
    story.append(Spacer(1, 0.4 * inch))

    story.append(Paragraph("Executive Summary", styles["SectionTitle"]))
    for block in summary_text.split("\n\n"):
        if block.strip():
            story.append(Paragraph(block.replace("\n", "<br/>"), styles["BodySmall"]))
            story.append(Spacer(1, 0.12 * inch))

    story.append(PageBreak())

    # Summary tables
    story.append(Paragraph("Concordance Summary", styles["SectionTitle"]))
    story.append(styled_table(results["concordance_table"], col_widths=[2.8*inch, 1.2*inch, 1.2*inch]))
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Discordance Subtype Summary", styles["SectionTitle"]))
    story.append(styled_table(results["subtype_table"], col_widths=[2.8*inch, 1.2*inch, 1.2*inch]))
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("HSIL Positive Predictive Value (PV+)", styles["SectionTitle"]))
    story.append(styled_table(results["hsil_pv_table"], col_widths=[4.5*inch, 1.2*inch]))

    story.append(PageBreak())

    # Figures
    story.append(Paragraph("Figures", styles["SectionTitle"]))

    figure_files = [
        ("Concordance Distribution", os.path.join(figure_dir, "concordance_bar.png")),
        ("Discordance Subtype Distribution", os.path.join(figure_dir, "subtype_bar.png")),
        ("Confusion Matrix", os.path.join(figure_dir, "confusion_matrix.png")),
    ]

    for title, path in figure_files:
        if os.path.exists(path):
            story.append(Paragraph(title, styles["Heading3"]))
            story.append(Spacer(1, 0.08 * inch))
            img = Image(path, width=6.5 * inch, height=3.8 * inch)
            story.append(img)
            story.append(Spacer(1, 0.2 * inch))

    doc.build(story)
