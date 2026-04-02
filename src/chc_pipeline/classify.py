import pandas as pd


def load_rules(rules_path: str) -> pd.DataFrame:
    return pd.read_csv(rules_path)


def classify_pairs(df: pd.DataFrame, rules_path: str) -> pd.DataFrame:
    rules = load_rules(rules_path)
    df = df.copy()

    df = df.merge(
        rules,
        how="left",
        left_on=["Cytology_Canonical", "Histology_Canonical"],
        right_on=["Cytology_Diagnosis", "Histology_Diagnosis"],
        suffixes=("", "_rule")
    )

    # remove duplicate rule key columns after merge
    df.drop(columns=["Cytology_Diagnosis_rule", "Histology_Diagnosis_rule"], inplace=True, errors="ignore")

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
