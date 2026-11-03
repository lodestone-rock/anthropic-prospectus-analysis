# Swarm prompts (verbatim)

Every prompt used by the two swarms, plus the retry prompts. Copy-paste ready; replace
`{placeholders}` and file paths.

## 1. Extraction swarm (record-level numbers)

Transport: one HTTPS call per chunk to `POST https://openrouter.ai/api/v1/chat/completions`,
model `z-ai/glm-5.3-flash`, `temperature: 0`, `max_tokens: 32000`, `reasoning_effort: low`
(the endpoint rejects `reasoning: {enabled: false}` — low is the floor), 4–6 concurrent workers,
retry ×4 with quadratic backoff.

### System prompt

```text
You are a forensic financial-data extractor working on a chunk of an SEC Form S-1/A prospectus (Anthropic, PBC, Nov 2 2026 amendment).

Output: JSONL only. One JSON object per line. No markdown fences, no commentary, no blank lines.

Record schema:
{"kind":"inline"|"table_row"|"blank","label":"short label","values":["values exactly as printed"],"unit":"$M|$B|%|x|shares|per-share|years|count|...","period":"FY2023|FY2024|FY2025|Q1'26|Q2'26|Q3'26|9M 2025|9M 2026|as of 2026-09-30|2026-2033|...","category":"offering|financials|commitments|metrics|stock_plan|governance|legal|other","quote":"verbatim span of 5-40 words from the chunk containing the figure"}

Rules:
1. Financial-statement and numeric tables: emit one "table_row" per line item, with EVERY column value in order in "values". If column headers appear in the chunk, add "columns":[...] once for the table using kind "table_row" with label "HEADER".
2. Narrative dollar figures, percentages, ratios, multiples, counts (customers, employees, shares), per-share amounts, date-bound obligations: one "inline" record each.
3. Blanked-out values (e.g. "$ and $", "$*", "approximately $,", "up to an additional shares", "$ per share" with no number): kind "blank", values ["[BLANK]"], quote the sentence fragment.
4. NEVER retype or round numbers — copy exactly as printed. The "quote" field must be copied verbatim from the chunk text (it is used to re-anchor the record by grep).
5. EXCLUDE: page numbers, page headers/footers, exhibit numbering, addresses, phone numbers, EIN/IRS numbers, statute section numbers with no dollar amount, pure boilerplate with no figures.
6. Include repeated figures wherever they recur (dedup happens later).
7. Stock-plan content (share classes, splits, plan reserves, vesting, exercise prices, RSU/option grants, conversion prices, ownership caps, dilution) → category "stock_plan". Be exhaustive there.
8. Be exhaustive. Missing a real number is the worst failure mode. Hundreds of records per chunk is normal.
```

### User message template

```text
Chunk: {cid} — filing {filing}, section: {section} (source lines {start}-{end}).

Extract every hard number per the rules. Output JSONL only.

CHUNK TEXT:
<<<
{text}
>>>
```

## 2. Table-transcription swarm (subagents)

Transport: one background subagent per overlapping window — 18 windows per filing
(step 2,600 lines, window 3,200 lines ⇒ ±~300 lines of padding at each edge; agents may read
beyond the window for context but may only transcribe tables fully inside it). Waves of 6.

Per-window parameters vary only in: window range, output filename, batch id, and a one-line
section hint (e.g. "this window is in the risk-factors section", "this window contains the
FINANCIAL STATEMENTS section (F-pages)..."). Canonical prompt (the F-pages variant; the base
variant is identical minus the statement-title hints):

```text
You are transcribing flattened SEC-filing tables into structured JSON. This is carbon-copy transcription work: accuracy of every cell is critical.

SOURCE: <repo>/data/filings/sx1a_extracted.txt
This is a text extraction of Anthropic's S-1/A prospectus. TABLE CELLS ARE FLATTENED: each cell value is typically on its own line, with row label lines immediately before their value lines. Ignore page furniture: lines like "NN Table of Contents", bare "Table of Contents", "F-NN", page numbers.

YOUR WINDOW: lines 33801 to 37000 (1-based inclusive). Read the file with the Read tool using offset/limit. You may read up to 200 lines beyond either edge for context, but ONLY transcribe tables whose caption/title line AND last row (or footnote) line fall fully within lines 33801–37000.

TASK: find EVERY tabular presentation fully inside your window. Tables are introduced by phrases like "The following table(s) ..." / "summarizes" / "sets forth" / "illustrates" / "presents ... :", OR by statement titles (e.g. "Anthropic, PBC Consolidated Balance Sheets", "Consolidated Statements of Operations", "Quarterly Consolidated Statements of Operations"), OR by a clear column-header row. This window contains the FINANCIAL STATEMENTS section (F-pages): the INDEX TO CONSOLIDATED FINANCIAL STATEMENTS, Reports of Independent Registered Public Accounting Firm (skip the prose reports themselves), Consolidated Balance Sheets, Consolidated Statements of Operations, Comprehensive Loss, Redeemable Convertible Preferred Stock and Stockholders Deficit, and Cash Flows. Transcribe each statement as a table: caption = statement title, columns = the period columns exactly as printed, rows = every line item with all its values. Skip pure prose.

OUTPUT: write a JSON file to
<repo>/data/tables/sx1a/sx1a_b13.json
with EXACTLY this structure:
{
  "batch": "sx1a_b13",
  "tables": [
    {
      "kind": "statement",
      "caption": "Anthropic, PBC Consolidated Balance Sheets",
      "caption_line": 123,
      "start_line": 130,
      "end_line": 200,
      "column_note": "(In millions, except share amounts which are in thousands, and per share data)",
      "columns": ["", "As of December 31, 2024", "As of December 31, 2025", "As of September 30, 2026 (unaudited)"],
      "rows": [
        {"label": "Cash and cash equivalents", "cells": ["$3,141", "$17,388", "$95,562"]}
      ],
      "footnotes": []
    }
  ]
}

RULES:
- Copy every cell EXACTLY as printed: keep $ signs, thousands commas, % signs, parentheses for negatives, and footnote markers attached to values.
- If a cell is blank in the source, use the string "[BLANK]".
- Row label = the non-numeric line(s) immediately before the row's cell values; merge continuation lines (e.g. "Compute and" + "infrastructure" becomes "Compute and infrastructure").
- Include ALL rows: subtotals, totals, share counts, per-share amounts, net loss per share. Do not skip any.
- Numbers-only footer lines like "F-13" or "Table of Contents" inside a table are page furniture — skip them.
- column headers in flattened text may appear as several repeated blocks — reconstruct the logical columns once.
- Before writing the file, re-verify: every non-[BLANK] cell's alphanumeric content must appear in the source window text.
- If there are NO tables fully inside your window, write {"batch":"sx1a_b13","tables":[]}.

After writing the file, reply with ONLY: batch id, number of tables, total row count.
```

Window/section hints used per batch (S-1/A): b00 cover+TOC+summary ("includes the cover-page
price/underwriting table and the summary financial-data tables; a lone `$` with no number is a
blank cell — record it as `[BLANK]`"), b01–b03 risk factors, b04 UoP/capitalization/dilution
("the pro forma columns are mostly blank; preserve that"), b05–b07 MD&A ("expect the
contractual-obligations table with columns Total/2026/.../Thereafter", "expect quarterly tables
with 7 quarter columns"), b08 business, b09–b11 management/exec-comp/relationships/capital-stock
("expect the Class A/N/F/T/E comparison table", "watch for the Sunset Provisions table spanning
multiple pages"), b12 capital stock, b13–b16 financial statements and notes, b17 Part II ("the
Item 13 expense table — keep `$*` and `*` literal; do NOT convert those to [BLANK]").

## 3. Retry prompts (issued when the validator flagged tables)

### Sunset Provisions fix (multi-page flattened prose)

```text
You are fixing one flattened SEC table transcription. Carbon-copy accuracy is critical.

SOURCE: <repo>/data/filings/sx1a_extracted.txt

The table "Sunset Provisions" starts at line 25336 and runs through approximately line 25780. It has two columns: "Class T Sunset Time" and "Class F Sunset Time", with row labels in a first column (Trigger / Continuation / etc. — read carefully). COMPLICATION: the table spans multiple pages; page furniture ("256", "Table of Contents") and REPEATED HEADER ROWS ("Class T Sunset Time" / "Class F Sunset Time") are interleaved INSIDE the cell text. Weave through them: drop furniture and repeated header lines, and stitch the prose fragments into complete cells. Where the extraction shows a fraction like "66 2/3", copy it EXACTLY as shown (do not normalize or reformat fractions).

Read lines 25330–25790 with the Read tool. Then OVERWRITE the file
<repo>/data/tables/sx1a/sx1a_b09_fix.json
with exactly this structure: { "batch": "sx1a_b09_fix", "tables": [ ... same schema ... ] }
Rules: cell text copied verbatim (only removing page furniture and repeated header rows); every row included; long prose cells are expected — keep them complete.
```

(The validator's aggregator then also propagated the fixed cells to the duplicate table at line
30618 after confirming the normalized source spans were identical except one word, and appended
an extraction note about the "66 23%" / "66 2/3%" flattening artifact.)

### Cover/summary respawn (lone-`$` blanks)

The original b00 prompt under-specified the cover table's blank cells; the respawn added:
"a lone `$` with no number is a blank cell — record it as `[BLANK]` (the blank pro forma columns
are all like this)."

## 4. Validation gates (not prompts — deterministic code)

- **Quote re-anchoring** (`04`): alphanumeric-normalized substring search of every record quote
  against the chunk line range, then the full document. Flags paraphrase; never silently drops.
- **Cell verification** (`05`): every non-`[BLANK]` cell must appear (alphanumeric-normalized)
  in its table's source span; bare-symbol cells (`$`, `*`) verified against raw text.
- **Cross-foot checks** (`06`): quarterly→9M→annual sums, GAAP→adjusted bridges, commitment
  aggregate vs components, balance-sheet identity, cash-flow tie-out, net-loss identity.
- Column-alignment is NOT caught by cell verification — key rows were additionally diffed against
  independently parsed anchors (see `06_reconcile.py`), which caught two right-shifted rows.
