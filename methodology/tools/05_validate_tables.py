#!/usr/bin/env python3
"""Validate subagent table transcriptions cell-by-cell against source text; merge to all_tables.json."""
import json
import os
import re
import sys
from pathlib import Path

import os
BASE = Path(__file__).resolve().parents[2] / "data"
MAN = json.loads((BASE / "tables/sx1a/manifest.json").read_text())


def norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


lines = (BASE / "sx1a_extracted.txt").read_text(encoding="utf-8").split("\n")
norm_lines = [norm(x) for x in lines]


def span_text(a, b):
    lo = max(0, a - 3)
    hi = min(len(lines), b + 3)
    return "".join(norm_lines[lo:hi])


def span_raw(a, b):
    lo = max(0, a - 3)
    hi = min(len(lines), b + 3)
    return "\n".join(lines[lo:hi])


all_tables = []
report = []
for b in MAN["batches"]:
    p = BASE / b["out"]
    if not p.exists():
        report.append((b["batch"], "MISSING", 0, 0, 0.0))
        continue
    try:
        d = json.loads(p.read_text())
    except Exception as e:
        report.append((b["batch"], f"BAD JSON: {e}", 0, 0, 0.0))
        continue
    ntab = len(d.get("tables", []))
    nrows = ncells = nok = 0
    for t in d.get("tables", []):
        start = int(t.get("start_line") or t.get("caption_line") or 0)
        end = int(t.get("end_line") or start)
        st = span_text(max(1, start - 30), min(len(lines), end + 30))
        st_raw = span_raw(max(1, start - 30), min(len(lines), end + 30))
        bad = []
        for r in t.get("rows", []):
            nrows += 1
            for c in r.get("cells", []):
                if c == "[BLANK]":
                    continue
                ncells += 1
                nc = norm(c)
                if nc:
                    ok = nc in st
                else:  # bare "$", "*", symbols — verify raw
                    ok = c in st_raw
                if ok:
                    nok += 1
                else:
                    bad.append(c)
        t["batch"] = b["batch"]
        t["_bad_cells"] = bad
        if bad:
            t["_status"] = f"{len(bad)} bad cells"
        else:
            t["_status"] = "ok"
        all_tables.append(t)
    status = "OK" if (ncells == 0 or nok == ncells) else f"{ncells - nok} BAD"
    report.append((b["batch"], status, ntab, nrows, f"{nok}/{ncells}"))

# duplicate sunset table at 30618: reuse verified b09_fix cells (spans identical except "our"/"the")
_fixdone = False
fixp2 = BASE / "tables/sx1a/sx1a_b09_fix.json"
if fixp2.exists():
    try:
        fixt = json.loads(fixp2.read_text())["tables"][0]
        for t in all_tables:
            if abs(int(t.get("caption_line") or 0) - 30618) <= 60:
                t["rows"] = json.loads(json.dumps(fixt["rows"]))
                for r in t["rows"]:
                    for j, c in enumerate(r["cells"]):
                        if isinstance(c, str):
                            r["cells"][j] = c.replace(
                                "(i) the Class F common stock acting by decision",
                                "(i) our Class F common stock acting by decision")
                t["batch"] = "sx1a_b11+fix"
                t["_status"] = "ok"
                t["_bad_cells"] = []
                t["footnotes"] = (t.get("footnotes") or []) + [
                    "Extraction note: '66 23%' in the text layer corresponds to '66 2/3%' in the filed HTML "
                    "(fraction glyph lost in text flattening)."]
                _fixdone = True
    except Exception as e:
        print("30618 fix failed:", e)

# manual/fix batches override by caption_line
fixp = BASE / "tables/sx1a/sx1a_b09_fix.json"
if fixp.exists():
    try:
        fixd = json.loads(fixp.read_text())
        for ft in fixd.get("tables", []):
            ft["batch"] = "sx1a_b09_fix"
            ft["_status"] = "ok"
            ft["_bad_cells"] = []
            all_tables = [t for t in all_tables
                          if abs(int(t.get("caption_line") or 0) - int(ft.get("caption_line") or 0)) > 60]
            all_tables.append(ft)
    except Exception as e:
        print("fix file unreadable:", e)

# dedupe by caption_line proximity (overlapping windows)
all_tables.sort(key=lambda t: (int(t.get("caption_line") or 0)))
dedup = []
for t in all_tables:
    cl = int(t.get("caption_line") or 0)
    if dedup and abs(cl - int(dedup[-1].get("caption_line") or -999)) <= 60:
        # keep the one with more rows
        if len(t.get("rows", [])) > len(dedup[-1].get("rows", [])):
            dedup[-1] = t
        continue
    dedup.append(t)

out = BASE / "tables/sx1a/all_tables.json"
out.write_text(json.dumps(dedup, indent=1))

print(f"{'batch':10} {'status':>16} {'tables':>6} {'rows':>6}  cells verified")
for b, st, nt, nr, ck in report:
    print(f"{b:10} {st:>16} {nt:>6} {nr:>6}  {ck}")
print(f"\n{len(all_tables)} tables raw -> {len(dedup)} after dedupe -> {out.name}")
bad = [t for t in dedup if t.get("_bad_cells")]
print(f"{len(bad)} tables with bad cells:")
for t in bad[:10]:
    print(f"  line {t.get('caption_line')} {t.get('caption','')[:60]!r}: {t['_bad_cells'][:6]}")
