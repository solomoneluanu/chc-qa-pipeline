import yaml
import pandas as pd


def load_dictionary(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def normalize_diagnoses(df: pd.DataFrame, dictionary_path: str) -> pd.DataFrame:
    """
    Normalize raw LIS diagnoses into canonical labels using dictionary.
    Auto-detects cytology and histology diagnosis columns.
    """
    mapping = load_dictionary(dictionary_path)
    df = df.copy()

    # Auto-detect cytology diagnosis column
    cyto_col = None
    cyto_candidates = [
        "Cytology_Diagnosis", "cytology_diagnosis",
        "Cytology_Canonical", "cytology_canonical",
        "CYTOLOGY_DIAGNOSIS", "cyto_diagnosis",
        "Cytology_canonical"
    ]
    for candidate in cyto_candidates:
        if candidate in df.columns:
            cyto_col = candidate
            break

    # Auto-detect histology diagnosis column
    histo_col = None
    histo_candidates = [
        "Histology_Diagnosis", "histology_diagnosis",
        "Histology_Canonical", "histology_canonical",
        "HISTOLOGY_DIAGNOSIS", "histo_diagnosis",
        "Histology_canonical"
    ]
    for candidate in histo_candidates:
        if candidate in df.columns:
            histo_col = candidate
            break

    if cyto_col is None:
        raise ValueError(
            f"Could not find cytology diagnosis column. "
            f"Available columns: {list(df.columns)}"
        )
    if histo_col is None:
        raise ValueError(
            f"Could not find histology diagnosis column. "
            f"Available columns: {list(df.columns)}"
        )

    # Standardize to expected column names
    if cyto_col != "Cytology_Diagnosis":
        df["Cytology_Diagnosis"] = df[cyto_col].astype(str).str.strip()
    else:
        df["Cytology_Diagnosis"] = df["Cytology_Diagnosis"].astype(str).str.strip()

    if histo_col != "Histology_Diagnosis":
        df["Histology_Diagnosis"] = df[histo_col].astype(str).str.strip()
    else:
        df["Histology_Diagnosis"] = df["Histology_Diagnosis"].astype(str).str.strip()

    # Map to canonical terms
    df["Cytology_Canonical"] = df["Cytology_Diagnosis"].map(
        mapping["cytology_raw_to_canonical"]
    )
    df["Histology_Canonical"] = df["Histology_Diagnosis"].map(
        mapping["histology_raw_to_canonical"]
    )

    df["Cytology_Unmapped"]  = df["Cytology_Canonical"].isna()
    df["Histology_Unmapped"] = df["Histology_Canonical"].isna()

    print(f"  Normalized using: {cyto_col} and {histo_col}")
    print(f"  Cyto unmapped:  {df['Cytology_Unmapped'].sum()}")
    print(f"  Histo unmapped: {df['Histology_Unmapped'].sum()}")

    return df
