readme = """# CHC-QA Pipeline

> The first open source, LIS-agnostic, LLM-assisted automated cytology-histology correlation quality assurance platform.

Every CAP-accredited cytopathology laboratory is required to correlate Pap test results with biopsy results for the same patient -- a process called cytology-histology correlation (CHC). Today this takes 20-40 hours of manual work every month. CHC-QA Pipeline does it in under 10 minutes.

---

## Live Demo

Try the app: YOUR_ACTUAL_URL_HERE

---

## The Problem

Manual CHC workflows rely on Excel and VLOOKUP which fail on the messy free-text terminology that real laboratory information systems (LIS) produce. A lab coordinator spends hours every month cleaning data before any analysis can begin. CHC-QA Pipeline eliminates that manual cleaning step entirely.

Manual process today:
- Export from LIS
- Clean column names
- Standardize terminology
- Run VLOOKUP
- Fix VLOOKUP errors
- Calculate metrics
- Build charts
- Write report
- Time: 20-40 hours per month

CHC-QA Pipeline:
- Upload Excel file
- Click Run
- Download QA report
- Time: 8 minutes first run, under 1 minute after
- Accuracy: 98.4%
- Major FN rate: 0.0%

---

## Key Features

- LIS-agnostic ingestion: works with any LIS export including CoPath, Epic Beaker, Sunquest, and Cerner. Column names are auto-detected.
- LLM-assisted normalization: local Gemma3 maps any free-text diagnosis variant to canonical Bethesda/CIN terminology. Runs offline. HIPAA compliant.
- Deterministic classification: CAP-aligned rules engine per ASC Birdsong Guideline 2017. Same input always produces same output.
- Complete Birdsong metrics: all five Section 7 statistical calculations plus intergrade follow-up rates, extended PV+, agreement within one grade, and PV+ interpretation flag.
- Professional reports: color-coded Excel workbook and multi-section PDF with CAP compliance signals, ready for lab meetings and inspection.
- Modern visualizations: concordance distribution, discrepancy buckets with zone labels, HSIL metrics with CAP target line, confusion matrix with diagonal highlighting, summary dashboard.
- Streamlit web UI: upload, run, download. No technical expertise required.

---

## Evaluation Results

Evaluated on a gold standard test set of 204 cases (105 cytology + 99 histology + 54 classification pairs):

| Metric | Result |
|--------|--------|
| Cytology LLM Normalization | 97.1% |
| Histology LLM Normalization | 98.0% |
| Classification Accuracy | 100.0% |
| Overall Average | 98.4% |
| Major Discordance False Negative Rate | 0.0% |
| High Confidence Prediction Accuracy | 99.0% |
| Expected Calibration Error (Cyto) | 10.57% |

Key Finding: When the LLM returns medium confidence the prediction is incorrect in 100% of cases. Medium confidence outputs trigger mandatory manual review in clinical deployment.

---

## Architecture

```
ingest.py         LIS-agnostic data loading, auto column detection
llm_normalizer.py Gemma3:4b via Ollama, free text to canonical term, persistent cache
pairer.py         MRN + date window matching, 3-tier fallback logic
normalize.py      Dictionary-based normalization
classify.py       Deterministic rules engine, Birdsong Figure 1 grid
metrics.py        Birdsong Section 5, 7, 8 metrics
export.py         Excel workbook generation
pdf_report.py     8-section PDF report generation
visualize.py      Modern chart generation
```

Design principle: LLM for semantic flexibility in normalization. Deterministic rules for clinical accountability in classification. Never the other way around.

---

## Birdsong Metrics Implemented

Per ASC Clinical Practice Committee Birdsong Guideline 2017:

Section 5 - Tabulation:
- Exact agreement rate
- Minor disagreement rate
- Major disagreement rate
- Agreement within one grade
- PV+

Section 7 - Statistical Calculations:
- Percent of HSIL Pap tests with HSIL histology
- Percent of HSIL Pap tests with minor discrepancies
- Percent of HSIL Pap tests with major FP discrepancies
- Number of major FN cytology undercalls
- PV+ for HSIL Pap tests
- PV+ interpretation flag (HIGH / ACCEPTABLE / LOW)
- Extended PV+ (HSIL + ASC-H + AGC-NEO)

Section 8 - Intergrade Follow-Up Rates:
- HSIL+ histology rates following ASC-US, ASC-H, LSIL, AGC, AGC-NEO, AGC-ECX, AGC-EMC

---

## CAP Compliance

This pipeline directly addresses CAP checklist requirement CYP.06600:

"Does the laboratory have a cytologic-histologic correlation program?"

The pipeline generates all required documentation including concordance rates, discrepancy classification, HSIL PV+, and major discordance case identification.

---

## Installation

Prerequisites:
- Python 3.10+
- Ollama installed and running (https://ollama.ai)
- Gemma3:4b model pulled

Install Ollama then pull the model:
    ollama pull gemma3:4b

Setup:
    git clone https://github.com/solomoneluanu/chc-qa-pipeline.git
    cd chc-qa-pipeline
    conda create -n chc python=3.10
    conda activate chc
    pip install -r requirements.txt

Run:
    streamlit run app/streamlit_app.py

Or run the pipeline directly:
    python scripts/run_pipeline.py --mode real --input data/input-data/your_file.xlsx

Run the evaluation framework:
    python scripts/evaluate_pipeline.py

---

## Input Format

Real Lab Mode:
Upload an Excel file with two sheets:
- Sheet 1: Cytology data (MRN, date, diagnosis columns auto-detected)
- Sheet 2: Histology data (MRN, date, diagnosis columns auto-detected)

Column names are auto-detected. Works with any LIS export format.

Evaluation Mode:
Upload a pre-paired CSV or Excel with Cytology_Diagnosis and Histology_Diagnosis columns.

---

## Output

| Output | Format | Contents |
|--------|--------|----------|
| QA Report | Excel | Color-coded case detail, concordance tables, all Birdsong metrics |
| QA Report | PDF | 8 sections: executive summary, concordance, buckets, HSIL metrics, intergrade analysis, key signals, figures, limitations |
| Figures | PNG | Concordance distribution, discrepancy buckets, HSIL metrics, confusion matrix, summary dashboard |
| Unmatched Cases | Excel | Cases with no histology pair found within the pairing window |

---

## HIPAA Compliance

All LLM processing runs locally via Ollama. No patient data leaves the institution. No Business Associate Agreement (BAA) required. No internet connection needed for core functionality.

---

## Project Structure

    chc-qa-pipeline/
    app/
        streamlit_app.py          Streamlit web interface
    src/chc_pipeline/
        ingest.py                 LIS-agnostic data loading
        llm_normalizer.py         LLM normalization with cache
        pairer.py                 Case pairing by MRN and date
        normalize.py              Dictionary normalization
        classify.py               Deterministic classification
        metrics.py                Birdsong metrics computation
        export.py                 Excel report generation
        pdf_report.py             PDF report generation
        visualize.py              Chart generation
    scripts/
        run_pipeline.py           Command line pipeline runner
        evaluate_pipeline.py      Comprehensive evaluation framework
    config/
        diagnosis_dictionary.yaml Terminology mapping
        discrepancy_rules.csv     Classification rules
    data/
        input-data/               Input files
        output-data/              Generated reports and figures

---

## Clinical Impact

For a typical cytopathology laboratory processing 100-200 cases per month:

| | Manual Process | CHC-QA Pipeline |
|---|---|---|
| Time per month | 20-40 hours | 8 minutes |
| Annual cost | $16,000-$32,000 | $0 |
| Reproducibility | Variable | 100% |
| Audit trail | Manual | Automatic |
| Major discordance detection | Human dependent | 0% FN rate |

---

## Published Work

Preprint available on Research Square.
Peer-reviewed journal submission in preparation targeting Journal of Pathology Informatics.

---

## Reference

Birdsong GG, Walker JW. Gynecologic Cytology-Histology Correlation Guideline.
ASC Bulletin. 2017;LIV(2):VIII-XIII.

---

## Author

Solomon Eluanu, MD
MD + MSc Artificial Intelligence in Medicine candidate
University of Louisville

---

## License

MIT License -- free to use, modify, and deploy in any laboratory setting.

---

## Citation

If you use this tool in research or clinical practice please cite:

    Eluanu S. CHC-QA Pipeline: An automated cytology-histology correlation
    quality assurance platform. GitHub. 2026.
    https://github.com/solomoneluanu/chc-qa-pipeline
"""

with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme)

print("README.md written successfully")#   C H C - Q A   P i p e l i n e  
 