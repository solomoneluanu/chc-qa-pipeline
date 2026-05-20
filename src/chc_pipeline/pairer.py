import pandas as pd


DATE_FORMATS = [
    "%Y-%m-%d",    # 2024-10-16
    "%m/%d/%Y",    # 04/10/2023
    "%d/%m/%Y",    # 10/04/2023
    "%d-%b-%Y",    # 15-Apr-2023
    "%d-%B-%Y",    # 15-April-2023
    "%b %d %Y",    # Apr 15 2023
    "%B %d %Y",    # April 15 2023
    "%Y/%m/%d",    # 2024/10/16
    "%d.%m.%Y",    # 15.04.2023
]


def parse_date_robust(value):
    """Try multiple date formats until one works."""
    if pd.isna(value) or str(value).strip() == "":
        return pd.NaT

    value = str(value).strip()

    # Try pandas default first
    try:
        return pd.to_datetime(value)
    except:
        pass

    # Try each format explicitly
    for fmt in DATE_FORMATS:
        try:
            return pd.to_datetime(value, format=fmt)
        except:
            continue

    return pd.NaT


def parse_date_column(series: pd.Series) -> pd.Series:
    """Apply robust date parsing to an entire column."""
    parsed = series.apply(parse_date_robust)
    failures = parsed.isna().sum()
    if failures > 0:
        print(f"   Date parse failures: {failures}/{len(series)}")
        failed = series[parsed.isna()].unique()
        print(f"   Failed values: {list(failed[:5])}")
    return parsed


def _best_date_match(cyto_row, candidates, window_days):
    """Find best histo match within date window."""
    if candidates.empty:
        return None

    cyto_date = cyto_row.get("date")
    if pd.isna(cyto_date):
        return None

    candidates = candidates.copy()
    candidates["date_diff"] = (candidates["date"] - cyto_date).dt.days

    in_window = candidates[
        (candidates["date_diff"] >= -30) &
        (candidates["date_diff"] <= window_days)
    ]

    if in_window.empty:
        return None

    return in_window.loc[in_window["date_diff"].abs().idxmin()]


def _build_pair(cyto_row, histo_row, match_method):
    """Build a paired record from matched cyto and histo rows."""
    cyto_date = cyto_row.get("date")
    return {
        "case_id":             f"CHC-{cyto_row.get('MRN', 'UNK')}-{str(cyto_date.date()) if pd.notna(cyto_date) else 'UNK'}",
        "MRN":                 cyto_row.get("MRN"),
        "match_method":        match_method,
        "days_between":        int(histo_row.get("date_diff", 0)),

        # Cytology
        "cyto_accession":      cyto_row.get("accession"),
        "cyto_date":           cyto_row.get("date"),
        "cyto_raw_diag":       cyto_row.get("raw_diag"),
        "cyto_adequacy":       cyto_row.get("adequacy"),
        "cyto_specimen":       cyto_row.get("specimen"),

        # Histology
        "histo_accession":     histo_row.get("accession"),
        "histo_date":          histo_row.get("date"),
        "histo_raw_diag":      histo_row.get("raw_diag"),
        "histo_procedure":     histo_row.get("procedure"),

        # Canonical columns filled after LLM normalization
        "Cytology_Diagnosis":  cyto_row.get("Cytology_Canonical"),
        "Histology_Diagnosis": histo_row.get("Histology_Canonical"),
    }


def pair_cases(
    cyto_df: pd.DataFrame,
    histo_df: pd.DataFrame,
    window_days: int = 180
) -> tuple:
    """
    Match cytology and histology cases using three-tier logic:

    Tier 1: MRN + date window
    Tier 2: Name + date window
    Tier 3: DOB + date window
    """

    cyto_df  = cyto_df.copy()
    histo_df = histo_df.copy()

    # Robust date parsing
    print("  Parsing cyto dates...")
    cyto_df["date"]  = parse_date_column(cyto_df["date"])

    print("  Parsing histo dates...")
    histo_df["date"] = parse_date_column(histo_df["date"])

    # Standardize name columns if present
    if "patient_name" in cyto_df.columns:
        cyto_df["patient_name"] = (
            cyto_df["patient_name"].astype(str).str.lower().str.strip()
        )
    if "patient_name" in histo_df.columns:
        histo_df["patient_name"] = (
            histo_df["patient_name"].astype(str).str.lower().str.strip()
        )

    # Standardize DOB if present
    if "dob" in cyto_df.columns:
        cyto_df["dob"]  = parse_date_column(cyto_df["dob"])
    if "dob" in histo_df.columns:
        histo_df["dob"] = parse_date_column(histo_df["dob"])

    paired    = []
    unmatched = []
    total     = len(cyto_df)

    for idx, cyto_row in cyto_df.iterrows():

        match        = None
        match_method = None

        # ── Tier 1: MRN + date ──────────────────────────────────────────
        mrn = cyto_row.get("MRN")

        if pd.notna(mrn) and str(mrn).strip() not in ["", "nan"]:
            candidates = histo_df[
                histo_df["MRN"].astype(str) == str(mrn)
            ].copy()

            match = _best_date_match(cyto_row, candidates, window_days)
            if match is not None:
                match_method = "MRN+DATE"

        # ── Tier 2: Name + date ─────────────────────────────────────────
        if match is None and "patient_name" in cyto_df.columns and "patient_name" in histo_df.columns:
            cyto_name = str(cyto_row.get("patient_name", "")).strip()

            if cyto_name and cyto_name != "nan":
                candidates = histo_df[
                    histo_df["patient_name"] == cyto_name
                ].copy()

                match = _best_date_match(cyto_row, candidates, window_days)
                if match is not None:
                    match_method = "NAME+DATE"

        # ── Tier 3: DOB + date ──────────────────────────────────────────
        if match is None and "dob" in cyto_df.columns and "dob" in histo_df.columns:
            cyto_dob = cyto_row.get("dob")

            if pd.notna(cyto_dob):
                candidates = histo_df[
                    histo_df["dob"] == cyto_dob
                ].copy()

                match = _best_date_match(cyto_row, candidates, window_days)
                if match is not None:
                    match_method = "DOB+DATE"

        # ── No match ────────────────────────────────────────────────────
        if match is None:
            unmatched.append(cyto_row.to_dict())
            continue

        paired.append(_build_pair(cyto_row, match, match_method))

    paired_df    = pd.DataFrame(paired)    if paired    else pd.DataFrame()
    unmatched_df = pd.DataFrame(unmatched) if unmatched else pd.DataFrame()

    print(f"\n-- Pairing Summary ──────────────────────────────")
    print(f"Cyto cases        : {total}")
    print(f"Paired            : {len(paired_df)}")
    print(f"Unmatched         : {len(unmatched_df)}")

    if len(paired_df) > 0:
        print(f"Match methods     : {paired_df['match_method'].value_counts().to_dict()}")
        print(f"Avg days between  : {paired_df['days_between'].mean():.0f} days")

    return paired_df, unmatched_df
