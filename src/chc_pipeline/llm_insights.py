import requests


def generate_qa_insights(results: dict, classified_df, model: str = "gemma3:4b") -> str:
    """
    Generate clinical QA commentary using local LLM.
    Covers: performance summary, root cause hypothesis,
    benchmark interpretation, intergrade analysis,
    corrective action recommendations.
    """

    # Core metrics
    total      = results.get("total_cases", 0)
    counts     = results.get("concordance_counts", {})
    concordant = counts.get("concordant", 0)
    major_disc = counts.get("major_discordant", 0)
    minor_disc = counts.get("minor_discordant", 0)
    buckets    = results.get("bucket_counts", {})
    maj_und    = buckets.get("MajUnd", 0)
    maj_over   = buckets.get("MajOver", 0)
    min_und    = buckets.get("MinUnd", 0)
    min_over   = buckets.get("MinOver", 0)

    concordance_rate = round(concordant / total * 100, 1) if total > 0 else 0
    major_rate       = round(major_disc / total * 100, 1) if total > 0 else 0
    minor_rate       = round(minor_disc / total * 100, 1) if total > 0 else 0
    cap_status       = "EXCEEDS CAP benchmark" if major_rate > 10 else "within CAP benchmark"

    # HSIL metrics
    hsil_pv      = results.get("hsil_pv_plus", 0) or 0
    ext_pv       = results.get("extended_pv_plus", 0) or 0
    major_fn     = results.get("major_fn_count", 0)
    hsil_to_hsil = results.get("hsil_to_hsil_pct", 0) or 0
    hsil_fp      = results.get("hsil_major_fp_pct", 0) or 0
    hsil_minor   = results.get("hsil_minor_discrepancy_pct", 0) or 0
    undercall    = results.get("undercall_proportion", 0)
    overcall     = results.get("overcall_proportion", 0)
    within_one   = results.get("agreement_within_one_pct", 0)

    # Intergrade follow-up rates
    intergrade     = results.get("intergrade_followup", {})
    intergrade_txt = ""
    for cyto, data in intergrade.items():
        if isinstance(data, dict):
            intergrade_txt += (
                f"{cyto}: {data.get('total', 0)} cases, "
                f"{data.get('hsil_rate', 0):.1f}% HSIL+ follow-up. "
            )

    # PV+ interpretation
    if hsil_pv < 60:
        pv_status = f"LOW at {hsil_pv:.1f}% - below CAP target of 60%"
    elif hsil_pv > 95:
        pv_status = f"UNUSUALLY HIGH at {hsil_pv:.1f}% - may indicate undercalling per Birdsong"
    else:
        pv_status = f"ACCEPTABLE at {hsil_pv:.1f}% - within CAP range"

    prompt = f"""You are an expert cytopathology quality assurance consultant
with deep knowledge of CAP accreditation and the ASC Birdsong CHC Guideline 2017.

Write a professional clinical QA commentary in exactly 5 paragraphs.
Use correct cytopathology terminology.
Do not use markdown, asterisks, or bullet points.
Write in clear professional prose suitable for a CAP inspection document.
Be specific and cite the metrics provided.

LABORATORY METRICS:
Total cases: {total}
Concordance rate: {concordance_rate}%
Major discordance rate: {major_rate}% - {cap_status} of less than 10%
Minor discordance rate: {minor_rate}%
Undercall proportion: {undercall:.1f}%
Overcall proportion: {overcall:.1f}%
Agreement within one grade: {within_one:.1f}%
Major undercalls: {maj_und}
Major overcalls: {maj_over}
Minor undercalls: {min_und}
Minor overcalls: {min_over}

HSIL METRICS:
HSIL PV+ status: {pv_status}
Extended PV+ (HSIL+ASC-H+AGC-NEO): {ext_pv:.1f}%
HSIL Pap with HSIL histology: {hsil_to_hsil:.1f}%
HSIL Pap with major false positive: {hsil_fp:.1f}%
HSIL Pap with minor discrepancy: {hsil_minor:.1f}%
Major false negative count: {int(major_fn)}

INTERGRADE FOLLOW-UP RATES:
{intergrade_txt}

Write exactly these 5 paragraphs:

Paragraph 1 - PATTERN ANALYSIS:
Identify the dominant discordance pattern.
Is undercalling or overcalling more prevalent?
Which metrics support this conclusion?
3 to 4 sentences.

Paragraph 2 - ROOT CAUSE HYPOTHESIS:
Based on Birdsong Section 8 root cause categories
which are sampling error, screening error,
interpretive error, and difference of opinion,
what are the most probable contributing factors?
Reference specific metrics to support each hypothesis.
3 to 4 sentences.

Paragraph 3 - BENCHMARK INTERPRETATION:
Compare performance against CAP major discordance
threshold of less than 10%, CAP PV+ target of
greater than 60%, and Australian Royal College
PV+ standard of greater than 65%.
State clearly whether corrective action is required.
3 to 4 sentences.

Paragraph 4 - INTERGRADE ANALYSIS:
Interpret the intergrade follow-up rates.
Flag any cytology category with rates outside
expected ranges: ASC-US expected 15 to 20%,
LSIL expected 20 to 25%, ASC-H expected 40 to 60%.
What do elevated or depressed rates suggest clinically?
3 to 4 sentences.

Paragraph 5 - CORRECTIVE ACTION RECOMMENDATIONS:
Provide 3 to 4 specific prioritized corrective actions.
Reference Birdsong Section 8 and CAP CYP.06600.
Include a monitoring timeline.
3 to 4 sentences."""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 600
                }
            },
            timeout=300
        )
        response.raise_for_status()
        text = response.json()["response"].strip()

        if not text:
            return generate_fallback_insights(results)

        # Clean up any markdown formatting
        text = text.replace("**", "")
        text = text.replace("*", "")
        text = text.replace("##", "")
        text = text.replace("#", "")

        return text

    except requests.exceptions.ConnectionError:
        return generate_fallback_insights(results)
    except Exception:
        return generate_fallback_insights(results)


def generate_fallback_insights(results: dict) -> str:
    """
    Rule-based fallback when LLM is unavailable.
    Ensures Section 7 always has content.
    """
    total        = results.get("total_cases", 0)
    major_rate   = results.get("concordance_percentages", {}).get("major_discordant", 0)
    minor_rate   = results.get("concordance_percentages", {}).get("minor_discordant", 0)
    conc_rate    = results.get("concordance_percentages", {}).get("concordant", 0)
    undercall    = results.get("undercall_proportion", 0)
    overcall     = results.get("overcall_proportion", 0)
    hsil_pv      = results.get("hsil_pv_plus", 0) or 0
    major_fn     = results.get("major_fn_count", 0)
    within_one   = results.get("agreement_within_one_pct", 0)
    intergrade   = results.get("intergrade_followup", {})

    dominant = "undercalling" if undercall > overcall else "overcalling"

    if hsil_pv < 60:
        pv_text = (
            f"The HSIL PV+ of {hsil_pv:.1f}% falls below both the CAP target of 60% "
            f"and the Australian Royal College standard of 65%, indicating either "
            f"systematic HSIL overcalling or inadequate colposcopic tissue sampling."
        )
    elif hsil_pv > 95:
        pv_text = (
            f"The HSIL PV+ of {hsil_pv:.1f}% is unusually high and per Birdsong may "
            f"indicate an excessive cytology undercall rate requiring threshold review."
        )
    else:
        pv_text = (
            f"The HSIL PV+ of {hsil_pv:.1f}% is within the acceptable CAP range, "
            f"indicating appropriate cytologic performance for high-grade lesions."
        )

    intergrade_flags = []
    for cyto, data in intergrade.items():
        if isinstance(data, dict):
            rate = data.get("hsil_rate", 0)
            if cyto == "ASC-US" and rate > 20:
                intergrade_flags.append(
                    f"ASC-US to HSIL+ rate of {rate:.1f}% exceeds the expected 15-20% range"
                )
            elif cyto == "LSIL" and rate > 25:
                intergrade_flags.append(
                    f"LSIL to HSIL+ rate of {rate:.1f}% exceeds the expected 20-25% range"
                )
            elif cyto == "ASC-H" and rate < 40:
                intergrade_flags.append(
                    f"ASC-H to HSIL+ rate of {rate:.1f}% is below the expected 40-60% range"
                )

    intergrade_text = (
        " ".join(intergrade_flags) + ", suggesting systematic undercalling patterns."
        if intergrade_flags
        else "Intergrade follow-up rates are within expected published ranges."
    )

    return (
        f"PATTERN ANALYSIS. Analysis of {total} cytology-histology correlation pairs "
        f"reveals a dominant pattern of {dominant} errors. The concordance rate of "
        f"{conc_rate:.1f}% and major discordance rate of {major_rate:.1f}% indicate "
        f"{'significant quality improvement opportunity requiring immediate corrective action' if major_rate > 10 else 'acceptable performance within CAP benchmarks'}. "
        f"The undercall proportion of {undercall:.1f}% and overcall proportion of "
        f"{overcall:.1f}% confirm {dominant} as the primary performance concern.\n\n"

        f"ROOT CAUSE HYPOTHESIS. Based on Birdsong Section 8 root cause categories, "
        f"the pattern of {dominant} with {int(major_fn)} major false negative cases "
        f"is most consistent with {'systematic screening or interpretive error' if major_fn > 10 else 'focal interpretive errors'}. "
        f"The distribution of discordance across cytology categories suggests "
        f"{'institutional threshold issues' if major_rate > 20 else 'case-specific interpretive variation'} "
        f"rather than isolated incidents. Colposcopic sampling adequacy should also "
        f"be evaluated as a contributing factor for overcall cases.\n\n"

        f"BENCHMARK INTERPRETATION. {pv_text} The major discordance rate of "
        f"{major_rate:.1f}% {'exceeds the CAP benchmark of less than 10% and requires corrective action documentation per CYP.06600' if major_rate > 10 else 'is within the CAP benchmark of less than 10%'}. "
        f"Agreement within one grade of {within_one:.1f}% provides additional "
        f"context for overall laboratory QA performance.\n\n"

        f"INTERGRADE ANALYSIS. {intergrade_text} Per Birdsong Section 8, rates "
        f"significantly outside published ranges should prompt mandatory slide review "
        f"of affected cases and targeted educational intervention. Intergrade follow-up "
        f"analysis is the most sensitive indicator of systematic cytologic threshold issues.\n\n"

        f"CORRECTIVE ACTION RECOMMENDATIONS. The following actions are recommended "
        f"in priority order: (1) Mandatory slide review of all {int(major_fn)} major "
        f"false negative cases by the lead cytopathologist within 14 days per Birdsong "
        f"Section 8. (2) {'Educational session on HSIL cytomorphology for cytotechnologists. ' if major_rate > 10 else 'Continue current QA protocols. '}"
        f"(3) Monthly CHC monitoring for 3 months to assess corrective action effectiveness. "
        f"(4) Summary data presentation to all cytology staff at the next quarterly QA "
        f"meeting per CAP CYP.06600 requirements."
    )


def generate_case_explanation(
    cyto_diag: str,
    histo_diag: str,
    concordance_class: str,
    discordance_subtype: str,
    model: str = "gemma3:4b"
) -> str:
    """Generate one-sentence explanation for a single discordant case."""

    prompt = (
        f"Cytology: {cyto_diag}. Histology: {histo_diag}. "
        f"Classification: {discordance_subtype}. "
        f"Write one sentence explaining this cytology-histology discordance "
        f"and one sentence recommending clinical action. "
        f"Use correct cytopathology terminology. No markdown."
    )

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 80}
            },
            timeout=60
        )
        response.raise_for_status()
        text = response.json()["response"].strip()
        text = text.replace("**", "").replace("*", "")
        return text
    except Exception as e:
        return (
            f"Cytology {cyto_diag} followed by histology {histo_diag} "
            f"represents a {discordance_subtype} requiring clinical review."
        )
