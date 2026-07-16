# Setup & Run Guide
## Step-by-step from zero to working project

---

## Prerequisites

Python 3.9+:
```bash
python --version
```

---

## Step 1 — Get the code

```bash
git clone https://github.com/YOUR_USERNAME/tech-layoffs-analysis.git
cd tech-layoffs-analysis
```

---

## Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

Using a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

---

## Step 3 — Generate the raw messy dataset

```bash
python data/generate_messy_data.py
```

Expected output:
```
Generated 945 records → data/raw/layoffs_raw.csv
```

Open `data/raw/layoffs_raw.csv` in Excel before cleaning —
you'll see the mixed dates, inconsistent labels, and missing values.

---

## Step 4 — Run Phase 1: Audit & Cleaning

```bash
python src/01_data_audit_and_cleaning.py
```

You'll see a full terminal report showing every issue found and every fix applied.
Outputs:
- `data/cleaned/layoffs_clean.csv` — the clean dataset
- `output/reports/data_audit_report.txt` — the written audit report

---

## Step 5 — Run Phase 2: Analysis

```bash
python src/02_analysis_and_visualisation.py
```

Outputs:
- `output/charts/` — 8 PNG charts
- `output/reports/insight_report.txt` — written findings

---

## Step 6 — Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: Tech Layoffs 2022-2025 messy data analysis"
git remote add origin https://github.com/YOUR_USERNAME/tech-layoffs-analysis.git
git branch -M main
git push -u origin main
```

Good commit messages for future changes:
```
Add near-duplicate detection logic
Fix funds parsing for B/M suffix formats
Add India UAE regional spotlight chart
Update audit report format
```

---

## Want to use the real dataset?

Download from Kaggle:
https://www.kaggle.com/datasets/ulrikeherold/tech-layoffs-2020-2024

Save as `data/raw/layoffs_raw.csv` (same filename).
The cleaning script works on both the synthetic and real dataset
since they share the same schema and messiness patterns.

---

## Common errors

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `FileNotFoundError: layoffs_raw.csv` | Run `python data/generate_messy_data.py` first |
| `FileNotFoundError: layoffs_clean.csv` | Run Phase 1 before Phase 2 |
| Charts not showing | They save to `output/charts/` — open the PNGs there |
