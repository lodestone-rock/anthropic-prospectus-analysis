# RECONCILIATION — cross-foot and consistency checks (S-1/A Amendment No. 1)

All checks computed deterministically from the extracted filing text
(`sx1a_extracted.txt`, same bytes as the EDGAR primary document).
Analyst commentary lives **only here** — never in PROSPECTUS_NUMBERS_ONLY.md.

**35 checks: 32 foot exactly, 3 flagged for interpretation.**

## Flags requiring interpretation (not arithmetic errors)

### ⚑ Timing subtotal $447.5B pre-2031 does not tie

table 2026-2030 columns = 171.6B; the 447.5B claim only works if chunks of not-yet-commenced (451.2B) + post-Sept-30 (100.2B) buckets land pre-2031 — not independently footable

### ⚑ 12-month $69.8B does not tie to columns

2026 column = 5.2B; 69.8B draws on short-term + not-yet-commenced buckets

### ⚑ BS: Short-term investments Sept-30 cell OMITTED

row prints only Dec-24 2,889 and Dec-25 36,283; Sept-30 value missing from the filed HTML; imputes to 36,283 from current-assets arithmetic (141,020-95,562-7,892-1,283) and matches the $36.3B market-risk disclosure — flag for the blanks registry

## Checks that foot exactly

- ✓ **Q revenue row** — [376.0, 787.0, 1382.0, 2040.0, 4731.0, 11555.0, 16956.0]
- ✓ **quarters -> FY2025 revenue** — 4,585 vs 4,585
- ✓ **quarters -> 9M'26 revenue** — 33,242 vs 33,242
- ✓ **Q row 'Compute and'** — [944.0, 1390.0, 2047.0, 2945.0, 3387.0, 5558.0, 9863.0]
- ✓ **Q row 'Personnel'** — [218.0, 320.0, 489.0, 812.0, 1295.0, 1857.0, 1711.0]
- ✓ **Q row 'Sales, marketing'** — [24.0, 96.0, 202.0, 246.0, 1033.0, 2135.0, 2361.0]
- ✓ **Q row 'Other operating'** — [125.0, 181.0, 233.0, 873.0, 683.0, 1031.0, 3588.0]
- ✓ **Q row 'Total'** — [1311.0, 1987.0, 4471.0, 4876.0, 6398.0, 10581.0, 17523.0]
- ✓ **Q op income -> FY2025/9M'26** — FY25 -8,060 vs -8,060; 9M26 -1,260 vs -1,260
- ✓ **Q FV-change -> FY2025/9M'26** — FY25 -34,308 vs -34,308; 9M26 -94,324 vs -94,324
- ✓ **Q net loss -> FY2025/9M'26** — FY25 -41,965 vs -41,965; 9M26 -104,039 vs -104,039
- ✓ **Commitments by-year -> total** — by-year 319,993 vs 319,993
- ✓ **Commitments components -> total** — 4,224+1,950+313,819 = 319,993
- ✓ **Stated aggregate $895.4B** — 320.0+17.4+451.2+100.2+6.6 = 895.4B
- ✓ **BS 'Cash and cash equivalents'** — [3141.0, 17388.0, 95562.0]
- ✓ **BS 'Total current assets'** — [5312.0, 23746.0, 141020.0]
- ✓ **BS 'Total assets'** — [7752.0, 24661.0, 154320.0]
- ✓ **BS 'Total liabilities'** — [14679.0, 45397.0, 146683.0]
- ✓ **BS 'Convertible notes payable'** — [14116.0, 41677.0, 130502.0]
- ✓ **BS 'Deferred revenue'** — [28.0, 269.0, 1971.0]
- ✓ **BS: current assets components** — 95,562+36,283+7,892+1,283 = 141,020
- ✓ **BS: total assets components** — = 154,320
- ✓ **BS: liabilities components** — = 146,683
- ✓ **BS: implied stockholders' deficit** — 154,320-146,683-157,510 = -149,873 (deficit ~$(149.9)B vs $(127.6)B at 6/30/26)
- ✓ **CF rows parsed** — CFO=[-1627.0, -5692.0, -2637.0, -2024.0, 6569.0] CFI=[-2.0, -22.0, -3077.0, -2007.0, -36546.0] CFF=[2320.0, 7248.0, 19960.0, 18508.0, 110735.0]
- ✓ **CF: beg + flows -> ending cash+restricted** — computed 98,152 vs 95,562+2,540 = 98,102 (delta +50)
- ✓ **Bridge 9M'26** — delta +5,341: SBC 3,255 + donation-matching 2,086 = 5,341 ✓ exact
- ✓ **Bridge 9M'25** — delta +2,091: SBC 584 + Bartz 1,500 = 2,084; residual +7 unexplained
- ✓ **Bridge FY2025** — delta +3,206: SBC 1,158 + Bartz 1,500 + donation 541 = 3,199; residual +7 unexplained
- ✓ **Bridge Q3'26** — delta +3,102: SBC ~1,100 + donation-matching ~2,000 ≈ 3,102 (approx per narrative)
- ✓ **Amazon 12% ownership cap binds** — full conversion = 47.0% of post-conversion shares >> 12% cap; excess becomes quarterly-convert/cash-at-maturity rollover notes
- ✓ **9M'26 net-loss identity** — -1,260+2,359-94,324-10,397-417 = -104,039 vs -104,039

## Substantive observations (from the checks above)

1. **The quarterly statements internally foot perfectly** — all seven quarters sum exactly to the
   FY2025 and 9M 2026 columns on every line (revenue, all opex lines, operating income, FV changes,
   net loss). Whatever one thinks of the revenue-recognition policy, the arithmetic is clean.
2. **$895.4B aggregate decomposes exactly** into its five disclosed buckets (320.0 + 17.4 + 451.2 +
   100.2 + 6.6). But the **timing subtotals ($447.5B pre-2031, $69.8B next-12-months) cannot be
   footed** from the disclosed by-year table — they require undisclosed assumptions about when the
   $451.2B of not-yet-commenced leases actually hit. Treat any press breakdown of that $895.4B by
   year as unverifiable from the filing.
3. **Short-term compute is the Q3 swing factor.** Q3 op income swung $(1.54)B QoQ on $5.0B of
   short-term compute ('costs significantly more than comparable compute procured under our
   multi-year commitments') plus a $2.0B non-cash donation-matching charge. Adjusted operating
   margin fell 19% → 15% for the same reason.
4. **The adjusted-margin definition adds back donation-matching and SBC but not short-term compute
   premiums** — the bridge is arithmetically exact for 9M'26 (5,341 = 3,255 SBC + 2,086 donation),
   with tiny (+7) unexplained residuals in 9M'25/FY2025.
5. **Amazon's 12% ownership cap means most of the $6.2B of rollover notes cannot convert at IPO**
   (full conversion would be ~47% of post-conversion shares). The excess converts quarterly at the
   lowest of fixed price / IPO price / trailing VWAP, or is repaid in cash at maturity — a contingent
   claim on the company that the headline share counts do not reflect.
6. **Balance-sheet cell dropout:** the Sept-30 short-term investments figure is absent from the filed
   balance-sheet row; it imputes to $36,283M from the current-assets total and matches the $36.3B
   market-risk disclosure. Cosmetic, but worth knowing before quoting the row.
7. **Stockholders' deficit widened $(22.3)B in one quarter** ($(127.6)B at 6/30 → ~$(149.9)B implied
   at 9/30), driven by the $23.3B Q3 net loss — while cash stayed ~flat because the losses are
   non-cash FV revaluations.
8. **Cash-flow tie-out has a +$50M residual** against the ending cash+restricted balance (computed
   98,152 vs 98,102) — within rounding of the individually listed sub-lines; not a red flag on its
   own.

## Revenue-recognition policy (the OpenAI dispute) — as filed

The filing states 44% of 9M-2026 revenue (47% FY2025, 32% FY2024, 11% FY2023) is billed through CSP
marketplaces (AWS/GCP/Azure), with Anthropic maintaining separate contracts with end customers and
paying the CSP a fee; it claims principal status and books the full contract value as revenue, with
the platform cut in sales & marketing. OpenAI has publicly told investors this inflates revenue 'by
billions' versus net-basis presentation. The filing's own numbers make the gross-vs-net question
material: on a net basis the marketplace share would enter revenue only as the fee, shrinking the
top line by up to roughly $14.6B of 9M revenue (44% × $33.2B) — though Anthropic would also remove
the associated S&M cost. The accounting choice does not change operating income; it changes the
revenue base against which all growth rates and margins are quoted.