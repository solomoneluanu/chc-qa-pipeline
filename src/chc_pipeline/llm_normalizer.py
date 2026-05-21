import json
import os
import requests
import pandas as pd
import yaml

CACHE_FILE = "data/llm_cache.json"


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    os.makedirs("data", exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def load_cyto_terms(dictionary_path: str) -> list:
    with open(dictionary_path, "r") as f:
        mapping = yaml.safe_load(f)
    return list(set(mapping["cytology_raw_to_canonical"].values()))


def load_histo_terms(dictionary_path: str) -> list:
    with open(dictionary_path, "r") as f:
        mapping = yaml.safe_load(f)
    return list(set(mapping["histology_raw_to_canonical"].values()))


def call_llm(prompt: str, model: str = "gemma3:4b") -> dict:
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.0, "num_predict": 50}
            },
            timeout=120
        )
        response.raise_for_status()
        return json.loads(response.json()["response"])
    except Exception as e:
        return {"error": str(e)}


def call_llm_cyto(raw_text: str, valid_terms: list) -> dict:
    prompt = f"""You are a cytopathology expert.
Map this raw cytology diagnosis to ONE canonical term.

VALID TERMS: {json.dumps(valid_terms)}

MAPPING RULES:
- NILM = negative, no lesion, no dysplasia, within normal limits
- ASC-US = atypical squamous cells undetermined significance
- ASC-H = atypical squamous cannot exclude HSIL
- LSIL = low grade squamous intraepithelial lesion
- HSIL = high grade squamous intraepithelial lesion
- AGC = atypical glandular cells NOS
- AGC-ECX = atypical endocervical cells
- AGC-EMC = atypical endometrial cells
- AGC-NEO = atypical glandular cells favor neoplasia
- AIS = adenocarcinoma in situ
- MALIGNANT = carcinoma, invasive cancer, malignant cells
- OTHER (EMC45) = endometrial cells age 45 or older

Raw cytology text: "{raw_text}"

JSON only: {{"cytology_canonical": "...", "confidence": "high/medium/low"}}"""
    return call_llm(prompt)


def call_llm_histo(raw_text: str, valid_terms: list) -> dict:
    prompt = f"""You are a histopathology expert.
Map this raw histology diagnosis to ONE canonical term.

VALID TERMS: {json.dumps(valid_terms)}

MAPPING RULES:
- Benign / Inflammatory (Negative) = negative, benign, no CIN, reactive, normal
- LSIL (CIN1) = CIN1 ONLY, mild dysplasia, koilocytic change. NOT CIN2.
- HSIL (CIN2) = CIN2 ONLY, moderate dysplasia. NOT CIN1, NOT CIN3.
- HSIL (CIN3) = CIN3 ONLY, severe dysplasia, full thickness atypia, CIS. NOT CIN2.
- Squamous Cell Carcinoma = SCC, invasive squamous carcinoma
- Adenocarcinoma = invasive adenocarcinoma, glandular carcinoma

Raw histology text: "{raw_text}"

JSON only: {{"histology_canonical": "...", "confidence": "high/medium/low"}}"""
    return call_llm(prompt)


def normalize_cyto_sheet(
    df: pd.DataFrame,
    raw_diag_col: str,
    dictionary_path: str,
    model: str = "gemma3:4b"
) -> pd.DataFrame:
    valid_cyto = load_cyto_terms(dictionary_path)
    df = df.copy()

    texts  = df[raw_diag_col].astype(str).str.strip().tolist()
    unique = list(dict.fromkeys(texts))

    # Load persistent cache
    persistent_cache = load_cache()
    prefix           = "cyto_"

    already_cached = [t for t in unique if prefix + t in persistent_cache]
    needs_llm      = [t for t in unique if prefix + t not in persistent_cache]

    print(f"  Total    : {len(texts)}")
    print(f"  Unique   : {len(unique)}")
    print(f"  Cached   : {len(already_cached)} texts (instant)")
    print(f"  LLM calls: {len(needs_llm)} texts (new)")

    for i, text in enumerate(needs_llm):
        print(f"  [{i+1}/{len(needs_llm)}] {text[:60]}")
        result     = call_llm_cyto(text, valid_cyto)
        canonical  = result.get("cytology_canonical")
        confidence = result.get("confidence", "low")
        is_valid   = canonical in valid_cyto

        persistent_cache[prefix + text] = {
            "canonical":  canonical,
            "confidence": confidence,
            "valid":      is_valid
        }

    save_cache(persistent_cache)

    df["Cytology_Canonical"]  = [persistent_cache[prefix + t]["canonical"]  for t in texts]
    df["Cyto_LLM_Confidence"] = [persistent_cache[prefix + t]["confidence"] for t in texts]
    df["Cyto_Valid"]          = [persistent_cache[prefix + t]["valid"]       for t in texts]

    ready = df["Cyto_Valid"].sum()
    total = len(texts)
    print(f"\n-- Cyto Normalization: {ready}/{total} valid ({ready/total*100:.1f}%)")

    return df


def normalize_histo_sheet(
    df: pd.DataFrame,
    raw_diag_col: str,
    dictionary_path: str,
    model: str = "gemma3:4b"
) -> pd.DataFrame:
    valid_histo = load_histo_terms(dictionary_path)
    df = df.copy()

    texts  = df[raw_diag_col].astype(str).str.strip().tolist()
    unique = list(dict.fromkeys(texts))

    # Load persistent cache
    persistent_cache = load_cache()
    prefix           = "histo_"

    already_cached = [t for t in unique if prefix + t in persistent_cache]
    needs_llm      = [t for t in unique if prefix + t not in persistent_cache]

    print(f"  Total    : {len(texts)}")
    print(f"  Unique   : {len(unique)}")
    print(f"  Cached   : {len(already_cached)} texts (instant)")
    print(f"  LLM calls: {len(needs_llm)} texts (new)")

    for i, text in enumerate(needs_llm):
        print(f"  [{i+1}/{len(needs_llm)}] {text[:60]}")
        result     = call_llm_histo(text, valid_histo)
        canonical  = result.get("histology_canonical")
        confidence = result.get("confidence", "low")
        is_valid   = canonical in valid_histo

        persistent_cache[prefix + text] = {
            "canonical":  canonical,
            "confidence": confidence,
            "valid":      is_valid
        }

    save_cache(persistent_cache)

    df["Histology_Canonical"]  = [persistent_cache[prefix + t]["canonical"]  for t in texts]
    df["Histo_LLM_Confidence"] = [persistent_cache[prefix + t]["confidence"] for t in texts]
    df["Histo_Valid"]          = [persistent_cache[prefix + t]["valid"]       for t in texts]

    ready = df["Histo_Valid"].sum()
    total = len(texts)
    print(f"\n-- Histo Normalization: {ready}/{total} valid ({ready/total*100:.1f}%)")

    return df
