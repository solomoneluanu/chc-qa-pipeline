import os
import pandas as pd


def export_results(classified_df, results, output_path):
    """
    Export CHC results into a structured Excel workbook.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        classified_df.to_excel(writer, sheet_name="Classified_Cases", index=False)
        results["concordance_table"].to_excel(writer, sheet_name="Concordance_Summary", index=False)
        results["subtype_table"].to_excel(writer, sheet_name="Subtype_Summary", index=False)
        results["direction_table"].to_excel(writer, sheet_name="Direction_Summary", index=False)
        results["severity_table"].to_excel(writer, sheet_name="Severity_Summary", index=False)
        results["confusion_matrix"].to_excel(writer, sheet_name="Confusion_Matrix")
        results["hsil_pv_table"].to_excel(writer, sheet_name="HSIL_PV_Plus", index=False)
