#!/usr/bin/env python3
"""Slice both filings into section-aligned chunks + deterministic blank sweep."""
import json
import os
import re
from pathlib import Path

import os
BASE = Path(__file__).resolve().parents[2] / "data"
CH = BASE / "chunks"
CH.mkdir(exist_ok=True)

# (start, end, label) — 1-based inclusive start, exclusive end. Anchors from grep.
SX1A = [
    (1, 360, "cover+TOC"),
    (360, 3300, "prospectus-summary"),
    (3300, 7000, "risk-factors-1"),
    (7000, 10700, "risk-factors-2"),
    (10700, 13266, "risk-factors-3"),
    (13266, 13982, "use-of-proceeds-capitalization-dilution"),
    (13982, 18614, "mda-1"),
    (18614, 20448, "mda-2-liquidity-commitments"),
    (20448, 25780, "business-legal-proceedings"),
    (25780, 29964, "management-execcomp-relationships"),
    (29964, 32916, "capital-stock-shares-eligible"),
    (32916, 34896, "underwriting-legal-experts"),
    (34896, 38500, "financial-statements-1"),
    (38500, 41500, "financial-statements-2-notes"),
    (41500, 44770, "financial-statements-3-notes"),
    (44770, 45537, "part-ii"),
]
SX1 = [
    (1, 354, "cover+TOC"),
    (354, 2402, "prospectus-summary"),
    (2402, 6200, "risk-factors-1"),
    (6200, 9700, "risk-factors-2"),
    (9700, 13120, "risk-factors-3"),
    (13120, 13798, "use-of-proceeds-capitalization-dilution"),
    (13798, 18000, "mda-1"),
    (18000, 19786, "mda-2-liquidity-commitments"),
    (19786, 25104, "business-legal-proceedings"),
    (25104, 29292, "management-execcomp-relationships"),
    (29292, 32194, "capital-stock-shares-eligible"),
    (32194, 34152, "underwriting-legal-experts"),
    (34152, 37600, "financial-statements-1"),
    (37600, 40800, "financial-statements-2-notes"),
    (40800, 43916, "financial-statements-3-notes"),
    (43916, 44679, "part-ii"),
]

manifest = {"chunks": []}
for filing, spec in (("sx1a", SX1A), ("sx1", SX1)):
    lines = (BASE / "filings" / f"{filing}_extracted.txt").read_text(encoding="utf-8").split("\n")
    for i, (a, b, label) in enumerate(spec, 1):
        cid = f"{filing}_{i:02d}"
        seg = "\n".join(lines[a - 1 : b - 1])
        p = CH / f"{cid}.txt"
        p.write_text(seg, encoding="utf-8")
        manifest["chunks"].append(
            {
                "id": cid,
                "filing": filing,
                "section": label,
                "start_line": a,
                "end_line": b,
                "n_lines": b - a,
                "file": str(p.relative_to(BASE)),
                "status": "pending",
            }
        )

(BASE / "manifest.json").write_text(json.dumps(manifest, indent=1))
print(f"{len(manifest['chunks'])} chunks written")

# ---- deterministic blank sweep ----
PATTERNS = {
    "price_range": re.compile(r"\$ and \$|\$ to \$|between \$"),
    "expense_star": re.compile(r"\$\*"),
    "blank_proceeds": re.compile(r"approximately \$[,;\s]|approximately \$\."),
    "blank_per_share": re.compile(r"of \$ per share|price of \$ per"),
    "blank_up_to_shares": re.compile(r"up to an additional shares"),
    "blank_billion": re.compile(r"approximately \$ billion|of \$ billion"),
    "blank_of_total": re.compile(r"approximately \$ of"),
    "blank_for_period": re.compile(r"to \$ for the|from \$ to \$"),
    "dated_blank": re.compile(r"Dated \.|on or about \."),
    "percent_blank": re.compile(r"approximately % of|% of our"),
    "shares_blank": re.compile(r"(purchase|sell|issuable|issue) (up to )? an additional shares"),
}
found = []
for c in manifest["chunks"]:
    text = (BASE / c["file"]).read_text(encoding="utf-8")
    for ln_no_off, ln in enumerate(text.split("\n")):
        for name, pat in PATTERNS.items():
            if pat.search(ln):
                found.append(
                    {
                        "filing": c["filing"],
                        "line": c["start_line"] + ln_no_off,
                        "pattern": name,
                        "text": ln.strip()[:200],
                        "chunk": c["id"],
                    }
                )
(BASE / "blanks_regex.json").write_text(json.dumps(found, indent=1))
print(f"{len(found)} regex blank hits")
