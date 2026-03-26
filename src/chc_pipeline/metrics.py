import pandas as pd


def compute_metrics(df: pd.DataFrame) -> dict:
    """
    Compute core CHC QA metrics from classified pairs.
    """
    results = {}

    total_cases = len(df)
    results["total_cases"] = total_cases

    # Concordance class
    concordance_counts = df["Concordance_Class"].value_counts(dropna=False).to_dict()
    results["concordance_counts"] = concordance_counts

    concordance_percentages = (
        df["Concordance_Class"].value_counts(normalize=True, dropna=False) * 100
    ).round(2).to_dict()
    results["concordance_percentages"] = concordance_percentages

    # Subtype
    subtype_counts = df["Discordance_Subtype"].value_counts(dropna=False).to_dict()
    results["subtype_counts"] = subtype_counts

    subtype_percentages = (
        df["Discordance_Subtype"].value_counts(normalize=True, dropna=False) * 100
    ).round(2).to_dict()
    results["subtype_percentages"] = subtype_percentages

    # Direction
    direction_counts = df["Direction"].value_counts(dropna=False).to_dict()
    results["direction_counts"] = direction_counts

    direction_percentages = (
        df["Direction"].value_counts(normalize=True, dropna=False) * 100
    ).round(2).to_dict()
    results["direction_percentages"] = direction_percentages

    # Severity
    severity_counts = df["Severity"].value_counts(dropna=False).to_dict()
    results["severity_counts"] = severity_counts

    severity_percentages = (
        df["Severity"].value_counts(normalize=True, dropna=False) * 100
    ).round(2).to_dict()
    results["severity_percentages"] = severity_percentages

    # Tables
    results["concordance_table"] = (
        df["Concordance_Class"]
        .value_counts(dropna=False)
        .rename_axis("Concordance_Class")
        .reset_index(name="Count")
    )
    results["concordance_table"]["Percent"] = (
        results["concordance_table"]["Count"] / total_cases * 100
    ).round(2)

    results["subtype_table"] = (
        df["Discordance_Subtype"]
        .value_counts(dropna=False)
        .rename_axis("Discordance_Subtype")
        .reset_index(name="Count")
    )
    results["subtype_table"]["Percent"] = (
        results["subtype_table"]["Count"] / total_cases * 100
    ).round(2)

    results["direction_table"] = (
        df["Direction"]
        .value_counts(dropna=False)
        .rename_axis("Direction")
        .reset_index(name="Count")
    )
    results["direction_table"]["Percent"] = (
        results["direction_table"]["Count"] / total_cases * 100
    ).round(2)

    results["severity_table"] = (
        df["Severity"]
        .value_counts(dropna=False)
        .rename_axis("Severity")
        .reset_index(name="Count")
    )
    results["severity_table"]["Percent"] = (
        results["severity_table"]["Count"] / total_cases * 100
    ).round(2)

    # Confusion matrix
    confusion_matrix = pd.crosstab(
        df["Cytology_Canonical"],
        df["Histology_Canonical"],
        dropna=False
    )
    results["confusion_matrix"] = confusion_matrix

    # HSIL PV+
    hsil_cytology_cases = df[
        df["Cytology_Canonical"].isin(["HSIL", "ASC-H", "AGC-NEO"])
    ].copy()

    hsil_followup_total = len(hsil_cytology_cases)

    hsil_positive_followup = len(
        hsil_cytology_cases[
            hsil_cytology_cases["Histology_Canonical"].isin(["HSIL (CIN2)", "HSIL (CIN3)"])
        ]
    )

    if hsil_followup_total > 0:
        hsil_pv_plus = round((hsil_positive_followup / hsil_followup_total) * 100, 2)
    else:
        hsil_pv_plus = None

    results["hsil_pv_plus"] = hsil_pv_plus
    results["hsil_followup_total"] = hsil_followup_total
    results["hsil_positive_followup"] = hsil_positive_followup

    # HSIL PV+ table
    results["hsil_pv_table"] = pd.DataFrame({
        "Metric": [
            "HSIL+ Cytology Cases with Histology Follow-up",
            "HSIL+ Cytology Cases with HSIL (CIN2/CIN3) Histology",
            "PV+ of HSIL Cytology (%)"
        ],
        "Value": [
            hsil_followup_total,
            hsil_positive_followup,
            hsil_pv_plus
        ]
    })

    return results
