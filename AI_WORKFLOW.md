# AI-Assisted Development Workflow
## How Claude Cowork was used to build this project

This document transparently describes how AI tools — specifically
**Claude Cowork** — were used throughout this project.
This is not a disclaimer. It is a deliberate part of the portfolio.

---

## Why document the AI workflow?

In 2024–2025, "I know how to use AI" is not a differentiator.
"I know *how to work with AI effectively*" is.

Working with an AI coding assistant is a skill:
- Knowing how to frame a problem so the model gives useful output
- Knowing when to trust the output and when to verify it
- Knowing how to iterate when the first result is wrong
- Knowing how to maintain your own understanding throughout

This document shows that skill. It is written for hiring managers,
technical interviewers, and anyone who wants to understand the
human decisions behind this codebase.

---

## Tool used

**Claude Cowork** (Anthropic) — a long-context AI assistant with file access,
code execution, and persistent task memory. Used via the Claude desktop application.

---

## Phase 1: Architecture design

**What I did with AI:**
I described the project goal to Claude — "build a data quality pipeline on
the layoffs.fyi dataset that showcases real messy data handling" — and asked
it to propose an architecture before writing any code.

**Prompt I used:**
> "I want to build a Python data project on the tech layoffs dataset.
> The main showcase should be messy data handling, not just analysis.
> Propose a file structure and two-phase pipeline design before we start coding."

**What I got:**
The two-phase structure (01_audit_and_cleaning → 02_analysis) came from this
conversation. I evaluated it against my own understanding of DQ workflows
from my role at TfGM and agreed it was the right separation.

**My decision, not the AI's:**
I insisted on a separate validation step (Step 4 in Phase 1) because in
professional DQ work, cleaning without validation is incomplete.
Claude had initially omitted this. I added it as a requirement.

---

## Phase 2: Generating the messy dataset

**What I did with AI:**
I asked Claude to generate a synthetic dataset that mirrors the *specific*
messiness of the layoffs.fyi data — not generic messiness, but the exact
issues documented in real analyses of that dataset.

**Prompt I used:**
> "The real layoffs.fyi dataset has: mixed date formats, inconsistent
> industry labels like 'Fintech' vs 'FinTech' vs 'Financial Services',
> country name variants like 'USA' vs 'US' vs 'United States',
> ~30% nulls in total_laid_off, and duplicates from multi-source scraping.
> Generate a synthetic dataset that recreates all of these authentically."

**What I verified:**
After generation, I ran a manual check on the raw CSV to confirm:
- Date formats were genuinely mixed (not all one format)
- Industry variants were realistic, not obviously synthetic
- Null rates matched the documented real-data rates (~27–45%)
- Duplicate rows existed with subtle differences (stripped whitespace, etc.)

I had Claude regenerate the funds column twice because the first version
produced only clean numeric strings — not realistic. I pushed back and got
the `$2,400`, `2.4B`, `$2400M` variants that appear in the real data.

---

## Phase 3: Writing the cleaning code

**What I did with AI:**
For each cleaning step, I described the problem and asked for a solution,
then reviewed the code before accepting it.

**Example — date parsing:**
> "The date column has 5 formats: YYYY-MM-DD, MM/DD/YYYY, DD-MM-YYYY,
> 'Month DD, YYYY', and 'DD Mon YYYY'. Write a function that tries each
> format in order and returns NaT if none parse."

Claude produced `parse_date()`. I tested it against edge cases manually
(what happens with an empty string? what happens with a partial date like "2023-01"?)
and found it returned an exception on empty strings. I reported this back
and Claude fixed it by adding the `str(date_str).strip() == ""` guard.

**Example — the near-duplicate detection:**
Claude's first version used `df.duplicated(subset=["company", "date"])` directly.
I flagged that this misses near-duplicates where `company` has extra whitespace
or `date` is in a different format on the second occurrence. Claude then
rewrote it to normalise both columns to a `_key` before comparison.
This is an example of my domain knowledge improving the AI's output.

---

## Phase 4: Visualisations

**What I did with AI:**
I described each chart by its purpose, not its code:
> "Chart 6 should show the 'funding paradox' — companies that raised the most
> capital were not protected from large layoffs. Show it as a scatter plot
> with company labels, x=funds raised, y=total laid off."

Claude generated the scaffold. I adjusted:
- Axis scale (billions, not millions — more readable)
- Added annotation offset to prevent label overlap
- Changed colour to red to reinforce the 'paradox' framing

**What I did not use AI for:**
The choice of which 8 charts to include was mine.
I deliberately included the India & UAE spotlight (Chart 8)
because my target job market includes UAE companies,
and showing regional awareness is a strategic choice, not a technical one.

---

## Phase 5: Debugging

**One real example:**
Phase 1 initially showed a validation FAIL on `total_laid_off is numeric`
even after the cast. I investigated and found `pd.api.types.is_float_dtype()`
returns False for columns with NaN values (they become float64 internally
but the check was ambiguous). I asked Claude to explain the difference between
`is_float_dtype` and `is_numeric_dtype`. It explained correctly.
I changed the check. This is an example of using AI as a reference,
not as an oracle — I understood the explanation before accepting the fix.

---

## What AI did in this project

| Task | AI involvement |
|------|---------------|
| Architecture design | Co-designed with Claude |
| Dataset messiness specification | I specified; Claude implemented |
| Cleaning code | Claude drafted; I reviewed and tested |
| Validation logic | I required it; Claude wrote it |
| Chart design | I specified purpose; Claude wrote scaffold |
| Chart styling and strategic choices | Mine |
| Regional spotlight inclusion | My strategic decision |
| Debugging | Collaborative — I diagnosed, Claude explained |
| Documentation | Co-written, I edited for accuracy |

---

## Skills this demonstrates

**Prompt engineering:**
- Task decomposition (architecture first, then implementation)
- Specifying constraints precisely ("5 date formats", "real variants, not generic")
- Iterative refinement ("regenerate the funds column with these specific formats")

**Critical evaluation of AI output:**
- Testing edge cases that AI didn't consider
- Pushing back when output was insufficiently realistic
- Understanding code before accepting it

**Domain knowledge applied to AI direction:**
- Validation step requirement came from professional DQ experience
- Near-duplicate detection improvement came from knowing how scrapers work
- Regional chart inclusion came from job market strategy awareness

---

## A note on authenticity

Every line of code in this project was reviewed and understood before being committed.
The AI was a development accelerator and code reviewer — not a replacement for
engineering judgment. The analytical insights, design decisions, and quality
standards throughout this project reflect my own professional standards.

This is the correct way to work with AI in a professional context:
transparently, critically, and with maintained personal accountability.
