#!/usr/bin/env python3
"""Run GLM extraction over prospectus chunks via OpenAI-compatible API."""
import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import os
BASE = Path(__file__).resolve().parents[2] / "data"

API_KEY = os.environ["OPENROUTER_API_KEY"]  # never hardcode
BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
MODEL = os.environ.get("SWARM_MODEL", "z-ai/glm-5.3-flash")

SYSTEM = """You are a forensic financial-data extractor working on a chunk of an SEC Form S-1/A prospectus (Anthropic, PBC, Nov 2 2026 amendment).

Output: JSONL only. One JSON object per line. No markdown fences, no commentary, no blank lines.

Record schema:
{"kind":"inline"|"table_row"|"blank","label":"short label","values":["values exactly as printed"],"unit":"$M|$B|%|x|shares|per-share|years|count|...","period":"FY2023|FY2024|FY2025|Q1'26|Q2'26|Q3'26|9M 2025|9M 2026|as of 2026-09-30|2026-2033|...","category":"offering|financials|commitments|metrics|stock_plan|governance|legal|other","quote":"verbatim span of 5-40 words from the chunk containing the figure"}

Rules:
1. Financial-statement and numeric tables: emit one "table_row" per line item, with EVERY column value in order in "values". If column headers appear in the chunk, add "columns":[...] once for the table using kind "table_row" with label "HEADER".
2. Narrative dollar figures, percentages, ratios, multiples, counts (customers, employees, shares), per-share amounts, date-bound obligations: one "inline" record each.
3. Blanked-out values (e.g. "$ and $", "$*", "approximately $,", "up to an additional shares", "$ per share" with no number): kind "blank", values ["[BLANK]"], quote the sentence fragment.
4. NEVER retype or round numbers — copy exactly as printed. The "quote" field must be copied verbatim from the chunk text (it is used to re-anchor the record by grep).
5. EXCLUDE: page numbers, page headers/footers, exhibit numbering, addresses, phone numbers, EIN/IRS numbers, statute section numbers with no dollar amount, pure boilerplate with no figures.
6. Include repeated figures wherever they recur (dedup happens later).
7. Stock-plan content (share classes, splits, plan reserves, vesting, exercise prices, RSU/option grants, conversion prices, ownership caps, dilution) → category "stock_plan". Be exhaustive there.
8. Be exhaustive. Missing a real number is the worst failure mode. Hundreds of records per chunk is normal."""

USER_TMPL = """Chunk: {cid} — filing {filing}, section: {section} (source lines {start}-{end}).

Extract every hard number per the rules. Output JSONL only.

CHUNK TEXT:
<<<
{text}
>>>"""


def extract_one(c):
    cid = c["id"]
    out_raw = BASE / "extractions" / f"{cid}.raw.txt"
    out_rec = BASE / "extractions" / f"{cid}.json"
    if out_rec.exists():
        return cid, "cached", 0

    text = (BASE / c["file"]).read_text(encoding="utf-8")
    body = USER_TMPL.format(
        cid=cid, filing=c["filing"], section=c["section"],
        start=c["start_line"], end=c["end_line"], text=text,
    )
    payload = json.dumps(
        {
            "model": MODEL,
            "temperature": 0,
            "max_tokens": 32000,
            "reasoning_effort": "low",
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": body},
            ],
        }
    ).encode()

    last_err = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(
                f"{BASE_URL}/chat/completions",
                data=payload,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
            )
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=900) as r:
                resp = json.loads(r.read())
            dt = time.time() - t0
            content = resp["choices"][0]["message"]["content"]
            finish = resp["choices"][0].get("finish_reason", "?")
            usage = resp.get("usage", {})
            out_raw.write_text(content, encoding="utf-8")

            records = []
            for ln in content.split("\n"):
                ln = ln.strip().strip("`")
                if not ln or ln.startswith("```"):
                    continue
                if ln.startswith("{"):
                    try:
                        records.append(json.loads(ln))
                    except json.JSONDecodeError:
                        m = re.search(r"\{.*\}", ln)
                        if m:
                            try:
                                records.append(json.loads(m.group(0)))
                            except Exception:
                                pass
            out_rec.write_text(json.dumps(
                {"chunk": cid, "section": c["section"], "filing": c["filing"],
                 "finish_reason": finish, "usage": usage,
                 "n_records": len(records), "records": records}, indent=1))
            flag = "" if finish == "stop" else f"  [finish={finish}]"
            return cid, f"ok {len(records)} recs, {usage.get('total_tokens','?')} tok, {dt:.0f}s{flag}", len(records)
        except urllib.error.HTTPError as e:
            last_err = f"HTTP {e.code}: {e.read()[:200]}"
            time.sleep(5 * (attempt + 1) ** 2)
        except Exception as e:
            last_err = str(e)[:200]
            time.sleep(5 * (attempt + 1) ** 2)
    return cid, f"FAILED: {last_err}", 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated chunk ids")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    manifest = json.loads((BASE / "manifest.json").read_text())
    chunks = manifest["chunks"]
    if args.only:
        want = set(args.only.split(","))
        chunks = [c for c in chunks if c["id"] in want]

    print(f"{len(chunks)} chunks, model={MODEL}, endpoint={BASE_URL}, workers={args.workers}")
    results = {}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(extract_one, c): c["id"] for c in chunks}
        for f in as_completed(futs):
            cid, msg, n = f.result()
            results[cid] = msg
            print(f"  {cid}: {msg}")
    failed = [c for c, m in results.items() if m.startswith("FAILED") or "[finish=" in m]
    print(f"\ndone. failed/incomplete: {failed if failed else 'none'}")


if __name__ == "__main__":
    main()
