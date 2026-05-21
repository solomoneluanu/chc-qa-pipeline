import requests
import json


def generate_qa_insights(results: dict, classified_df, model: str = "gemma3:4b") -> str:
    """
    Generate clinical QA commentary using local LLM.
    Takes metrics dict and classified dataframe.
    Returns professional clinical narrative for PDF report.
    """

    # Extract key metrics
    total         = results.get("total_cases", 0)
    counts        = results.get("concordance_counts", {})
    concordant    = counts.get("concordant", 0)
    major_disc    = counts.get("major_discordant", 0)
    minor_disc    = counts.get("minor_discordant", 0)

    buckets       = results.get("bucket_counts", {})
    maj_und       = buckets.get("MajUnd", 0)
    min_und       = buckets.get("MinUnd", 0)
    maj_over      = buckets.get("MajOver", 0)
    min_over      = buckets.get("MinOver", 0)
    agree         = buckets.get("Agree", 0)

    hsil_pv       = results.get("hsil_pv_plus", 0)
    major_fn      = results.get("major_fn_count", 0)

    concordance_rate  = round(concordant / total * 100, 1) if total > 0 else 0
    major_disc_rate   = round(major_disc / total * 100, 1) if total > 0 else 0
    minor_disc_rate   = round(minor_disc / total * 100, 1) if total > 0 else 0
    undercall_rate    = round((maj_und + min_und) / total * 100, 1) if total > 0 else 0
    overcall_rate     = round((maj_over + min_over) / total * 100, 1) if total > 0 else 0

    # Get top discordant pairs
    top_pairs_text = ""
    try:
        if "Cytology_Canonical" in classified_df.columns and "Histology_Canonical" in classified_df.columns:
            discordant_df = classified_df[
                classified_df["Concordance_Class"] != "concordant"
            ]
            if len(discordant_df) > 0:
                top_pairs = (
                    discordant_df
                    .groupby(["Cytology_Canonical", "Histology_Canonical", "Discordance_Subtype"])
                    .size()
                    .reset_index(name="count")
                    .sort_values("count", ascending=False)
                    .head(5)
                )
                lines = []
                for _, row in top_pairs.iterrows():
                    lines.append(
                        f"{row['Cytology_Canonical']} vs {row['Histology_Canonical']} "
                        f"({row['Discordance_Subtype']}): {row['count']} cases"
                    )
                top_pairs_text = "\n".join(lines)
    except Exception:
        top_pairs_text = "Not available"

    prompt = f"""You are an expert cytopathologist and laboratory quality assurance specialist with deep knowledge of CAP accreditation requirements.

Analyze the following cytology-histology correlation QA results and write a professional clinical commentary for a laboratory QA report. This commentary will be read by the laboratory director and pathologists at the monthly QA meeting and filed as CAP documentation.

QA RESULTS FOR THIS PERIOD:
- Total cases analyzed: {total}
- Concordant: {concordant} ({concordance_rate}%)
- Major discordant: {major_disc} ({major_disc_rate}%)
- Minor discordant: {minor_disc} ({minor_disc_rate}%)
- Major undercalls: {maj_und}
- Minor undercalls: {min_und}
- Major overcalls: {maj_over}
- Minor overcalls: {min_over}
- Undercall proportion: {undercall_rate}%
- Overcall proportion: {overcall_rate}%
- HSIL positive predictive value: {hsil_pv}%
- Major false negative count: {major_fn}

TOP DISCORDANT PAIRS:
{top_pairs_text}

CAP BENCHMARK REFERENCE:
- Major discordance rate benchmark: less than 10%
- HSIL PPV benchmark: greater than 60%
- Undercall proportion benchmark: less than 15%
- A major discordance rate above 10% requires documented corrective action

Write a professional clinical QA commentary that covers all five of these areas:

1. OVERALL PERFORMANCE: Interpret the concordance rate against CAP benchmarks. State clearly whether performance is within or outside acceptable limits.

2. DOMINANT PATTERN: Identify whether undercalling or overcalling is the dominant pattern and what this means clinically.

3. CRITICAL FINDINGS: Highlight the most clinically significant discordant pairs and their patient safety implications.

4. ROOT CAUSE HYPOTHESES: For the dominant discordance pattern suggest the most likely contributing factors based on the data.

5. RECOMMENDED ACTIONS: Provide specific actionable recommendations appropriate to the findings including any mandatory CAP corrective action requirements.

Write in formal pathology report style. Be specific and data-driven. Reference actual numbers from the results. Maximum 350 words. Write in paragraphs not bullet points."""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 500
                }
            },
            timeout=180
        )
        response.raise_for_status()
        return response.json()["response"].strip()

    except requests.exceptions.ConnectionError:
        return "Clinical commentary unavailable: Ollama is not running."
    except Exception as e:
        return f"Clinical commentary unavailable: {str(e)}"


def generate_case_explanation(
    cyto_diag: str,
    histo_diag: str,
    concordance_class: str,
    discordance_subtype: str,
    model: str = "gemma3:4b"
) -> str:
    """
    Generate a brief explanation for a single discordant case.
    Used for major discordant cases in the detailed report.
    """

    prompt = f"""You are an expert cytopathologist.

Write one concise paragraph explaining this cytology-histology discordance for a laboratory QA report.

Cytology diagnosis:   {cyto_diag}
Histology diagnosis:  {histo_diag}
Classification:       {concordance_class}
Subtype:              {discordance_subtype}

Cover in one paragraph:
- Why this is classified as {discordance_subtype}
- The clinical significance for the patient
- The most likely reason for the discordance
- The recommended action

Maximum 60 words. Use professional pathology language."""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 120
                }
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()["response"].strip()

    except Exception as e:
        return f"Explanation unavailable: {str(e)}"
