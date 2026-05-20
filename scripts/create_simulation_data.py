import pandas as pd
import random
from datetime import datetime, timedelta

random.seed(42)

CYTO_RAW = [
    "NEGATIVE FOR INTRAEPITHELIAL LESION OR MALIGNANCY",
    "Satisfactory for evaluation. Negative for intraepithelial lesion or malignancy (NILM).",
    "NILM. Endocervical/transformation zone component present.",
    "Negative. No significant atypia identified.",
    "Within normal limits. Mild inflammatory changes noted.",
    "No malignant cells identified. Reactive cellular changes.",
    "NILLM",
    "Neg for malignancy",
    "ATYPICAL SQUAMOUS CELLS OF UNDETERMINED SIGNIFICANCE (ASC-US)",
    "ASC-US. Cannot exclude low grade squamous intraepithelial lesion.",
    "Atypical squamous cells, undetermined significance. Reflex HPV testing recommended.",
    "ASCUS",
    "LOW GRADE SQUAMOUS INTRAEPITHELIAL LESION (LSIL)",
    "LSIL. Consistent with HPV effect/CIN 1.",
    "Low-grade squamous intraepithelial lesion. Koilocytic atypia present.",
    "lsil",
    "HIGH GRADE SQUAMOUS INTRAEPITHELIAL LESION (HSIL)",
    "HSIL. Features consistent with CIN 2-3. Colposcopy recommended.",
    "High grade squamous intraepithelial lesion. Cannot exclude invasion.",
    "HSIL - SEE COMMENT. Correlate with clinical findings.",
    "HGSIL",
    "ATYPICAL SQUAMOUS CELLS, CANNOT EXCLUDE HSIL (ASC-H)",
    "ASC-H. High grade lesion cannot be excluded. Colposcopy recommended.",
    "ATYPICAL GLANDULAR CELLS (AGC), NOT OTHERWISE SPECIFIED",
    "Atypical glandular cells, favor neoplasia. Further evaluation recommended.",
    "AGC-NEO. Endocervical adenocarcinoma in situ cannot be excluded.",
    "MALIGNANT CELLS PRESENT. Features consistent with squamous cell carcinoma.",
    "Positive for malignancy. Adenocarcinoma cannot be excluded.",
    "AIS. Adenocarcinoma in situ identified.",
    "Endometrial cells present in woman age 45 or older.",
]

HISTO_RAW = [
    "Benign cervical squamous and endocervical mucosa. No dysplasia identified.",
    "Cervical biopsy: reactive squamous epithelium. No CIN.",
    "Chronic cervicitis. Squamous metaplasia. No significant atypia.",
    "Benign findings. Transformation zone adequately sampled.",
    "Negative. No intraepithelial lesion identified.",
    "Cervical intraepithelial neoplasia, grade 1 (CIN 1/LSIL).",
    "CIN 1. Koilocytic atypia consistent with HPV effect.",
    "Low grade CIN (CIN 1). Changes limited to lower third of epithelium.",
    "Mild dysplasia consistent with CIN 1.",
    "Cervical intraepithelial neoplasia, grade 2 (CIN 2/HSIL).",
    "CIN 2. Atypia involving lower two thirds of epithelial thickness.",
    "Moderate dysplasia (CIN 2). Ectocervical margin uninvolved.",
    "CIN 2-3. Cannot exclude higher grade lesion.",
    "Cervical intraepithelial neoplasia, grade 3 (CIN 3/HSIL).",
    "CIN 3. Full thickness epithelial atypia. Numerous mitotic figures.",
    "Severe dysplasia/carcinoma in situ (CIN 3). Margins involved.",
    "High grade CIN (CIN 2-3). Cannot exclude early invasion.",
    "Invasive squamous cell carcinoma, moderately differentiated.",
    "Squamous cell carcinoma. Stromal invasion present.",
    "Invasive adenocarcinoma, endocervical type.",
    "Adenocarcinoma. Glandular invasion present.",
]

def random_date(start_year=2023, end_year=2024):
    start = datetime(start_year, 1, 1)
    end   = datetime(end_year, 12, 31)
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))

def random_histo_date(cyto_date, max_days=180):
    delay = random.randint(7, max_days)
    return cyto_date + timedelta(days=delay)

n_patients = 150
patient_ids = [f"PT{str(i).zfill(5)}" for i in range(1, n_patients + 1)]

cyto_records = []
cyto_dates = {}

for pid in patient_ids:
    cyto_date = random_date()
    cyto_dates[pid] = cyto_date

    cyto_records.append({
        "Patient_ID":            pid,
        "Cytology_Accession_No": f"CYT-{random.randint(10000,99999)}",
        "Collection_Date":       cyto_date.strftime(
                                     random.choice([
                                         "%Y-%m-%d",
                                         "%m/%d/%Y",
                                         "%d-%b-%Y"
                                     ])
                                 ),
        "Pap_Result":            random.choice(CYTO_RAW),
        "Specimen_Adequacy":     random.choice([
                                     "Satisfactory",
                                     "Satisfactory for evaluation",
                                     "Unsatisfactory",
                                     "Adequate"
                                 ]),
        "Specimen_Type":         random.choice([
                                     "ThinPrep", "SurePath",
                                     "Conventional", "LBC"
                                 ]),
        "Ordering_Physician":    f"Dr. {random.choice(['Smith','Jones','Patel','Lee','Kim'])}",
        "Lab_Location":          random.choice(["Main Lab", "Outpatient", "Clinic A"]),
    })

cyto_df = pd.DataFrame(cyto_records)

histo_records = []
matched_patients = random.sample(patient_ids, 130)

for pid in matched_patients:
    cyto_date  = cyto_dates[pid]
    histo_date = random_histo_date(cyto_date)

    histo_records.append({
        "Pt_ID":            pid,
        "Surgical_Path_No": f"SP-{random.randint(10000,99999)}",
        "Procedure_Date":   histo_date.strftime(
                                random.choice([
                                    "%Y-%m-%d",
                                    "%m/%d/%Y",
                                ])
                            ),
        "Final_Diagnosis":  random.choice(HISTO_RAW),
        "Procedure_Type":   random.choice([
                                "Cervical biopsy",
                                "Punch biopsy",
                                "Cone biopsy",
                                "LEEP",
                                "ECC"
                            ]),
        "Pathologist":      f"Dr. {random.choice(['Brown','White','Green','Black'])}",
        "Department":       random.choice(["Surgical Pathology", "GYN Path"]),
    })

histo_df = pd.DataFrame(histo_records)

output_path = "data/input-data/real_lab_simulation.xlsx"

with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
    cyto_df.to_excel(writer,  sheet_name="Cytology",  index=False)
    histo_df.to_excel(writer, sheet_name="Histology", index=False)

print(f"Created: {output_path}")
print(f"Cyto sheet  : {len(cyto_df)} rows")
print(f"Histo sheet : {len(histo_df)} rows")
print(f"Unmatched   : {n_patients - len(matched_patients)} cyto cases have no histo")
