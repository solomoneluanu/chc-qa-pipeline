import pandas as pd


def compute_metrics(df: pd.DataFrame) -> dict:
    """
    Compute CHC QA metrics per Birdsong ASC Guideline 2017.
    Covers all required statistical calculations from Section 5 and 7.
    """
    results = {}
    total_cases = len(df)
    results["total_cases"] = total_cases

    # ?? Core concordance summaries ?????????????????????????????????????????????
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

    # ?? Summary tables ?????????????????????????????????????????????????????????
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

    # ?? CAP discrepancy buckets ????????????????????????????????????????????????
    bucket_order = [
        "minor_variance", "major_undercall", "minor_undercall",
        "exact_agreement", "minor_overcall",  "major_overcall",
    ]
    bucket_label_map = {
        "minor_variance":  "MinVar",
        "major_undercall": "MajUnd",
        "minor_undercall": "MinUnd",
        "exact_agreement": "Agree",
        "minor_overcall":  "MinOver",
        "major_overcall":  "MajOver",
    }
    bucket_counts = {
        bucket_label_map[k]: int(subtype_counts.get(k, 0))
        for k in bucket_order
    }
    results["bucket_counts"] = bucket_counts

    bucket_table = pd.DataFrame({
        "Bucket": list(bucket_counts.keys()),
        "Count":  list(bucket_counts.values())
    })
    bucket_table["Percent"] = (
        bucket_table["Count"] / total_cases * 100
    ).round(2)
    results["bucket_table"] = bucket_table

    # ?? Confusion matrix ???????????????????????????????????????????????????????
    results["confusion_matrix"] = pd.crosstab(
        df["Cytology_Canonical"],
        df["Histology_Canonical"],
        dropna=False
    )

    # ?? Birdsong Section 7 ? HSIL focused metrics ??????????????????????????????
    hsil_pap_cases  = df[df["Cytology_Canonical"] == "HSIL"].copy()
    total_hsil_paps = len(hsil_pap_cases)

    hsil_to_hsil = len(
        hsil_pap_cases[
            hsil_pap_cases["Histology_Canonical"].isin(["HSIL (CIN2)", "HSIL (CIN3)"])
        ]
    )
    hsil_minor_disc = len(
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
        pct_hsil_to_hsil  = round(hsil_to_hsil   / total_hsil_paps * 100, 2)
        pct_hsil_minor    = round(hsil_minor_disc / total_hsil_paps * 100, 2)
        pct_hsil_major_fp = round(hsil_major_fp   / total_hsil_paps * 100, 2)
        hsil_pv_plus      = pct_hsil_to_hsil
    else:
        pct_hsil_to_hsil  = None
        pct_hsil_minor    = None
        pct_hsil_major_fp = None
        hsil_pv_plus      = None

    results["total_hsil_paps"]             = total_hsil_paps
    results["hsil_to_hsil_count"]          = hsil_to_hsil
    results["hsil_to_hsil_pct"]            = pct_hsil_to_hsil
    results["hsil_minor_discrepancy_count"]= hsil_minor_disc
    results["hsil_minor_discrepancy_pct"]  = pct_hsil_minor
    results["hsil_major_fp_count"]         = hsil_major_fp
    results["hsil_major_fp_pct"]           = pct_hsil_major_fp
    results["major_fn_count"]              = major_fn_count
    results["hsil_pv_plus"]                = hsil_pv_plus
    results["hsil_followup_total"]         = total_hsil_paps
    results["hsil_positive_followup"]      = hsil_to_hsil

    results["hsil_pv_table"] = pd.DataFrame({
        "Metric": [
            "HSIL Pap tests with histologic HSIL (CIN2/CIN3)",
            "HSIL Pap tests with minor discrepancies",
            "HSIL Pap tests with major false-positive discrepancies",
            "Number of major false-negative / cytology undercall discrepancies",
            "PV+ for HSIL Pap tests (%)"
        ],
        "Value": [
            pct_hsil_to_hsil, pct_hsil_minor,
            pct_hsil_major_fp, major_fn_count, hsil_pv_plus
        ]
    })

    # ?? Birdsong Addition 1 ? PV+ interpretation flag ?????????????????????????
    if hsil_pv_plus is not None:
        if hsil_pv_plus > 95:
            pv_flag = "HIGH ? May indicate excessive cytology undercall rate per Birdsong"
        elif hsil_pv_plus >= 60:
            pv_flag = "ACCEPTABLE ? Within CAP expected range (60-95%)"
        else:
            pv_flag = "LOW ? Below CAP target of 60%. Review HSIL overcall rate."
    else:
        pv_flag = "INSUFFICIENT ? Not enough HSIL cases for meaningful PV+ calculation"

    results["hsil_pv_interpretation"] = pv_flag

    # ?? Birdsong Addition 2 ? Agreement within one grade ??????????????????????
    # Birdsong: pairs with exact agreement OR minor disagreement
    within_one = (
        concordance_counts.get("concordant",       0) +
        concordance_counts.get("minor_discordant", 0)
    )
    results["agreement_within_one_grade"]  = within_one
    results["agreement_within_one_pct"]   = round(
        within_one / total_cases * 100, 2
    ) if total_cases > 0 else 0

    # ?? Birdsong Addition 3 ? Intergrade follow-up rates ??????????????????????
    # Birdsong Section 8: Review rates of HSIL histology following
    # ASC-US, ASC-H, and LSIL cytologic interpretations
    hsil_histo_terms = ["HSIL (CIN2)", "HSIL (CIN3)", "Squamous Cell Carcinoma", "Adenocarcinoma"]

    intergrade = {}
    for cyto_diag in ["ASC-US", "ASC-H", "LSIL", "AGC", "AGC-NEO", "AGC-ECX", "AGC-EMC"]:
        cyto_cases = df[df["Cytology_Canonical"] == cyto_diag]
        if len(cyto_cases) > 0:
            hsil_follow = cyto_cases[
                cyto_cases["Histology_Canonical"].isin(hsil_histo_terms)
            ]
            intergrade[cyto_diag] = {
                "total":         len(cyto_cases),
                "hsil_followup": len(hsil_follow),
                "hsil_rate":     round(len(hsil_follow) / len(cyto_cases) * 100, 1)
            }

    results["intergrade_followup"] = intergrade

    intergrade_table = pd.DataFrame([
        {
            "Cytology":          cyto,
            "Total Cases":       data["total"],
            "HSIL+ Follow-up":   data["hsil_followup"],
            "HSIL+ Rate (%)":    data["hsil_rate"]
        }
        for cyto, data in intergrade.items()
    ])
    results["intergrade_table"] = intergrade_table

    # ?? Birdsong Addition 4 ? Extended PV+ (HSIL + ASC-H + AGC-NEO) ??????????
    # Birdsong Figure 1 groups HSIL, ASC-H, AGC-NEO together
    high_grade_cyto = df[
        df["Cytology_Canonical"].isin(["HSIL", "ASC-H", "AGC-NEO", "AIS", "MALIGNANT"])
    ]
    total_high_grade = len(high_grade_cyto)

    high_grade_to_hsil = len(
        high_grade_cyto[
            high_grade_cyto["Histology_Canonical"].isin(hsil_histo_terms)
        ]
    )

    results["extended_pv_plus"] = round(
        high_grade_to_hsil / total_high_grade * 100, 2
    ) if total_high_grade > 0 else None
    results["total_high_grade_paps"] = total_high_grade
    results["high_grade_to_hsil"]    = high_grade_to_hsil

    # ?? Birdsong Addition 5 ? Undercall proportion summary ????????????????????
    undercall_total = (
        concordance_counts.get("minor_discordant", 0) *
        (direction_counts.get("undercall", 0) /
         max(concordance_counts.get("minor_discordant", 1), 1))
    )

    total_undercall = direction_counts.get("undercall", 0)
    total_overcall  = direction_counts.get("overcall",  0)
    total_matched   = direction_counts.get("matched",   0)

    results["undercall_proportion"] = round(
        total_undercall / total_cases * 100, 2
    ) if total_cases > 0 else 0
    results["overcall_proportion"] = round(
        total_overcall / total_cases * 100, 2
    ) if total_cases > 0 else 0

    # ?? Key signals summary for report ????????????????????????????????????????
    results["key_signals"] = {
        "major_discordance_rate":       concordance_percentages.get("major_discordant", 0),
        "minor_discordance_rate":       concordance_percentages.get("minor_discordant", 0),
        "undercall_proportion":         results["undercall_proportion"],
        "overcall_proportion":          results["overcall_proportion"],
        "hsil_pv_plus":                 hsil_pv_plus,
        "agreement_within_one_grade":   results["agreement_within_one_pct"],
        "major_fn_count":               major_fn_count,
        "extended_pv_plus":             results["extended_pv_plus"],
        "pv_interpretation":            pv_flag,
        "cap_major_disc_threshold":     10.0,
        "cap_pv_plus_threshold":        60.0,
        "major_disc_exceeds_cap":       concordance_percentages.get("major_discordant", 0) > 10,
        "pv_below_cap_target":          (hsil_pv_plus is not None and hsil_pv_plus < 60),
    }

    return results
