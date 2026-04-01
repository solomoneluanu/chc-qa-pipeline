# CHC-QA Pipeline: Automated Cytology-Histology Correlation

## Overview
This project implements a deterministic, rule-based pipeline for automated cervical cytology-histology correlation (CHC) quality assurance.

The pipeline:
- normalizes LIS-derived diagnoses
- classifies cytology-histology pairs using explicit discrepancy rules
- computes QA metrics
- exports a structured Excel workbook
- generates figures
- builds a PDF report

## Project Structure

- `src/chc_pipeline/` - core pipeline modules
- `config/` - diagnosis dictionary and discrepancy rules
- `scripts/run_pipeline.py` - end-to-end pipeline runner
- `data/` - input and output files

## Requirements

 Add `requirements.txt`

Create this:

```txt
pandas
openpyxl
pyyaml
matplotlib
reportlab
