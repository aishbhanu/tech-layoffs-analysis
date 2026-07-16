"""
01_data_audit_and_cleaning.py
==============================
Phase 1: Data Audit → Document Issues → Clean → Validate

This script does exactly what a Data Quality professional does on a new dataset:
  STEP 1  Profile the raw data — shape, types, nulls, distributions
  STEP 2  Detect every quality issue — duplicates, inconsistencies, format errors
  STEP 3  Document issues BEFORE fixing them (the audit report)
  STEP 4  Apply fixes with clear before/after logging
  STEP 5  Validate the cleaned data
  STEP 6  Save cleaned CSV + written audit report

Run: python src/01_data_audit_and_cleaning.py
Output:
  data/cleaned/layoffs_clean.csv
  output/reports/data_audit_report.txt
"""

import os
import re
from datetime import datetime

import numpy as np
import pandas as pd

os.makedirs("data/cleaned", exist_ok=True)
os.makedirs("output/reports", exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: LOAD & PROFILE
# ─────────────────────────────────────────────────────────────────────────────

# The raw CSV uses the real layoffs.fyi/Kaggle column names, which don't match
# the lowercase snake_case names the rest of this pipeline was written against.
# Rename once at load time so every downstream step can stay unchanged.
RAW_COLUMN_MAP = {
    "Nr": "nr",
    "Company": "company",
    "Location_HQ": "location_hq",
    "Region": "region",
    "USState": "us_state",
    "Country": "country",
    "Continent": "continent",
    "Laid_Off": "total_laid_off",
    "Date_layoffs": "date",
    "Percentage": "percentage_laid_off",
    "Company_Size_before_Layoffs": "company_size_before",
    "Company_Size_after_layoffs": "company_size_after",
    "Industry": "industry",
    "Stage": "stage",
    "Money_Raised_in__mil": "funds_raised_millions",
    "Year": "year_reported",   # raw source's own Year column — kept for reference,
                                # but NOT trusted (see Issue: year_date_mismatch below).
                                # The canonical `year` column is always derived from `date`.
    "latitude": "latitude",
    "longitude": "longitude",
}


def load_and_profile(path):
    df = pd.read_csv(path, dtype=str)   # load everything as string — no silent casting
    df = df.rename(columns=RAW_COLUMN_MAP)
    df = df.where(df.notna(), other=None)   # normalise pandas NaN → None

    print("\n" + "="*60)
    print("STEP 1: RAW DATA PROFILE")
    print("="*60)
    print(f"  Shape             : {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"  Columns           : {list(df.columns)}")

    print("\n  Null counts per column:")
    for col in df.columns:
        n_null  = df[col].isna().sum()
        n_empty = (df[col] == "").sum() if df[col].dtype == object else 0
        total_missing = n_null + n_empty
        pct = round(total_missing / len(df) * 100, 1)
        print(f"    {col:<30} {total_missing:>4} missing ({pct}%)")

    return df


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: DETECT ISSUES
# ─────────────────────────────────────────────────────────────────────────────

def detect_issues(df):
    issues = {}

    # Issue 1: Exact duplicates
    n_dupes = df.duplicated().sum()
    issues["exact_duplicates"] = n_dupes

    # Issue 2: Near-duplicates (same company + date, different formatting)
    df["_company_stripped"] = df["company"].str.strip().str.lower()
    df["_date_stripped"]    = df["date"].str.strip()
    near_dupes = df.duplicated(subset=["_company_stripped", "_date_stripped"], keep=False)
    issues["near_duplicates"] = near_dupes.sum() - n_dupes * 2   # subtract exact ones

    # Issue 3: Rows where BOTH numeric columns are null
    both_null = (
        (df["total_laid_off"].isna()   | (df["total_laid_off"] == "")) &
        (df["percentage_laid_off"].isna() | (df["percentage_laid_off"] == ""))
    )
    issues["both_numeric_null"] = both_null.sum()

    # Issue 4: Inconsistent industry labels
    industries = df["industry"].dropna().str.strip().str.lower().unique()
    issues["unique_industry_raw"] = df["industry"].dropna().str.strip().nunique()

    # Issue 5: Inconsistent country names
    issues["unique_country_raw"] = df["country"].dropna().str.strip().nunique()

    # Issue 6: Mixed date formats (count non-ISO-format dates)
    iso_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    non_iso = df["date"].dropna().apply(lambda x: not bool(iso_pattern.match(str(x).strip())))
    issues["non_iso_dates"] = non_iso.sum()

    # Issue 7: Whitespace in company names
    has_whitespace = df["company"].dropna().apply(lambda x: x != x.strip())
    issues["company_whitespace"] = has_whitespace.sum()

    # Issue 8: Inconsistent stage labels
    issues["unique_stage_raw"] = df["stage"].dropna().str.strip().nunique()

    # Issue 9: Non-numeric values in numeric columns
    for col in ["total_laid_off", "percentage_laid_off"]:
        non_numeric = df[col].dropna().apply(
            lambda x: x != "" and not str(x).replace(".", "").replace("-", "").isnumeric()
        )
        issues[f"{col}_non_numeric"] = non_numeric.sum()

    # Issue 10: Funds raised with mixed formats ($, M, B, commas)
    fund_messy = df["funds_raised_millions"].dropna().apply(
        lambda x: bool(re.search(r"[$,MBb]", str(x)))
    )
    issues["funds_messy_format"] = fund_messy.sum()

    # Issue 11: Percentage values outside the valid 0–100 range
    pct_numeric = pd.to_numeric(df["percentage_laid_off"], errors="coerce")
    issues["percentage_out_of_range"] = ((pct_numeric < 0) | (pct_numeric > 100)).sum()

    # Issue 12: Source's own `year_reported` column disagrees with the year
    # implied by `date` (found in the real data — the raw Year field is not
    # reliable and should not be trusted downstream).
    derived_year = pd.to_datetime(df["date"], errors="coerce").dt.year
    year_reported_numeric = pd.to_numeric(df["year_reported"], errors="coerce")
    issues["year_date_mismatch"] = (derived_year != year_reported_numeric).sum()

    print("\n" + "="*60)
    print("STEP 2: ISSUES DETECTED")
    print("="*60)
    issue_descriptions = {
        "exact_duplicates":          "Exact duplicate rows",
        "near_duplicates":           "Near-duplicate rows (same company+date, diff formatting)",
        "both_numeric_null":         "Rows where BOTH total_laid_off AND percentage are null",
        "unique_industry_raw":       "Unique industry label variants (before standardisation)",
        "unique_country_raw":        "Unique country name variants (before standardisation)",
        "non_iso_dates":             "Dates not in ISO format (YYYY-MM-DD)",
        "company_whitespace":        "Company names with leading/trailing whitespace",
        "unique_stage_raw":          "Unique funding stage variants (before standardisation)",
        "total_laid_off_non_numeric":"Non-numeric values in total_laid_off",
        "percentage_laid_off_non_numeric": "Non-numeric values in percentage_laid_off",
        "funds_messy_format":        "Funds raised with $, M, B, or comma characters",
        "percentage_out_of_range":   "Percentage values outside the 0-100 range",
        "year_date_mismatch":        "Rows where source Year disagrees with date-derived year",
    }
    for key, desc in issue_descriptions.items():
        val = issues.get(key, 0)
        flag = " ← ACTION REQUIRED" if val > 0 else " ✓"
        print(f"  {desc:<55} {val:>4}{flag}")

    df.drop(columns=["_company_stripped", "_date_stripped"], inplace=True)
    return df, issues


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: CLEAN
# ─────────────────────────────────────────────────────────────────────────────

# ── Industry classification ────────────────────────────────────────────────
# The real raw data does NOT have simple abbreviation/casing variants of a
# fixed label set (that was the original assumption). Instead `Industry` is
# 118 distinct, mostly free-text descriptions written by different scrapers,
# e.g. "AI chip startup", "Autonomous-driving vehicles", "The Animation Tool
# for UI/UX Designers.", "cloud" vs "Cloud technology" vs "Cloud Technology
# Company". An exact-match lookup table would leave almost everything
# unmapped, so instead we classify by keyword, in priority order (first
# matching rule wins). Anything that matches nothing falls into "Other".
# NOTE: keyword roots that are prefixes of longer real words in this dataset
# (financ-e/ial, health-care, transport-ation, logistic-s, game-s,
# semiconductor-s, biotech-nology) use `\w*` instead of a trailing `\b`.
# The original version used `\bfinanc\b` etc., which only matches the exact
# word "financ" and NEVER matches "Finance" or "Financial Services" — that
# bug alone left ~300 Finance rows and ~200 Transportation rows sitting in
# "Other". Verified against the raw data: this drops Other from 860 to 192
# rows (36% -> 8%), and the 192 that remain are genuinely unclassifiable
# (raw value "Other" itself, plus vague labels "Product"/"Support").
INDUSTRY_RULES = [
    (r"\binsurance\w*\b",                                          "Insurance"),
    (r"\bcrypto\w*\b",                                             "Crypto / Web3"),
    (r"(^ai\b|\bchatbot\w*\b|\bmachine learning\b)",               "AI / Machine Learning"),
    (r"\b(fintech|financ\w*|banking)\b",                           "Fintech / Finance"),
    (r"\b(e-?commerce|retail\w*)\b",                               "E-commerce / Retail"),
    (r"\b(game\w*|gaming|e-?sport\w*)\b",                          "Gaming / Esports"),
    (r"\b(food|meat|catering)\b",                                  "Food"),
    (r"\b(automotive|vehicle\w*|driving|motor\w*|transport\w*|logistic\w*)\b", "Transportation / Automotive"),
    (r"\b(travel\w*|hospitality)\b",                               "Travel / Hospitality"),
    (r"\b(cyber\s?security|security|network\w*)\b",                "Cybersecurity"),
    (r"\b(hr|recruiting|employment|job search|freelance|worker skills)\b", "HR / Recruiting"),
    (r"\b(health\w*|biotech\w*|wellness|fitness)\b",               "Healthcare / Biotech"),
    (r"\b(education|e-learning|school\w*)\b",                      "Education"),
    (r"\b(media|social|video|entertainment|spectator|animation|translation|localization|conversation|sports?)\b", "Media / Social / Entertainment"),
    (r"\b(real estate|construction)\b",                            "Real Estate / Construction"),
    (r"\b(energy|environmental)\b",                                "Energy / Environmental"),
    (r"\blegal\b",                                                 "Legal"),
    (r"\b(marketing|advertising|sales)\b",                         "Marketing / Advertising / Sales"),
    (r"\b(hardware|electronics|semiconductor\w*|manufacturing|appliances|aerospace|memory)\b", "Hardware / Manufacturing"),
    (r"\b(venture capital|private equity)\b",                      "Venture Capital / Investment"),
    (r"\btelecommunication",                                       "Telecommunications"),
    (r"\b(cloud|saas|software|it services|infrastructure|enterprise|technology|internet|digital|data)\b", "Software / SaaS / Cloud"),
    (r"\b(consulting|outsourcing|business)\b",                     "Business Services / Consulting"),
    (r"\bconsumer\b",                                               "Consumer"),
]
INDUSTRY_RULES = [(re.compile(pattern), label) for pattern, label in INDUSTRY_RULES]


def classify_industry(raw):
    if pd.isna(raw) or str(raw).strip() == "":
        return "Unknown"
    text = str(raw).strip().lower()
    for pattern, label in INDUSTRY_RULES:
        if pattern.search(text):
            return label
    return "Other"


# ── Country standardisation ────────────────────────────────────────────────
# Real variants found in the raw data: "UK" alongside "United Kingdom", plus
# two scraping typos ("United Arabian Emirates", "Uruquay"). Everything else
# in the raw `Country` column is already a clean, full country name.
COUNTRY_MAP = {
    "usa": "United States",
    "uk": "United Kingdom",
    "united kingdom": "United Kingdom",
    "united arabian emirates": "United Arab Emirates",   # scraping typo
    "uruquay": "Uruguay",                                 # scraping typo
}

# ── Funding stage standardisation ──────────────────────────────────────────
# The real `Stage` column is already a clean, canonical set of 16 values
# (Seed, Series A-J, Post-IPO, Private Equity, Acquired, Subsidiary,
# Unknown). There are no casing/abbreviation variants to collapse here, so
# this map is intentionally an identity map — it exists to protect against
# the previous blind `.str.title()` fallback, which would have silently
# corrupted "Post-IPO" into "Post-Ipo".
STAGE_MAP = {
    "seed": "Seed",
    "series a": "Series A", "series b": "Series B", "series c": "Series C",
    "series d": "Series D", "series e": "Series E", "series f": "Series F",
    "series g": "Series G", "series h": "Series H", "series i": "Series I",
    "series j": "Series J",
    "post-ipo": "Post-IPO",
    "private equity": "Private Equity",
    "acquired": "Acquired",
    "subsidiary": "Subsidiary",
    "unknown": "Unknown",
}

DATE_FORMATS_PARSE = [
    "%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y",
    "%B %d, %Y", "%d %b %Y", "%d/%m/%Y",
]


def parse_date(date_str):
    if pd.isna(date_str) or str(date_str).strip() == "":
        return pd.NaT
    for fmt in DATE_FORMATS_PARSE:
        try:
            return datetime.strptime(str(date_str).strip(), fmt)
        except ValueError:
            continue
    return pd.NaT


def parse_funds(val):
    """Convert messy fund strings to float (millions)."""
    if pd.isna(val) or str(val).strip() == "":
        return np.nan
    s = str(val).strip().replace("$", "").replace(",", "")
    try:
        if s.upper().endswith("B"):
            return float(s[:-1]) * 1000
        if s.upper().endswith("M"):
            return float(s[:-1])
        return float(s)
    except ValueError:
        return np.nan


def clean(df):
    print("\n" + "="*60)
    print("STEP 3: CLEANING")
    print("="*60)
    original_rows = len(df)

    # Fix 1: Strip whitespace everywhere
    str_cols = df.select_dtypes(include="object").columns
    for col in str_cols:
        df[col] = df[col].str.strip()
    print(f"  [1] Stripped whitespace from all string columns")

    # Fix 2: Remove exact duplicates
    df.drop_duplicates(inplace=True)
    after_exact = len(df)
    print(f"  [2] Removed {original_rows - after_exact} exact duplicate rows "
          f"({original_rows} → {after_exact})")

    # Fix 3: Remove near-duplicates (same company + date after normalisation)
    # Real duplicate pairs found in this dataset (e.g. Ginkgo Bioworks
    # 2024-06-24, BeReal 2024-06-25) often have one row with a usable
    # total_laid_off value and one blank re-scrape of the same event. Sort so
    # the row WITH data comes first, then keep-first, so we don't
    # accidentally throw away the informative row.
    df["_key"] = df["company"].str.lower() + "|" + df["date"].str.strip()
    df = df.sort_values(
        by="total_laid_off",
        key=lambda s: s.isna(),   # False (has data) sorts before True (null)
        kind="stable",
    )
    before_near = len(df)
    df = df[~df.duplicated(subset=["_key"], keep="first")]
    df.drop(columns=["_key"], inplace=True)
    print(f"  [3] Removed {before_near - len(df)} near-duplicate rows "
          f"(same company+date, kept the more complete row, "
          f"{before_near} → {len(df)})")

    # Fix 4: Drop rows where BOTH numeric columns are empty
    both_null = (
        (df["total_laid_off"].isna() | (df["total_laid_off"] == "")) &
        (df["percentage_laid_off"].isna() | (df["percentage_laid_off"] == ""))
    )
    before_both = len(df)
    df = df[~both_null]
    print(f"  [4] Dropped {before_both - len(df)} rows with no layoff data at all "
          f"({before_both} → {len(df)})")

    # Fix 5: Classify free-text industry descriptions into canonical buckets
    df["industry"] = df["industry"].apply(classify_industry)
    n_other = (df["industry"] == "Other").sum()
    print(f"  [5] Classified industry → {df['industry'].nunique()} canonical categories "
          f"({n_other} rows fell into 'Other' — no keyword rule matched)")

    # Fix 6: Standardise country names (merge UK/United Kingdom, fix 2 typos)
    df["country"] = df["country"].str.lower().map(
        lambda x: COUNTRY_MAP.get(x, x.title()) if pd.notna(x) and x != "" else "Unknown"
    )
    print(f"  [6] Standardised country → {df['country'].nunique()} clean values")

    # Fix 7: Standardise funding stage
    # Real Stage values are already canonical (Seed, Series A-J, Post-IPO,
    # Private Equity, Acquired, Subsidiary, Unknown) — STAGE_MAP is an
    # identity map. Anything NOT in the map is unexpected/new and is labelled
    # "Unknown" rather than blindly title-cased (title() would corrupt
    # "Post-IPO" into "Post-Ipo").
    df["stage"] = df["stage"].str.lower().map(
        lambda x: STAGE_MAP.get(x, "Unknown") if pd.notna(x) and x != "" else "Unknown"
    )
    print(f"  [7] Standardised stage → {df['stage'].nunique()} clean values")

    # Fix 8: Parse all dates to YYYY-MM-DD
    df["date"] = df["date"].apply(parse_date)
    n_unparsed = df["date"].isna().sum()
    print(f"  [8] Parsed all dates to datetime "
          f"({n_unparsed} unparseable → NaT)")

    # Fix 9: Cast numeric columns
    df["total_laid_off"] = pd.to_numeric(df["total_laid_off"], errors="coerce")
    df["percentage_laid_off"] = pd.to_numeric(df["percentage_laid_off"], errors="coerce")
    for col in ["company_size_before", "company_size_after", "latitude", "longitude"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    print(f"  [9] Cast total_laid_off, percentage_laid_off, company size, "
          f"and lat/long to numeric")

    # Fix 10: Normalise funds_raised_millions
    df["funds_raised_millions"] = df["funds_raised_millions"].apply(parse_funds)
    print(f"  [10] Normalised funds_raised_millions to float (millions)")

    # Derive useful columns. `year` is always computed from the parsed date,
    # NEVER from the source's raw `year_reported` column — the real data has
    # 37 rows where the two disagree (see year_date_mismatch in the audit).
    df["year"]    = pd.to_datetime(df["date"]).dt.year
    df["month"]   = pd.to_datetime(df["date"]).dt.to_period("M").astype(str)
    df["quarter"] = pd.to_datetime(df["date"]).dt.to_period("Q").astype(str)
    n_year_fixed = (df["year"] != pd.to_numeric(df["year_reported"], errors="coerce")).sum()
    print(f"  [+] Derived year, month, quarter columns from date "
          f"({n_year_fixed} rows had a source year_reported that disagreed — date wins)")

    # Fix 11: Restore original row order (Fix 3's sort-for-dedup step
    # reordered rows to prefer complete records; put it back to source order).
    # `nr` was loaded as a string, so cast to numeric first — otherwise
    # sorting is lexicographic ("10" before "2") rather than numeric.
    df["nr"] = pd.to_numeric(df["nr"], errors="coerce")
    df = df.sort_values("nr").reset_index(drop=True)

    print(f"\n  Final shape: {len(df)} rows × {df.shape[1]} columns "
          f"(removed {original_rows - len(df)} rows total)")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4: VALIDATE
# ─────────────────────────────────────────────────────────────────────────────

def validate(df):
    print("\n" + "="*60)
    print("STEP 4: VALIDATION")
    print("="*60)
    checks = {
        "Zero exact duplicates":           df.duplicated().sum() == 0,
        "No rows with both numerics null": (
            df["total_laid_off"].isna() & df["percentage_laid_off"].isna()
        ).sum() == 0,
        "All dates parseable":             df["date"].isna().sum() == 0,
        "total_laid_off is numeric":       pd.api.types.is_numeric_dtype(df["total_laid_off"]),
        "percentage_laid_off is numeric":  pd.api.types.is_float_dtype(df["percentage_laid_off"]),
        "No leading/trailing whitespace":  not df["company"].str.match(r"^\s|\s$").any(),
        "Year column populated":           df["year"].notna().all(),
        "Percentage within 0-100 range":   df["percentage_laid_off"].dropna().between(0, 100).all(),
        "Stage values all canonical":      df["stage"].isin(list(STAGE_MAP.values()) + ["Unknown"]).all(),
    }
    all_pass = True
    for check, result in checks.items():
        status = "✓ PASS" if result else "✗ FAIL"
        if not result:
            all_pass = False
        print(f"  {status}  {check}")

    if all_pass:
        print("\n  All validation checks passed. Data is clean.")
    else:
        print("\n  ⚠  Some checks failed. Review cleaning logic.")
    return all_pass


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5: WRITE AUDIT REPORT
# ─────────────────────────────────────────────────────────────────────────────

def write_audit_report(raw_shape, clean_shape, issues, output_path):
    lines = [
        "=" * 65,
        "  DATA AUDIT REPORT — Tech Layoffs 2022–2025",
        f"  Generated: {datetime.now().strftime('%d %b %Y %H:%M')}",
        "=" * 65,
        "",
        "1. DATASET OVERVIEW",
        "-" * 40,
        f"  Source        : layoffs.fyi (via Kaggle)",
        f"  Raw records   : {raw_shape[0]}",
        f"  Clean records : {clean_shape[0]}",
        f"  Records removed: {raw_shape[0] - clean_shape[0]} "
          f"({round((raw_shape[0]-clean_shape[0])/raw_shape[0]*100,1)}%)",
        f"  Columns       : {raw_shape[1]}",
        "",
        "2. ISSUES FOUND",
        "-" * 40,
        "  Issue                                              Count",
    ]
    issue_descriptions = {
        "exact_duplicates":          "Exact duplicate rows",
        "near_duplicates":           "Near-duplicates (same company+date)",
        "both_numeric_null":         "Rows with no layoff count AND no percentage",
        "unique_industry_raw":       "Raw industry label variants (before clean)",
        "unique_country_raw":        "Raw country name variants (before clean)",
        "non_iso_dates":             "Dates not in ISO format",
        "company_whitespace":        "Company names with extra whitespace",
        "funds_messy_format":        "Funds values with $, M, B, or commas",
        "percentage_out_of_range":   "Percentage values outside 0-100 range",
        "year_date_mismatch":        "Rows where source Year disagrees with date",
    }
    for key, desc in issue_descriptions.items():
        val = issues.get(key, 0)
        lines.append(f"  {desc:<50} {val:>5}")

    lines += [
        "",
        "3. CLEANING ACTIONS TAKEN",
        "-" * 40,
        "  [1]  Stripped leading/trailing whitespace from all string columns",
        "  [2]  Removed exact duplicate rows",
        "  [3]  Removed near-duplicate rows (same company + date after normalisation)",
        "  [4]  Dropped rows where both total_laid_off and percentage_laid_off are null",
        "         → These rows contain no usable information",
        "  [5]  Classified 118 raw free-text industry descriptions into canonical",
        "       categories via keyword rules (not simple label variants —",
        "       e.g. 'Autonomous-driving vehicles', 'Motor Vehicle Manufacturing',",
        "       'Vehicle Cybersecurity' → 'Transportation / Automotive').",
        "       Unmatched descriptions are labelled 'Other', not silently dropped.",
        "  [6]  Standardised country names",
        "         e.g. 'UK' / 'United Kingdom' → 'United Kingdom' (merged)",
        "         e.g. 'United Arabian Emirates' (typo) → 'United Arab Emirates'",
        "         e.g. 'Uruquay' (typo) → 'Uruguay'",
        "  [7]  Verified funding stage labels against the canonical 16-value set",
        "       (Seed, Series A-J, Post-IPO, Private Equity, Acquired, Subsidiary,",
        "       Unknown). This field arrived already clean — no variants found —",
        "       so this step is a safety check, not a transformation.",
        "  [8]  Parsed date column to datetime",
        "       Dates arrived already in ISO format (YYYY-MM-DD) in this dataset;",
        "       the multi-format parser is kept as a defensive measure only.",
        "  [9]  Cast total_laid_off and percentage_laid_off to numeric (float)",
        "         Non-parseable values → NaN (preserved, not dropped)",
        "  [10] Normalised funds_raised_millions to float in millions",
        "       Values arrived already numeric in this dataset; parser kept",
        "       defensively in case future scrapes reintroduce '$2,400'/'2.4B' text.",
        "  [11] Derived year/month/quarter from date, ignoring the source's own",
        f"       year_reported column, which disagreed with date in "
          f"{issues.get('year_date_mismatch', 0)} raw rows.",
        "       Restored original row order (Nr) after the dedup sort.",
        "",
        "4. DATA QUALITY DIMENSIONS ASSESSED",
        "-" * 40,
        "  Completeness  : Null rates per column measured and documented",
        "  Uniqueness    : Exact and near-duplicate detection and removal",
        "                  (preferring the more complete row on conflict)",
        "  Consistency   : Industry, country, stage standardised to canonical values",
        "  Validity      : Dates parsed; numeric columns type-enforced",
        "  Accuracy      : Out-of-range values flagged (percentage outside 0-100)",
        "  Timeliness    : year_reported vs. date-derived year cross-checked "
          f"({issues.get('year_date_mismatch', 0)} disagreements found; "
          "date-derived year is authoritative)",
        "",
        "=" * 65,
    ]
    report = "\n".join(lines)
    with open(output_path, "w") as f:
        f.write(report)
    print("\n" + report)
    return report


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    RAW_PATH    = "data/raw/layoffs_raw.csv"
    CLEAN_PATH  = "data/cleaned/layoffs_clean.csv"
    REPORT_PATH = "output/reports/data_audit_report.txt"

    print("Tech Layoffs 2022–2025 — Data Audit & Cleaning Pipeline")
    print("=" * 60)

    df_raw = load_and_profile(RAW_PATH)
    raw_shape = df_raw.shape

    df_raw, issues = detect_issues(df_raw)
    df_clean = clean(df_raw.copy())
    validate(df_clean)

    df_clean.to_csv(CLEAN_PATH, index=False)
    print(f"\n  Cleaned data saved → {CLEAN_PATH}")

    write_audit_report(raw_shape, df_clean.shape, issues, REPORT_PATH)
    print(f"\n  Audit report saved → {REPORT_PATH}")
