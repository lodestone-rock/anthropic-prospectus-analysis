#!/usr/bin/env python3
"""Assemble PROSPECTUS_NUMBERS_ONLY.md from digests + changed_between_filings.md."""
import json
from pathlib import Path

import os
BASE = Path(__file__).resolve().parents[2] / "data"
manifest = json.loads((BASE / "manifest.json").read_text())

# ---------- PROSPECTUS_NUMBERS_ONLY.md ----------
parts = [
    "# Anthropic, PBC — Prospectus, Numbers Only",
    "",
    "Reconstructed from the public S-1 (2026-10-26) and S-1/A Amendment No. 1 (2026-11-02).",
    "All figures as filed. `[BLANK]` marks values the company left blank.",
    "Narrative, risk discussion, and analyst commentary are stripped — numbers only.",
    "Each section footer carries provenance (source lines, extracting agent, verification rate).",
    "",
    "---",
    "",
]
for filing in ("sx1a", "sx1"):
    title = ("# FILING: S-1/A — Amendment No. 1 (filed November 2, 2026)" if filing == "sx1a"
             else "# FILING: S-1 — Original (filed October 26, 2026)")
    parts += [title, ""]
    for c in [x for x in manifest["chunks"] if x["filing"] == filing]:
        dp = BASE / "digest" / f"{c['id']}.md"
        if not dp.exists():
            continue
        body = dp.read_text(encoding="utf-8")
        # strip the digest's own H1, keep metadata block + records
        lines = body.split("\n")
        body = "\n".join(lines[1:]) if lines and lines[0].startswith("# ") else body
        parts += [f"## {c['section']} (`{c['id']}`)", "", body.strip(), "", "---", ""]
(BASE / "PROSPECTUS_NUMBERS_ONLY.md").write_text("\n".join(parts), encoding="utf-8")
print("PROSPECTUS_NUMBERS_ONLY.md assembled")

# ---------- changed_between_filings.md ----------
curated = """# Changed between the two filings (Oct 26 S-1 → Nov 2 S-1/A)

## Numbers that moved

| Item | Original S-1 | Amendment No. 1 | Note |
|---|---|---|---|
| Google CSP minimum spend | ≥$114.5B (Apr 2026–Jul 2033) | **≥$121.3B** | +$6.8B; agreements amended through Oct 2026 |
| Microsoft commitment end | May 2033 | **June 2033** | date extended one month |
| Aggregate committed spend | **blank** ("approximately $ billion") | **$895.4B** | first quantification: 320.0 table + 17.4 short-term + 451.2 not-commenced + 100.2 post-Sept + 6.6 post-Sept short-term |
| 12-month commitment due | **blank** | **$69.8B** | was "approximately $ of these commitments" |
| Post-balance-sheet commitments | $245B (post–June 30) + $21B short-term | **$100.2B (post–Sept 30)** + $6.6B short-term | different as-of date, not directly comparable |
| Q3 2026 financials | **blank** (statements stopped at June 30) | **added**: revenue $16,956M, op loss $(567)M, net loss $(23,291)M, adjusted op income $2,535M | investor-day number was $16.8B pre-final |
| CSP marketplace revenue share | 48% (H1 2026) | **44%** (9M 2026) | AR via marketplaces 58% → 52% |
| Cash + ST investments | $131.7B (June 30) | **$131.845B** (Sept 30) | cash $95.6B / ST $36.3B (ST cell omitted from BS, imputed) |
| Convertible notes payable | $108.6B (June 30) | **$130.5B** (Sept 30) | NPA derivative obligations |
| Balance sheet date | June 30, 2026 | **Sept 30, 2026** | full Q3 statements, quarterly table, cash flows added |
| SpaceXAI capacity | ~$3.1B/month at full capacity | same; **full delivery now December 2026**; non-cancelable periods end Jan/Mar 2027 | timing pinned |
| Broadcom 2026 Lease Arrangement | assigned partly to a third party (Q2 2026) | **Oct 2026: partial assignment to a newly formed SPV financing entity** | rent unchanged; cash in restricted account; NPA can finance quarterly rent |
| Capital raised (aggregate) | $141.1B as of June 30 | $141.1B as of Sept 30 | same figure, moved date |
| Revenue growth stat | +1,368% YoY (Q2) vs compute +300% | **+1,127% YoY (Q3) vs compute +382%** | ratio deteriorating each quarter |
| Model naming | "Claude Opus 5.5" | **"Opus 5.5"** | branding shortened throughout |

## Blanks in BOTH filings (still withheld)

- IPO price range: "between $ and $"
- Shares offered by company / selling stockholders
- Underwriters' option shares
- Net proceeds (and sensitivity per $1.00 of price / per 1.0M shares)
- Underwriting discount table
- Offering expense table (all lines "$*"): SEC registration, FINRA, listing, printing, legal, accounting, transfer agent, misc, total
- Delivery date ("on or about ."), cover date ("Subject to Completion. Dated .")
- Dilution per-share figures; pro forma as-adjusted columns
- Convertible-notes post-IPO %: "approximately % of our Class N common stock and % of our total outstanding common stock"

## New in Amendment No. 1 (no original counterpart)

- ~47M post–Sept 30 RSU grants (service-vesting, ~4 yr)
- Oct 2026: 28.0M Class N shares issued for donation-matching accrual
- Oct 2026: executive severance/acceleration amendments; RSU remeasurement at modification-date fair value
- Oct 2026: charter amendment — authorized Class N raised to 7,975.7M; 846.8M Class N approved for Public Benefit Fund
- 2026 Equity Incentive Plan (2,950.0M shares) and 2026 ESPP (160.0M shares), effective day before effectiveness
- Convertible-notes note: $6,203M Amazon rollover notes; conversion at lower of fixed price ($2.0928 / $5.0478) or IPO price; 12% Amazon ownership cap; quarterly conversion at lowest of fixed/IPO/10-day VWAP post-IPO; cash repayment at maturity for uncapped remainder; ~1,840.4M Class N shares issuable pre-cap
- Marketplace principal-vs-agent revenue-recognition policy with 44% of revenue / 52% of AR attached
"""
(BASE / "changed_between_filings.md").write_text(curated, encoding="utf-8")
print("changed_between_filings.md written")
