import json
import os
import requests
import pandas as pd

def load_cyto_terms(dictionary_path: str) -> list:
    import yaml
    with open(dictionary_path, "r") as f:
        mapping = yaml.safe_load(f)
    return list(set(mapping["cytology_raw_to_canonical"].values()))


def load_histo_terms(dictionary_path: str) -> list:
    import yaml
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
def call_claude_api(prompt: str) -> dict:
    """
    Call Claude Haiku API as fallback when Ollama unavailable.
    Requires ANTHROPIC_API_KEY environment variable.
    """
    import re
    try:
        import anthropic
    except ImportError:
        return {"error": "anthropic package not installed"}

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not set"}

    try:
        client  = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = message.content[0].text.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {"error": f"Could not parse: {raw[:100]}"}
    except Exception as e:
        return {"error": str(e)}


def call_llm_or_claude(prompt: str, model: str = "gemma3:4b") -> dict:
    """
    Try Ollama first. Fall back to Claude Haiku if unavailable.
    Enables both local HIPAA-compliant and cloud deployment.
    """
    result = call_llm(prompt, model)
    if not result or "error" in result:
        result = call_claude_api(prompt)
    return result

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
    return call_llm_or_claude(prompt, model)


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
    return call_llm_or_claude(prompt, model)


CACHE_FILE = "data/llm_cache.json"

def load_cache():
    """Load persistent LLM cache from disk."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    """Save LLM cache to disk."""
    os.makedirs("data", exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def normalize_cyto_sheet(df, raw_diag_col, dictionary_path, model="gemma3:4b"):
    valid_cyto = load_cyto_terms(dictionary_path)
    df = df.copy()

    texts  = df[raw_diag_col].astype(str).str.strip().tolist()
    unique = list(dict.fromkeys(texts))

    # Load persistent cache
    persistent_cache = load_cache()
    cache_key_prefix = "cyto_"

    already_cached = [t for t in unique if cache_key_prefix + t in persistent_cache]
    needs_llm      = [t for t in unique if cache_key_prefix + t not in persistent_cache]

    print(f"  Total    : {len(texts)}")
    print(f"  Unique   : {len(unique)}")
    print(f"  Cached   : {len(already_cached)} (no LLM call needed)")
    print(f"  LLM calls: {len(needs_llm)}")

    # Only call LLM for uncached texts
    for i, text in enumerate(needs_llm):
        print(f"  [{i+1}/{len(needs_llm)}] {text[:60]}")
        result     = call_llm_cyto(text, valid_cyto)
        canonical  = result.get("cytology_canonical")
        confidence = result.get("confidence", "low")
        is_valid   = canonical in valid_cyto

        persistent_cache[cache_key_prefix + text] = {
            "canonical":  canonical,
            "confidence": confidence,
            "valid":      is_valid
        }

    # Save updated cache
    save_cache(persistent_cache)

    # Build results from cache
    df["Cytology_Canonical"]  = [
        persistent_cache[cache_key_prefix + t]["canonical"]  for t in texts
    ]
    df["Cyto_LLM_Confidence"] = [
        persistent_cache[cache_key_prefix + t]["confidence"] for t in texts
    ]
    df["Cyto_Valid"]          = [
        persistent_cache[cache_key_prefix + t]["valid"]      for t in texts
    ]

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
    """
    Normalize histology sheet with cache.
    One LLM call per unique text - duplicates are free.
    """
    valid_histo = load_histo_terms(dictionary_path)
    df = df.copy()

    texts  = df[raw_diag_col].astype(str).str.strip().tolist()
    unique = list(dict.fromkeys(texts))

    print(f"  Total    : {len(texts)}")
    print(f"  Unique   : {len(unique)} (cache saves {len(texts) - len(unique)} LLM calls)")

    cache = {}
    for i, text in enumerate(unique):
        print(f"  [{i+1}/{len(unique)}] {text[:60]}")
        result     = call_llm_histo(text, valid_histo)
        canonical  = result.get("histology_canonical")
        confidence = result.get("confidence", "low")
        is_valid   = canonical in valid_histo
        cache[text] = {
            "canonical":  canonical,
            "confidence": confidence,
            "valid":      is_valid
        }

    df["Histology_Canonical"]  = [cache[t]["canonical"]  for t in texts]
    df["Histo_LLM_Confidence"] = [cache[t]["confidence"] for t in texts]
    df["Histo_Valid"]          = [cache[t]["valid"]       for t in texts]

    ready = sum(cache[t]["valid"] for t in texts)
    total = len(texts)
    print(f"\n-- Histo Normalization: {ready}/{total} valid ({ready/total*100:.1f}%)")

    return df
