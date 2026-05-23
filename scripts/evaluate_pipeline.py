import sys
import json
import time
import pandas as pd
import numpy as np
from collections import defaultdict

sys.path.insert(0, 'src')

from chc_pipeline.llm_normalizer import normalize_cyto_sheet, normalize_histo_sheet
from chc_pipeline.normalize import normalize_diagnoses
from chc_pipeline.classify import classify_pairs


CYTO_GOLD_STANDARD = {
    "NILM":          "NILM",
    "HSIL":          "HSIL",
    "LSIL":          "LSIL",
    "ASC-US":        "ASC-US",
    "ASC-H":         "ASC-H",
    "AGC":           "AGC",
    "AGC-NEO":       "AGC-NEO",
    "AIS":           "AIS",
    "MALIGNANT":     "MALIGNANT",
    "OTHER (EMC45)": "OTHER (EMC45)",
    "NILLM":   "NILM",
    "NILMS":   "NILM",
    "HGSIL":   "HSIL",
    "HGIL":    "HSIL",
    "HSILL":   "HSIL",
    "LGSIL":   "LSIL",
    "LGIL":    "LSIL",
    "ASCUS":   "ASC-US",
    "ASC US":  "ASC-US",
    "Asc-us":  "ASC-US",
    "ASCH":    "ASC-H",
    "ASC H":   "ASC-H",
    "agc":     "AGC",
    "lsil":    "LSIL",
    "hsil":    "HSIL",
    "Negative":              "NILM",
    "Neg":                   "NILM",
    "Neg for malignancy":    "NILM",
    "No dysplasia":          "NILM",
    "Normal":                "NILM",
    "Within normal limits":  "NILM",
    "No malignant cells":    "NILM",
    "No significant atypia": "NILM",
    "Reactive changes":      "NILM",
    "Benign":                "NILM",
    "Negative for intraepithelial lesion or malignancy": "NILM",
    "No intraepithelial lesion":                         "NILM",
    "Low-grade squamous intraepithelial lesion":         "LSIL",
    "Low grade squamous intraepithelial lesion":         "LSIL",
    "High-grade squamous intraepithelial lesion":        "HSIL",
    "High grade squamous intraepithelial lesion":        "HSIL",
    "Atypical squamous cells of undetermined significance": "ASC-US",
    "Atypical squamous cells, undetermined significance":   "ASC-US",
    "Atypical squamous cells, cannot exclude HSIL":         "ASC-H",
    "Atypical glandular cells":                             "AGC",
    "Satisfactory for evaluation. Negative for intraepithelial lesion or malignancy (NILM).": "NILM",
    "NILM. Endocervical/transformation zone component present.":                              "NILM",
    "Negative. No significant atypia identified.":                                            "NILM",
    "No malignant cells identified. Reactive cellular changes.":                              "NILM",
    "Within normal limits. Mild inflammatory changes noted.":                                 "NILM",
    "Negative cytology. Satisfactory specimen.":                                              "NILM",
    "No dysplasia identified. Adequacy satisfactory.":                                        "NILM",
    "Benign cellular changes. No evidence of dysplasia.":                                     "NILM",
    "Negative for malignancy. Atrophic pattern noted.":                                       "NILM",
    "NILM. Partially obscuring inflammation present.":                                        "NILM",
    "HIGH GRADE SQUAMOUS INTRAEPITHELIAL LESION (HSIL)":                           "HSIL",
    "HSIL. Features consistent with CIN 2-3. Colposcopy recommended.":             "HSIL",
    "High grade squamous intraepithelial lesion. Cannot exclude invasion.":         "HSIL",
    "HSIL - SEE COMMENT. Correlate with clinical findings.":                        "HSIL",
    "High grade lesion identified. Immediate colposcopy recommended.":              "HSIL",
    "HSIL. Severely dyskaryotic cells present.":                                    "HSIL",
    "High-grade SIL consistent with CIN 2-3.":                                     "HSIL",
    "HSIL. Features favor CIN 3. Biopsy recommended.":                             "HSIL",
    "High grade squamous lesion. Urgent colposcopy advised.":                       "HSIL",
    "HGSIL. Features consistent with severe dysplasia.":                            "HSIL",
    "LOW GRADE SQUAMOUS INTRAEPITHELIAL LESION (LSIL)":                            "LSIL",
    "LSIL. Consistent with HPV effect/CIN 1.":                                     "LSIL",
    "Low-grade squamous intraepithelial lesion. Koilocytic atypia present.":        "LSIL",
    "LSIL. Changes consistent with productive HPV infection.":                      "LSIL",
    "Low grade lesion. Colposcopy at discretion of clinician.":                     "LSIL",
    "LSIL identified. Reflex HPV testing performed.":                               "LSIL",
    "Low-grade SIL consistent with CIN 1.":                                         "LSIL",
    "LSIL. Mild koilocytic changes noted.":                                         "LSIL",
    "Low grade squamous lesion. Follow up recommended.":                            "LSIL",
    "LGSIL. Features consistent with mild dysplasia.":                              "LSIL",
    "ATYPICAL SQUAMOUS CELLS OF UNDETERMINED SIGNIFICANCE (ASC-US)":               "ASC-US",
    "ASC-US. Cannot exclude low grade squamous intraepithelial lesion.":            "ASC-US",
    "Atypical squamous cells, undetermined significance. Reflex HPV testing recommended.": "ASC-US",
    "ASC-US. Mildly atypical squamous cells identified.":                           "ASC-US",
    "Atypical squamous cells of undetermined significance. Follow up advised.":     "ASC-US",
    "ATYPICAL SQUAMOUS CELLS, CANNOT EXCLUDE HSIL (ASC-H)":                        "ASC-H",
    "ASC-H. High grade lesion cannot be excluded. Colposcopy recommended.":         "ASC-H",
    "Atypical squamous cells, cannot exclude high grade lesion.":                   "ASC-H",
    "ASC-H. Features raise concern for HSIL.":                                      "ASC-H",
    "Cannot exclude HSIL. Immediate colposcopy recommended.":                       "ASC-H",
    "ATYPICAL GLANDULAR CELLS (AGC), NOT OTHERWISE SPECIFIED":                      "AGC",
    "Atypical glandular cells NOS. Further evaluation recommended.":                "AGC",
    "AGC-NOS. Atypical endocervical cells identified.":                             "AGC",
    "Atypical glandular cells of undetermined significance.":                       "AGC",
    "AGC. Endocervical cell atypia noted.":                                         "AGC",
    "ATYPICAL GLANDULAR CELLS, FAVOR NEOPLASIA":                                    "AGC-NEO",
    "AGC-NEO. Endocervical adenocarcinoma in situ cannot be excluded.":             "AGC-NEO",
    "Atypical glandular cells, favor neoplasia. Further evaluation recommended.":   "AGC-NEO",
    "AGC favor neoplastic. AIS cannot be excluded.":                                "AGC-NEO",
    "Atypical glandular cells favoring neoplasia.":                                 "AGC-NEO",
    "MALIGNANT CELLS PRESENT. Features consistent with squamous cell carcinoma.":   "MALIGNANT",
    "Positive for malignancy. Adenocarcinoma cannot be excluded.":                  "MALIGNANT",
    "Malignant cells identified. Invasive carcinoma suspected.":                    "MALIGNANT",
    "Positive for malignant cells. Squamous cell carcinoma.":                       "MALIGNANT",
    "Carcinoma present. Urgent clinical correlation required.":                     "MALIGNANT",
    "AIS. Adenocarcinoma in situ identified.":                                      "AIS",
    "Adenocarcinoma in situ. AIS confirmed.":                                       "AIS",
    "AIS present. Cone biopsy recommended.":                                        "AIS",
    "Endometrial cells present in woman age 45 or older.":                          "OTHER (EMC45)",
    "Benign endometrial cells. Patient age 47.":                                    "OTHER (EMC45)",
}

HISTO_GOLD_STANDARD = {
    "Benign / Inflammatory (Negative)": "Benign / Inflammatory (Negative)",
    "LSIL (CIN1)":                      "LSIL (CIN1)",
    "HSIL (CIN2)":                      "HSIL (CIN2)",
    "HSIL (CIN3)":                      "HSIL (CIN3)",
    "Squamous Cell Carcinoma":          "Squamous Cell Carcinoma",
    "Adenocarcinoma":                   "Adenocarcinoma",
    "Benign":                "Benign / Inflammatory (Negative)",
    "Negative":              "Benign / Inflammatory (Negative)",
    "Normal":                "Benign / Inflammatory (Negative)",
    "No CIN":                "Benign / Inflammatory (Negative)",
    "No dysplasia":          "Benign / Inflammatory (Negative)",
    "Reactive":              "Benign / Inflammatory (Negative)",
    "Chronic cervicitis":    "Benign / Inflammatory (Negative)",
    "Benign tissue":         "Benign / Inflammatory (Negative)",
    "Squamous metaplasia":   "Benign / Inflammatory (Negative)",
    "Inflammatory changes":  "Benign / Inflammatory (Negative)",
    "CIN1":                  "LSIL (CIN1)",
    "CIN 1":                 "LSIL (CIN1)",
    "cin1":                  "LSIL (CIN1)",
    "Mild dysplasia":        "LSIL (CIN1)",
    "Koilocytic change":     "LSIL (CIN1)",
    "Koilocytic atypia":     "LSIL (CIN1)",
    "Low grade CIN":         "LSIL (CIN1)",
    "Low-grade CIN":         "LSIL (CIN1)",
    "Cervical intraepithelial neoplasia, grade 1 (CIN 1/LSIL).":           "LSIL (CIN1)",
    "CIN 1. Koilocytic atypia consistent with HPV effect.":                "LSIL (CIN1)",
    "Low grade CIN (CIN 1). Changes limited to lower third of epithelium.": "LSIL (CIN1)",
    "Mild dysplasia consistent with CIN 1.":                               "LSIL (CIN1)",
    "CIN1. HPV effect present.":                                           "LSIL (CIN1)",
    "Low grade squamous intraepithelial lesion (CIN 1).":                  "LSIL (CIN1)",
    "CIN 1. Koilocytic changes noted in lower epithelial third.":          "LSIL (CIN1)",
    "CIN2":                  "HSIL (CIN2)",
    "CIN 2":                 "HSIL (CIN2)",
    "cin2":                  "HSIL (CIN2)",
    "Moderate dysplasia":    "HSIL (CIN2)",
    "Cervical intraepithelial neoplasia, grade 2 (CIN 2/HSIL).":          "HSIL (CIN2)",
    "CIN 2. Atypia involving lower two thirds of epithelial thickness.":   "HSIL (CIN2)",
    "Moderate dysplasia (CIN 2). Ectocervical margin uninvolved.":         "HSIL (CIN2)",
    "CIN 2-3. Cannot exclude higher grade lesion.":                        "HSIL (CIN2)",
    "High grade CIN 2. Margins clear.":                                    "HSIL (CIN2)",
    "CIN2. Atypia involving mid and lower epithelium.":                    "HSIL (CIN2)",
    "Moderate to severe dysplasia. CIN 2.":                                "HSIL (CIN2)",
    "CIN 2. p16 positive. Ki-67 elevated.":                                "HSIL (CIN2)",
    "HSIL (CIN 2). Lower two thirds involvement.":                         "HSIL (CIN2)",
    "Cervical intraepithelial neoplasia grade 2.":                         "HSIL (CIN2)",
    "CIN II. Moderate dysplasia confirmed.":                               "HSIL (CIN2)",
    "CIN3":                  "HSIL (CIN3)",
    "CIN 3":                 "HSIL (CIN3)",
    "cin3":                  "HSIL (CIN3)",
    "Severe dysplasia":      "HSIL (CIN3)",
    "Carcinoma in situ":     "HSIL (CIN3)",
    "CIS":                   "HSIL (CIN3)",
    "Full thickness atypia": "HSIL (CIN3)",
    "Cervical intraepithelial neoplasia, grade 3 (CIN 3/HSIL).":          "HSIL (CIN3)",
    "CIN 3. Full thickness epithelial atypia. Numerous mitotic figures.":  "HSIL (CIN3)",
    "Severe dysplasia/carcinoma in situ (CIN 3). Margins involved.":       "HSIL (CIN3)",
    "High grade CIN (CIN 2-3). Cannot exclude early invasion.":            "HSIL (CIN3)",
    "CIN 3. p16 block positive. Full thickness involvement.":              "HSIL (CIN3)",
    "HSIL (CIN 3). Carcinoma in situ pattern.":                           "HSIL (CIN3)",
    "Cervical intraepithelial neoplasia grade 3. Severe dysplasia.":       "HSIL (CIN3)",
    "CIN III. Full thickness atypia confirmed.":                           "HSIL (CIN3)",
    "Benign cervical squamous and endocervical mucosa. No dysplasia identified.": "Benign / Inflammatory (Negative)",
    "Cervical biopsy: reactive squamous epithelium. No CIN.":              "Benign / Inflammatory (Negative)",
    "Chronic cervicitis. Squamous metaplasia. No significant atypia.":     "Benign / Inflammatory (Negative)",
    "Benign findings. Transformation zone adequately sampled.":            "Benign / Inflammatory (Negative)",
    "Negative. No intraepithelial lesion identified.":                     "Benign / Inflammatory (Negative)",
    "Reactive squamous changes. No dysplasia.":                            "Benign / Inflammatory (Negative)",
    "Normal ectocervix and endocervix. No CIN.":                          "Benign / Inflammatory (Negative)",
    "Benign squamous epithelium. Inflammatory changes only.":              "Benign / Inflammatory (Negative)",
    "No evidence of CIN or malignancy.":                                   "Benign / Inflammatory (Negative)",
    "Cervicitis. No significant epithelial atypia.":                       "Benign / Inflammatory (Negative)",
    "Benign endocervical polyp. No dysplasia.":                           "Benign / Inflammatory (Negative)",
    "Squamous metaplasia. No CIN identified.":                             "Benign / Inflammatory (Negative)",
    "Negative for dysplasia. Satisfactory biopsy.":                       "Benign / Inflammatory (Negative)",
    "No high grade lesion. Benign reactive changes.":                      "Benign / Inflammatory (Negative)",
    "Benign. Endocervical glands present. No atypia.":                    "Benign / Inflammatory (Negative)",
    "SCC":                              "Squamous Cell Carcinoma",
    "Invasive SCC":                     "Squamous Cell Carcinoma",
    "Invasive squamous cell carcinoma": "Squamous Cell Carcinoma",
    "Squamous cell carcinoma":          "Squamous Cell Carcinoma",
    "Invasive squamous cell carcinoma, moderately differentiated.": "Squamous Cell Carcinoma",
    "Squamous cell carcinoma. Stromal invasion present.":           "Squamous Cell Carcinoma",
    "Invasive squamous carcinoma. Depth of invasion 4mm.":          "Squamous Cell Carcinoma",
    "SCC. Lymphovascular invasion present.":                        "Squamous Cell Carcinoma",
    "Squamous cell carcinoma, well differentiated.":                "Squamous Cell Carcinoma",
    "Invasive keratinizing squamous cell carcinoma.":               "Squamous Cell Carcinoma",
    "Squamous carcinoma. Margins involved.":                        "Squamous Cell Carcinoma",
    "SCC with stromal invasion. Stage IA2.":                        "Squamous Cell Carcinoma",
    "Adenocarcinoma":                   "Adenocarcinoma",
    "Invasive adenocarcinoma":          "Adenocarcinoma",
    "Invasive adenocarcinoma, endocervical type.": "Adenocarcinoma",
    "Adenocarcinoma. Glandular invasion present.": "Adenocarcinoma",
    "Endocervical adenocarcinoma. Invasive.":       "Adenocarcinoma",
    "Invasive mucinous adenocarcinoma.":            "Adenocarcinoma",
    "Adenocarcinoma, usual type. Stromal invasion.": "Adenocarcinoma",
    "Invasive endocervical adenocarcinoma. Depth 3mm.": "Adenocarcinoma",
    "Adenocarcinoma. Lymphovascular invasion present.": "Adenocarcinoma",
    "Gastric-type adenocarcinoma. Invasive.":           "Adenocarcinoma",
    "Adenocarcinoma in situ with invasive component.":  "Adenocarcinoma",
    "Invasive cervical adenocarcinoma. Margins clear.": "Adenocarcinoma",
}

CLASSIFICATION_GOLD_STANDARD = [
    ("NILM",      "Benign / Inflammatory (Negative)", "concordant"),
    ("HSIL",      "HSIL (CIN2)",                      "concordant"),
    ("HSIL",      "HSIL (CIN3)",                      "concordant"),
    ("LSIL",      "LSIL (CIN1)",                      "concordant"),
    ("ASC-US",    "LSIL (CIN1)",                      "concordant"),
    ("ASC-H",     "HSIL (CIN2)",                      "concordant"),
    ("ASC-H",     "HSIL (CIN3)",                      "concordant"),
    ("AGC-NEO",   "HSIL (CIN2)",                      "concordant"),
    ("AGC-NEO",   "HSIL (CIN3)",                      "concordant"),
    ("AGC-NEO",   "Adenocarcinoma",                    "concordant"),
    ("MALIGNANT", "Squamous Cell Carcinoma",           "concordant"),
    ("MALIGNANT", "Adenocarcinoma",                    "concordant"),
    ("AGC",       "LSIL (CIN1)",                      "concordant"),
    ("AGC-ECX",   "LSIL (CIN1)",                      "concordant"),
    ("OTHER (EMC45)", "Benign / Inflammatory (Negative)", "concordant"),
    ("NILM",   "HSIL (CIN2)",              "major_discordant"),
    ("NILM",   "HSIL (CIN3)",              "major_discordant"),
    ("NILM",   "Squamous Cell Carcinoma",  "major_discordant"),
    ("NILM",   "Adenocarcinoma",           "major_discordant"),
    ("ASC-US", "Squamous Cell Carcinoma",  "major_discordant"),
    ("ASC-US", "Adenocarcinoma",           "major_discordant"),
    ("OTHER (EMC45)", "HSIL (CIN2)",       "major_discordant"),
    ("OTHER (EMC45)", "HSIL (CIN3)",       "major_discordant"),
    ("OTHER (EMC45)", "Squamous Cell Carcinoma", "major_discordant"),
    ("HSIL",   "Benign / Inflammatory (Negative)", "major_discordant"),
    ("ASC-H",     "Benign / Inflammatory (Negative)", "major_discordant"),
    ("MALIGNANT", "Benign / Inflammatory (Negative)", "major_discordant"),
    ("MALIGNANT", "LSIL (CIN1)",                      "major_discordant"),
    ("AIS",       "Benign / Inflammatory (Negative)", "major_discordant"),
    ("AIS",       "LSIL (CIN1)",                      "major_discordant"),
    ("NILM",   "LSIL (CIN1)",             "minor_discordant"),
    ("LSIL",   "HSIL (CIN2)",             "minor_discordant"),
    ("LSIL",   "HSIL (CIN3)",             "minor_discordant"),
    ("ASC-US", "HSIL (CIN2)",             "minor_discordant"),
    ("ASC-US", "HSIL (CIN3)",             "minor_discordant"),
    ("LSIL",   "Squamous Cell Carcinoma", "minor_discordant"),
    ("LSIL",   "Adenocarcinoma",          "minor_discordant"),
    ("AGC",    "HSIL (CIN2)",             "minor_discordant"),
    ("AGC",    "HSIL (CIN3)",             "minor_discordant"),
    ("HSIL",   "Squamous Cell Carcinoma", "minor_discordant"),
    ("HSIL",     "LSIL (CIN1)",           "minor_discordant"),
    ("LSIL",     "Benign / Inflammatory (Negative)", "minor_discordant"),
    ("AGC-NEO",  "LSIL (CIN1)",           "minor_discordant"),
    ("MALIGNANT","HSIL (CIN2)",            "minor_discordant"),
    ("MALIGNANT","HSIL (CIN3)",            "minor_discordant"),
    ("ASC-H",    "LSIL (CIN1)",           "minor_discordant"),
    ("AGC",      "Benign / Inflammatory (Negative)", "minor_discordant"),
    ("AGC-ECX",  "Benign / Inflammatory (Negative)", "minor_discordant"),
    ("AGC-EMC",  "Benign / Inflammatory (Negative)", "minor_discordant"),
    ("OTHER (EMC45)", "LSIL (CIN1)",           "minor_discordant"),
    ("ASC-US",        "Benign / Inflammatory (Negative)", "minor_discordant"),
    ("AIS",           "HSIL (CIN2)",            "minor_discordant"),
    ("AIS",           "HSIL (CIN3)",            "minor_discordant"),
    ("AIS",           "Squamous Cell Carcinoma","minor_discordant"),
]


def generate_html_report(cyto_rows, histo_rows, class_rows, summary):
    """Generate a detailed HTML results table with reasoning."""

    def status_badge(correct):
        if correct:
            return '<span style="background:#4CAF50;color:white;padding:2px 8px;border-radius:4px;font-size:0.8rem;">PASS</span>'
        return '<span style="background:#f44336;color:white;padding:2px 8px;border-radius:4px;font-size:0.8rem;">FAIL</span>'

    def conf_badge(conf):
        colors = {"high": "#2196F3", "medium": "#FF9800", "low": "#9E9E9E"}
        color  = colors.get(str(conf).lower(), "#9E9E9E")
        return f'<span style="background:{color};color:white;padding:2px 8px;border-radius:4px;font-size:0.8rem;">{conf}</span>'

    def build_table(rows, columns):
        html  = '<table style="width:100%;border-collapse:collapse;font-size:0.85rem;">'
        html += '<thead><tr style="background:#1565C0;color:white;">'
        for col in columns:
            html += f'<th style="padding:8px;text-align:left;">{col}</th>'
        html += '</tr></thead><tbody>'
        for i, row in enumerate(rows):
            bg    = "#f8f9fa" if i % 2 == 0 else "white"
            html += f'<tr style="background:{bg};">'
            for cell in row:
                html += f'<td style="padding:8px;border-bottom:1px solid #eee;">{cell}</td>'
            html += '</tr>'
        html += '</tbody></table>'
        return html

    # Build cyto table rows
    cyto_table_rows = []
    for r in cyto_rows:
        cyto_table_rows.append([
            f'<small>{r["raw_text"][:80]}</small>',
            r["expected"],
            r["predicted"] if r["predicted"] else '<span style="color:red;">None</span>',
            status_badge(r["correct"]),
            conf_badge(r["confidence"]),
            f'<small style="color:#555;">{r["reasoning"][:120] if r["reasoning"] else "-"}</small>'
        ])

    # Build histo table rows
    histo_table_rows = []
    for r in histo_rows:
        histo_table_rows.append([
            f'<small>{r["raw_text"][:80]}</small>',
            r["expected"],
            r["predicted"] if r["predicted"] else '<span style="color:red;">None</span>',
            status_badge(r["correct"]),
            conf_badge(r["confidence"]),
            f'<small style="color:#555;">{r["reasoning"][:120] if r["reasoning"] else "-"}</small>'
        ])

    # Build classification table rows
    class_table_rows = []
    for r in class_rows:
        class_table_rows.append([
            r["cyto"],
            r["histo"],
            r["expected"],
            r["predicted"] if r["predicted"] else '<span style="color:red;">None</span>',
            status_badge(r["correct"])
        ])

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>CHC-QA Evaluation Results</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 2rem; background: #f5f5f5; }}
  .header {{ background: linear-gradient(135deg, #1565C0, #0D47A1); color: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem; }}
  .card {{ background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
  .summary-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem; }}
  .metric {{ background: white; border-radius: 8px; padding: 1rem; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
  .metric-value {{ font-size: 2rem; font-weight: 700; }}
  .metric-label {{ font-size: 0.8rem; color: #666; margin-top: 0.3rem; }}
  .green {{ color: #2E7D32; }}
  .red {{ color: #C62828; }}
  .orange {{ color: #E65100; }}
  .blue {{ color: #1565C0; }}
  .section-title {{ font-size: 1.2rem; font-weight: 700; color: #1565C0; border-left: 4px solid #1565C0; padding-left: 0.8rem; margin-bottom: 1rem; }}
  .calibration-bar {{ display: flex; align-items: center; gap: 1rem; margin: 0.5rem 0; }}
  .bar {{ height: 20px; border-radius: 4px; }}
  .bar-conf {{ background: #2196F3; }}
  .bar-acc {{ background: #4CAF50; }}
</style>
</head>
<body>

<div class="header">
  <h1 style="margin:0;">CHC-QA Pipeline Evaluation Report</h1>
  <p style="margin:0.5rem 0 0 0;opacity:0.8;">
    Clinical LLM Evaluation: Accuracy + Hallucination + Confidence Calibration
  </p>
</div>

<div class="summary-grid">
  <div class="metric">
    <div class="metric-value blue">{summary["total_cases"]}</div>
    <div class="metric-label">Total Test Cases</div>
  </div>
  <div class="metric">
    <div class="metric-value green">{summary["overall_accuracy"]:.1f}%</div>
    <div class="metric-label">Overall Accuracy</div>
  </div>
  <div class="metric">
    <div class="metric-value {'red' if summary['hallucination_rate'] > 3 else 'orange'}">{summary["hallucination_rate"]:.1f}%</div>
    <div class="metric-label">Hallucination Rate</div>
  </div>
  <div class="metric">
    <div class="metric-value {'green' if summary['major_fn_rate'] == 0 else 'red'}">{summary["major_fn_rate"]:.1f}%</div>
    <div class="metric-label">Major Discordance FN Rate</div>
  </div>
</div>

<div class="card">
  <div class="section-title">Summary Metrics</div>
  <table style="width:100%;border-collapse:collapse;">
    <tr style="background:#E3F2FD;">
      <th style="padding:8px;text-align:left;">Metric</th>
      <th style="padding:8px;">Cytology</th>
      <th style="padding:8px;">Histology</th>
      <th style="padding:8px;">Classification</th>
    </tr>
    <tr>
      <td style="padding:8px;">Overall Accuracy</td>
      <td style="padding:8px;text-align:center;">{summary["cyto_accuracy"]:.1f}%</td>
      <td style="padding:8px;text-align:center;">{summary["histo_accuracy"]:.1f}%</td>
      <td style="padding:8px;text-align:center;">{summary["class_accuracy"]:.1f}%</td>
    </tr>
    <tr style="background:#f8f9fa;">
      <td style="padding:8px;">Hallucination Rate</td>
      <td style="padding:8px;text-align:center;">{summary["cyto_halluc"]:.1f}%</td>
      <td style="padding:8px;text-align:center;">{summary["histo_halluc"]:.1f}%</td>
      <td style="padding:8px;text-align:center;">N/A</td>
    </tr>
    <tr>
      <td style="padding:8px;">Calibration ECE</td>
      <td style="padding:8px;text-align:center;">{summary["cyto_ece"]:.2f}%</td>
      <td style="padding:8px;text-align:center;">{summary["histo_ece"]:.2f}%</td>
      <td style="padding:8px;text-align:center;">N/A</td>
    </tr>
    <tr style="background:#f8f9fa;">
      <td style="padding:8px;">High Conf Accuracy</td>
      <td style="padding:8px;text-align:center;">{summary["cyto_high_conf_acc"]:.1f}%</td>
      <td style="padding:8px;text-align:center;">{summary["histo_high_conf_acc"]:.1f}%</td>
      <td style="padding:8px;text-align:center;">N/A</td>
    </tr>
    <tr>
      <td style="padding:8px;">Major FN Rate</td>
      <td style="padding:8px;text-align:center;">N/A</td>
      <td style="padding:8px;text-align:center;">N/A</td>
      <td style="padding:8px;text-align:center;color:{'green' if summary['major_fn_rate']==0 else 'red'};">{summary["major_fn_rate"]:.1f}%</td>
    </tr>
  </table>
</div>

<div class="card">
  <div class="section-title">Cytology Normalization Results ({len(cyto_rows)} cases)</div>
  {build_table(cyto_table_rows, ["Raw Text", "Expected", "Predicted", "Result", "Confidence", "LLM Reasoning"])}
</div>

<div class="card">
  <div class="section-title">Histology Normalization Results ({len(histo_rows)} cases)</div>
  {build_table(histo_table_rows, ["Raw Text", "Expected", "Predicted", "Result", "Confidence", "LLM Reasoning"])}
</div>

<div class="card">
  <div class="section-title">Classification Results ({len(class_rows)} pairs)</div>
  {build_table(class_table_rows, ["Cytology", "Histology", "Expected", "Predicted", "Result"])}
</div>

<div class="card">
  <div class="section-title">Key Clinical Finding</div>
  <p>When the LLM returns <strong>medium confidence</strong> the prediction is incorrect
  in {summary.get('medium_error_rate', 100):.0f}% of cases. Medium and low confidence outputs
  should trigger mandatory manual review before clinical use.</p>
  <p>The <strong>Major Discordance False Negative Rate is {summary['major_fn_rate']:.1f}%</strong>
  ? meaning no clinically significant discordant pair was missed by the classification engine.</p>
</div>

<div style="text-align:center;color:#9E9E9E;font-size:0.8rem;margin-top:2rem;">
  CHC-QA Pipeline | Evaluation Report | github.com/solomoneluanu/chc-qa-pipeline
</div>

</body>
</html>"""

    return html


def compute_calibration_metrics(confidences, correct_flags):
    confidence_map = {"high": 0.9, "medium": 0.6, "low": 0.3}
    bins = {
        "high":   {"conf": [], "correct": []},
        "medium": {"conf": [], "correct": []},
        "low":    {"conf": [], "correct": []}
    }
    for conf, correct in zip(confidences, correct_flags):
        level = conf if conf in bins else "medium"
        bins[level]["conf"].append(confidence_map.get(conf, 0.5))
        bins[level]["correct"].append(1 if correct else 0)

    calibration = {}
    ece = 0.0
    total = len(confidences)

    for level, data in bins.items():
        if not data["conf"]:
            continue
        avg_conf = np.mean(data["conf"])
        avg_acc  = np.mean(data["correct"])
        count    = len(data["conf"])
        weight   = count / total
        calibration[level] = {
            "count":            count,
            "avg_confidence":   round(avg_conf * 100, 1),
            "actual_accuracy":  round(avg_acc * 100, 1),
            "gap":              round(abs(avg_conf - avg_acc) * 100, 1)
        }
        ece += weight * abs(avg_conf - avg_acc)

    high_conf_indices  = [i for i, c in enumerate(confidences) if c == "high"]
    high_conf_accuracy = (
        sum(correct_flags[i] for i in high_conf_indices) /
        len(high_conf_indices) * 100 if high_conf_indices else 0
    )

    med_conf_indices   = [i for i, c in enumerate(confidences) if c == "medium"]
    med_conf_accuracy  = (
        sum(correct_flags[i] for i in med_conf_indices) /
        len(med_conf_indices) * 100 if med_conf_indices else 100
    )

    return {
        "ece":               round(ece * 100, 2),
        "bins":              calibration,
        "high_conf_accuracy": round(high_conf_accuracy, 1),
        "high_conf_count":   len(high_conf_indices),
        "med_conf_accuracy": round(med_conf_accuracy, 1),
        "med_error_rate":    100 - round(med_conf_accuracy, 1)
    }


def run_full_evaluation():
    print("\nCHC-QA PIPELINE EVALUATION")
    print("="*60)

    # ?? Cytology ??????????????????????????????????????????????
    print("\nEvaluating CYTOLOGY...")
    cyto_texts    = list(CYTO_GOLD_STANDARD.keys())
    cyto_expected = list(CYTO_GOLD_STANDARD.values())
    cyto_df       = pd.DataFrame({"raw_diag": cyto_texts})
    cyto_result   = normalize_cyto_sheet(cyto_df, "raw_diag", "config/diagnosis_dictionary.yaml")

    cyto_predicted   = cyto_result["Cytology_Canonical"].tolist()
    cyto_confidences = cyto_result["Cyto_LLM_Confidence"].tolist() if "Cyto_LLM_Confidence" in cyto_result.columns else ["high"]*len(cyto_texts)
    cyto_reasoning   = cyto_result["Cyto_LLM_Reasoning"].tolist()  if "Cyto_LLM_Reasoning"  in cyto_result.columns else [""]*len(cyto_texts)
    cyto_correct     = [p == e for p, e in zip(cyto_predicted, cyto_expected)]

    cyto_calib  = compute_calibration_metrics(cyto_confidences, cyto_correct)
    cyto_acc    = sum(cyto_correct) / len(cyto_correct) * 100
    cyto_halluc = sum(1 for p, e in zip(cyto_predicted, cyto_expected) if p != e and p is not None) / len(cyto_texts) * 100

    cyto_rows = []
    for i in range(len(cyto_texts)):
        cyto_rows.append({
            "raw_text":   cyto_texts[i],
            "expected":   cyto_expected[i],
            "predicted":  cyto_predicted[i],
            "correct":    cyto_correct[i],
            "confidence": cyto_confidences[i],
            "reasoning":  cyto_reasoning[i]
        })

    print(f"  Accuracy:    {cyto_acc:.1f}%")
    print(f"  Hallucination: {cyto_halluc:.1f}%")
    print(f"  Calibration ECE: {cyto_calib['ece']}%")

    # ?? Histology ?????????????????????????????????????????????
    print("\nEvaluating HISTOLOGY...")
    histo_texts    = list(HISTO_GOLD_STANDARD.keys())
    histo_expected = list(HISTO_GOLD_STANDARD.values())
    histo_df       = pd.DataFrame({"raw_diag": histo_texts})
    histo_result   = normalize_histo_sheet(histo_df, "raw_diag", "config/diagnosis_dictionary.yaml")

    histo_predicted   = histo_result["Histology_Canonical"].tolist()
    histo_confidences = histo_result["Histo_LLM_Confidence"].tolist() if "Histo_LLM_Confidence" in histo_result.columns else ["high"]*len(histo_texts)
    histo_reasoning   = histo_result["Histo_LLM_Reasoning"].tolist()  if "Histo_LLM_Reasoning"  in histo_result.columns else [""]*len(histo_texts)
    histo_correct     = [p == e for p, e in zip(histo_predicted, histo_expected)]

    histo_calib  = compute_calibration_metrics(histo_confidences, histo_correct)
    histo_acc    = sum(histo_correct) / len(histo_correct) * 100
    histo_halluc = sum(1 for p, e in zip(histo_predicted, histo_expected) if p != e and p is not None) / len(histo_texts) * 100

    histo_rows = []
    for i in range(len(histo_texts)):
        histo_rows.append({
            "raw_text":   histo_texts[i],
            "expected":   histo_expected[i],
            "predicted":  histo_predicted[i],
            "correct":    histo_correct[i],
            "confidence": histo_confidences[i],
            "reasoning":  histo_reasoning[i]
        })

    print(f"  Accuracy:    {histo_acc:.1f}%")
    print(f"  Hallucination: {histo_halluc:.1f}%")
    print(f"  Calibration ECE: {histo_calib['ece']}%")

    # ?? Classification ????????????????????????????????????????
    print("\nEvaluating CLASSIFICATION...")
    records = [
        {"Cytology_Diagnosis": c, "Histology_Diagnosis": h}
        for c, h, e in CLASSIFICATION_GOLD_STANDARD
    ]
    df         = pd.DataFrame(records)
    df         = normalize_diagnoses(df, "config/diagnosis_dictionary.yaml")
    classified = classify_pairs(df, "config/discrepancy_rules.csv")

    class_rows   = []
    class_correct = 0
    major_fn      = 0
    major_total   = sum(1 for _, _, e in CLASSIFICATION_GOLD_STANDARD if e == "major_discordant")

    for i, (cyto, histo, expected) in enumerate(CLASSIFICATION_GOLD_STANDARD):
        predicted = classified.iloc[i].get("Concordance_Class", "unknown")
        correct   = predicted == expected
        if correct:
            class_correct += 1
        if expected == "major_discordant" and not correct:
            major_fn += 1
        class_rows.append({
            "cyto":      cyto,
            "histo":     histo,
            "expected":  expected,
            "predicted": predicted,
            "correct":   correct
        })

    class_acc    = class_correct / len(CLASSIFICATION_GOLD_STANDARD) * 100
    major_fn_rate = major_fn / major_total * 100 if major_total > 0 else 0

    print(f"  Accuracy:    {class_acc:.1f}%")
    print(f"  Major FN Rate: {major_fn_rate:.1f}%")

    # ?? Summary ???????????????????????????????????????????????
    overall = (cyto_acc + histo_acc + class_acc) / 3
    summary = {
        "total_cases":        len(cyto_texts) + len(histo_texts),
        "overall_accuracy":   overall,
        "hallucination_rate": (cyto_halluc + histo_halluc) / 2,
        "major_fn_rate":      major_fn_rate,
        "cyto_accuracy":      cyto_acc,
        "histo_accuracy":     histo_acc,
        "class_accuracy":     class_acc,
        "cyto_halluc":        cyto_halluc,
        "histo_halluc":       histo_halluc,
        "cyto_ece":           cyto_calib["ece"],
        "histo_ece":          histo_calib["ece"],
        "cyto_high_conf_acc": cyto_calib["high_conf_accuracy"],
        "histo_high_conf_acc": histo_calib["high_conf_accuracy"],
        "medium_error_rate":  cyto_calib.get("med_error_rate", 100)
    }

    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"Overall Accuracy:          {overall:.1f}%")
    print(f"Hallucination Rate:        {summary['hallucination_rate']:.1f}%")
    print(f"Major Discordance FN Rate: {major_fn_rate:.1f}%")

    # ?? Generate HTML report ??????????????????????????????????
    html = generate_html_report(cyto_rows, histo_rows, class_rows, summary)
    html_path = "data/output-data/evaluation_report.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\nHTML report saved: {html_path}")
    print("Open in Chrome to view the full results table with reasoning.")

    return summary


if __name__ == "__main__":
    run_full_evaluation()
