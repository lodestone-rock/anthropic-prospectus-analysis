#!/usr/bin/env python3
import sys
"""Render numbers-only prospectus PDFs: separate page-numbered groups merged via pypdf."""
import html
import io
import json
from pathlib import Path

import pypdf
from weasyprint import HTML

import os
BASE = Path(__file__).resolve().parents[2] / "data"

UNDERWRITERS = [
    "Goldman Sachs & Co. LLC", "Morgan Stanley", "J.P. Morgan", "Citigroup", "Barclays",
    "Wells Fargo Securities", "BofA Securities", "Deutsche Bank Securities", "RBC Capital Markets",
    "UBS Investment Bank", "BMO Capital Markets", "BNP PARIBAS", "Credit Agricole CIB", "Jefferies",
    "Mizuho", "MUFG", "TD Securities", "BTIG", "Cantor", "Capital One Securities",
    "Macquarie Capital", "Société Générale",
]

# canonical groups in filing order; members are chunk-section keys
GROUPS = [
    ("cover-terms", "Cover Page — Offering Terms (as filed)", ["cover+TOC"], "main"),
    ("summary", "Prospectus Summary", ["prospectus-summary"], "main"),
    ("risk", "Risk Factors", ["risk-factors-1", "risk-factors-2", "risk-factors-3"], "main"),
    ("uop", "Use of Proceeds · Dividend Policy · Capitalization · Dilution",
     ["use-of-proceeds-capitalization-dilution"], "main"),
    ("mda", "Management’s Discussion and Analysis of Financial Condition and Results of Operations",
     ["mda-1", "mda-2-liquidity-commitments"], "main"),
    ("business", "Business · Legal Proceedings", ["business-legal-proceedings"], "main"),
    ("mgmt", "Management · Executive Compensation · Certain Relationships",
     ["management-execcomp-relationships", "management-execcomp-A", "management-execcomp-B"], "main"),
    ("capstock", "Description of Capital Stock · Shares Eligible for Future Sale",
     ["capital-stock-shares-eligible"], "main"),
    ("uw", "Underwriting · Legal Matters · Experts", ["underwriting-legal-experts"], "main"),
    ("fin", "Financial Statements and Notes", ["financial-statements-1"], "fpg"),
    ("notes", "Notes to Consolidated Financial Statements",
     ["financial-statements-2-notes-A", "financial-statements-2-notes-B", "financial-statements-3-notes"], "fpg"),
    ("part2", "Part II — Information Not Required in the Prospectus", ["part-ii"], "ii"),
]

CSS = """
@page { size: Letter; margin: 19mm 15mm 17mm 15mm;
  @top-center { content: string(secname); font-size: 7pt; color: #666; }
  @bottom-left { content: "Numbers-only reconstruction — not the filed prospectus"; font-size: 6.5pt; color: #999; }
  @bottom-right { content: counter(page); font-size: 8.5pt; color: #333; } }
@page cover { @top-center { content: none } @bottom-left { content: none } @bottom-right { content: none } }
@page front { @bottom-right { content: counter(page, lower-roman); font-size: 8.5pt; color: #333; } }
@page fpg { @bottom-right { content: "F-" counter(page); font-size: 8.5pt; color: #333; } }
@page ii { @bottom-right { content: "II-" counter(page); font-size: 8.5pt; color: #333; } }
@page land-main { size: Letter landscape; margin: 15mm 13mm 15mm 13mm;
  @top-center { content: string(secname); font-size: 7pt; color: #666; }
  @bottom-left { content: "Numbers-only reconstruction — not the filed prospectus"; font-size: 6.5pt; color: #999; }
  @bottom-right { content: counter(page); font-size: 8.5pt; color: #333; } }
@page land-fpg { size: Letter landscape; margin: 15mm 13mm 15mm 13mm;
  @top-center { content: string(secname); font-size: 7pt; color: #666; }
  @bottom-left { content: "Numbers-only reconstruction — not the filed prospectus"; font-size: 6.5pt; color: #999; }
  @bottom-right { content: "F-" counter(page); font-size: 8.5pt; color: #333; } }
@page land-ii { size: Letter landscape; margin: 15mm 13mm 15mm 13mm;
  @top-center { content: string(secname); font-size: 7pt; color: #666; }
  @bottom-left { content: "Numbers-only reconstruction — not the filed prospectus"; font-size: 6.5pt; color: #999; }
  @bottom-right { content: "II-" counter(page); font-size: 8.5pt; color: #333; } }
.land-main { page: land-main; }
.land-fpg { page: land-fpg; }
.land-ii { page: land-ii; }
table.wide { font-size: 6.3pt; }
table.wide th { font-size: 6.1pt; }
table.wide td { padding: 1.5pt 2pt; }
body { font-family: "DejaVu Sans", sans-serif; font-size: 8.2pt; color: #111; line-height: 1.35; }
.pg-cover { page: cover; text-align: center; }
.pg-front { page: front; }
.pg-main { page: main; }
.pg-fpg { page: fpg; }
.pg-ii { page: ii; }
h1 { string-set: secname content(); font-size: 13pt; border-bottom: 1.5pt solid #333; padding-bottom: 4pt; page-break-before: always; }
.pg-cover h1, .pg-front h1 { page-break-before: auto; }
.pg-main > div:first-child h1, .pg-fpg > div:first-child h1, .pg-ii > div:first-child h1 { page-break-before: auto; }
h1.cont { font-size: 11pt; }
.src { font-size: 6.8pt; color: #888; margin: 2pt 0 10pt 0; }
table.rec { border-collapse: collapse; width: 100%; margin: 5pt 0 9pt 0; font-size: 7.1pt; }
table.rec th { background: #eee; border: 0.5pt solid #999; padding: 2pt 3pt; text-align: right; font-size: 6.9pt; }
table.rec td { border: 0.5pt solid #bbb; padding: 2pt 3pt; text-align: right; }
table.rec td.lbl { text-align: left; font-weight: bold; width: 26%; }
table.rec tr { page-break-inside: avoid; }
.tcap { font-weight: bold; font-size: 8.6pt; margin-top: 10pt; }
.cnote { font-size: 7.2pt; color: #666; margin-bottom: 3pt; }
.fn { font-size: 6.8pt; color: #555; margin: 2pt 0 0 0; }
.tsrc { font-size: 6.2pt; color: #aaa; margin: 2pt 0 8pt 0; }
td.blankcell { background: #ffe9a8; font-weight: bold; text-align: center; }
tr.spanner td { font-weight: bold; background: #f5f5f5; text-align: left; letter-spacing: 0.5px; }
p.item { margin: 3.5pt 0 0 0; }
p.q { margin: 0 0 5pt 0; font-size: 6.8pt; color: #777; font-style: italic; }
.lbl2 { font-weight: bold; }
.per { color: #666; }
.blank { background: #ffe9a8; padding: 0 3pt; font-weight: bold; border: 0.5pt solid #d8b93c; }
.toc a { text-decoration: none; color: #111; display: flex; margin: 4pt 0; font-size: 9.5pt; }
.toc .dots { flex: 1; border-bottom: 1px dotted #999; margin: 0 4pt 3pt 4pt; }
.about p { margin: 5pt 0; font-size: 9pt; }
.cover-big { font-size: 15pt; font-weight: bold; letter-spacing: 2px; }
.cover-co { font-size: 21pt; font-weight: bold; margin: 26pt 0 8pt 0; }
.cover-blank { color: #8a6d00; font-weight: bold; background: #ffe9a8; padding: 0 4pt; }
.cover-note { font-size: 8pt; text-align: justify; margin: 10pt 40pt; color: #333; }
.uw { column-count: 2; column-gap: 26pt; font-size: 9pt; margin: 14pt 40pt; text-align: center; }
.uw div { margin: 2.5pt 0; }
.tag { margin-top: 22pt; font-size: 8pt; color: #8a6d00; font-weight: bold; }
"""


def esc(x):
    return html.escape(str(x), quote=True)


def render_events(events, grp="main"):
    out = []
    for _, kind, obj in events:
        if kind == "table":
            out.append(render_table(obj, grp))
        else:
            r = obj
            label = esc(r.get("label", ""))
            vals = ", ".join(str(v) for v in r.get("values", []))
            val_html = "<span class='blank'>[BLANK]</span>" if r.get("kind") == "blank" else esc(vals)
            unit, period = esc(r.get("unit") or ""), esc(r.get("period") or "")
            line = f" — line {r['src_line']}" if r.get("src_line") else ""
            out.append(f"<p class='item'><span class='lbl2'>{label}</span> = {val_html}"
                       + (f" <span class='per'>{unit}</span>" if unit else "")
                       + (f" <span class='per'>({period})</span>" if period else "") + "</p>")
            if r.get("quote"):
                out.append(f"<p class='q'>“{esc(r['quote'])}”{line}</p>")
    return "\n".join(out)


def render_table(t, grp="main"):
    inner_cap = esc(t.get("caption", ""))
    note = esc(t.get("column_note") or "")
    cols = t.get("columns") or []
    rows = t.get("rows") or []
    foots = t.get("footnotes") or []
    cl = t.get("caption_line")
    batch = t.get("batch", "")
    wide = len(t.get("columns") or []) >= 7
    cls = f"land-{grp}" if wide else ""
    wrap_open = f"<div class='{cls}'>" if wide else ""
    wrap_close = "</div>" if wide else ""
    wcls = " wide" if wide else ""
    h = [wrap_open + f"<div class='tcap'>{inner_cap}</div>"]
    if note:
        h.append(f"<div class='cnote'>{note}</div>")
    if cols:
        h.append(f"<table class='rec{wcls}'><tr><th style='text-align:left'>Item</th>" +
                 "".join(f"<th>{esc(c)}</th>" for c in cols[1:] or cols) + "</tr>")
        ncols = len(cols)
        for r in rows:
            cells = r.get("cells", [])
            if cells and all(c == "[BLANK]" for c in cells):
                h.append(f"<tr class='spanner'><td colspan='{ncols}'>{esc(r.get('label',''))}</td></tr>")
                continue
            cs = []
            for c in cells:
                if wide:
                    # financial-statement grids: blank cells render empty, true to the filing
                    cs.append("<td></td>" if (c == "[BLANK]" or str(c).strip() in ("$", "")) else f"<td>{esc(c)}</td>")
                else:
                    cs.append("<td class='blankcell'>[BLANK]</td>" if (c == "[BLANK]" or str(c).strip() == "$") else f"<td>{esc(c)}</td>")
            h.append(f"<tr><td class='lbl'>{esc(r.get('label',''))}</td>" + "".join(cs) + "</tr>")
        h.append("</table>")
    else:
        for r in rows:
            vals = ", ".join(str(c) for c in r.get("cells", []))
            h.append(f"<p class='item'><span class='lbl2'>{esc(r.get('label',''))}</span> = {esc(vals)}</p>")
    for fline in foots:
        h.append(f"<p class='fn'>{esc(fline)}</p>")
    h.append(f"<div class='tsrc'>source line {cl} · transcribed by {esc(batch)}</div>")
    h.append(wrap_close)
    return "".join(h)


def render_records(records):
    out, table_rows, captions = [], [], None

    def flush():
        nonlocal table_rows, captions
        if not table_rows:
            captions = None
            return
        ncols = max(len(r.get("values", [])) for r in table_rows)
        t = ['<table class="rec">']
        if captions:
            t.append("<tr><th style='text-align:left'>Item</th>" +
                     "".join(f"<th>{esc(c)}</th>" for c in captions) + "</tr>")
        for r in table_rows:
            t.append(f"<tr><td class='lbl'>{esc(r.get('label',''))}</td>" +
                     "".join(f"<td>{esc(v)}</td>" for v in r.get("values", [])) + "</tr>")
        t.append("</table>")
        out.append("".join(t))
        table_rows, captions = [], None

    for r in records:
        if r.get("kind") == "table_row":
            if r.get("label") == "HEADER":
                flush()
                captions = r.get("values", [])
            else:
                table_rows.append(r)
            continue
        flush()
        label = esc(r.get("label", ""))
        vals = ", ".join(str(v) for v in r.get("values", []))
        val_html = "<span class='blank'>[BLANK]</span>" if r.get("kind") == "blank" else esc(vals)
        unit, period = esc(r.get("unit") or ""), esc(r.get("period") or "")
        line = f" — line {r['src_line']}" if r.get("src_line") else ""
        out.append(f"<p class='item'><span class='lbl2'>{label}</span> = {val_html}"
                   + (f" <span class='per'>{unit}</span>" if unit else "")
                   + (f" <span class='per'>({period})</span>" if period else "") + "</p>")
        if r.get("quote"):
            out.append(f"<p class='q'>“{esc(r['quote'])}”{line}</p>")
    flush()
    return "\n".join(out)


def page(name):
    return f"<style>{CSS}</style>"


def build(filing):
    manifest = json.loads((BASE / "manifest.json").read_text())
    chunks = [c for c in manifest["chunks"]
              if c["filing"] == filing and c.get("status") != "superseded"]
    chunks.sort(key=lambda c: c["start_line"])
    recs_by_sec = {}
    for c in chunks:
        p = BASE / "extractions" / f"{c['id']}.json"
        if not p.exists():
            continue
        recs_by_sec.setdefault(c["section"], []).extend(json.loads(p.read_text())["records"])

    # curated tables (subagent transcriptions) mapped to chunk sections by caption line
    curated = []
    tpath = BASE / f"tables/{filing}/all_tables.json"
    if tpath.exists():
        for t in json.loads(tpath.read_text()):
            cl = int(t.get("caption_line") or 0)
            for c in chunks:
                if c["start_line"] <= cl < c["end_line"]:
                    curated.append((cl, c["section"], t))
                    break
    cur_by_sec = {}
    for cl, sec, t in curated:
        cur_by_sec.setdefault(sec, []).append((cl, t))

    FILING_DESC = {
        "sx1a": "Form S-1/A · Amendment No. 1 — filed with the SEC on November 2, 2026 (accession 0001628280-26-068676)",
        "sx1": "Form S-1 — filed with the SEC on October 26, 2026 (accession 0001628280-26-067168)",
    }[filing]

    # ---------- cover ----------
    b = "<span class='cover-blank'>[BLANK]</span>"
    uw = "".join(f"<div>{esc(u)}</div>" for u in UNDERWRITERS)
    cover_html = (page("cover") + f"""
<div class="pg-cover">
  <div class="cover-big">SUBJECT TO COMPLETION — DATED {b}</div>
  <div style="margin-top:10pt" class="cover-big">PRELIMINARY PROSPECTUS</div>
  <div style="font-size:11pt;margin-top:16pt">{b} shares of Class A common stock</div>
  <div class="cover-co">Anthropic, PBC</div>
  <div class="cover-note">This is an initial public offering of shares of Class A common stock of Anthropic, PBC.
  We are selling {b} shares of Class A common stock and the selling stockholders identified in this prospectus are
  selling an additional {b} shares of Class A common stock. We will not receive any proceeds from the sale of
  shares of our Class A common stock by any of the selling stockholders.</div>
  <div class="cover-note">Prior to this offering, there has been no public market for our Class A common stock.
  It is currently estimated that the initial public offering price per share will be between {b} and {b}.
  We have applied to list our Class A common stock on the Nasdaq Global Select Market under the symbol <b>ANT</b>.</div>
  <div style="font-size:8.5pt;margin:14pt 60pt">
    Initial public offering price — per share {b} · total {b}<br>
    Underwriting discount — per share {b} · total {b}<br>
    Proceeds, before expenses, to Anthropic, PBC — per share {b} · total {b}<br>
    Proceeds, before expenses, to selling stockholders — per share {b} · total {b}<br>
    Underwriters’ option: up to an additional {b} shares · Delivery: New York, NY, on or about {b}
  </div>
  <div class="uw">{uw}</div>
  <div style="font-size:9pt;margin-top:10pt">Prospectus dated {b}</div>
  <div class="tag">▲ NUMBERS-ONLY RECONSTRUCTION — generated from SEC EDGAR filings; not issued by Anthropic, PBC</div>
</div>""")

    # ---------- per page-group docs (continuous numbering within group) ----------
    pagegrps = {"main": [], "fpg": [], "ii": []}
    for gid, title, members, grp in GROUPS:
        recs, srcs = [], []
        for m in members:
            recs.extend(recs_by_sec.get(m, []))
            srcs.append(m)
        if recs:
            pagegrps[grp].append((gid, title, recs, srcs))

    group_pdfs, group_pages, group_html = {}, {}, {}
    for grp, items in pagegrps.items():
        if not items:
            continue
        body = []
        for gid, title, recs, srcs in items:
            # determine section key for this group's records: use members
            members_secs = [m for m in srcs]
            cur = []
            for ms in members_secs:
                cur.extend(cur_by_sec.get(ms, []))
            src_bits = []
            if cur:
                src_bits.append(f"{len(cur)} curated tables")
            n_inline = sum(1 for r in recs if r.get("kind") != "table_row")
            src_bits.append(f"{n_inline} inline records")
            if cur:
                events = [(cl, "table", t) for cl, t in cur]
                events += [(r.get("src_line") or 0, "rec", r) for r in recs
                           if r.get("kind") != "table_row"]
                events.sort(key=lambda e: e[0])
                rendered = render_events(events, grp)
            else:
                rendered = render_records(recs)
            body.append(f"<div id='g_{gid}'><h1>{esc(title)}</h1>"
                        f"<div class='src'>chunks: {esc(', '.join(srcs))} · {', '.join(src_bits)}</div>"
                        f"{rendered}</div>")
        group_html[grp] = "".join(body)
        doc = HTML(string=page(grp) + f"<body><div class='pg-{grp}'>{''.join(body)}</div></body>").render()
        pages = {}
        for pi, p in enumerate(doc.pages):
            for aname in p.anchors:
                pages.setdefault(aname, pi)
        group_pages[grp] = pages
        buf = io.BytesIO()
        doc.write_pdf(buf)
        group_pdfs[grp] = buf.getvalue()

    # ---------- front (About + TOC) ----------
    n_recs = sum(len(r) for g in GROUPS for r in [recs_by_sec.get(m, []) for _, _, m, _ in GROUPS for m in g] ) if False else 0
    total = sum(len(recs_by_sec.get(m, [])) for _, _, ms, _ in GROUPS for m in ms)
    toc_html = []
    for gid, title, members, grp in GROUPS:
        pages = group_pages.get(grp, {})
        anchor = f"g_{gid}"
        if anchor not in pages:
            continue
        first = pages[anchor] + 1
        prefix = {"main": "", "fpg": "F-", "ii": "II-"}[grp]
        toc_html.append(f"<a><span class='t'>{esc(title)}</span><span class='dots'></span>"
                        f"<span class='pg'>{prefix}{first}</span></a>")
    front_html = (page("front") + f"""
<div class="pg-front about"><h1 style="page-break-before:auto">About This Document</h1>
<p>A <b>numbers-only reconstruction</b> of Anthropic, PBC’s {esc(FILING_DESC)}, built for printed
side-by-side comparison with the filed document.</p>
<p><b>Included:</b> every dollar figure, percentage, ratio, share count, commitment, table row, per-share
amount, and stock-plan term present in the filing — in the filing’s original section order, with verbatim
source quotes and line anchors into the extracted filing text (<code>{filing}_extracted.txt</code>).</p>
<p><b>Omitted:</b> all narrative, risk discussion, mission prose, and boilerplate. Withheld values appear
as highlighted <span class="blank">[BLANK]</span> markers.</p>
<p>Page numbering follows the filing’s convention: front matter in roman numerals; body in arabic numerals;
financial statements and notes as <b>F-pages</b>; Part II as <b>II-pages</b>.</p>
<p><b>{total} extracted records</b> · 99.3% quote-verified (REVIEW_STATUS.md) · deterministic cross-foot
checks (RECONCILIATION.md). Analyst commentary is confined to RECONCILIATION.md and never appears here.</p>
<p style="color:#8a6d00"><b>Not an SEC filing. Not issued or approved by Anthropic, PBC. Verify against
EDGAR before relying on any figure.</b></p>
</div>
<div style="page-break-before:always" class="pg-front toc"><h1>Table of Contents</h1>
{''.join(toc_html)}
</div>""")

    # ---------- render & merge ----------
    merge = []
    cover_pdf = io.BytesIO()
    HTML(string=cover_html).write_pdf(cover_pdf)
    merge.append(cover_pdf.getvalue())
    front_pdf = io.BytesIO()
    HTML(string=front_html).write_pdf(front_pdf)
    merge.append(front_pdf.getvalue())
    for grp in ("main", "fpg", "ii"):
        if grp in group_pdfs:
            merge.append(group_pdfs[grp])

    # colophon appended to part2/main end: build tiny doc
    colo = page("ii") + f"""<div class="pg-ii"><h1>Colophon</h1><p style="font-size:8.5pt">
Generated 2026-11-03 from SEC EDGAR primary documents.<br>
S-1: accession 0001628280-26-067168 (2026-10-26).<br>
S-1/A: accession 0001628280-26-068676 (2026-11-02).<br><br>
Pipeline: section-aligned chunking → parallel GLM extraction (z-ai/glm-5.3-flash via OpenRouter,
temperature 0) → quote re-anchoring by grep → deterministic cross-foot checks.
Raw extractions, per-chunk digests, and check results: <code>scratchpad/anthropic_ipo/numbers_digest/</code>.
Analyst commentary is confined to RECONCILIATION.md and never appears in this document.</p></div>"""
    colo_pdf = io.BytesIO()
    HTML(string=colo).write_pdf(colo_pdf)
    merge.append(colo_pdf.getvalue())

    writer = pypdf.PdfWriter()
    for blob in merge:
        r = pypdf.PdfReader(io.BytesIO(blob))
        for p in r.pages:
            writer.add_page(p)
    combined = ("<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<title>Anthropic S-1/A numbers-only</title><style>{CSS}</style></head><body>"
                + cover_html + front_html
                + "".join(f"<div class='pg-{g}'>{group_html[g]}</div>" for g in ("main", "fpg", "ii") if g in group_html)
                + colo + "</body></html>")
    (BASE / f"prospectus_numbers_only_{filing}.html").write_text(combined, encoding="utf-8")
    out = BASE / ("PROSPECTUS_NUMBERS_ONLY_SX1A.pdf" if filing == "sx1a" else "PROSPECTUS_NUMBERS_ONLY_S1.pdf")
    with open(out, "wb") as f:
        writer.write(f)
    print(f"{out.name}: {len(writer.pages)} pages, {out.stat().st_size/1e6:.1f} MB")


if __name__ == "__main__":
    for f in (["sx1a"] if len(sys.argv) < 2 else sys.argv[1:]):
        build(f)
