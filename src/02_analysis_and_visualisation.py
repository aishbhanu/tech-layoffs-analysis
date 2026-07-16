"""
02_analysis_and_visualisation.py
=================================
Phase 2: Analysis & Insights on the cleaned dataset

Charts produced:
  01  Layoffs by year — total headcount per year
  02  Monthly wave chart — the four waves of layoffs
  03  Industry breakdown — which sectors got hit hardest
  04  Country heatmap — geographic distribution
  05  Funding stage vs layoffs — do well-funded companies cut more?
  06  Funding paradox — top companies by funds raised vs employees cut
  07  Layoff size distribution — histogram
  08  India & UAE deep dive — regional focus
  09  Serial layoffs — companies with the most separate layoff events

Run: python src/02_analysis_and_visualisation.py
Output: output/charts/*.png + output/reports/insight_report.txt
"""

import os
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns
from adjustText import adjust_text

os.makedirs("output/charts", exist_ok=True)
os.makedirs("output/reports", exist_ok=True)

sns.set_theme(style="whitegrid", font_scale=1.05)
PALETTE = ["#2E75B6", "#E74C3C", "#2ECC71", "#F39C12", "#9B59B6",
           "#1ABC9C", "#E67E22", "#3498DB", "#E91E63", "#00BCD4"]
NAVY   = "#1F3864"
RED    = "#E74C3C"
GREEN  = "#27AE60"
AMBER  = "#F39C12"


def load(path="data/cleaned/layoffs_clean.csv"):
    df = pd.read_csv(path, parse_dates=["date"])
    df["year"] = df["date"].dt.year
    df = df[df["year"].between(2022, 2025)]
    print(f"Loaded {len(df)} clean records | {df['year'].min()}–{df['year'].max()}")
    return df


# ── Chart helpers ──────────────────────────────────────────────────────────────

def save(name):
    plt.tight_layout()
    path = f"output/charts/{name}"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ {name}")


# ── Chart 1: Layoffs by Year ───────────────────────────────────────────────────

def chart_layoffs_by_year(df):
    fig, ax = plt.subplots(figsize=(9, 5))
    yearly = df.groupby("year")["total_laid_off"].sum().dropna()

    colors = [RED if v == yearly.max() else "#2E75B6" for v in yearly.values]
    bars = ax.bar(yearly.index.astype(str), yearly.values / 1000,
                  color=colors, edgecolor="white", width=0.55)

    for bar, val in zip(bars, yearly.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f"{val/1000:.0f}K", ha="center", fontsize=11, fontweight="bold")

    ax.set_title("Total Tech Layoffs by Year (2022–2025)",
                 fontsize=14, fontweight="bold", pad=12)
    ax.set_ylabel("Employees Laid Off (thousands)")
    ax.set_xlabel("")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}K"))
    save("01_layoffs_by_year.png")


# ── Chart 2: Monthly Wave Chart ────────────────────────────────────────────────

def chart_monthly_wave(df):
    fig, ax = plt.subplots(figsize=(14, 5))
    monthly = (df.groupby("month")["total_laid_off"]
                 .sum()
                 .dropna()
                 .reset_index())
    monthly["month_dt"] = pd.to_datetime(monthly["month"])
    monthly = monthly.sort_values("month_dt")

    ax.fill_between(monthly["month_dt"], monthly["total_laid_off"] / 1000,
                    alpha=0.3, color="#2E75B6")
    ax.plot(monthly["month_dt"], monthly["total_laid_off"] / 1000,
            color="#2E75B6", linewidth=2)

    # Annotate key events
    annotations = [
        ("2022-11-01", "Twitter/Meta\nmassive cuts"),
        ("2023-01-01", "2023 wave\npeak"),
        ("2024-01-01", "Intel/SAP\ncuts"),
        ("2025-01-01", "AI-driven\nrestructuring"),
    ]
    for date_str, label in annotations:
        dt = pd.to_datetime(date_str)
        if dt in monthly["month_dt"].values:
            idx = monthly[monthly["month_dt"] == dt].index[0]
            y = monthly.loc[idx, "total_laid_off"] / 1000
            ax.annotate(label, xy=(dt, y), xytext=(0, 18),
                        textcoords="offset points", ha="center",
                        fontsize=8, color="#444",
                        arrowprops=dict(arrowstyle="-", color="#aaa"))

    ax.set_title("Monthly Tech Layoffs — The Four Waves (2022–2025)",
                 fontsize=14, fontweight="bold", pad=12)
    ax.set_ylabel("Employees Laid Off (thousands)")
    ax.set_xlabel("")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}K"))
    save("02_monthly_wave.png")


# ── Chart 3: Industry Breakdown ────────────────────────────────────────────────

def chart_industry(df):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Left: total laid off by industry
    ind = (df.groupby("industry")["total_laid_off"]
             .sum().dropna().sort_values(ascending=False).head(10))
    colors = [PALETTE[i % len(PALETTE)] for i in range(len(ind))]
    axes[0].barh(ind.index[::-1], ind.values[::-1] / 1000,
                 color=colors[::-1], edgecolor="white")
    axes[0].set_title("Total Layoffs by Industry", fontweight="bold")
    axes[0].set_xlabel("Employees (thousands)")
    axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}K"))

    # Right: number of companies (events) by industry
    ind_count = df.groupby("industry")["company"].count().sort_values(ascending=False).head(10)
    axes[1].barh(ind_count.index[::-1], ind_count.values[::-1],
                 color=colors[::-1], edgecolor="white")
    axes[1].set_title("Number of Layoff Events by Industry", fontweight="bold")
    axes[1].set_xlabel("Number of Layoff Events")

    plt.suptitle("Industry Analysis — Who Got Hit Hardest?",
                 fontsize=14, fontweight="bold", y=1.02)
    save("03_industry_breakdown.png")


# ── Chart 4: Country Bar Chart ─────────────────────────────────────────────────

def chart_country(df):
    fig, ax = plt.subplots(figsize=(11, 6))
    country = (df.groupby("country")["total_laid_off"]
                 .sum().dropna().sort_values(ascending=False).head(12))

    colors = [RED if c == "United States"
              else AMBER if c in ["India", "United Arab Emirates"]
              else "#2E75B6"
              for c in country.index]

    bars = ax.barh(country.index[::-1], country.values[::-1] / 1000,
                   color=colors[::-1], edgecolor="white", height=0.65)
    for bar, val in zip(bars, country.values[::-1]):
        ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2,
                f"{val/1000:.0f}K", va="center", fontsize=9)

    ax.set_title("Total Layoffs by Country (Top 12)", fontsize=14,
                 fontweight="bold", pad=12)
    ax.set_xlabel("Employees Laid Off (thousands)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}K"))

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=RED,    label="United States"),
        Patch(facecolor=AMBER,  label="India / UAE (highlighted)"),
        Patch(facecolor="#2E75B6", label="Other countries"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=9)
    save("04_country_distribution.png")


# ── Chart 5: Funding Stage vs Layoffs ──────────────────────────────────────────

def chart_stage(df):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Matches the real cleaned Stage vocabulary (see 01_data_audit_and_cleaning.py
    # STAGE_MAP): "Private" doesn't exist in the real data — it's "Private
    # Equity". "Subsidiary" and "Unknown" are also real values but excluded
    # here since they aren't a funding round and would clutter this chart.
    stage_order = ["Seed", "Series A", "Series B", "Series C", "Series D",
                   "Series E", "Series F", "Series G", "Series H", "Series I",
                   "Series J", "Post-IPO", "Private Equity", "Acquired"]
    stage_data = df[df["stage"].isin(stage_order)]

    # Left: median layoff size per stage
    med = (stage_data.groupby("stage")["total_laid_off"]
                     .median().dropna().reindex(stage_order).dropna())
    axes[0].bar(range(len(med)), med.values, color="#2E75B6", edgecolor="white")
    axes[0].set_xticks(range(len(med)))
    axes[0].set_xticklabels(med.index, rotation=40, ha="right", fontsize=8)
    axes[0].set_title("Median Layoff Size by Funding Stage", fontweight="bold")
    axes[0].set_ylabel("Median employees laid off")

    # Right: event count per stage
    cnt = (stage_data.groupby("stage")["company"]
                     .count().reindex(stage_order).dropna())
    axes[1].bar(range(len(cnt)), cnt.values, color=AMBER, edgecolor="white")
    axes[1].set_xticks(range(len(cnt)))
    axes[1].set_xticklabels(cnt.index, rotation=40, ha="right", fontsize=8)
    axes[1].set_title("Number of Layoff Events by Stage", fontweight="bold")
    axes[1].set_ylabel("Number of events")

    plt.suptitle("Does Funding Stage Predict Layoff Size?",
                 fontsize=14, fontweight="bold", y=1.02)
    save("05_stage_analysis.png")


# ── Chart 6: The Funding Paradox ───────────────────────────────────────────────

def chart_funding_paradox(df):
    """Shows companies that raised most money but still cut most people."""
    fig, ax = plt.subplots(figsize=(11, 8))
    paradox = (df[df["funds_raised_millions"].notna() & df["total_laid_off"].notna()]
               .groupby("company")
               .agg(funds=("funds_raised_millions", "max"),
                    laid_off=("total_laid_off", "sum"))
               .sort_values("funds", ascending=False)
               .head(15))

    x = paradox["funds"] / 1000     # $B
    y = paradox["laid_off"] / 1000  # thousands of employees

    ax.scatter(x, y, s=110, color=RED, alpha=0.75,
               edgecolors="white", linewidth=0.8, zorder=3)

    # Funds span ~25x (Netflix at $121.9B vs. Lyft at $4.9B) and layoffs span
    # ~140x (Amazon 27.7K vs. Waymo 0.2K). On a linear scale that squeezes 14
    # of the 15 companies into the bottom-left corner right next to each
    # other — that's what made the old fixed-offset labels overlap. Log
    # scale on both axes spreads every point out properly.
    ax.set_xscale("log")
    ax.set_yscale("log")

    # adjustText auto-repositions each label to avoid overlapping any other
    # label or point, drawing a thin leader line back to its actual point
    # when it has to move — every company name stays fully readable.
    texts = [
        ax.text(xi, yi, company, fontsize=9.5, color="#222", zorder=4)
        for company, xi, yi in zip(paradox.index, x, y)
    ]
    adjust_text(
        texts, ax=ax,
        arrowprops=dict(arrowstyle="-", color="#999", lw=0.7),
        expand=(1.4, 1.7),
    )

    ax.set_title("The Funding Paradox: Billions Raised, Thousands Cut",
                 fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Total Funds Raised ($B, log scale)")
    ax.set_ylabel("Total Employees Laid Off (thousands, log scale)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:g}B"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:g}K"))
    ax.grid(True, which="both", axis="both", alpha=0.25)
    save("06_funding_paradox.png")


# ── Chart 7: Layoff Size Distribution ──────────────────────────────────────────

def chart_distribution(df):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    data = df["total_laid_off"].dropna()

    # Left: histogram
    axes[0].hist(data[data < 5000], bins=40, color="#2E75B6",
                 edgecolor="white", alpha=0.85)
    axes[0].axvline(data.median(), color=RED, linestyle="--", linewidth=1.5,
                    label=f"Median: {data.median():.0f}")
    axes[0].axvline(data.mean(), color=AMBER, linestyle="--", linewidth=1.5,
                    label=f"Mean: {data.mean():.0f}")
    axes[0].set_title("Distribution of Layoff Size (< 5,000)", fontweight="bold")
    axes[0].set_xlabel("Employees laid off")
    axes[0].set_ylabel("Number of events")
    axes[0].legend(fontsize=9)

    # Right: box by year
    yearly_data = [df[df["year"] == y]["total_laid_off"].dropna().values
                   for y in [2022, 2023, 2024, 2025]]
    bp = axes[1].boxplot(yearly_data, labels=["2022","2023","2024","2025"],
                         patch_artist=True, showfliers=False)
    for patch, color in zip(bp["boxes"], PALETTE):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    axes[1].set_title("Layoff Size Distribution by Year", fontweight="bold")
    axes[1].set_ylabel("Employees laid off")

    plt.suptitle("How Big Are Individual Layoff Events?",
                 fontsize=14, fontweight="bold", y=1.02)
    save("07_distribution.png")


# ── Chart 8: India & UAE Spotlight ────────────────────────────────────────────

def chart_regional_spotlight(df):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for ax, country, color in zip(
        axes,
        ["India", "United Arab Emirates"],
        ["#FF6B35", "#2E75B6"]
    ):
        sub = df[df["country"] == country]
        if sub.empty:
            ax.set_title(f"{country} — no data")
            continue

        ind = (sub.groupby("industry")["total_laid_off"]
                  .sum().dropna().sort_values(ascending=False).head(8))
        ax.barh(ind.index[::-1], ind.values[::-1], color=color,
                edgecolor="white", alpha=0.85)
        ax.set_title(f"{country} — Layoffs by Industry", fontweight="bold")
        ax.set_xlabel("Total employees laid off")
        n_events = len(sub)
        total = sub["total_laid_off"].sum()
        ax.set_xlabel(f"Total laid off  |  {n_events} events, {total:,.0f} total employees")

    plt.suptitle("Regional Spotlight: India & UAE",
                 fontsize=14, fontweight="bold", y=1.02)
    save("08_regional_spotlight.png")


# ── Chart 9: Serial Layoffs ─────────────────────────────────────────────────────

def chart_serial_layoffs(df):
    """Top 10 companies by NUMBER OF SEPARATE LAYOFF EVENTS, not headcount.
    A company that cut staff 3 times counts as 3 here, even if each round
    was small — this surfaces repeat/rolling layoffs that the headcount-based
    charts (01-08) don't distinguish from a single large cut."""
    fig, ax = plt.subplots(figsize=(10, 6))
    events = df.groupby("company").size().sort_values(ascending=False).head(10)

    bars = ax.barh(events.index[::-1], events.values[::-1],
                    color="#9B59B6", edgecolor="white", height=0.6)
    for bar, val in zip(bars, events.values[::-1]):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                f"{val}", va="center", fontsize=9, fontweight="bold")

    ax.set_title("Serial Layoffs: Companies With the Most Separate Rounds (2022–2025)",
                 fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Number of Separate Layoff Events")
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    save("09_serial_layoffs.png")


# ── Insight Report ─────────────────────────────────────────────────────────────

def write_insight_report(df):
    total = df["total_laid_off"].sum()
    n_companies = df["company"].nunique()
    worst_year = df.groupby("year")["total_laid_off"].sum().idxmax()
    worst_industry = df.groupby("industry")["total_laid_off"].sum().idxmax()
    worst_country = df.groupby("country")["total_laid_off"].sum().idxmax()
    top5 = (df.groupby("company")["total_laid_off"]
              .sum().dropna().sort_values(ascending=False).head(5))

    paradox = (df[df["funds_raised_millions"].notna() & df["total_laid_off"].notna()]
               .groupby("company")
               .agg(funds=("funds_raised_millions","max"),
                    laid_off=("total_laid_off","sum"))
               .sort_values("funds", ascending=False).head(1))

    lines = [
        "=" * 65,
        "  INSIGHT REPORT — Tech Layoffs 2022–2025",
        f"  Generated: {datetime.now().strftime('%d %b %Y %H:%M')}",
        "=" * 65, "",
        "1. HEADLINE NUMBERS",
        "-" * 40,
        f"  Total employees laid off   : {total:,.0f}",
        f"  Unique companies affected  : {n_companies}",
        f"  Worst year                 : {worst_year}",
        f"  Hardest-hit industry       : {worst_industry}",
        f"  Hardest-hit country        : {worst_country}",
        "",
        "2. TOP 5 COMPANIES BY TOTAL LAYOFFS",
        "-" * 40,
    ]
    for company, count in top5.items():
        lines.append(f"  {company:<25} {count:>8,.0f}")

    lines += [
        "",
        "3. THE FUNDING PARADOX",
        "-" * 40,
    ]
    for company, row in paradox.iterrows():
        lines.append(
            f"  {company} raised ${row['funds']/1000:.1f}B "
            f"yet laid off {row['laid_off']:,.0f} employees"
        )

    lines += [
        "",
        "4. YEAR-BY-YEAR BREAKDOWN",
        "-" * 40,
    ]
    for year, total_y in df.groupby("year")["total_laid_off"].sum().items():
        events = df[df["year"] == year]["company"].count()
        lines.append(f"  {year}  {total_y:>8,.0f} employees  ({events} events)")

    lines += [
        "",
        "5. KEY FINDINGS",
        "-" * 40,
    ]

    # Every finding below is computed from this run's data (not hardcoded
    # prose), so it stays accurate if the underlying dataset changes later.

    # Finding 1: worst year + whether events got bigger or more frequent
    yearly_totals = df.groupby("year")["total_laid_off"].sum()
    yearly_events = df.groupby("year")["company"].count()
    avg_size = yearly_totals / yearly_events
    peak_year = int(yearly_totals.idxmax())
    first_yr, last_yr = int(avg_size.index.min()), int(avg_size.index.max())
    lines.append(
        f"  1. {peak_year} was the worst year on record ({yearly_totals[peak_year]:,.0f} "
        f"employees, {int(yearly_events[peak_year])} events) — despite that, the average "
        f"layoff event grew from {avg_size[first_yr]:,.0f} employees/event in {first_yr} "
        f"to {avg_size[last_yr]:,.0f} in {last_yr}: fewer but larger cuts over time."
    )

    # Finding 2: hardest-hit industries by volume (excluding the "Other" catch-all)
    industry_totals = (df[df["industry"] != "Other"]
                        .groupby("industry")["total_laid_off"].sum()
                        .sort_values(ascending=False))
    if len(industry_totals) >= 3:
        top3 = industry_totals.head(3)
        lines.append(
            f"  2. {top3.index[0]}, {top3.index[1]}, and {top3.index[2]} were the hardest-hit "
            f"industries by volume ({top3.iloc[0]:,.0f}, {top3.iloc[1]:,.0f}, and "
            f"{top3.iloc[2]:,.0f} employees respectively)."
        )

    # Finding 3: funding stage — absolute size vs. % of workforce cut.
    # "Unknown"/"Subsidiary" excluded — not real funding rounds.
    REAL_STAGES = ["Seed", "Series A", "Series B", "Series C", "Series D", "Series E",
                   "Series F", "Series G", "Series H", "Series I", "Series J",
                   "Post-IPO", "Private Equity", "Acquired"]
    stage_df = df[df["stage"].isin(REAL_STAGES)]
    stage_abs = stage_df.groupby("stage")["total_laid_off"].sum().sort_values(ascending=False)
    stage_pct = stage_df.groupby("stage")["percentage_laid_off"].median().sort_values(ascending=False)
    if len(stage_abs) and len(stage_pct):
        lines.append(
            f"  3. {stage_abs.index[0]} companies laid off the most employees in absolute "
            f"terms ({stage_abs.iloc[0]:,.0f}), but {stage_pct.index[0]} had the highest "
            f"median % of workforce cut ({stage_pct.iloc[0]:.0f}%) — early-stage companies "
            f"cut deepest relative to headcount, even though the absolute numbers are small."
        )

    # Finding 4: the funding paradox (reuses the single-row table from section 3)
    if len(paradox):
        p = paradox.iloc[0]
        lines.append(
            f"  4. {paradox.index[0]} raised ${p['funds']/1000:.1f}B yet laid off only "
            f"{p['laid_off']:,.0f} employees — 'funds raised' here reflects lifetime "
            f"VC/IPO raises, not current headcount risk, so it doesn't predict layoff size."
        )

    # Findings 5 & 6: regional spotlight (India / UAE), computed directly —
    # no assumed company names or causes, only what's actually in the data.
    def region_note(country_name, n):
        sub = df[df["country"] == country_name]
        if sub.empty:
            return f"  {n}. No {country_name} layoffs recorded in this dataset."
        total_r = sub["total_laid_off"].sum()
        events_r = len(sub)
        top_ind = sub.groupby("industry")["total_laid_off"].sum().sort_values(ascending=False)
        top_co = sub.sort_values("total_laid_off", ascending=False).iloc[0]
        return (
            f"  {n}. {country_name}: {events_r} events, {total_r:,.0f} employees laid off, "
            f"led by {top_ind.index[0]} ({top_ind.iloc[0]:,.0f}); largest single event was "
            f"{top_co['company']} ({top_co['total_laid_off']:,.0f})."
        )

    lines.append(region_note("India", 5))
    lines.append(region_note("United Arab Emirates", 6))

    lines += [
        "",
        "=" * 65,
    ]
    report = "\n".join(lines)
    path = "output/reports/insight_report.txt"
    with open(path, "w") as f:
        f.write(report)
    print("\n" + report)


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Tech Layoffs 2022–2025 — Analysis & Visualisation")
    print("=" * 55)

    df = load()

    print("\nGenerating charts...")
    chart_layoffs_by_year(df)
    chart_monthly_wave(df)
    chart_industry(df)
    chart_country(df)
    chart_stage(df)
    chart_funding_paradox(df)
    chart_distribution(df)
    chart_regional_spotlight(df)
    chart_serial_layoffs(df)

    print("\nWriting insight report...")
    write_insight_report(df)
    print("\n✓ All outputs saved to output/")
