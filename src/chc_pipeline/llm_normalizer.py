import os
import json
import re
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
    import os
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


def parse_llm_response(raw_response: str, result_key: str) -> dict:
    """
    Fix 2: Robust JSON parsing.
    Handles conversational text before/after JSON,
    markdown code blocks, and malformed responses.
    """
    text = raw_response.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    code_block = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if code_block:
        try:
            return json.loads(code_block.group(1))
        except json.JSONDecodeError:
            pass

    # Try extracting any JSON object from text
    json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Failed to parse
    return {"error": f"Could not parse JSON from: {text[:100]}"}


def call_llm(prompt: str, model: str = "gemma3:4b") -> dict:
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.0, "num_predict": 150}
            },
            timeout=120
        )
        response.raise_for_status()
        raw = response.json()["response"]
        return parse_llm_response(raw, "")
    except Exception as e:
        return {"error": str(e)}


def call_llm_cyto(raw_text: str, valid_terms: list) -> dict:
    """
    Fix 1: Clarified cannot-exclude rule
    Fix 3: Added UNMAPPABLE category
    Fix 4: Chain-of-thought reasoning field
    """
    valid_with_unmappable = valid_terms + ["UNMAPPABLE"]

    prompt = f"""You are a cytopathology expert performing LIS data normalization.
Map this raw cytology diagnosis to ONE canonical term.

VALID TERMS: {json.dumps(valid_with_unmappable)}

MAPPING RULES:
- NILM = negative, no lesion, no dysplasia, within normal limits
- ASC-US = atypical SQUAMOUS cells undetermined significance
- ASC-H = atypical SQUAMOUS cells cannot exclude HSIL
- LSIL = low grade squamous intraepithelial lesion
- HSIL = high grade squamous intraepithelial lesion
- AGC = atypical GLANDULAR cells NOS
- AGC-ECX = ONLY when text explicitly says atypical ENDOCERVICAL cells
- AGC-EMC = ONLY when text explicitly says atypical ENDOMETRIAL cells
- AGC-NEO = atypical glandular cells favor neoplasia
- AIS = adenocarcinoma in situ
- MALIGNANT = confirmed invasive carcinoma or malignant cells PRESENT
- OTHER (EMC45) = endometrial cells in woman age 45 or older
- UNMAPPABLE = non-diagnostic text, administrative note, broken data

CRITICAL RULES:

RULE 1 - SQUAMOUS vs GLANDULAR:
Atypical SQUAMOUS cells = ASC-US or ASC-H only.
Atypical GLANDULAR cells = AGC variants only.
Never confuse squamous with glandular. These are different cell types.

RULE 2 - CANNOT EXCLUDE:
'Cannot exclude' means the PRIMARY diagnosis is still the main finding.
'HSIL, cannot exclude invasion' = HSIL (invasion not confirmed)
'LSIL, cannot exclude HSIL' = ASC-H (upgrading concern, use ASC-H)
'NILM, cannot exclude LSIL' = ASC-US (minor concern)
Exception: If text says 'malignant cells cannot be excluded' = MALIGNANT

RULE 3 - AGC SUBTYPES:
Use AGC-ECX ONLY when primary diagnosis is 'atypical endocervical cells'
Use AGC-EMC ONLY when primary diagnosis is 'atypical endometrial cells'
If text mentions endocervical in context but diagnosis is AGC = use AGC
Default to AGC when subtype is ambiguous

RULE 4 - MALIGNANT:
Use MALIGNANT only for CONFIRMED invasive carcinoma or explicit
'malignant cells present' statements.
'Cannot exclude malignancy' alone does NOT equal MALIGNANT.

RULE 5 - UNMAPPABLE:
Use UNMAPPABLE for:
- Specimen collection errors (broken, insufficient)
- Administrative notes (see addendum, refer to report)
- Non-diagnostic text (patient name, date, accession only)
- Text with no cytopathology diagnosis content

Raw cytology text: "{raw_text}"

Think step by step:
1. What is the primary diagnosis in this text?
2. Which RULE applies?
3. What is the canonical term?

JSON only: {{"reasoning": "brief explanation", "cytology_canonical": "...", "confidence": "high/medium/low"}}"""

    return call_llm(prompt)


def call_llm_histo(raw_text: str, valid_terms: list) -> dict:
    """
    Fix 1: Clarified CIN 2-3 ambiguity rule
    Fix 3: Added UNMAPPABLE category
    Fix 4: Chain-of-thought reasoning field
    """
    valid_with_unmappable = valid_terms + ["UNMAPPABLE"]

    prompt = f"""You are a histopathology expert performing LIS data normalization.
Map this raw histology diagnosis to ONE canonical term.

VALID TERMS: {json.dumps(valid_with_unmappable)}

MAPPING RULES:
- Benign / Inflammatory (Negative) = negative, benign, no CIN, reactive, normal
- LSIL (CIN1) = CIN1 ONLY, mild dysplasia, koilocytic change
- HSIL (CIN2) = CIN2 ONLY, moderate dysplasia
- HSIL (CIN3) = CIN3 ONLY, severe dysplasia, full thickness atypia, CIS
- Squamous Cell Carcinoma = invasive SCC confirmed
- Adenocarcinoma = invasive adenocarcinoma confirmed
- UNMAPPABLE = non-diagnostic, administrative, broken data

CRITICAL RULES:

RULE 1 - CIN GRADE PRECISION:
CIN 1 = LSIL (CIN1). Do NOT upgrade to CIN2.
CIN 2 = HSIL (CIN2). Do NOT upgrade to CIN3.
CIN 3 = HSIL (CIN3). Do NOT downgrade to CIN2.
Each CIN grade maps to exactly one canonical term.

RULE 2 - CIN 2-3 AMBIGUITY:
When text says 'CIN 2-3' or 'CIN2-3':
- If text says 'cannot exclude higher grade' = HSIL (CIN3)
- If text says 'at least CIN 2' = HSIL (CIN2)
- If no qualifier = HSIL (CIN2) as conservative default
- If text says 'favor CIN 3' = HSIL (CIN3)

RULE 3 - INVASION:
'Cannot exclude invasion' in CIN context = still map to CIN grade
Only use Squamous Cell Carcinoma when invasion is CONFIRMED
'High grade CIN, cannot exclude early invasion' = HSIL (CIN3)

RULE 4 - BENIGN:
Any reactive, inflammatory, metaplastic, or no-dysplasia finding
= Benign / Inflammatory (Negative)
Squamous metaplasia alone = Benign / Inflammatory (Negative)

RULE 5 - UNMAPPABLE:
Use UNMAPPABLE for non-diagnostic text, administrative notes,
collection errors, or text with no histopathology diagnosis.

Raw histology text: "{raw_text}"

Think step by step:
1. What CIN grade or diagnosis is stated?
2. Are there any qualifiers that change the grade?
3. What is the canonical term?

JSON only: {{"reasoning": "brief explanation", "histology_canonical": "...", "confidence": "high/medium/low"}}"""

    return call_llm(prompt)


def normalize_cyto_sheet(
    df: pd.DataFrame,
    raw_diag_col: str,
    dictionary_path: str,
    model: str = "gemma3:4b"
) -> pd.DataFrame:
    import os
    valid_cyto = load_cyto_terms(dictionary_path)
    df = df.copy()

    texts  = df[raw_diag_col].astype(str).str.strip().tolist()
    unique = list(dict.fromkeys(texts))

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
        reasoning  = result.get("reasoning", "")
        is_valid   = canonical in valid_cyto or canonical == "UNMAPPABLE"

        persistent_cache[prefix + text] = {
            "canonical":  canonical,
            "confidence": confidence,
            "reasoning":  reasoning,
            "valid":      is_valid
        }

    save_cache(persistent_cache)

    df["Cytology_Canonical"]  = [persistent_cache[prefix + t].get("canonical")  for t in texts]
    df["Cyto_LLM_Confidence"] = [persistent_cache[prefix + t].get("confidence", "low") for t in texts]
    df["Cyto_LLM_Reasoning"]  = [persistent_cache[prefix + t].get("reasoning", "") for t in texts]
    df["Cyto_Valid"]          = [persistent_cache[prefix + t].get("valid", False) for t in texts]

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
    import os
    valid_histo = load_histo_terms(dictionary_path)
    df = df.copy()

    texts  = df[raw_diag_col].astype(str).str.strip().tolist()
    unique = list(dict.fromkeys(texts))

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
        reasoning  = result.get("reasoning", "")
        is_valid   = canonical in valid_histo or canonical == "UNMAPPABLE"

        persistent_cache[prefix + text] = {
            "canonical":  canonical,
            "confidence": confidence,
            "reasoning":  reasoning,
            "valid":      is_valid
        }

    save_cache(persistent_cache)

    df["Histology_Canonical"]  = [persistent_cache[prefix + t].get("canonical")  for t in texts]
    df["Histo_LLM_Confidence"] = [persistent_cache[prefix + t].get("confidence", "low") for t in texts]
    df["Histo_LLM_Reasoning"]  = [persistent_cache[prefix + t].get("reasoning", "") for t in texts]
    df["Histo_Valid"]          = [persistent_cache[prefix + t].get("valid", False) for t in texts]

    ready = df["Histo_Valid"].sum()
    total = len(texts)
    print(f"\n-- Histo Normalization: {ready}/{total} valid ({ready/total*100:.1f}%)")

    return df
