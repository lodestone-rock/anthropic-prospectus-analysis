# Filing sources

All content in `data/` derives from these public SEC EDGAR filings:

| Filing | Filed | Accession | CIK | File no. |
|---|---|---|---|---|
| Form S-1 | 2026-10-26 | 0001628280-26-067168 | 0002130357 | 333-299633 |
| Form S-1/A Amendment No. 1 | 2026-11-02 | 0001628280-26-068676 | 0002130357 | 333-299633 |

- Filing index (S-1/A): https://www.sec.gov/Archives/edgar/data/2130357/000162828026068676/0001628280-26-068676-index.html
- Primary document (S-1/A): https://www.sec.gov/Archives/edgar/data/2130357/000162828026068676/anthropicpbc-sx1ax1.htm
- Filing index (S-1): https://www.sec.gov/Archives/edgar/data/2130357/000162828026067168/0001628280-26-067168-index.html
- Primary document (S-1): https://www.sec.gov/Archives/edgar/data/2130357/000162828026067168/anthropicpbc-sx1.htm
- Company submissions feed: https://data.sec.gov/submissions/CIK0002130357.json

Preceding confidential drafts (DRS 2026-06-01 and amendments through 2026-10-09) are on EDGAR
under the same CIK but were not used in this analysis.

## Extraction notes

- `sx1a_extracted.txt` / `sx1_extracted.txt` were produced by `methodology/tools/01_extract_text.py`
  from the EDGAR primary documents. Table cells are flattened to one-value-per-line by EDGAR's
  inline-XBRL rendering; the table swarm re-grids them.
- Line numbers cited throughout `data/` refer to these text files.

## Known text-layer artifacts

1. Fraction glyphs are lost: "66 2/3%" (filed HTML) → "66 23%" (any text extraction, including
   ours). Appears in the Sunset Provisions provisions and related risk text.
2. The consolidated balance sheet omits the Sept-30-2026 short-term-investments cell entirely.
   It imputes to $36,283M from the current-assets total (141,020 − 95,562 − 7,892 − 1,283) and
   matches the $36.3B market-risk disclosure.
3. FY2023–FY2025 statements are audited; Sept-30-2026 statements are unaudited.
