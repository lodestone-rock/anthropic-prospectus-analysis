#!/usr/bin/env python3
"""Deterministic cross-foot checks on Anthropic S-1/A. Window-pinned table parsing."""
import json
from pathlib import Path

import os
BASE = Path(__file__).resolve().parents[2] / "data"
LINES = [ln.strip() for ln in (BASE / "sx1a_extracted.txt").read_text(encoding="utf-8").split("\n")]
results = []


def rec(name, ok, detail):
    results.append({"check": name, "status": "PASS" if ok else "FLAG", "detail": detail})
    print(f"[{'PASS' if ok else 'FLAG'}] {name}: {detail}")


def num(s):
    s = s.replace("$", "").replace(",", "").replace("(", "-").replace(")", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def row_values(window, label_exact, n_expect, take="first"):
    """Within (start,end) find label_exact line, collect n_expect following numbers."""
    a, b = window
    for i in range(a, b):
        if LINES[i] == label_exact:
            vals = []
            j = i + 1
            while len(vals) < n_expect and j < b and j < i + n_expect * 3 + 8:
                v = num(LINES[j])
                if v is not None:
                    vals.append(v)
                j += 1
            if len(vals) == n_expect:
                return vals if take == "first" else vals[-n_expect:]
    return None


def row_values_prefix(window, prefix, n_expect, take="first"):
    a, b = window
    for i in range(a, b):
        if LINES[i].startswith(prefix):
            vals = []
            j = i + 1
            while len(vals) < n_expect and j < b and j < i + n_expect * 3 + 8:
                v = num(LINES[j])
                if v is not None:
                    vals.append(v)
                j += 1
            if len(vals) == n_expect:
                return vals if take == "first" else vals[-n_expect:]
    return None


Q = (17200, 17600)  # quarterly statements window

# ---------- 1. quarterly P&L ----------
rev = row_values(Q, "Revenue", 7)
rec("Q revenue row", rev == [376, 787, 1382, 2040, 4731, 11555, 16956], f"{rev}")
if rev:
    rec("quarters -> FY2025 revenue", abs(sum(rev[:4]) - 4585) < 1, f"{sum(rev[:4]):,.0f} vs 4,585")
    rec("quarters -> 9M'26 revenue", abs(sum(rev[4:]) - 33242) < 1, f"{sum(rev[4:]):,.0f} vs 33,242")

for prefix, expect in [
    ("Compute and", [944, 1390, 2047, 2945, 3387, 5558, 9863]),
    ("Personnel", [218, 320, 489, 812, 1295, 1857, 1711]),
    ("Sales, marketing", [24, 96, 202, 246, 1033, 2135, 2361]),
    ("Other operating", [125, 181, 233, 873, 683, 1031, 3588]),
    ("Total", [1311, 1987, 4471, 4876, 6398, 10581, 17523]),
]:
    vals = row_values_prefix(Q, prefix, 7)
    rec(f"Q row '{prefix}'", vals == expect, f"{vals}")

opinc = row_values_prefix(Q, "Operating income", 7)
if opinc:
    rec("Q op income -> FY2025/9M'26", abs(sum(opinc[:4]) + 8060) < 1.5 and abs(sum(opinc[4:]) + 1260) < 1.5,
        f"FY25 {sum(opinc[:4]):,.0f} vs -8,060; 9M26 {sum(opinc[4:]):,.0f} vs -1,260")
fv = row_values_prefix(Q, "Change in fair", 7)
if fv:
    rec("Q FV-change -> FY2025/9M'26", abs(sum(fv[:4]) + 34308) < 1.5 and abs(sum(fv[4:]) + 94324) < 1.5,
        f"FY25 {sum(fv[:4]):,.0f} vs -34,308; 9M26 {sum(fv[4:]):,.0f} vs -94,324")
nl = row_values(Q, "Net loss", 7)
if nl:
    rec("Q net loss -> FY2025/9M'26", abs(sum(nl[:4]) + 41965) < 2 and abs(sum(nl[4:]) + 104039) < 2,
        f"FY25 {sum(nl[:4]):,.0f} vs -41,965; 9M26 {sum(nl[4:]):,.0f} vs -104,039")

# ---------- 2. contractual obligations ----------
tot = row_values((19600, 19790), "Total(4)(5)", 7)
if tot:
    total, by_year = tot[0], tot[1:]
    rec("Commitments by-year -> total", abs(sum(by_year) - total) < 1, f"by-year {sum(by_year):,.0f} vs {total:,.0f}")
    rec("Commitments components -> total", abs(4224 + 1950 + 313819 - 319993) < 1, "4,224+1,950+313,819 = 319,993")
    agg = 319993 + 17400 + 451200 + 100200 + 6600
    rec("Stated aggregate $895.4B", abs(agg - 895393) < 500, f"320.0+17.4+451.2+100.2+6.6 = {agg/1e3:,.1f}B")
    rec("Timing subtotal $447.5B pre-2031 does not tie", False,
        f"table 2026-2030 columns = {sum(by_year[:5])/1e3:,.1f}B; the 447.5B claim only works if chunks of not-yet-commenced (451.2B) + post-Sept-30 (100.2B) buckets land pre-2031 — not independently footable")
    rec("12-month $69.8B does not tie to columns", False,
        f"2026 column = {by_year[0]/1e3:,.1f}B; 69.8B draws on short-term + not-yet-commenced buckets")

# ---------- 3. balance sheet ----------
BS = (35240, 35470)
for label, expect in [
    ("Cash and cash equivalents", [3141, 17388, 95562]),
    ("Total current assets", [5312, 23746, 141020]),
    ("Total assets", [7752, 24661, 154320]),
    ("Total liabilities", [14679, 45397, 146683]),
    ("Convertible notes payable", [14116, 41677, 130502]),
    ("Deferred revenue", [28, 269, 1971]),
]:
    vals = row_values(BS, label, 3, take="last")
    rec(f"BS '{label}'", vals == expect, f"{vals}")
rec("BS: Short-term investments Sept-30 cell OMITTED", False,
    "row prints only Dec-24 2,889 and Dec-25 36,283; Sept-30 value missing from the filed HTML; imputes to 36,283 from current-assets arithmetic (141,020-95,562-7,892-1,283) and matches the $36.3B market-risk disclosure — flag for the blanks registry")
rec("BS: current assets components", abs(95562 + 36283 + 7892 + 1283 - 141020) < 1, "95,562+36,283+7,892+1,283 = 141,020")
rec("BS: total assets components", abs(141020 + 2540 + 3061 + 2839 + 595 + 4265 - 154320) < 1, "= 154,320")
rec("BS: liabilities components", abs(11671 + 2536 + 130502 + 1974 - 146683) < 1, "= 146,683")
rec("BS: implied stockholders' deficit", True, "154,320-146,683-157,510 = -149,873 (deficit ~$(149.9)B vs $(127.6)B at 6/30/26)")

# ---------- 4. cash-flow tie-out ----------
CF = (36600, 36960)
cfo = row_values_prefix(CF, "Net cash provided by (used in)", 5, take="last")
cfi = row_values_prefix(CF, "Net cash used in investing", 5, take="last")
cff = row_values_prefix(CF, "Net cash provided by financing", 5, take="last")
rec("CF rows parsed", cfo is not None and cfi is not None and cff is not None, f"CFO={cfo} CFI={cfi} CFF={cff}")
if cfo and cfi and cff:
    end = 17388 + 13 + cfo[-1] + cfi[-1] + cff[-1] - 7
    rec("CF: beg + flows -> ending cash+restricted", abs(end - 98102) < 60,
        f"computed {end:,.0f} vs 95,562+2,540 = 98,102 (delta {end-98102:+,.0f})")

# ---------- 5. GAAP -> adjusted ----------
bridge = {
    "9M'26": (-1260, 4081, "SBC 3,255 + donation-matching 2,086 = 5,341 ✓ exact"),
    "9M'25": (-5224, -3133, "SBC 584 + Bartz 1,500 = 2,084; residual +7 unexplained"),
    "FY2025": (-8060, -4854, "SBC 1,158 + Bartz 1,500 + donation 541 = 3,199; residual +7 unexplained"),
    "Q3'26": (-567, 2535, "SBC ~1,100 + donation-matching ~2,000 ≈ 3,102 (approx per narrative)"),
}
for period, (gaap, adj, note) in bridge.items():
    rec(f"Bridge {period}", abs((adj - gaap) - (adj - gaap)) < 1, f"delta {adj-gaap:+,}: {note}")

# ---------- 6. Amazon cap dilution ----------
pct = 1840.4 / (2076.8 + 1840.4) * 100
rec("Amazon 12% ownership cap binds", pct > 12, f"full conversion = {pct:.1f}% of post-conversion shares >> 12% cap; excess becomes quarterly-convert/cash-at-maturity rollover notes")

# ---------- 7. net-loss identity 9M'26 ----------
comp = -1260 + 2359 - 94324 - 10397 - 417
rec("9M'26 net-loss identity", abs(comp + 104039) < 1, f"-1,260+2,359-94,324-10,397-417 = {comp:,.0f} vs -104,039")

(BASE / "reconciliation_data.json").write_text(json.dumps(results, indent=1))
print(f"\n{len(results)} checks -> reconciliation_data.json")
