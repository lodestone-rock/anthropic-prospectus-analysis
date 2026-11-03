# anthropic-prospectus-analysis

A numbers-only reconstruction of Anthropic, PBC's IPO prospectus (Form S-1, filed 2026-10-26, and
Form S-1/A Amendment No. 1, filed 2026-11-02), built with a swarm of parallel GLM agents.

Every dollar figure, percentage, ratio, share count, commitment, and stock-plan term from the
filing — and nothing else. All narrative, mission prose, and safety discussion stripped out.
Values the company left blank are preserved and highlighted as `[BLANK]`.

NOTE: not a financial advice, just me fooling around with LLMs so i don't have to read the entire prospectus ad nauseam 
## What's here

| Path | What |
|---|---|
| `print/PROSPECTUS_NUMBERS_ONLY_SX1A.pdf` | **The deliverable.** 129-page print-ready PDF of the S-1/A, numbers only. Filing structure preserved: cover → summary → risk factors → MD&A → financial statements (F-pages) → Part II (II-pages). Wide tables auto-rotate to landscape pages. |
| `print/prospectus_numbers_only_sx1a.html` | Same document as standalone HTML. |
| `data/PROSPECTUS_NUMBERS_ONLY.md` | Markdown source of the same reconstruction (both filings). |
| `data/master_numbers.csv` / `.json` | 4,608 extracted records — value, unit, period, category, verbatim quote, source line. 99.3% machine-verified. |
| `data/tables/sx1a/all_tables.json` | 111 financial-statement tables transcribed verbatim by the table swarm, every cell verified. |
| `data/blanks_registry.md` | Every value Anthropic withheld across both filings (305 records + 163 regex hits). |
| `data/RECONCILIATION.md` | 35 deterministic cross-foot checks and what they show. |
| `data/changed_between_filings.md` | Every number that moved between Oct 26 and Nov 2. |
| `data/REVIEW_STATUS.md` | Per-chunk human spot-check index. |
| `methodology/` | Full replication guide + verbatim swarm prompts + all tools. |

## Headline findings

1. **The arithmetic is clean; the framing is the story.** All seven disclosed quarters foot exactly
   to the annual and nine-month columns. The $895.4B commitment aggregate decomposes exactly — but
   the timing subtotals ($447.5B pre-2031, $69.8B next-12-months) cannot be footed from the
   disclosed by-year table.
2. **Gross-vs-net revenue is a ~$14.6B question.** 44% of 9M-2026 revenue is billed through CSP
   marketplaces under a principal (gross) treatment that OpenAI has publicly disputed.
3. **Amazon's 12% ownership cap means most of the $6.2B rollover notes cannot convert at IPO**
   (full conversion would be ~47% of post-conversion shares) — they become quarterly-converting or
   cash-repayable claims outside the headline share count.
4. **Q3-2026's operating swing** is driven by $5.0B of short-term compute that the filing itself
   says "costs significantly more" than multi-year commitments — and the adjusted-margin metric
   adds back SBC and donation charges but not that premium.
5. Plus: a balance-sheet cell that is simply absent (Sept-30 short-term investments), a fraction
   glyph ("66 2/3%") that flattens to "66 23%" in the text layer, and 305 withheld values.

Full analysis in `data/RECONCILIATION.md`.

## Replicate it

See [`methodology/PIPELINE.md`](methodology/PIPELINE.md) and
[`methodology/PROMPTS.md`](methodology/PROMPTS.md). The extracted filing texts are included in
`data/filings/`, so you can start from any step. You need: Python 3, `weasyprint`, `pypdf`, and an
OpenRouter API key (`export OPENROUTER_API_KEY=...`). Model used: `z-ai/glm-5.3-flash` — any
long-context instruct model works.

## Disclaimers

- This is an independent analysis of public SEC filings. Not affiliated with, endorsed by, or
  issued by Anthropic, PBC. Not investment advice.
- Every figure carries a verbatim quote and line anchor into the extracted filing text — verify
  against [SEC EDGAR](https://www.sec.gov/cgi-bin/browse-edgar?CIK=0002130357) before relying on
  anything.
- The reconstruction intentionally omits context. Read the actual prospectus before drawing
  conclusions.

## License

MIT — see [LICENSE](LICENSE). The underlying filings are public records of the U.S. Securities
and Exchange Commission.
