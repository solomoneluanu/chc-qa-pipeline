import pandas as pd
from pathlib import Path


CYTO_COLUMN_ALIASES = {
    "MRN":        ["mrn", "patient_id", "pat_id", "medical_record_number", "patient number"],
   "accession":   ["accession", "acc_no", "accession_no", "accession_number",
                "spec_no", "cyto_no", "lab_no", "case_no",
                "cytology_accession_number", "cytology accession number",
                "cytology_accession_no", "cytology accession no"],
    "date":       ["date", "collection_date", "cyto_date", "specimen_date",
                   "proc_date", "report_date", "exam_date"],
    "raw_diag":   ["diagnosis", "final_dx", "cyto_dx", "final_diagnosis",
                   "pap_result", "result", "cytologic_diagnosis", "cyto_diag",
                   "cytology_diagnosis", "cytology diagnosis", "pap result"],
    "adequacy":   ["adequacy", "specimen_adequacy", "cyto_adequacy", "adequate"],
    "report_text":["report_text", "cyto_text", "report", "narrative",
                   "comment", "rpt_txt", "report text"],
    "patient_name":["patient_name", "name", "pat_name", "patient", "full_name"]
}

HISTO_COLUMN_ALIASES = {
    "MRN":        ["mrn", "patient_id", "pat_id", "medical_record_number", "patient number", "pt_id", "pt id"],
    "accession":  ["accession", "acc_no", "accession_no", "accession_number", "spec_no", "sp_no", "surgical_no", "path_no", "biopsy_no", "histology_accession_number", "histology accession number", "surgical_path_no", "surgical path no"],
    "date":       ["date", "procedure_date", "histo_date", "specimen_date",
                   "biopsy_date", "proc_date", "report_date", "exam_date"],
    "raw_diag":   ["diagnosis", "final_dx", "histo_dx", "final_diagnosis",
                   "surgical_dx", "path_dx", "histologic_diagnosis", "histo_diag",
                   "histology_diagnosis", "histology diagnosis", "biopsy result"],
    "procedure":  ["procedure", "procedure_type", "specimen_type", "proc_desc",
                   "specimen_desc", "specimen", "biopsy_type"],
    "report_text":["report_text", "histo_text", "report", "narrative",
                   "comment", "rpt_txt", "report text"],
    "patient_name":["patient_name", "name", "pat_name", "patient", "full_name"]
}


def detect_columns(df: pd.DataFrame, aliases: dict, sheet_type: str) -> dict:
    """
    Auto-detect column mapping regardless of LIS naming convention.
    Returns mapping of standard_name -> actual_column_name.
    """
    col_lower = {c.lower().strip(): c for c in df.columns}
    detected = {}
    missing = []

    for standard_name, alias_list in aliases.items():
        found = False
        for alias in alias_list:
            if alias.lower() in col_lower:
                detected[standard_name] = col_lower[alias.lower()]
                found = True
                break
        if not found:
            missing.append(standard_name)

    print(f"\n-- {sheet_type.upper()} sheet column detection --")
    print(f"   Detected : {list(detected.keys())}")
    print(f"   Missing  : {missing}")
    print(f"   Raw cols : {list(df.columns)}")

    return detected, missing


def load_cyto_sheet(filepath: str, sheet_name=None) -> tuple:
    """
    Load cytology sheet from CSV or Excel.
    Returns (dataframe, column_mapping, missing_columns)
    """
    df = _load_file(filepath, sheet_name)
    col_map, missing = detect_columns(df, CYTO_COLUMN_ALIASES, "cytology")

    # Rename detected columns to standard names
    rename = {v: k for k, v in col_map.items()}
    df = df.rename(columns=rename)

    return df, col_map, missing


def load_histo_sheet(filepath: str, sheet_name=None) -> tuple:
    """
    Load histology sheet from CSV or Excel.
    Returns (dataframe, column_mapping, missing_columns)
    """
    df = _load_file(filepath, sheet_name)
    col_map, missing = detect_columns(df, HISTO_COLUMN_ALIASES, "histology")

    # Rename detected columns to standard names
    rename = {v: k for k, v in col_map.items()}
    df = df.rename(columns=rename)

    return df, col_map, missing


def load_combined_excel(filepath: str) -> tuple:
    """
    Load an Excel file with separate cyto and histo sheets.
    Auto-detects which sheet is which by sheet name keywords.
    Returns (cyto_df, histo_df)
    """
    xl = pd.ExcelFile(filepath)
    print(f"\nSheets found: {xl.sheet_names}")

    cyto_sheet  = None
    histo_sheet = None

    cyto_keywords  = ["cyto", "pap", "cervical", "cytology"]
    histo_keywords = ["histo", "biopsy", "surgical", "pathology", "histology"]

    for sheet in xl.sheet_names:
        sheet_lower = sheet.lower()
        if any(kw in sheet_lower for kw in cyto_keywords):
            cyto_sheet = sheet
        elif any(kw in sheet_lower for kw in histo_keywords):
            histo_sheet = sheet

    if cyto_sheet is None or histo_sheet is None:
        print(f"Could not auto-detect sheets.")
        print(f"Available sheets: {xl.sheet_names}")
        print(f"Please specify sheet names manually.")
        return None, None

    print(f"Cyto sheet  : {cyto_sheet}")
    print(f"Histo sheet : {histo_sheet}")

    cyto_df,  _, _ = load_cyto_sheet(filepath,  sheet_name=cyto_sheet)
    histo_df, _, _ = load_histo_sheet(filepath, sheet_name=histo_sheet)

    return cyto_df, histo_df


def _load_file(filepath: str, sheet_name=None) -> pd.DataFrame:
    """Load CSV or Excel file."""
    path = Path(filepath)

    if path.suffix in [".xlsx", ".xls"]:
        if sheet_name:
            df = pd.read_excel(filepath, sheet_name=sheet_name)
        else:
            df = pd.read_excel(filepath)
    elif path.suffix == ".csv":
        df = pd.read_csv(filepath)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

    print(f"\nLoaded {len(df)} rows from {path.name}")
    return df
