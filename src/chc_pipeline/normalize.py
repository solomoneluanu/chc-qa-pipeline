import yaml
import pandas as pd


def load_dictionary(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def normalize_diagnoses(df: pd.DataFrame, dictionary_path: str) -> pd.DataFrame:
    """
    Normalize raw LIS diagnoses into canonical labels using dictionary.
    """
    mapping = load_dictionary(dictionary_path)

    df = df.copy()

    df["Cytology_Diagnosis"] = df["Cytology_Diagnosis"].astype(str).str.strip()
    df["Histology_Diagnosis"] = df["Histology_Diagnosis"].astype(str).str.strip()

    df["Cytology_Canonical"] = df["Cytology_Diagnosis"].map(
        mapping["cytology_raw_to_canonical"]
    )

    df["Histology_Canonical"] = df["Histology_Diagnosis"].map(
        mapping["histology_raw_to_canonical"]
    )

    df["Cytology_Unmapped"] = df["Cytology_Canonical"].isna()
    df["Histology_Unmapped"] = df["Histology_Canonical"].isna()

    return df
