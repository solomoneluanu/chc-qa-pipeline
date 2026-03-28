from typing import Dict, Any


def build_summary_prompt(payload: Dict[str, Any]) -> str:
    """
    Create a grounded prompt for LLM-based QA summary generation.
    """
    return f"""
You are writing a cervical cytology-histology correlation quality assurance summary.

Use only the statistics provided below.
Do not invent any values.
Do not add diagnoses or interpretations not supported by the data.
Write in a professional pathology QA style.

Statistics:
- Total cases: {payload.get('total_cases')}
- Concordance counts: {payload.get('concordance_counts')}
- Concordance percentages: {payload.get('concordance_percentages')}
- Discordance subtype counts: {payload.get('subtype_counts')}
- Discordance subtype percentages: {payload.get('subtype_percentages')}
- Direction counts: {payload.get('direction_counts')}
- Direction percentages: {payload.get('direction_percentages')}
- Severity counts: {payload.get('severity_counts')}
- Severity percentages: {payload.get('severity_percentages')}
- HSIL follow-up total: {payload.get('hsil_followup_total')}
- HSIL positive follow-up: {payload.get('hsil_positive_followup')}
- HSIL PV+: {payload.get('hsil_pv_plus')}

Write the output in this format:

1. Executive Summary
2. Key Findings
3. Quality Improvement Considerations
4. Short Recommendation

Keep it concise and factual.
""".strip()


def generate_mock_summary(payload: Dict[str, Any]) -> str:
    """
    Deterministic fallback summary without calling an external LLM.
    Useful for testing the pipeline before model integration.
    """
    total_cases = payload.get("total_cases")
    concordance = payload.get("concordance_percentages", {}).get("concordant")
    minor = payload.get("concordance_percentages", {}).get("minor_discordant")
    major = payload.get("concordance_percentages", {}).get("major_discordant")
    hsil_pv = payload.get("hsil_pv_plus")

    return (
        f"1. Executive Summary\n"
        f"A total of {total_cases} cytology-histology paired cases were analyzed. "
        f"Exact agreement was observed in {concordance}% of cases, with minor discordance in {minor}% "
        f"and major discordance in {major}%.\n\n"
        f"2. Key Findings\n"
        f"The dataset demonstrates a structured distribution of concordant and discordant pairs. "
        f"Major and minor discrepancy categories were successfully identified using the rule-based engine. "
        f"HSIL positive predictive value (PV+) was {hsil_pv}%.\n\n"
        f"3. Quality Improvement Considerations\n"
        f"Review of major undercall and major overcall cases may help identify threshold-related or interpretive issues. "
        f"Monitoring subtype distributions over time may support ongoing laboratory QA.\n\n"
        f"4. Short Recommendation\n"
        f"Continue periodic CHC review using standardized discrepancy rules, with focused review of major discordant cases and HSIL-related follow-up patterns."
    )
