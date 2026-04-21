# Symphony Content Engine

## Trigger: `symphony, compose magic`

When I say **symphony, compose magic**, execute the full pipeline below. Do not skip steps.

### Step 1 — Ingest

Run this command:

    python3 ingest.py

This converts any .docx or .pdf files in `/inbox/` to readable .md files. Wait for it to complete before proceeding.

### Step 2 — Load Context

Read all five context files into working memory. You will reference these throughout asset generation:

- `/context/company.md` — proof points, metrics, leadership, product details
- `/context/icp.md` — ICP segments, personas, pain language, buying triggers
- `/context/positioning.md` — value props, competitive differentiation, why-now narrative
- `/context/competitors.md` — competitor profiles, displacement angles, objection ammo
- `/context/brand-voice.md` — voice for each author (Narsingh, CEO, corporate), banned phrases, style rules

### Step 3 — Process Each Source Document

For every `.md` file in `/inbox/` (skip `.docx`, `.pdf`, and any dotfiles):

#### 3a. Extract

Follow `/prompts/01-extract.md` against the source document. This produces a structured briefing. Hold the result in memory as EXTRACT.

#### 3b. Multiply

Follow `/prompts/02-multiply.md` to generate all 10 marketing assets. Inputs are EXTRACT (from 3a) and all context files (from Step 2).

#### 3c. Write Output

Create the directory `/output/{source-filename-without-extension}/` and write these 10 files:

1. `linkedin-narsingh.md`
2. `linkedin-ceo.md`
3. `nurture-email-1-wealth.md`
4. `nurture-email-2-wealth.md`
5. `nurture-email-3-wealth.md`
6. `bdr-sequence-asset-mgr.md`
7. `sales-one-pager.md`
8. `objection-handling.md`
9. `blog-post.md`
10. `enablement-talking-points.md`

### Step 4 — Report

After all source documents are processed, report:

- Number of source documents processed
- Output directory path for each
- One-line summary of each of the 10 generated assets
- Any quality flags or issues encountered

## Quality Rules (apply to EVERY asset)

These are non-negotiable. Violating any one is a failure.

1. **Ground in context.** Every asset pulls voice from `brand-voice.md`, ICP language from `icp.md`, positioning from `positioning.md`, and competitive framing from `competitors.md`. The source document provides substance; the context files provide frame.
2. **Deployable, not drafts.** A CMO should read any asset and think "I could ship this Monday." No placeholder brackets, no TODO markers, no "insert X here."
3. **ICP segmentation is visible.** Wealth manager assets use wealth manager pain language. Asset manager assets use asset manager pain language. If you swapped the ICP labels, a reader should notice something is wrong.
4. **No AI tells.** Banned phrases from `brand-voice.md` are hard constraints. Also avoid: filler openings ("In today's..."), hollow superlatives ("revolutionary"), and any phrasing that reads like a model trying to sound impressive rather than a PMM trying to be useful.
5. **Specificity over generality.** Use PureFacts stats from `company.md`. Cite data from the source document. Name the problem precisely. If you catch yourself writing a sentence that could apply to any SaaS company, rewrite it.
