%%writefile src/chc_pipeline/metrics.py
import pandas as pd


def compute_metrics(df: pd.DataFrame) -> dict:
    """
    Compute core CHC QA metrics from classified pairs.
    """
    results = {}

    total_cases = len(df)
    results["total_cases"] = total_cases

    # -------------------------
    # Core class summaries
    # -------------------------
    concordance_counts = df["Concordance_Class"].value_counts(dropna=False).to_dict()
    results["concordance_counts"] = concordance_counts

    concordance_percentages = (
        df["Concordance_Class"].value_counts(normalize=True, dropna=False) * 100
    ).round(2).to_dict()
    results["concordance_percentages"] = concordance_percentages

    subtype_counts = df["Discordance_Subtype"].value_counts(dropna=False).to_dict()
    results["subtype_counts"] = subtype_counts

    subtype_percentages = (
        df["Discordance_Subtype"].value_counts(normalize=True, dropna=False) * 100
    ).round(2).to_dict()
    results["subtype_percentages"] = subtype_percentages

    direction_counts = df["Direction"].value_counts(dropna=False).to_dict()
    results["direction_counts"] = direction_counts

    direction_percentages = (
        df["Direction"].value_counts(normalize=True, dropna=False) * 100
    ).round(2).to_dict()
    results["direction_percentages"] = direction_percentages

    severity_counts = df["Severity"].value_counts(dropna=False).to_dict()
    results["severity_counts"] = severity_counts

    severity_percentages = (
        df["Severity"].value_counts(normalize=True, dropna=False) * 100
    ).round(2).to_dict()
    results["severity_percentages"] = severity_percentages

    # -------------------------
    # Summary tables
    # -------------------------
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

    # -------------------------
    # CAP-style discrepancy buckets
    # -------------------------
    bucket_order = [
        "minor_variance",
        "major_undercall",
        "minor_undercall",
        "exact_agreement",
        "minor_overcall",
        "major_overcall",
    ]

    bucket_label_map = {
        "minor_variance": "MinVar",
        "major_undercall": "MajUnd",
        "minor_undercall": "MinUnd",
        "exact_agreement": "Agree",
        "minor_overcall": "MinOver",
        "major_overcall": "MajOver",
    }

    bucket_counts = {
        bucket_label_map[k]: int(subtype_counts.get(k, 0))
        for k in bucket_order
    }
    results["bucket_counts"] = bucket_counts

    bucket_table = pd.DataFrame({
        "Bucket": list(bucket_counts.keys()),
        "Count": list(bucket_counts.values())
    })
    bucket_table["Percent"] = (bucket_table["Count"] / total_cases * 100).round(2)
    results["bucket_table"] = bucket_table

    # -------------------------
    # Confusion matrix
    # -------------------------
    confusion_matrix = pd.crosstab(
        df["Cytology_Canonical"],
        df["Histology_Canonical"],
        dropna=False
    )
    results["confusion_matrix"] = confusion_matrix

    # -------------------------
    # HSIL-focused metrics
    # CAP-style: HSIL Pap tests and follow-up
    # -------------------------
    hsil_pap_cases = df[df["Cytology_Canonical"] == "HSIL"].copy()
    total_hsil_paps = len(hsil_pap_cases)

    hsil_to_hsil = len(
        hsil_pap_cases[
            hsil_pap_cases["Histology_Canonical"].isin(["HSIL (CIN2)", "HSIL (CIN3)"])
        ]
    )

    hsil_minor_discrepancies = len(
        hsil_pap_cases[hsil_pap_cases["Concordance_Class"] == "minor_discordant"]
    )

    hsil_major_fp = len(
        hsil_pap_cases[
            (hsil_pap_cases["Concordance_Class"] == "major_discordant") &
            (hsil_pap_cases["Direction"] == "overcall")
        ]
    )

    major_fn_count = len(
        df[
            (df["Concordance_Class"] == "major_discordant") &
            (df["Direction"] == "undercall")
        ]
    )

    if total_hsil_paps > 0:
        pct_hsil_to_hsil = round((hsil_to_hsil / total_hsil_paps) * 100, 2)
        pct_hsil_minor = round((hsil_minor_discrepancies / total_hsil_paps) * 100, 2)
        pct_hsil_major_fp = round((hsil_major_fp / total_hsil_paps) * 100, 2)
        hsil_pv_plus = pct_hsil_to_hsil
    else:
        pct_hsil_to_hsil = None
        pct_hsil_minor = None
        pct_hsil_major_fp = None
        hsil_pv_plus = None

    results["total_hsil_paps"] = total_hsil_paps
    results["hsil_to_hsil_count"] = hsil_to_hsil
    results["hsil_to_hsil_pct"] = pct_hsil_to_hsil
    results["hsil_minor_discrepancy_count"] = hsil_minor_discrepancies
    results["hsil_minor_discrepancy_pct"] = pct_hsil_minor
    results["hsil_major_fp_count"] = hsil_major_fp
    results["hsil_major_fp_pct"] = pct_hsil_major_fp
    results["major_fn_count"] = major_fn_count

    # Backward-compatible HSIL fields
    results["hsil_pv_plus"] = hsil_pv_plus
    results["hsil_followup_total"] = total_hsil_paps
    results["hsil_positive_followup"] = hsil_to_hsil

    results["hsil_pv_table"] = pd.DataFrame({
        "Metric": [
            "HSIL Pap tests with histologic HSIL (CIN2/CIN3)",
            "HSIL Pap tests with minor discrepancies",
            "HSIL Pap tests with major false-positive discrepancies",
            "Number of major false-negative / cytology undercall discrepancies",
            "PV+ for HSIL Pap tests (%)"
        ],
        "Value": [
            pct_hsil_to_hsil,
            pct_hsil_minor,
            pct_hsil_major_fp,
            major_fn_count,
            hsil_pv_plus
        ]
    })

    return results
