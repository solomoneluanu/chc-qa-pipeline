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

## Data

The `data/` directory contains example input data for demonstration and testing.

- `data/input/evaluation_01_input.xlsx` — sample dataset formatted as LIS export

Users can run the pipeline on this file to reproduce results.

All outputs (Excel reports, figures, and PDF summaries) will be automatically generated in:

- `data/output/`

No real patient data is included.

## Usage

Run the pipeline with:

```bash
python scripts/run_pipeline.py

## Requirements

This project requires Python 3.9 or higher.

Install dependencies using:

```bash
pip install -r requirements.txt
