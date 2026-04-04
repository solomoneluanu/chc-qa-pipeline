import sys
import os
import pandas as pd
import argparse  

sys.path.append(os.getcwd())

from src.chc_pipeline.normalize import normalize_diagnoses
from src.chc_pipeline.classify import classify_pairs
from src.chc_pipeline.metrics import compute_metrics
from src.chc_pipeline.export import export_results
from src.chc_pipeline.visualize import generate_all_figures
from src.chc_pipeline.pdf_report import build_pdf_report


def main():
    parser = argparse.ArgumentParser(description="Run CHC-QA pipeline")
    parser.add_argument(
        "--input",
        default="data/input-data/Evalution04.xlsx",
        help="Path to input Excel file"
    )
    args = parser.parse_args()

    input_file = args.input  

    dictionary_file = "config/diagnosis_dictionary.yaml"
    rules_file = "config/discrepancy_rules.csv"

    output_excel = "data/output-data/chc_report.xlsx"
    output_pdf = "data/output-data/chc_report.pdf"
    figure_dir = "data/output-data/figures"

    os.makedirs("data/output", exist_ok=True)
    os.makedirs(figure_dir, exist_ok=True)

    # Step 1: Load data
    df = pd.read_excel(input_file)

    required_columns = ["Cytology_Diagnosis", "Histology_Diagnosis"]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Step 2: Normalize
    df = normalize_diagnoses(df, dictionary_file)

    # Step 3: Classify
    classified_df = classify_pairs(df, rules_file)

    # Step 4: Metrics
    results = compute_metrics(classified_df)

    # Step 5: Export Excel
    export_results(classified_df, results, output_excel)

    # Step 6: Visualization
    generate_all_figures(results, classified_df, figure_dir)

    # Step 7: PDF Report
    summary_text = (
        f"A total of {results.get('total_cases')} cases were analyzed using a "
        f"deterministic cytology-histology correlation QA pipeline."
    )

    build_pdf_report(
        results=results,
        figure_dir=figure_dir,
        output_pdf=output_pdf,
        summary_text=summary_text
    )

    print("Pipeline completed successfully.")
    print(f"Excel report: {output_excel}")
    print(f"PDF report: {output_pdf}")


if __name__ == "__main__":
    main()
