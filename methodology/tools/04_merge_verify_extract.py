#!/usr/bin/env python3
"""Merge chunk extractions: quote-verify, re-anchor line numbers, build digest files,
master CSV/JSON, blanks registry, and REVIEW_STATUS.md."""
import bisect
import csv
import json
import os
import re
from pathlib import Path

import os
BASE = Path(__file__).resolve().parents[2] / "data"
FILING_NAME = {"sx1a": "S-1/A (Amendment No. 1, filed 2026-11-02)", "sx1": "S-1 (original, filed 2026-10-26)"}


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


texts = {}
for f in ("sx1a", "sx1"):
    lines = (BASE / f"{f}_extracted.txt").read_text(encoding="utf-8").split("\n")
    nl = [norm(x) for x in lines]
    joined = "".join(nl)
    cum, t = [], 0
    for x in nl:
        t += len(x)
        cum.append(t)
    texts[f] = {"lines": lines, "norm": nl, "joined": joined, "cum": cum}


def verify_quote(filing, quote, hint_start, hint_end):
    """Find quote (alnum-normalized) in filing text; return (found, start_line, end_line)."""
    q = norm(quote)
    if len(q) < 8:
        return False, None, None
    a = texts[filing]["norm"]
    joined = texts[filing]["joined"]
    n = len(a)
    probes = [q, q[:80], q[-80:], q[:50]]
    for probe in probes:
        lo, hi = max(0, hint_start - 3), min(n, hint_end + 3)
        window = "".join(a[lo:hi])
        if probe in window:
            first = probe[:20]
            for i in range(lo, hi):
                if first and first in a[i]:
                    return True, i + 1, min(i + 8, hi + 1)
            return True, lo + 1, hi + 1
        if probe in joined:
            pos = joined.find(probe)
            return True, bisect.bisect_right(texts[filing]["cum"], pos) + 1, \
                bisect.bisect_right(texts[filing]["cum"], pos + len(probe)) + 1
    return False, None, None


manifest = json.loads((BASE / "manifest.json").read_text())
all_records = []
status_rows = []

for c in manifest["chunks"]:
    if c.get("status") == "superseded":
        continue
    p = BASE / "extractions" / f"{c['id']}.json"
    if not p.exists():
        status_rows.append((c, "MISSING", 0, 0))
        continue
    d = json.loads(p.read_text())
    recs = d["records"]
    verified = 0
    out = []
    for r in recs:
        quote = r.get("quote", "")
        ok, ln, ln2 = verify_quote(c["filing"], quote, c["start_line"], c["end_line"])
        if ok:
            verified += 1
        r2 = dict(r)
        r2["chunk"] = c["id"]
        r2["filing"] = c["filing"]
        r2["section"] = c["section"]
        r2["src_line"] = ln
        r2["verified"] = ok
        out.append(r2)
    all_records.extend(out)
    status_rows.append((c, d.get("finish_reason", "?"), len(recs), verified))

    # ---- per-chunk digest ----
    cats = {}
    for r in out:
        cats.setdefault(r.get("category", "other"), []).append(r)
    md = [
        f"# `{c['id']}` — {c['section']}",
        "",
        f"- **Filing:** {FILING_NAME[c['filing']]} · source lines {c['start_line']}–{c['end_line'] - 1}",
        f"- **Extracted by:** GLM (`z-ai/glm-5.3-flash` via OpenRouter) · finish: {d.get('finish_reason')}",
        f"- **Records:** {len(out)} · quote-verified against source text: {verified}/{len(out)}",
        f"- **Review:** read source at `chunks/{c['id']}.txt` (or lines {c['start_line']}–{c['end_line']} of `{c['filing']}_extracted.txt`)",
        "",
    ]
    for cat in sorted(cats):
        md.append(f"## {cat} ({len(cats[cat])} records)")
        md.append("")
        for r in cats[cat]:
            vals = ", ".join(str(v) for v in r.get("values", []))
            flag = "" if r["verified"] else " ⚠️*unverified*"
            vflag = " **[BLANK]**" if r.get("kind") == "blank" else ""
            md.append(
                f"- **{r.get('label','?')}**{vflag} = {vals} `{r.get('unit','') or ''}` "
                f"({r.get('period','') or 'n/a'}) — line {r['src_line']}{flag}\n"
                f"  > “{r.get('quote','')}”"
            )
        md.append("")
    (BASE / "digest" / f"{c['id']}.md").write_text("\n".join(md), encoding="utf-8")

# ---- master csv/json ----
cols = ["filing", "chunk", "section", "category", "kind", "label", "values", "unit", "period", "src_line", "verified", "quote"]
with open(BASE / "master_numbers.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(cols)
    for r in all_records:
        w.writerow([
            r["filing"], r["chunk"], r["section"], r.get("category", ""), r.get("kind", ""),
            r.get("label", ""), "|".join(str(v) for v in r.get("values", [])), r.get("unit", ""),
            r.get("period", ""), r["src_line"] or "", r["verified"], r.get("quote", ""),
        ])
(BASE / "master_numbers.json").write_text(json.dumps(all_records, indent=1))

# ---- blanks registry ----
blanks = [r for r in all_records if r.get("kind") == "blank"]
md = ["# Blanks registry — every withheld value across both filings", "",
      "Model-extracted blanks (each anchored to a source line) plus the deterministic regex sweep (`blanks_regex.json`).",
      ""]
for filing in ("sx1a", "sx1"):
    rows = [r for r in blanks if r["filing"] == filing]
    md.append(f"## {FILING_NAME[filing]} — {len(rows)} blank records")
    md.append("")
    for r in sorted(rows, key=lambda x: (x["section"], x["src_line"] or 0)):
        md.append(f"- **{r.get('label','?')}** ({r['section']}, line {r['src_line']}) — “{r.get('quote','')}”")
    md.append("")
(BASE / "blanks_registry.md").write_text("\n".join(md), encoding="utf-8")

# ---- review status ----
md = ["# REVIEW_STATUS — human spot-check index", "",
      "| chunk | filing | section | lines | finish | records | verified | digest |",
      "|---|---|---|---|---|---|---:|---|"]
for c, finish, n, v in status_rows:
    md.append(f"| `{c['id']}` | {c['filing']} | {c['section']} | {c['start_line']}–{c['end_line']} | {finish} | {n} | {v}/{n} | [`digest/{c['id']}.md`](digest/{c['id']}.md) |")
tot = sum(n for _, _, n, _ in status_rows)
ver = sum(v for _, _, _, v in status_rows)
md.append("")
md.append(f"**Total: {tot} records, {ver} quote-verified ({ver / tot * 100 if tot else 0:.1f}%)**")
(BASE / "REVIEW_STATUS.md").write_text("\n".join(md), encoding="utf-8")

print(f"{len(all_records)} records; {len(blanks)} blanks; verified {ver}/{tot} ({ver / tot * 100 if tot else 0:.1f}%)")
