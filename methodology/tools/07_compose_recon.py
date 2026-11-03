#!/usr/bin/env python3
"""Compose RECONCILIATION.md from reconciliation_data.json + curated findings."""
import json
from pathlib import Path

import os
BASE = Path(__file__).resolve().parents[2] / "data"
checks = json.loads((BASE / "reconciliation_data.json").read_text())

passed = [c for c in checks if c["status"] == "PASS"]
flagged = [c for c in checks if c["status"] == "FLAG"]

md = [
    "# RECONCILIATION — cross-foot and consistency checks (S-1/A Amendment No. 1)",
    "",
    "All checks computed deterministically from the extracted filing text",
    "(`sx1a_extracted.txt`, same bytes as the EDGAR primary document).",
    "Analyst commentary lives **only here** — never in PROSPECTUS_NUMBERS_ONLY.md.",
    "",
    f"**{len(checks)} checks: {len(passed)} foot exactly, {len(flagged)} flagged for interpretation.**",
    "",
    "## Flags requiring interpretation (not arithmetic errors)",
    "",
]
for c in flagged:
    md += [f"### ⚑ {c['check']}", "", c["detail"], ""]
md += ["## Checks that foot exactly", ""]
for c in passed:
    md.append(f"- ✓ **{c['check']}** — {c['detail']}")
md += [
    "",
    "## Substantive observations (from the checks above)",
    "",
    "1. **The quarterly statements internally foot perfectly** — all seven quarters sum exactly to the",
    "   FY2025 and 9M 2026 columns on every line (revenue, all opex lines, operating income, FV changes,",
    "   net loss). Whatever one thinks of the revenue-recognition policy, the arithmetic is clean.",
    "2. **$895.4B aggregate decomposes exactly** into its five disclosed buckets (320.0 + 17.4 + 451.2 +",
    "   100.2 + 6.6). But the **timing subtotals ($447.5B pre-2031, $69.8B next-12-months) cannot be",
    "   footed** from the disclosed by-year table — they require undisclosed assumptions about when the",
    "   $451.2B of not-yet-commenced leases actually hit. Treat any press breakdown of that $895.4B by",
    "   year as unverifiable from the filing.",
    "3. **Short-term compute is the Q3 swing factor.** Q3 op income swung $(1.54)B QoQ on $5.0B of",
    "   short-term compute ('costs significantly more than comparable compute procured under our",
    "   multi-year commitments') plus a $2.0B non-cash donation-matching charge. Adjusted operating",
    "   margin fell 19% → 15% for the same reason.",
    "4. **The adjusted-margin definition adds back donation-matching and SBC but not short-term compute",
    "   premiums** — the bridge is arithmetically exact for 9M'26 (5,341 = 3,255 SBC + 2,086 donation),",
    "   with tiny (+7) unexplained residuals in 9M'25/FY2025.",
    "5. **Amazon's 12% ownership cap means most of the $6.2B of rollover notes cannot convert at IPO**",
    "   (full conversion would be ~47% of post-conversion shares). The excess converts quarterly at the",
    "   lowest of fixed price / IPO price / trailing VWAP, or is repaid in cash at maturity — a contingent",
    "   claim on the company that the headline share counts do not reflect.",
    "6. **Balance-sheet cell dropout:** the Sept-30 short-term investments figure is absent from the filed",
    "   balance-sheet row; it imputes to $36,283M from the current-assets total and matches the $36.3B",
    "   market-risk disclosure. Cosmetic, but worth knowing before quoting the row.",
    "7. **Stockholders' deficit widened $(22.3)B in one quarter** ($(127.6)B at 6/30 → ~$(149.9)B implied",
    "   at 9/30), driven by the $23.3B Q3 net loss — while cash stayed ~flat because the losses are",
    "   non-cash FV revaluations.",
    "8. **Cash-flow tie-out has a +$50M residual** against the ending cash+restricted balance (computed",
    "   98,152 vs 98,102) — within rounding of the individually listed sub-lines; not a red flag on its",
    "   own.",
    "",
    "## Revenue-recognition policy (the OpenAI dispute) — as filed",
    "",
    "The filing states 44% of 9M-2026 revenue (47% FY2025, 32% FY2024, 11% FY2023) is billed through CSP",
    "marketplaces (AWS/GCP/Azure), with Anthropic maintaining separate contracts with end customers and",
    "paying the CSP a fee; it claims principal status and books the full contract value as revenue, with",
    "the platform cut in sales & marketing. OpenAI has publicly told investors this inflates revenue 'by",
    "billions' versus net-basis presentation. The filing's own numbers make the gross-vs-net question",
    "material: on a net basis the marketplace share would enter revenue only as the fee, shrinking the",
    "top line by up to roughly $14.6B of 9M revenue (44% × $33.2B) — though Anthropic would also remove",
    "the associated S&M cost. The accounting choice does not change operating income; it changes the",
    "revenue base against which all growth rates and margins are quoted.",
]
(BASE / "RECONCILIATION.md").write_text("\n".join(md), encoding="utf-8")
print(f"RECONCILIATION.md: {len(checks)} checks ({len(flagged)} flagged)")
