import requests
import json


def generate_qa_insights(results: dict, classified_df, model: str = "gemma3:4b") -> str:
    """
    Generate clinical QA commentary using local LLM.
    Ultra-short prompt optimized for CPU hardware.
    """

    total         = results.get("total_cases", 0)
    counts        = results.get("concordance_counts", {})
    concordant    = counts.get("concordant", 0)
    major_disc    = counts.get("major_discordant", 0)
    minor_disc    = counts.get("minor_discordant", 0)
    buckets       = results.get("bucket_counts", {})
    maj_und       = buckets.get("MajUnd", 0)
    hsil_pv       = results.get("hsil_pv_plus", 0)

    concordance_rate = round(concordant / total * 100, 1) if total > 0 else 0
    major_rate       = round(major_disc / total * 100, 1) if total > 0 else 0
    cap_status       = "exceeds CAP benchmark" if major_rate > 10 else "within CAP benchmark"

    prompt = f"""Lab QA results: {total} cases, {concordance_rate}% concordant, {major_rate}% major discordant ({cap_status}), {maj_und} major undercalls, HSIL PPV {hsil_pv}%.

Write 2 short paragraphs: (1) performance summary, (2) recommended actions."""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 200
                }
            },
            timeout=300
        )
        response.raise_for_status()
        text = response.json()["response"].strip()
        return text if text else "Clinical commentary could not be generated."

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
    prompt = f"Cytology {cyto_diag} vs Histology {histo_diag} = {discordance_subtype}. One sentence explanation and action."

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 60}
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()["response"].strip()
    except Exception as e:
        return f"Explanation unavailable: {str(e)}"
