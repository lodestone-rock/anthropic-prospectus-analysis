#!/usr/bin/env python3
"""Group GNU-diff hunks over token streams into readable change regions."""
import re
import subprocess
import sys

GAP = 45  # words between hunks to merge into one region
MAXSHOW = 700  # tokens to show per side


def toks(path):
    text = open(path, encoding="utf-8", errors="replace").read().lower()
    text = text.replace("\u2019", "'").replace("\u2014", "-")
    return re.findall(r"[a-z0-9'$%.+-]+", text)


a = toks(sys.argv[1])
b = toks(sys.argv[2])

out = subprocess.run(
    ["diff", "-U0", sys.argv[1], sys.argv[2]], capture_output=True, text=True
).stdout

hunks = []  # (a1, a2, b1, b2) 0-based half-open
for m in re.finditer(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", out, re.M):
    a1 = int(m.group(1)) - 1
    a2 = a1 + (int(m.group(2)) if m.group(2) is not None else 1)
    b1 = int(m.group(3)) - 1
    b2 = b1 + (int(m.group(4)) if m.group(4) is not None else 1)
    hunks.append((a1, a2, b1, b2))

# merge hunks closer than GAP on either side
regions = []
for h in hunks:
    if regions and (h[0] - regions[-1][1] < GAP or h[2] - regions[-1][3] < GAP):
        pa1, pa2, pb1, pb2, _ = regions[-1]
        regions[-1] = (pa1, max(pa2, h[1]), pb1, max(pb2, h[2]), True)
    else:
        regions.append((h[0], h[1], h[2], h[3], False))

# recompute b ranges properly after merging (they drift when both files shift)
# simpler: rebuild each region by diffing the slice with padding
def render(text, lo, hi):
    seg = text[lo:hi]
    return " ".join(seg)


print(f"hunks: {len(hunks)}  regions: {len(regions)}\n")
for i, (a1, a2, b1, b2, _) in enumerate(regions):
    # pad with context
    ca1, ca2 = max(0, a1 - 18), min(len(a), a2 + 18)
    cb1, cb2 = max(0, b1 - 18), min(len(b), b2 + 18)
    a_txt = render(a, ca1, ca2)
    b_txt = render(b, cb1, cb2)
    print(f"===== REGION {i}  orig:{a1}-{a2}  amnd:{b1}-{b2}")
    print(f"  ORIG: …{a_txt[:MAXSHOW * 6]}…")
    print(f"  AMND: …{b_txt[:MAXSHOW * 6]}…")
    print()
