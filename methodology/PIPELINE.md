# Replication pipeline

End-to-end guide to rebuilding everything in this repo from the SEC filings. Total cost on a
flash-tier model was a few dollars; wall-clock was ~1 hour including verification.

## Files and accessions

| Filing | Date | Accession | Primary document |
|---|---|---|---|
| Form S-1 | 2026-10-26 | 0001628280-26-067168 | `anthropicpbc-sx1.htm` |
| Form S-1/A Amendment No. 1 | 2026-11-02 | 0001628280-26-068676 | `anthropicpbc-sx1ax1.htm` |

CIK 0002130357, file no. 333-299633. EDGAR filing index:
`https://www.sec.gov/Archives/edgar/data/2130357/000162828026068676/0001628280-26-068676-index.html`
(and `...000162828026067168/...` for the original). Use a declared User-Agent header when fetching
EDGAR (they 403 bare clients). Extracted texts are included at `data/filings/*.txt` so steps 2+
work offline.

## Step 1 — text extraction

EDGAR inline-XBRL HTML flattens tables to one-cell-per-line. `01_extract_text.py` converts HTML to
text (block tags → newlines, scripts/styles stripped):

```bash
python3 methodology/tools/01_extract_text.py filing.htm filing.txt
```

Run it identically on both filings — downstream diffing requires the same extractor for both.

## Step 2 — section-aligned chunking

`02_build_chunks.py` cuts each filing into 16 chunks aligned to the filing's own section anchors
(cover, summary, risk factors ×3, use-of-proceeds/capitalization/dilution, MD&A ×2, business,
management, capital stock, underwriting, financial statements ×3, Part II), writing `chunks/` and
`manifest.json`. Section alignment matters: an agent that receives half a table or half a note
will miss numbers.

```bash
python3 methodology/tools/02_build_chunks.py
```

## Step 3 — extraction swarm

`03_run_extract_swarm.py` fires one API call per chunk (see `PROMPTS.md` §1 for the exact
prompt). Key requirements:

- `temperature: 0`, JSONL output (one record per line — parseable even when truncated)
- values copied **verbatim**; every record carries a **verbatim quote** of 5–40 words containing
  the figure (used to re-anchor by grep — never trust model-generated line numbers)
- blanks are first-class records (`kind: "blank"`), not gaps

```bash
export OPENROUTER_API_KEY=sk-or-...
python3 methodology/tools/03_run_extract_swarm.py --workers 6
```

Observed: 36 calls (18 chunks × 2 filings), ~700k input tokens total, 27–185 s per chunk at
6 workers. Two chunks hit the 32k output cap (`finish_reason=length`) — fix: split the chunk in
half, re-run those halves, mark the original superseded in the manifest. One call returned null
content — a plain retry fixed it.

## Step 4 — merge, quote-verify, re-anchor

`04_merge_verify_extract.py` re-anchors every record: it normalizes quotes and source text to
alphanumeric-only and greps each quote against the chunk's line range (fast path) or the whole
file (fallback). Record gets an absolute `src_line`; unverifiable quotes are flagged, never
silently dropped. Outputs: `master_numbers.csv/.json`, per-chunk `digest/*.md`, `blanks_registry.md`,
`REVIEW_STATUS.md`.

Run a deterministic blank sweep alongside (regexes like `\$ and \$`, `\$\*`,
`approximately \$,`, `up to an additional shares`) — blanks are regex-shaped and this pass has
perfect recall on them; see `blanks_regex.json` for the patterns.

## Step 5 — table swarm

The record-level `table_row` extractions are lossy for big grids, so a second swarm transcribes
tables wholesale:

1. Slice each filing into overlapping windows (step 2,600 lines, window 3,200 — tables at edges
   survive via overlap; dedupe later by `caption_line` ±60).
2. Spawn one agent per window (18 for the S-1/A) with the prompt in `PROMPTS.md` §2. Each agent
   finds **every** tabular presentation fully inside its window — captions, statement titles, or
   bare column-header rows — and transcribes to the JSON schema.
3. Validate every cell (`05_validate_tables.py`): alphanumeric-normalized substring check of each
   cell against the source span; blank cells skipped; bare-symbol cells (`$`, `*`) checked raw.
   Dedupe overlapping windows, keeping the transcription with more rows.

Observed: 171 raw tables → 111 after dedupe, ~3,450 cells, 0 unverified. Two known failure modes
and fixes (both surfaced by the validator, both fixed by one re-scoped retry agent):
- **Column shift** on rows whose last cell is missing from the source (the filing itself omits
  two Sept-30 cells) — agents right-aligned values into the last columns. Fix: hand-patch from
  balance-sheet arithmetic, add an imputation footnote.
- **Multi-page flattened prose tables** (sunset provisions): page furniture and repeated header
  rows are interleaved inside cells. Fix: one re-scoped agent per table instructed to weave
  fragments and drop furniture.

A second copy of the sunset table elsewhere in the filing got the same drift — the aggregator
reuses verified cells when the normalized source spans match (they did, except one word).

## Step 6 — reconciliation

`06_reconcile.py` runs deterministic cross-foot checks by parsing the tables back out of the text
with pinned line windows:

- quarterly sums → 9M columns → (FY2025 quarters →) FY2025 annual
- GAAP → adjusted bridges per period
- commitment aggregate vs its components; by-year columns vs totals
- balance-sheet identity and component sums; cash-flow tie-out
- net-loss identity; ownership-cap dilution math

`07_compose_recon.py` renders `RECONCILIATION.md`. Commentary lives ONLY there — never in the
numbers-only reconstruction.

## Step 7 — deliverables

- `08_build_outputs.py` assembles `PROSPECTUS_NUMBERS_ONLY.md` (filing order, digests inlined,
  provenance footers) and `changed_between_filings.md`.
- `09_build_pdf.py` renders the print PDF via WeasyPrint: cover-page mimic, roman-numeral front
  matter, arabic body, **F-page and Part II counter restarts**, running section headers, and
  **landscape named pages** for tables with ≥6 data columns (numbering continues across the
  orientation switch). Also emits the standalone HTML.

```bash
python3 methodology/tools/09_build_pdf.py sx1a   # and sx1
```

## Verification stats (this run)

| Layer | Result |
|---|---|
| Inline records | 4,608 extracted, 4,575 quote-verified (99.3%) |
| Table cells | ~3,450 verified, 0 unverified after fixes |
| Cross-foot checks | 35 (32 foot exactly, 3 flagged for interpretation) |
| Blanks | 305 model-extracted + 163 regex hits |
| Human spot-checks | `REVIEW_STATUS.md` indexes every chunk; 33 flagged quotes manually reviewed (all paraphrase artifacts) |

## Known extraction artifacts (worth knowing before you start)

- "66 2/3%" in the filed HTML flattens to "66 23%" in any text layer — a fraction glyph is lost.
  If you see "66 23%" in our tables, the filed document reads 66 2/3%.
- The Sept-30-2026 short-term-investments cell is absent from the filed balance sheet (imputes to
  $36,283M from the current-assets total; matches the $36.3B market-risk disclosure).
- Risk-factor windows contain no tables; empty batches there are correct.
