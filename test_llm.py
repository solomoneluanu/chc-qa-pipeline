import requests
import json

prompt = """You are a cytopathology expert.
Map these diagnoses to canonical terms.

VALID CYTOLOGY TERMS: ["NILM", "ASC-US", "ASC-H", "LSIL", "HSIL", "AGC", "AGC-ECX", "AGC-EMC", "AGC-NEO", "AIS", "MALIGNANT"]
VALID HISTOLOGY TERMS: ["Benign / Inflammatory (Negative)", "LSIL (CIN1)", "HSIL (CIN2)", "HSIL (CIN3)", "Squamous Cell Carcinoma", "Adenocarcinoma"]

Raw cytology: "NILLM"
Raw histology: "CIN 2"

Respond in JSON only:
{
  "cytology_canonical": "...",
  "histology_canonical": "..."
}"""

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "gemma3:4b",
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.0, "num_predict": 200}
    },
    timeout=60
)

raw = response.json()
print("RAW RESPONSE:")
print(raw["response"])
print()
print("PARSED:")
parsed = json.loads(raw["response"])
print(parsed)
