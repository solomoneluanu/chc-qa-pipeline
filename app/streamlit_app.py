import streamlit as st
import pandas as pd
import os
import sys
import tempfile

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.chc_pipeline.ingest import load_combined_excel, load_cyto_sheet, load_histo_sheet
from src.chc_pipeline.llm_normalizer import normalize_cyto_sheet, normalize_histo_sheet
from src.chc_pipeline.pairer import pair_cases
from src.chc_pipeline.normalize import normalize_diagnoses
from src.chc_pipeline.classify import classify_pairs
from src.chc_pipeline.metrics import compute_metrics
from src.chc_pipeline.export import export_results
from src.chc_pipeline.visualize import generate_all_figures
from src.chc_pipeline.pdf_report import build_pdf_report
from src.chc_pipeline.llm_insights import generate_qa_insights

st.set_page_config(page_title="CHC-QA Pipeline", layout="wide")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 2rem;}
    .app-header {
        background: linear-gradient(135deg, #1565C0 0%, #0D47A1 100%);
        padding: 2rem 2.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        color: white;
    }
    .app-header h1 {color: white; font-size: 2rem; font-weight: 700; margin: 0; padding: 0;}
    .app-header p {color: #BBDEFB; margin: 0.3rem 0 0 0; font-size: 1rem;}
    .step-header {
        background: #E3F2FD;
        border-left: 5px solid #1565C0;
        padding: 0.7rem 1rem;
        border-radius: 0 8px 8px 0;
        font-weight: 700;
        font-size: 1.1rem;
        color: #1565C0;
        margin-bottom: 1rem;
    }
    .info-card {background: #F8F9FA; border: 1px solid #E0E0E0; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;}
    .success-card {background: #E8F5E9; border: 1px solid #66BB6A; border-radius: 8px; padding: 0.8rem 1rem; color: #2E7D32; font-weight: 600; margin-bottom: 1rem;}
    .warning-card {background: #FFF8E1; border: 1px solid #FFA726; border-radius: 8px; padding: 0.8rem 1rem; color: #E65100; font-weight: 600; margin-bottom: 1rem;}
    .error-card {background: #FFEBEE; border: 1px solid #EF5350; border-radius: 8px; padding: 0.8rem 1rem; color: #C62828; font-weight: 600; margin-bottom: 1rem;}
    .metric-box {background: white; border: 1px solid #E0E0E0; border-radius: 10px; padding: 1.2rem; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);}
    .metric-value {font-size: 2.2rem; font-weight: 700; line-height: 1;}
    .metric-label {font-size: 0.85rem; color: #666; margin-top: 0.3rem;}
    .metric-sub {font-size: 1rem; font-weight: 600; margin-top: 0.2rem;}
    .color-green {color: #2E7D32;}
    .color-red {color: #C62828;}
    .color-orange {color: #E65100;}
    .color-blue {color: #1565C0;}
    .footer-text {text-align: center; color: #9E9E9E; font-size: 0.8rem; padding: 1rem; border-top: 1px solid #EEEEEE; margin-top: 2rem;}
    div[data-testid="stDownloadButton"] button {width: 100%; border-radius: 8px; font-weight: 600; padding: 0.6rem;}
</style>
""", unsafe_allow_html=True)

DICTIONARY_PATH = "config/diagnosis_dictionary.yaml"
RULES_PATH      = "config/discrepancy_rules.csv"
OUTPUT_DIR      = "data/output-data"
FIGURE_DIR      = os.path.join(OUTPUT_DIR, "figures")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FIGURE_DIR, exist_ok=True)

def save_upload(f, suffix):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(f.read())
    tmp.close()
    return tmp.name

def cleanup(path):
    try:
        os.unlink(path)
    except:
        pass

st.markdown("""
<div class="app-header">
    <h1>CHC-QA Pipeline</h1>
    <p>Cytology-Histology Correlation Quality Assurance | CAP CYP.06600 | Automated Laboratory Platform</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Pipeline Settings")
    mode = st.radio("Input mode", ["Real lab data (two sheets)", "Evaluation data (pre-paired)"])
    st.markdown("---")
    window_days = st.slider("Pairing date window (days)", 30, 365, 180, 30)
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
**CHC-QA Pipeline** automates cytology-histology
correlation per CAP accreditation requirements.

**Key features:**
- LIS-agnostic data ingestion
- LLM-assisted normalization
- CAP-aligned classification
- Birdsong guideline metrics
- Professional report generation

**CAP Requirement:** CYP.06600
    """)
    st.markdown("---")
    st.markdown("[GitHub](https://github.com/solomoneluanu/chc-qa-pipeline)")

if "Real lab" in mode:
    st.markdown('<div class="step-header">Step 1 - Upload Laboratory Data</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-card">
    Upload an Excel file with separate <b>Cytology</b> and <b>Histology</b> sheets,
    or upload two separate files. Column names are auto-detected from any LIS format
    including CoPath, Epic Beaker, Sunquest, and Cerner.
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Option A - Single Excel file**")
        st.caption("Recommended: One Excel with separate Cytology and Histology sheets")
        excel_file = st.file_uploader("Excel file", type=["xlsx","xls"], key="excel_upload", label_visibility="collapsed")
    with col2:
        st.markdown("**Option B - Two separate files**")
        st.caption("Upload cytology and histology as separate CSV or Excel files")
        cyto_file  = st.file_uploader("Cytology file",  type=["csv","xlsx","xls"], key="cyto_upload")
        histo_file = st.file_uploader("Histology file", type=["csv","xlsx","xls"], key="histo_upload")

    has_excel = excel_file is not None
    has_two   = cyto_file is not None and histo_file is not None
    can_run   = has_excel or has_two

    if can_run:
        for key in ["results", "classified_df", "output_excel", "output_pdf", "unmatched_df"]:
            if key in st.session_state:
                del st.session_state[key]

        st.markdown('<div class="success-card">Files uploaded successfully. Auto-detecting columns...</div>', unsafe_allow_html=True)

        tmp_path = tmp_c = tmp_h = None
        try:
            if has_excel:
                tmp_path = save_upload(excel_file, ".xlsx")
                xl = pd.ExcelFile(tmp_path)
                if len(xl.sheet_names) < 2:
                    st.markdown("""
                    <div class="error-card">
                    This file only has one sheet. Real lab mode requires separate
                    Cytology and Histology sheets. Use Evaluation mode for pre-paired data.
                    </div>""", unsafe_allow_html=True)
                    cleanup(tmp_path)
                    st.stop()
                cyto_df, histo_df = load_combined_excel(tmp_path)
            else:
                tmp_c = save_upload(cyto_file,  ".csv" if cyto_file.name.endswith(".csv") else ".xlsx")
                tmp_h = save_upload(histo_file, ".csv" if histo_file.name.endswith(".csv") else ".xlsx")
                cyto_df,  _, _ = load_cyto_sheet(tmp_c)
                histo_df, _, _ = load_histo_sheet(tmp_h)

            if cyto_df is not None and histo_df is not None:
                st.markdown('<div class="step-header">Step 2 - Review Detected Data</div>', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Cytology Sheet** ({len(cyto_df)} cases)")
                    st.dataframe(cyto_df.head(5), use_container_width=True, hide_index=True)
                    found = [c for c in ["MRN","accession","date","raw_diag","adequacy"] if c in cyto_df.columns]
                    st.caption(f"Detected: {', '.join(found)}")
                with c2:
                    st.markdown(f"**Histology Sheet** ({len(histo_df)} cases)")
                    st.dataframe(histo_df.head(5), use_container_width=True, hide_index=True)
                    found = [c for c in ["MRN","accession","date","raw_diag","procedure"] if c in histo_df.columns]
                    st.caption(f"Detected: {', '.join(found)}")
                st.session_state["cyto_df"]  = cyto_df
                st.session_state["histo_df"] = histo_df

        except Exception as e:
            st.error(f"Error loading files: {str(e)}")
        finally:
            for p in [tmp_path, tmp_c, tmp_h]:
                if p: cleanup(p)

else:
    st.markdown('<div class="step-header">Step 1 - Upload Evaluation Data</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-card">
    Upload a pre-paired Excel or CSV file with <b>Cytology_Diagnosis</b> and
    <b>Histology_Diagnosis</b> columns.
    </div>""", unsafe_allow_html=True)

    eval_file = st.file_uploader("Paired data file", type=["xlsx","xls","csv"], key="eval_upload", label_visibility="collapsed")

    if eval_file is not None:
        try:
            df = pd.read_csv(eval_file) if eval_file.name.endswith(".csv") else pd.read_excel(eval_file)
            st.markdown(f'<div class="success-card">Loaded {len(df)} cases successfully.</div>', unsafe_allow_html=True)
            st.dataframe(df.head(5), use_container_width=True, hide_index=True)
            st.session_state["eval_df"] = df
        except Exception as e:
            st.error(f"Error: {str(e)}")

st.markdown("---")
st.markdown('<div class="step-header">Step 3 - Run Pipeline</div>', unsafe_allow_html=True)

run_ready = (
    ("Real lab" in mode and "cyto_df" in st.session_state and "histo_df" in st.session_state) or
    ("Evaluation" in mode and "eval_df" in st.session_state)
)

if not run_ready:
    st.markdown('<div class="warning-card">Please upload your data files above before running the pipeline.</div>', unsafe_allow_html=True)

if run_ready:
    if st.button("Run CHC-QA Pipeline", type="primary", use_container_width=True):
        progress = st.progress(0)
        status   = st.empty()

        try:
            if "Real lab" in mode:
                cyto_df  = st.session_state["cyto_df"]
                histo_df = st.session_state["histo_df"]

                status.info("Step 1/6: Normalizing cytology diagnoses via LLM...")
                progress.progress(10)
                cyto_df = normalize_cyto_sheet(cyto_df, raw_diag_col="raw_diag", dictionary_path=DICTIONARY_PATH)

                status.info("Step 2/6: Normalizing histology diagnoses via LLM...")
                progress.progress(25)
                histo_df = normalize_histo_sheet(histo_df, raw_diag_col="raw_diag", dictionary_path=DICTIONARY_PATH)

                status.info("Step 3/6: Pairing cases by MRN and date...")
                progress.progress(40)
                paired_df, unmatched_df = pair_cases(cyto_df, histo_df, window_days=window_days)

                if len(paired_df) == 0:
                    st.error("No cases were paired. Check your MRN and date columns.")
                    st.stop()

                unmatched_df.to_excel(os.path.join(OUTPUT_DIR, "unmatched_cases.xlsx"), index=False)
                df = paired_df.copy()

            else:
                df = st.session_state["eval_df"]

            status.info("Step 4/6: Applying dictionary normalization...")
            progress.progress(55)
            df = normalize_diagnoses(df, DICTIONARY_PATH)

            status.info("Step 5/6: Classifying CHC pairs...")
            progress.progress(70)
            classified_df = classify_pairs(df, RULES_PATH)

            status.info("Step 6/6: Computing metrics and generating reports...")
            progress.progress(85)
            results = compute_metrics(classified_df)

            output_excel = os.path.join(OUTPUT_DIR, "chc_report.xlsx")
            output_pdf   = os.path.join(OUTPUT_DIR, "chc_report.pdf")

            export_results(classified_df, results, output_excel)
            generate_all_figures(results, classified_df, FIGURE_DIR)

            # Generate LLM insights
            status.info("Generating AI clinical commentary (this may take 2-3 minutes)...")
            try:
               insights = generate_qa_insights(results, classified_df)
            except Exception:
               insights = None

            build_pdf_report(
                results=results,
                figure_dir=FIGURE_DIR,
                output_pdf=output_pdf,
                summary_text=f"A total of {results.get('total_cases')} cases were analyzed.",
                insights=insights
            )

            progress.progress(100)
            status.empty()

            st.session_state["results"]       = results
            st.session_state["classified_df"] = classified_df
            st.session_state["output_excel"]  = output_excel
            st.session_state["output_pdf"]    = output_pdf
            if "Real lab" in mode:
                st.session_state["unmatched_df"] = unmatched_df

            st.markdown('<div class="success-card">Pipeline completed successfully. Download your reports below.</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Pipeline error: {str(e)}")
            st.exception(e)

if "results" in st.session_state:

    results       = st.session_state["results"]
    classified_df = st.session_state["classified_df"]

    total      = results.get("total_cases", 1)
    concordant = results.get("concordance_counts", {}).get("concordant", 0)
    major      = results.get("concordance_counts", {}).get("major_discordant", 0)
    minor      = results.get("concordance_counts", {}).get("minor_discordant", 0)
    major_rate = round(major / total * 100, 1) if total > 0 else 0
    conc_rate  = round(concordant / total * 100, 1) if total > 0 else 0
    minor_rate = round(minor / total * 100, 1) if total > 0 else 0
    hsil_pv    = results.get("hsil_pv_plus", 0) or 0
    major_fn   = results.get("major_fn_count", 0)
    within_one = results.get("agreement_within_one_pct", 0)
    ext_pv     = results.get("extended_pv_plus", 0) or 0
    pv_flag    = results.get("hsil_pv_interpretation", "")

    st.markdown("---")
    st.markdown('<div class="step-header">QA Results</div>', unsafe_allow_html=True)

    if major_rate > 10:
        st.markdown(f"""
        <div class="error-card">
        CAP Alert: Major discordance rate of {major_rate}% exceeds the CAP
        benchmark of less than 10%. Corrective action required per CYP.06600.
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="success-card">
        CAP Status: Major discordance rate of {major_rate}% is within the
        CAP benchmark of less than 10%.
        </div>""", unsafe_allow_html=True)

    if hsil_pv > 0 and hsil_pv < 60:
        st.markdown(f"""
        <div class="error-card">
        PV+ Alert: HSIL positive predictive value of {hsil_pv:.1f}%
        is below the CAP target of 60%.
        </div>""", unsafe_allow_html=True)
    elif hsil_pv > 95:
        st.markdown(f"""
        <div class="warning-card">
        PV+ Flag: HSIL PV+ of {hsil_pv:.1f}% is unusually high.
        Per Birdsong, this may indicate an excessive cytology undercall rate.
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value color-blue">{total}</div>
            <div class="metric-label">Total Cases</div>
        </div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value color-green">{concordant}</div>
            <div class="metric-sub color-green">{conc_rate}%</div>
            <div class="metric-label">Concordant</div>
        </div>""", unsafe_allow_html=True)
    with m3:
        color = "color-red" if major_rate > 10 else "color-orange"
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value {color}">{major}</div>
            <div class="metric-sub {color}">{major_rate}%</div>
            <div class="metric-label">Major Discordant</div>
        </div>""", unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value color-orange">{minor}</div>
            <div class="metric-sub color-orange">{minor_rate}%</div>
            <div class="metric-label">Minor Discordant</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    b1, b2, b3, b4 = st.columns(4)
    with b1:
        pv_color = "color-red" if hsil_pv < 60 else "color-green"
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value {pv_color}">{hsil_pv:.1f}%</div>
            <div class="metric-sub" style="color:#64748B;">Target: 60%</div>
            <div class="metric-label">HSIL PV+</div>
        </div>""", unsafe_allow_html=True)
    with b2:
        ext_color = "color-red" if ext_pv < 60 else "color-green"
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value {ext_color}">{ext_pv:.1f}%</div>
            <div class="metric-sub" style="color:#64748B;">HSIL+ASC-H+AGC-NEO</div>
            <div class="metric-label">Extended PV+</div>
        </div>""", unsafe_allow_html=True)
    with b3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value color-blue">{within_one:.1f}%</div>
            <div class="metric-sub" style="color:#64748B;">Concordant + Minor</div>
            <div class="metric-label">Within One Grade</div>
        </div>""", unsafe_allow_html=True)
    with b4:
        fn_color = "color-red" if major_fn > 0 else "color-green"
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value {fn_color}">{int(major_fn)}</div>
            <div class="metric-sub" style="color:#64748B;">Must review all</div>
            <div class="metric-label">Major False Negatives</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    if pv_flag:
        st.info(f"PV+ Interpretation: {pv_flag}")

    intergrade = results.get("intergrade_table")
    if intergrade is not None and len(intergrade) > 0:
        st.markdown("---")
        st.markdown('<div class="step-header">Intergrade Follow-Up Rates (Birdsong Section 8)</div>', unsafe_allow_html=True)
        st.caption("HSIL+ histology rates following each cytology category. Elevated rates may indicate systematic undercalling.")
        st.dataframe(intergrade, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown('<div class="step-header">Case Detail</div>', unsafe_allow_html=True)

    display_cols = [c for c in [
        "case_id", "MRN", "cyto_raw_diag", "histo_raw_diag",
        "Cytology_Canonical", "Histology_Canonical",
        "Concordance_Class", "Discordance_Subtype", "Severity"
    ] if c in classified_df.columns]

    st.dataframe(classified_df[display_cols], use_container_width=True, height=400, hide_index=True)

    if "unmatched_df" in st.session_state and len(st.session_state["unmatched_df"]) > 0:
        n = len(st.session_state["unmatched_df"])
        with st.expander(f"Unmatched Cases ({n}) - No histology pair found within {window_days} days"):
            st.dataframe(st.session_state["unmatched_df"], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown('<div class="step-header">Download Reports</div>', unsafe_allow_html=True)
    st.markdown("Reports are ready for laboratory meeting presentation and CAP inspection filing.")
    st.markdown("")

    d1, d2 = st.columns(2)
    with d1:
        excel_path = st.session_state.get("output_excel", "")
        if os.path.exists(excel_path):
            with open(excel_path, "rb") as f:
                st.download_button(
                    label="Download Excel QA Report",
                    data=f.read(),
                    file_name="chc_qa_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary",
                    key="dl_excel_main"
                )
            st.caption("Color-coded case detail with all Birdsong metrics")

    with d2:
        pdf_path = st.session_state.get("output_pdf", "")
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="Download PDF QA Report",
                    data=f.read(),
                    file_name="chc_qa_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="dl_pdf_main"
                )
            st.caption("Full report with Birdsong metrics, intergrade analysis and CAP signals")

    st.markdown("---")
    st.markdown('<div class="step-header">Visualizations</div>', unsafe_allow_html=True)

    fig_files = [
        ("concordance_bar.png",     "Concordance Distribution"),
        ("discrepancy_buckets.png", "Discrepancy Buckets"),
        ("hsil_metrics.png",        "HSIL Correlation Metrics"),
        ("confusion_matrix.png",    "Confusion Matrix"),
    ]

    v1, v2 = st.columns(2)
    for i, (fname, title) in enumerate(fig_files):
        fpath = os.path.join(FIGURE_DIR, fname)
        if os.path.exists(fpath):
            with (v1 if i % 2 == 0 else v2):
                st.markdown(f"**{title}**")
                st.image(fpath, use_container_width=True)

    st.markdown("""
    <div class="footer-text">
    CHC-QA Pipeline | Per ASC Birdsong Guideline 2017 | CAP CYP.06600 |
    github.com/solomoneluanu/chc-qa-pipeline
    </div>""", unsafe_allow_html=True)
