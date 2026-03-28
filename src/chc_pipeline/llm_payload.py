import json
from typing import Dict, Any


def build_llm_payload(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a grounded payload for LLM summarization from precomputed metrics.
    """
    payload = {
        "total_cases": results.get("total_cases"),
        "concordance_counts": results.get("concordance_counts"),
        "concordance_percentages": results.get("concordance_percentages"),
        "subtype_counts": results.get("subtype_counts"),
        "subtype_percentages": results.get("subtype_percentages"),
        "direction_counts": results.get("direction_counts"),
        "direction_percentages": results.get("direction_percentages"),
        "severity_counts": results.get("severity_counts"),
        "severity_percentages": results.get("severity_percentages"),
        "hsil_followup_total": results.get("hsil_followup_total"),
        "hsil_positive_followup": results.get("hsil_positive_followup"),
        "hsil_pv_plus": results.get("hsil_pv_plus"),
    }
    return payload


def save_llm_payload(results: Dict[str, Any], output_path: str) -> None:
    payload = build_llm_payload(results)
    with open(output_path, "w") as f:
        json.dump(payload, f, indent=2)
