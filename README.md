# CHC-QA Pipeline

**Automated cytology–histology correlation for CAP-accredited laboratories.**
Upload your LIS export. Get an inspection-ready QA report.

[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://chc--pipeline.streamlit.app/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/)

---

|  |  |  |
|:--:|:--:|:--:|
| **40 hrs → 8 min** | **98.4%** | **0.0%** |
| monthly QA workload | normalization + classification accuracy | major discordance false-negative rate |

**→ [Try it now](https://chc--pipeline.streamlit.app/)** — no installation required.

---

<!-- Add a screenshot of the Streamlit app or a page of the PDF report here.
     ![CHC-QA Pipeline report](docs/screenshot.png) -->

## The problem

Every CAP-accredited cytopathology lab must correlate Pap results with subsequent biopsies. The requirement is clear; the work is not. Real LIS exports arrive as messy free text — a dozen ways to write the same diagnosis — and Excel VLOOKUP breaks on all of them. So a coordinator spends the first several hours of every month cleaning data before any analysis can start, then rebuilds the same charts and the same report they built last month.

CHC-QA Pipeline removes the cleaning step entirely. Upload the export, click Run, download the report.

## How it works

```
ingest  →  LLM normalization  →  pairing  →  deterministic classification  →  metrics  →  report
```

| Stage | What happens |
|---|---|
| **Ingest** | Auto-detects columns from any LIS export — CoPath, Epic Beaker, Sunquest, Cerner |
| **Normalize** | Local Gemma3 maps free-text diagnoses to canonical Bethesda/CIN terminology |
| **Pair** | MRN + date-window matching with three-tier fallback |
| **Classify** | CAP-aligned rules engine, ASC Birdsong Guideline 2017 |
| **Report** | Color-coded Excel workbook, 8-section PDF, publication-quality figures |

> **Design principle:** LLM for semantic flexibility in normalization.
> Deterministic rules for clinical accountability in classification.
> **Never the other way around.**

The LLM handles language, where variation is the problem. The rules engine handles classification, where reproducibility is the requirement — the same input always produces the same output, and every result is traceable to a published guideline.

All LLM processing runs locally through Ollama. No patient data leaves the institution, and no vendor Business Associate Agreement is required.

## Evaluation

Measured against a gold-standard set of 204 cases — 105 cytology, 99 histology, 54 classification pairs.

| Metric | Result |
|---|---|
| Classification accuracy | **100.0%** |
| Histology normalization | 98.0% |
| Cytology normalization | 97.1% |
| **Overall** | **98.4%** |
| Major discordance, false-negative rate | **0.0%** |
| High-confidence prediction accuracy | 99.0% |
| Expected calibration error (cytology) | 10.57% |

**The finding that shaped deployment:** when the model returns *medium* confidence, it is wrong in 100% of cases. Medium-confidence outputs therefore trigger mandatory manual review rather than flowing into the report. Calibration is a safety feature, not a statistic.

## What you get

Concordance rates, discrepancy classification, HSIL PV+, and major-discordance case identification — the documentation CAP checklist item **CYP.06600** asks for.

- **Excel** — color-coded case detail, concordance tables, all Birdsong metrics
- **PDF** — 8 sections from executive summary through limitations
- **Figures** — concordance distribution, discrepancy buckets, HSIL metrics against the CAP target line, confusion matrix, summary dashboard
- **Unmatched cases** — every cytology case with no histology pair in the window

<details>
<summary><b>Birdsong metrics implemented</b> — full list</summary>

Per ASC Clinical Practice Committee Birdsong Guideline 2017.

**Section 5 — Tabulation**
Exact agreement rate · minor disagreement rate · major disagreement rate · agreement within one grade · PV+

**Section 7 — Statistical calculations**
HSIL Pap tests with HSIL histology · HSIL Pap tests with minor discrepancies · HSIL Pap tests with major FP discrepancies · major FN cytology undercalls · PV+ for HSIL Pap tests · PV+ interpretation flag (HIGH / ACCEPTABLE / LOW) · extended PV+ (HSIL + ASC-H + AGC-NEO)

**Section 8 — Intergrade follow-up rates**
HSIL+ histology rates following ASC-US, ASC-H, LSIL, AGC, AGC-NEO, AGC-ECX, AGC-EMC

</details>

<details>
<summary><b>Installation</b> — run it locally</summary>

Requires Python 3.10+ and [Ollama](https://ollama.ai).

```bash
ollama pull gemma3:4b

git clone https://github.com/solomoneluanu/chc-qa-pipeline.git
cd chc-qa-pipeline
conda create -n chc python=3.10 && conda activate chc
pip install -r requirements.txt

streamlit run app/streamlit_app.py
```

Command line:

```bash
python scripts/run_pipeline.py --mode real --input data/input-data/your_file.xlsx
python scripts/evaluate_pipeline.py     # evaluation framework
```

**Input format.** Real-lab mode takes an Excel file with two sheets — cytology and histology. MRN, date, and diagnosis columns are auto-detected. Evaluation mode takes a pre-paired CSV or Excel with `Cytology_Diagnosis` and `Histology_Diagnosis` columns.

</details>

<details>
<summary><b>Project structure</b></summary>

```
app/streamlit_app.py            web interface
src/chc_pipeline/
    ingest.py                   LIS-agnostic loading, column detection
    llm_normalizer.py           Gemma3 normalization + persistent cache
    pairer.py                   MRN/date pairing, 3-tier fallback
    normalize.py                dictionary normalization
    classify.py                 deterministic rules engine
    metrics.py                  Birdsong Sections 5, 7, 8
    export.py / pdf_report.py / visualize.py
scripts/
    run_pipeline.py             CLI runner
    evaluate_pipeline.py        evaluation framework
config/
    diagnosis_dictionary.yaml   terminology mapping
    discrepancy_rules.csv       classification rules
```

</details>

## Status

Preprint on Research Square. Peer-reviewed submission in preparation, targeting *Journal of Pathology Informatics*.

Evaluation was performed on a gold-standard test set; prospective validation in a live laboratory workflow has not yet been completed.

## Reference

Birdsong GG, Walker JW. *Gynecologic Cytology–Histology Correlation Guideline.* ASC Bulletin. 2017;LIV(2):VIII–XIII.

## Author

**Solomon Eluanu, MD** — MD, MSc Artificial Intelligence in Medicine candidate, University of Louisville

## License

MIT — free to use, modify, and deploy in any laboratory setting.

```
Eluanu S. CHC-QA Pipeline: An automated cytology–histology correlation
quality assurance platform. GitHub. 2026.
https://github.com/solomoneluanu/chc-qa-pipeline
```
