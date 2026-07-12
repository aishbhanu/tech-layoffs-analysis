# Tech Layoffs 2022–2025 — Real-World Messy Data Analysis
### Real-world data cleaning · Python · Pandas · Matplotlib · Claude AI-assisted development

An end-to-end data project on the global tech layoff wave, built on the
**real layoffs.fyi dataset (via Kaggle)**. This project demonstrates
professional-grade messy data handling, a structured audit pipeline,
and analytical insight generation — developed using **AI-assisted workflows with Claude Cowork**.

---

## Why this project exists

Most portfolio projects use clean, pre-processed datasets. Real-world data
never looks like that. This project works with the actual raw scrape from
layoffs.fyi and treats cleaning as the primary showcase — not something to
hide.

The raw dataset (2,412 rows, 18 columns, March 2020 – December 2025) contains:
- **15.4% nulls** in `total_laid_off` and **18.6% nulls** in `percentage_laid_off` (layoff counts not always publicly disclosed)
- **26.7% / 23.0% nulls** in company size before/after
- **118 raw industry descriptions** — mostly free text, not simple label variants (e.g. "AI chip startup", "Autonomous-driving vehicles", "The Animation Tool for UI/UX Designers.")
- **46 near-duplicate rows** (23 company+date pairs re-scraped from multiple sources, some with conflicting data completeness)
- **Country typos**: `UK` alongside `United Kingdom`, plus scraping typos `United Arabian Emirates` and `Uruquay`
- A source `Year` column that **disagrees with the actual event date in 37 rows** — not reliable on its own

Dates and funding amounts arrive already clean (ISO format, numeric) in this
dataset — the messiness here is nulls, free-text categorisation, near-duplicates,
and a handful of data-entry errors, rather than the "5 date formats /
`$2,400` strings" style of messiness often used in synthetic demo datasets.

---

## Project structure

```
tech-layoffs-analysis/
│
├── data/
│   ├── raw/
│   │   └── layoffs_raw.csv        ← Raw data (2,412 rows, real layoffs.fyi/Kaggle scrape)
│   └── cleaned/
│       └── layoffs_clean.csv      ← Cleaned data (2,229 rows, audit-verified)
│
├── src/
│   ├── 01_data_audit_and_cleaning.py    ← Phase 1: Audit → Detect → Clean → Validate
│   └── 02_analysis_and_visualisation.py ← Phase 2: Analysis + 9 charts + report
│
├── output/
│   ├── charts/                    ← 9 PNG charts
│   └── reports/
│       ├── data_audit_report.txt  ← Full DQ audit report
│       └── insight_report.txt     ← Analysis findings (computed from the data, not hardcoded)
│
├── AI_WORKFLOW.md                 ← How Claude Cowork was used in this project
├── HOW_IT_WORKS.md                ← Technical deep dive
├── SETUP_AND_RUN.md               ← Step-by-step run guide
├── requirements.txt
└── .gitignore
```

---

## Quickstart

```bash
git clone https://github.com/YOUR_USERNAME/tech-layoffs-analysis.git
cd tech-layoffs-analysis
pip install -r requirements.txt

# Step 1: Audit and clean the raw data (already included in data/raw/)
python src/01_data_audit_and_cleaning.py

# Step 2: Analyse and visualise
python src/02_analysis_and_visualisation.py
```

---

## What Phase 1 detects and fixes

| Issue | Count found | Fix applied |
|-------|------------|-------------|
| Exact duplicate rows | 0 | — (none found) |
| Near-duplicate rows (same company+date) | 46 (23 pairs) | Deduplicated, keeping the more complete row |
| Rows with no usable layoff data at all | 165 | Dropped |
| Raw industry descriptions | 118 → 25 | Classified into canonical categories by keyword rules (not exact-match lookup — the raw text is free-form) |
| Country name variants | 49 → 48 | `UK`/`United Kingdom` merged; 2 scraping typos fixed |
| Funding stage variants | 16 (already clean) | Verified against canonical set, not blindly re-cased |
| Source `Year` vs. date-derived year | 37 disagreements | Date-derived year used as authoritative |
| Company name whitespace | 1 | Stripped |

After cleaning: **2,412 → 2,229 rows** (183 removed, 7.6%). All 9 automated
validation checks pass (zero duplicates, no missing dates, percentages in
range, canonical stage values, etc.) — see `data_audit_report.txt`.

---

## What Phase 2 analyses

Phase 2 scopes to 2022–2025 (1,883 of the 2,229 cleaned rows; the raw data
goes back to March 2020, but that COVID-era window is outside this
project's analysis scope).

| Chart | What it shows |
|-------|--------------|
| 01. Layoffs by year | Total headcount cut per year 2022–2025 |
| 02. Monthly wave | Month-by-month trend across the full window |
| 03. Industry breakdown | Which sectors were hit hardest by volume and event count |
| 04. Country distribution | Geographic spread, India & UAE highlighted |
| 05. Funding stage analysis | Does funding stage predict layoff size? |
| 06. The funding paradox | Companies that raised billions vs. employees cut (log-scale scatter with auto-placed, non-overlapping labels) |
| 07. Layoff size distribution | Histogram + box plots by year |
| 08. India & UAE spotlight | Regional industry breakdown |
| 09. Serial layoffs | Top 10 companies by *number of separate layoff events*, not headcount — surfaces repeat/rolling layoffs a headcount chart can't show |

`insight_report.txt`'s "Key Findings" section is computed directly from
whatever data is loaded (not hardcoded prose), so it stays accurate if the
underlying dataset changes.

---

## AI-assisted development

This project was built using **Claude Cowork** as a development partner.
See `AI_WORKFLOW.md` for a full account of how AI tools were used —
including prompt design, iterative debugging, and validation strategy.

---

## Skills demonstrated

**Data Quality & Cleaning**
- Keyword-based classification for free-text categorical data (not simple label-variant mapping)
- Duplicate detection: exact + near-duplicate, preferring the more complete row on conflict
- Null strategy: preserve informative nulls, drop rows with no usable data
- Cross-field validation (source `Year` vs. date-derived year) to catch unreliable source columns
- Before/after audit documentation with a DQ dimension framework
- Defensive parsing kept for fields that are already clean, in case future data reintroduces messiness

**Analysis & Visualisation**
- Pandas: groupby, agg, pivot, reindex, method chaining
- Matplotlib: bar, line, scatter, histogram, boxplot, fill_between, log-scale axes
- `adjustText` for automatic, overlap-free scatter-plot labelling
- Seaborn: theming
- Domain insight: funding paradox, serial-layoffs analysis, regional breakdown

**Engineering Practices**
- Two-phase pipeline with clear separation of concerns
- Validation step with explicit pass/fail checks
- Structured, data-driven audit and insight reports
- Adjusted a cleaning pipeline originally written for one schema to match the real dataset's actual column names, issue types, and edge cases

**AI-Assisted Development**
- Claude Cowork used for architecture design, code review, and debugging
- Prompt engineering for code generation and iteration
- AI workflow documented transparently in `AI_WORKFLOW.md`

---

## Data source

Uses the real layoffs.fyi dataset (via Kaggle): 2,412 records, March 2020 – December 2025.
Available on Kaggle: [Tech Layoffs 2020–2025](https://www.kaggle.com/datasets/ulrikeherold/tech-layoffs-2020-2024)
Free to use with attribution to layoffs.fyi.

---

## Requirements

```
pandas>=2.0.0
matplotlib>=3.7.0
seaborn>=0.12.0
numpy>=1.24.0
adjustText>=0.8
```
