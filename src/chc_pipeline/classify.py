import pandas as pd


def load_rules(rules_path: str) -> pd.DataFrame:
    """
    Load discrepancy rules from CSV.
    """
    rules = pd.read_csv(rules_path)
    return rules


def classify_pairs(df: pd.DataFrame, rules_path: str) -> pd.DataFrame:
    """
    Classify cytology-histology pairs using canonical diagnoses and a rule table.
    """
    rules = load_rules(rules_path)

    df = df.copy()

    df = df.merge(
        rules,
        how="left",
        left_on=["Cytology_Canonical", "Histology_Canonical"],
        right_on=["Cytology_Diagnosis", "Histology_Diagnosis"]
    )

    df["Subtype_Flag"] = (
        df["Cytology_Canonical"].fillna("UNMAPPED")
        + "→"
        + df["Histology_Canonical"].fillna("UNMAPPED")
    )

    df["Rule_Matched"] = df["Concordance_Class"].notna()

    df["Concordance_Class"] = df["Concordance_Class"].fillna("unmapped")
    df["Discordance_Subtype"] = df["Discordance_Subtype"].fillna("unmapped")
    df["Direction"] = df["Direction"].fillna("unknown")
    df["Severity"] = df["Severity"].fillna("unknown")

    return df
