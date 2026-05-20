import requests
import json
import yaml

with open("config/diagnosis_dictionary.yaml") as f:
    mapping = yaml.safe_load(f)

valid_cyto = list(set(mapping["cytology_raw_to_canonical"].values()))

texts = ["NILM", "HSIL", "High grade squamous lesion"]
cases = [{"id": i, "text": t} for i, t in enumerate(texts)]

prompt = f"""You are a cytopathology expert.
Map each raw cytology diagnosis to ONE canonical term.

VALID TERMS: {json.dumps(valid_cyto)}

Cases:
{json.dumps(cases, indent=2)}

Return a JSON array:
[{{"id": 0, "cytology_canonical": "..."}}, ...]

JSON array only."""

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "gemma3:4b",
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.0, "num_predict": 300}
    },
    timeout=120
)

raw = response.json()["response"]
print("RAW RESPONSE:")
print(raw)
print()
parsed = json.loads(raw)
print("PARSED TYPE:", type(parsed))
print("PARSED:", parsed)
