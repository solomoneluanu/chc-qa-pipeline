import streamlit as st
import pandas as pd
import os
import sys
import tempfile
from pathlib import Path

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

st.set_page_config(
    page_title="CHC-QA Pipeline",
    page_icon="🔬",
    layout="wide"
)

DICTIONARY_PATH = "config/diagnosis_dictionary.yaml"
RULES_PATH      = "config/discrepancy_rules.csv"
OUTPUT_DIR      = "data/output-data"
FIGURE_DIR      = os.path.join(OUTPUT_DIR, "figures")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FIGURE_DIR, exist_ok=True)

st.title("🔬 CHC-QA Pipeline")
st.markdown("**Cytology-Histology Correlation Quality Assurance**")
st.markdown("---")

with st.sidebar:
    st.header("Settings")
    mode = st.radio(
        "Input mode",
        ["Real lab data (two sheets)", "Evaluation data (pre-paired)"],
    )
    window_days = st.slider(
        "Pairing date window (days)",
        min_value=30, max_value=365, value=180, step=30
    )
    st.markdown("---")
    st.markdown("**About**")
    st.markdown("Automated CHC-QA pipeline with LLM normalization and deterministic CAP-aligned classification.")
    st.markdown("[GitHub](https://github.com/solomoneluanu/chc-qa-pipeline)")


def save_upload(uploaded_file, suffix):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded_file.read())
    tmp.close()
    return tmp.name


def cleanup(path):
    try:
        os.unlink(path)
    except Exception:
        pass


if "Real lab" in mode:

    st.header("Upload Laboratory Data")
    st.info("Upload an Excel file with separate Cytology and Histology sheets, or upload two separate CSV/Excel files.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Option A - Single Excel file")
        excel_file = st.file_uploader(
            "Upload Excel with Cytology and Histology sheets",
            type=["xlsx", "xls"],
            key="excel_upload"
        )

    with col2:
        st.subheader("Option B - Two separate files")
        cyto_file  = st.file_uploader("Upload Cytology CSV or Excel",  type=["csv","xlsx","xls"], key="cyto_upload")
        histo_file = st.file_uploader("Upload Histology CSV or Excel", type=["csv","xlsx","xls"], key="histo_upload")

    has_excel = excel_file is not None
    has_two   = cyto_file is not None and histo_file is not None
    can_run   = has_excel or has_two

    if can_run:
        st.success("Files uploaded successfully")
        st.markdown("---")
        st.header("Column Mapping")
        st.info("Auto-detecting columns from your files.")

        tmp_path  = None
        tmp_c     = None
        tmp_h     = None

        try:
            if has_excel:
                tmp_path = save_upload(excel_file, ".xlsx")
                cyto_df, histo_df = load_combined_excel(tmp_path)

            else:
                suffix_c = ".csv" if cyto_file.name.endswith(".csv") else ".xlsx"
                suffix_h = ".csv" if histo_file.name.endswith(".csv") else ".xlsx"

                tmp_c = save_upload(cyto_file,  suffix_c)
                tmp_h = save_upload(histo_file, suffix_h)

                cyto_df,  _, _ = load_cyto_sheet(tmp_c)
                histo_df, _, _ = load_histo_sheet(tmp_h)

            if cyto_df is not None and histo_df is not None:
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Cytology sheet")
                    st.dataframe(cyto_df.head(5), use_container_width=True)
                    st.caption(f"{len(cyto_df)} rows")

                with col2:
                    st.subheader("Histology sheet")
                    st.dataframe(histo_df.head(5), use_container_width=True)
                    st.caption(f"{len(histo_df)} rows")

                st.session_state["cyto_df"]  = cyto_df
                st.session_state["histo_df"] = histo_df

        except Exception as e:
            st.error(f"Error loading files: {str(e)}")

        finally:
            if tmp_path: cleanup(tmp_path)
            if tmp_c:    cleanup(tmp_c)
            if tmp_h:    cleanup(tmp_h)

else:
    st.header("Upload Evaluation Data")
    st.info("Upload a pre-paired Excel file with Cytology_Diagnosis and Histology_Diagnosis columns.")

    eval_file = st.file_uploader(
        "Upload paired Excel or CSV file",
        type=["xlsx","xls","csv"],
        key="eval_upload"
    )

    if eval_file is not None:
        try:
            if eval_file.name.endswith(".csv"):
                df = pd.read_csv(eval_file)
            else:
                df = pd.read_excel(eval_file)

            st.success(f"Loaded {len(df)} cases")
            st.dataframe(df.head(5), use_container_width=True)
            st.session_state["eval_df"] = df

        except Exception as e:
            st.error(f"Error loading file: {str(e)}")

st.markdown("---")
st.header("Run Pipeline")

run_ready = (
    ("Real lab" in mode and "cyto_df" in st.session_state and "histo_df" in st.session_state) or
    ("Evaluation" in mode and "eval_df" in st.session_state)
)

if not run_ready:
    st.warning("Please upload your data files above before running the pipeline.")

if run_ready:
    if st.button("Run CHC-QA Pipeline", type="primary", use_container_width=True):

        with st.spinner("Running pipeline..."):
            progress = st.progress(0)
            status   = st.empty()

            try:
                if "Real lab" in mode:
                    cyto_df  = st.session_state["cyto_df"]
                    histo_df = st.session_state["histo_df"]

                    status.text("Step 1/6: Normalizing cytology via LLM...")
                    progress.progress(10)
                    cyto_df = normalize_cyto_sheet(
                        cyto_df,
                        raw_diag_col="raw_diag",
                        dictionary_path=DICTIONARY_PATH
                    )

                    status.text("Step 2/6: Normalizing histology via LLM...")
                    progress.progress(25)
                    histo_df = normalize_histo_sheet(
                        histo_df,
                        raw_diag_col="raw_diag",
                        dictionary_path=DICTIONARY_PATH
                    )

                    status.text("Step 3/6: Pairing cases...")
                    progress.progress(40)
                    paired_df, unmatched_df = pair_cases(
                        cyto_df, histo_df, window_days=window_days
                    )

                    if len(paired_df) == 0:
                        st.error("No cases were paired. Check MRN and date columns.")
                        st.stop()

                    unmatched_path = os.path.join(OUTPUT_DIR, "unmatched_cases.xlsx")
                    unmatched_df.to_excel(unmatched_path, index=False)
                    df = paired_df.copy()

                else:
                    df = st.session_state["eval_df"]

                status.text("Step 4/6: Dictionary normalization...")
                progress.progress(55)
                df = normalize_diagnoses(df, DICTIONARY_PATH)

                status.text("Step 5/6: Classifying CHC pairs...")
                progress.progress(70)
                classified_df = classify_pairs(df, RULES_PATH)

                status.text("Step 6/6: Computing metrics and generating reports...")
                progress.progress(85)
                results = compute_metrics(classified_df)

                output_excel = os.path.join(OUTPUT_DIR, "chc_report.xlsx")
                output_pdf   = os.path.join(OUTPUT_DIR, "chc_report.pdf")

                export_results(classified_df, results, output_excel)
                generate_all_figures(results, classified_df, FIGURE_DIR)

                summary_text = (
                    f"A total of {results.get('total_cases')} cases were analyzed using a "
                    f"deterministic cytology-histology correlation QA pipeline."
                )
                build_pdf_report(
                    results=results,
                    figure_dir=FIGURE_DIR,
                    output_pdf=output_pdf,
                    summary_text=summary_text
                )

                progress.progress(100)
                status.text("Pipeline completed successfully.")

                st.session_state["results"]       = results
                st.session_state["classified_df"] = classified_df
                st.session_state["output_excel"]  = output_excel
                st.session_state["output_pdf"]    = output_pdf

                if "Real lab" in mode:
                    st.session_state["unmatched_df"] = unmatched_df

            except Exception as e:
                st.error(f"Pipeline error: {str(e)}")
                st.exception(e)

if "results" in st.session_state:

    results       = st.session_state["results"]
    classified_df = st.session_state["classified_df"]

    st.markdown("---")
    st.header("QA Results")

    total      = results.get("total_cases", 1)
    concordant = results.get("concordant_count", 0)
    major      = results.get("major_discordant_count", 0)
    minor      = results.get("minor_discordant_count", 0)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Cases", total)
    with col2:
        st.metric("Concordant", f"{concordant} ({concordant/total*100:.1f}%)")
    with col3:
        st.metric("Major Discordant", f"{major} ({major/total*100:.1f}%)",
                  delta=f"{major/total*100:.1f}%", delta_color="inverse")
    with col4:
        st.metric("Minor Discordant", f"{minor} ({minor/total*100:.1f}%)")

    st.subheader("Case Detail")
    display_cols = [c for c in [
        "case_id", "MRN", "cyto_raw_diag", "histo_raw_diag",
        "Cytology_Canonical", "Histology_Canonical",
        "Concordance_Class", "Discordance_Subtype", "Severity"
    ] if c in classified_df.columns]

    st.dataframe(classified_df[display_cols], use_container_width=True, height=400)

    if "unmatched_df" in st.session_state and len(st.session_state["unmatched_df"]) > 0:
        with st.expander(f"{len(st.session_state['unmatched_df'])} Unmatched Cytology Cases"):
            st.dataframe(st.session_state["unmatched_df"], use_container_width=True)

    st.markdown("---")
    st.header("Download Reports")

    col1, col2 = st.columns(2)

    with col1:
        excel_path = st.session_state.get("output_excel", "")
        if os.path.exists(excel_path):
            with open(excel_path, "rb") as f:
                st.download_button(
                    label="Download Excel Report",
                    data=f.read(),
                    file_name="chc_qa_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

    with col2:
        pdf_path = st.session_state.get("output_pdf", "")
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="Download PDF Report",
                    data=f.read(),
                    file_name="chc_qa_report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

    st.markdown("---")
    st.header("Visualizations")

    fig_files = [
        ("concordance_bar.png",    "Concordance Distribution"),
        ("discrepancy_buckets.png","Discrepancy Buckets"),
        ("hsil_metrics.png",       "HSIL Metrics"),
        ("confusion_matrix.png",   "Confusion Matrix"),
    ]

    col1, col2 = st.columns(2)
    for i, (fname, title) in enumerate(fig_files):
        fpath = os.path.join(FIGURE_DIR, fname)
        if os.path.exists(fpath):
            with (col1 if i % 2 == 0 else col2):
                st.subheader(title)
                st.image(fpath, use_container_width=True)
