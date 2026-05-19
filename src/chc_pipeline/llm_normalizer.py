"""
llm_normalizer.py

Uses a local LLM (Gemma3 via Ollama) to map any raw LIS diagnosis text
to a canonical term from the CHC dictionary before the existing
normalize.py dictionary lookup runs.

Flow:
    raw text → LLM → canonical term → normalize.py → classify.py
"""

import json
import requests
import pandas as pd
import yaml
from pathlib import Path


# ── Load canonical terms from your existing dictionary ───────────────────────

def load_canonical_terms(dictionary_path: str) -> dict:
    """Load valid canonical terms from your existing config dictionary."""
    with open(dictionary_path, "r") as f:
        mapping = yaml.safe_load(f)

    cyto_terms  = list(set(mapping["cytology_raw_to_canonical"].values()))
    histo_terms = list(set(mapping["histology_raw_to_canonical"].values()))

    return {
        "cytology":  cyto_terms,
        "histology": histo_terms
    }


# ── Build the normalization prompt ───────────────────────────────────────────

def build_prompt(raw_cyto: str, raw_histo: str, valid_terms: dict) -> str:
    return f"""You are a cytopathology informatics expert.

Your task is to map raw laboratory diagnosis text to EXACT canonical terms.

VALID CYTOLOGY TERMS — you must return exactly one of these:
{json.dumps(valid_terms["cytology"], indent=2)}

VALID HISTOLOGY TERMS — you must return exactly one of these:
{json.dumps(valid_terms["histology"], indent=2)}

MAPPING RULES:
Cytology:
- NILM = negative, no lesion, within normal limits, no dysplasia
- ASC-US = atypical squamous cells undetermined significance
- ASC-H = atypical squamous cells cannot exclude HSIL
- LSIL = low grade squamous intraepithelial lesion, mild dysplasia
- HSIL = high grade squamous intraepithelial lesion, severe dysplasia
- AGC = atypical glandular cells NOS
- AGC-ECX = atypical endocervical cells
- AGC-EMC = atypical endometrial cells
- AGC-NEO = atypical glandular cells favor neoplasia
- AGC-ECX/EMC NEO = atypical endo cells favor neoplasia
- AIS = adenocarcinoma in situ
- MALIGNANT = carcinoma, invasive cancer, malignant cells
- OTHER (EMC45) = endometrial cells age 45 or older

Histology:
- Benign / Inflammatory (Negative) = negative, benign, no CIN, reactive
- LSIL (CIN1) = CIN1, mild dysplasia, low grade CIN, koilocytic change
- HSIL (CIN2) = CIN2, moderate dysplasia
- HSIL (CIN3) = CIN3, severe dysplasia, carcinoma in situ
- Squamous Cell Carcinoma = SCC, invasive squamous carcinoma
- Adenocarcinoma = invasive adenocarcinoma, glandular carcinoma

CRITICAL RULES:
- Return ONLY terms from the valid lists above
- Never invent new terms
- If ambiguous pick the closest clinical equivalent
- Temperature is 0 — always return the single best match

Raw cytology text:  "{raw_cyto}"
Raw histology text: "{raw_histo}"

Respond in JSON only. No explanation. No preamble.
{{
  "cytology_canonical":  "...",
  "histology_canonical": "...",
  "cyto_confidence":     "high/medium/low",
  "histo_confidence":    "high/medium/low",
  "cyto_reasoning":      "one sentence",
  "histo_reasoning":     "one sentence"
}}"""


# ── Call Gemma3 via Ollama ────────────────────────────────────────────────────

def call_llm(prompt: str, model: str = "gemma3:4b") -> dict:
    """Call local Ollama LLM and return parsed JSON response."""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model":  model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.0,
                    "top_p":       0.9,
                    "num_predict": 300
                }
            },
            timeout=60
        )
        response.raise_for_status()
        return json.loads(response.json()["response"])

    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            "Ollama is not running. Start it with: ollama serve"
        )
    except Exception as e:
        return {
            "cytology_canonical":  None,
            "histology_canonical": None,
            "cyto_confidence":     "low",
            "histo_confidence":    "low",
            "cyto_reasoning":      f"LLM error: {str(e)}",
            "histo_reasoning":     f"LLM error: {str(e)}"
        }


# ── Validate LLM output against dictionary ───────────────────────────────────

def validate_output(result: dict, valid_terms: dict) -> dict:
    """
    Check LLM output is a valid canonical term.
    If not valid flag it for manual review.
    """
    cyto_valid  = result.get("cytology_canonical")  in valid_terms["cytology"]
    histo_valid = result.get("histology_canonical") in valid_terms["histology"]

    result["cyto_valid"]  = cyto_valid
    result["histo_valid"] = histo_valid
    result["ready"]       = cyto_valid and histo_valid

    if not cyto_valid:
        result["cyto_reasoning"] = (
            f"INVALID OUTPUT: '{result.get('cytology_canonical')}' "
            f"not in dictionary — needs manual review"
        )
    if not histo_valid:
        result["histo_reasoning"] = (
            f"INVALID OUTPUT: '{result.get('histology_canonical')}' "
            f"not in dictionary — needs manual review"
        )

    return result


# ── Main normalization function ───────────────────────────────────────────────

def llm_normalize_dataframe(
    df: pd.DataFrame,
    cyto_col:        str,
    histo_col:       str,
    dictionary_path: str,
    model:           str = "gemma3:4b"
) -> pd.DataFrame:
    """
    Takes a dataframe with raw LIS diagnosis columns.
    Returns same dataframe with new canonical columns added.
    These canonical columns feed directly into your existing normalize.py

    Args:
        df:              raw LIS dataframe
        cyto_col:        column name containing raw cytology diagnosis
        histo_col:       column name containing raw histology diagnosis
        dictionary_path: path to your config/dictionary.yaml
        model:           Ollama model name

    Returns:
        df with added columns:
            Cytology_Diagnosis   ← ready for normalize.py
            Histology_Diagnosis  ← ready for normalize.py
            LLM_Cyto_Confidence
            LLM_Histo_Confidence
            LLM_Cyto_Reasoning
            LLM_Histo_Reasoning
            LLM_Ready            ← True if both valid
    """

    valid_terms = load_canonical_terms(dictionary_path)
    df          = df.copy()

    cyto_canonical  = []
    histo_canonical = []
    cyto_conf       = []
    histo_conf      = []
    cyto_reason     = []
    histo_reason    = []
    ready_flags     = []

    total = len(df)

    for idx, row in df.iterrows():

        raw_cyto  = str(row[cyto_col]).strip()
        raw_histo = str(row[histo_col]).strip()

        print(f"  [{idx+1}/{total}] Normalizing: {raw_cyto} | {raw_histo}")

        prompt = build_prompt(raw_cyto, raw_histo, valid_terms)
        result = call_llm(prompt, model=model)
        result = validate_output(result, valid_terms)

        cyto_canonical.append(result.get("cytology_canonical"))
        histo_canonical.append(result.get("histology_canonical"))
        cyto_conf.append(result.get("cyto_confidence",  "low"))
        histo_conf.append(result.get("histo_confidence", "low"))
        cyto_reason.append(result.get("cyto_reasoning",  ""))
        histo_reason.append(result.get("histo_reasoning", ""))
        ready_flags.append(result.get("ready", False))

    # These column names match exactly what normalize.py expects
    df["Cytology_Diagnosis"]   = cyto_canonical
    df["Histology_Diagnosis"]  = histo_canonical
    df["LLM_Cyto_Confidence"]  = cyto_conf
    df["LLM_Histo_Confidence"] = histo_conf
    df["LLM_Cyto_Reasoning"]   = cyto_reason
    df["LLM_Histo_Reasoning"]  = histo_reason
    df["LLM_Ready"]            = ready_flags

    # Summary
    ready_count   = sum(ready_flags)
    review_count  = total - ready_count

    print(f"\n── LLM Normalization Summary ────────────────")
    print(f"Total rows        : {total}")
    print(f"Ready for engine  : {ready_count}  ({ready_count/total*100:.1f}%)")
    print(f"Needs review      : {review_count} ({review_count/total*100:.1f}%)")

    return df