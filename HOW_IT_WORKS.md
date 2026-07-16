# How It Works — Tech Layoffs 2022–2025
## Technical Deep Dive: Every Decision Explained

---

## Overall design: why two separate scripts?

Most tutorials put cleaning and analysis in one script.
This project separates them deliberately:

```
01_data_audit_and_cleaning.py   →   data/cleaned/layoffs_clean.csv
02_analysis_and_visualisation.py  ←  reads cleaned data
```

**Why this matters:**
- You can re-run the analysis many times without re-running the cleaning
- The cleaning step produces an audit report — a deliverable in its own right
- It mirrors how production data pipelines work: ETL → analytics are separate layers
- If the source data updates, you re-run only Phase 1

---

## Phase 1 — The Audit Pipeline

### Why load everything as `dtype=str`?

```python
df = pd.read_csv(path, dtype=str)
```

Pandas is helpful by default — it infers types. But inference hides problems.
If `total_laid_off` has mostly numbers but some strings like "Unknown", pandas
silently converts the whole column to object type. You lose the numbers without
knowing it.

Loading as string forces you to be explicit about every type conversion.
This is defensive coding — the same principle as defensive driving.

### The four categories of data quality issues

**Completeness** — is the data there?
```python
n_null  = df[col].isna().sum()
n_empty = (df[col] == "").sum()
total_missing = n_null + n_empty
```
Nulls and empty strings are both "missing". A blank cell and a `NaN`
are the same problem — you must check for both.

**Uniqueness** — is the data duplicated?
Two types of duplicates exist:
1. Exact duplicates: byte-for-byte identical rows (from scraping the same source twice)
2. Near-duplicates: same event, slightly different formatting (from two sources)

```python
# Exact: pandas built-in
df.drop_duplicates(inplace=True)

# Near: normalise first, then compare
df["_key"] = df["company"].str.lower() + "|" + df["date"].str.strip()
df = df[~df.duplicated(subset=["_key"], keep="first")]
```

The `_key` column creates a normalised fingerprint per row.
Two rows with "Amazon" and " Amazon" produce the same key after `.lower()`.

**Consistency** — does the same thing have the same name?
This is the hardest problem in real data. The industry standardisation
uses an explicit lookup table:
```python
INDUSTRY_MAP = {
    "fintech": "Finance",
    "financial services": "Finance",
    "finance": "Finance",
    ...
}
df["industry"] = df["industry"].str.lower().map(
    lambda x: INDUSTRY_MAP.get(x, "Other") if pd.notna(x) else "Unknown"
)
```
Why a dictionary map instead of `str.replace()`?
`str.replace()` does substring matching — it might match "Healthcare Finance"
and incorrectly reclassify it. A dictionary only matches the full normalised string.

**Validity** — is the data in the right format?
Date parsing is the clearest example:
```python
DATE_FORMATS_PARSE = [
    "%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y",
    "%B %d, %Y", "%d %b %Y", "%d/%m/%Y",
]

def parse_date(date_str):
    for fmt in DATE_FORMATS_PARSE:
        try:
            return datetime.strptime(str(date_str).strip(), fmt)
        except ValueError:
            continue
    return pd.NaT
```
Try each format in order. Return `NaT` (Not a Time) on failure rather than raising.
`NaT` is pandas' null for datetime — it propagates correctly through date operations.

### Why drop rows where BOTH numerics are null?

```python
both_null = (
    (df["total_laid_off"].isna() | (df["total_laid_off"] == "")) &
    (df["percentage_laid_off"].isna() | (df["percentage_laid_off"] == ""))
)
df = df[~both_null]
```

A row with no layoff count AND no percentage tells you nothing about the layoff.
It only tells you a layoff happened at some company on some date.
That's not enough for any analysis. Dropping it is correct.

A row with ONLY `total_laid_off` null is kept — the percentage still tells you
something (e.g. 30% of the company was cut, even if the absolute number is unknown).

### The funds parsing function

```python
def parse_funds(val):
    s = str(val).strip().replace("$", "").replace(",", "")
    if s.upper().endswith("B"):
        return float(s[:-1]) * 1000   # convert billions to millions
    if s.upper().endswith("M"):
        return float(s[:-1])
    return float(s)
```

This handles: `"$2,400"` → `2400.0`, `"2.4B"` → `2400.0`, `"$2400M"` → `2400.0`.
All three represent the same value: $2.4 billion = 2,400 million.

Order matters: check for "B" before "M" because "1.2B" ends with "B" not "M".

---

## Phase 2 — Analysis

### Why `df.groupby("year")["total_laid_off"].sum().dropna()`?

The `.dropna()` is important here. `sum()` on a column with NaN values
includes the NaN groups in the output by default, but `NaN` years (from
unparseable dates) would produce a meaningless category. `.dropna()` removes it.

### The funding paradox scatter (Chart 6)

```python
paradox = (df[df["funds_raised_millions"].notna() & df["total_laid_off"].notna()]
           .groupby("company")
           .agg(funds=("funds_raised_millions", "max"),
                laid_off=("total_laid_off", "sum"))
           .sort_values("funds", ascending=False)
           .head(15))
```

Two things to notice:
1. `.max()` for funds (a company might appear in multiple layoff events — take the highest known raise)
2. `.sum()` for laid_off (accumulate all layoff events per company)
3. Filter requires BOTH columns to be non-null — a scatter needs both axes

### Why boxplot without fliers (`showfliers=False`)?

```python
bp = axes[1].boxplot(yearly_data, ..., showfliers=False)
```

The dataset has a handful of very large events (Amazon: 18,000, Meta: 11,000)
that make the y-axis scale unreadable if shown. `showfliers=False` hides
outlier points while keeping the interquartile range visible.
The outliers are discussed in the insight report instead.

---

## Data quality dimensions — the professional framework

The audit report uses a standard DQ framework:

| Dimension | What it means | How measured here |
|-----------|--------------|-------------------|
| **Completeness** | Data is present where expected | Null + empty counts per column |
| **Uniqueness** | No unintended duplicates | Exact + near-duplicate detection |
| **Consistency** | Same concept, same representation | Category variant counting + standardisation |
| **Validity** | Data conforms to its format | Date parsing, numeric type enforcement |
| **Accuracy** | Data reflects reality | Out-of-range checks (pct > 1.0) |
| **Timeliness** | Dates are parseable and in range | Date format validation |

This is the DAMA (Data Management Association) framework used in professional DQ roles.
Referencing these dimensions by name in an interview demonstrates that you think
about data quality systematically, not just as "fixing nulls".

---

## Interview talking points

**Q: "Walk me through your data cleaning process."**

"I start with a profile — shape, types, null rates per column before touching anything.
Then I document every issue I find before fixing anything. That way I have a before/after
record. I separate cleaning from analysis into different scripts so the audit is a
standalone deliverable. And I always end with a validation step — explicit pass/fail
checks that the cleaning achieved what I intended."

**Q: "How did you handle the missing values?"**

"It depends on which column and why they're missing. In this dataset, `total_laid_off`
was often missing because companies don't publicly disclose exact numbers — that's
informative missingness, not data error. I kept those rows if the percentage was
available. I only dropped rows where both numeric columns were null simultaneously —
those contained no usable layoff information at all."

**Q: "How did you use AI in this project?"**

"I used Claude Cowork as a development partner. I designed the architecture and
specified the requirements — including the validation step and the specific types
of messiness to model — and Claude helped me implement them. Every piece of code
was reviewed and tested by me before committing. The AI_WORKFLOW.md in the repo
documents the exact prompts and decisions throughout."
