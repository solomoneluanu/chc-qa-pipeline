import sys
import os
import pandas as pd
import argparse

sys.path.append(os.getcwd())

from src.chc_pipeline.ingest        import load_combined_excel
from src.chc_pipeline.llm_normalizer import normalize_cyto_sheet, normalize_histo_sheet
from src.chc_pipeline.pairer        import pair_cases
from src.chc_pipeline.normalize     import normalize_diagnoses
from src.chc_pipeline.classify      import classify_pairs
from src.chc_pipeline.metrics       import compute_metrics
from src.chc_pipeline.export        import export_results
from src.chc_pipeline.visualize     import generate_all_figures
from src.chc_pipeline.pdf_report    import build_pdf_report


def main():
    parser = argparse.ArgumentParser(description="Run CHC-QA pipeline")
    parser.add_argument("--input",  default="data/input-data/real_lab_simulation.xlsx")
    parser.add_argument("--mode",   choices=["real", "eval"], default="real")
    parser.add_argument("--window", type=int, default=180)
    args = parser.parse_args()

    dictionary_file = "config/diagnosis_dictionary.yaml"
    rules_file      = "config/discrepancy_rules.csv"
    output_excel    = "data/output-data/chc_report.xlsx"
    output_pdf      = "data/output-data/chc_report.pdf"
    figure_dir      = "data/output-data/figures"

    os.makedirs("data/output-data", exist_ok=True)
    os.makedirs(figure_dir,         exist_ok=True)

    print("\nCHC-QA PIPELINE")
    print(f"Input : {args.input}")
    print(f"Mode  : {args.mode}\n")

    if args.mode == "real":

        print("STEP 1: Ingesting sheets...")
        cyto_df, histo_df = load_combined_excel(args.input)

        if cyto_df is None or histo_df is None:
            raise ValueError("Could not load sheets.")

        print("\nSTEP 2: Normalizing cytology via LLM...")
        cyto_df = normalize_cyto_sheet(
            cyto_df,
            raw_diag_col="raw_diag",
            dictionary_path=dictionary_file
        )

        print("\nSTEP 2b: Normalizing histology via LLM...")
        histo_df = normalize_histo_sheet(
            histo_df,
            raw_diag_col="raw_diag",
            dictionary_path=dictionary_file
        )

        print(f"\nSTEP 3: Pairing cases (window={args.window} days)...")
        paired_df, unmatched_df = pair_cases(cyto_df, histo_df, window_days=args.window)

        if len(paired_df) == 0:
            raise ValueError("No cases paired.")

        unmatched_df.to_excel("data/output-data/unmatched_cases.xlsx", index=False)
        print(f"  Unmatched saved: data/output-data/unmatched_cases.xlsx")

        df = paired_df.copy()

    else:
        print("STEP 1-3: Loading pre-paired evaluation data...")
        df = pd.read_excel(args.input)
        required = ["Cytology_Diagnosis", "Histology_Diagnosis"]
        missing  = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")

    print("\nSTEP 5: Dictionary normalization...")
    df = normalize_diagnoses(df, dictionary_file)

    print("\nSTEP 6: Classifying...")
    classified_df = classify_pairs(df, rules_file)

    print("\nSTEP 7: Computing metrics...")
    results = compute_metrics(classified_df)

    print("\nSTEP 7b: Generating LLM clinical commentary...")
    from src.chc_pipeline.llm_insights import generate_qa_insights
    insights = generate_qa_insights(results, classified_df)
    print(f"  Commentary generated: {len(insights)} characters")

    print("\nSTEP 8: Exporting Excel...")
    export_results(classified_df, results, output_excel)

    print("\nSTEP 9: Generating figures...")
    generate_all_figures(results, classified_df, figure_dir)

    print("\nSTEP 10: Building PDF...")
    summary_text = (
        f"A total of {results.get('total_cases')} cases were analyzed using a "
        f"deterministic cytology-histology correlation QA pipeline."
    )
    build_pdf_report(
        results=results,
        figure_dir=figure_dir,
        output_pdf=output_pdf,
        summary_text=summary_text,
        insights=insights
    )

    print("\nPipeline completed successfully.")
    print(f"Excel : {output_excel}")
    print(f"PDF   : {output_pdf}")


if __name__ == "__main__":
    main()


