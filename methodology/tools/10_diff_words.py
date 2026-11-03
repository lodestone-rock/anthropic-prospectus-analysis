#!/usr/bin/env python3
"""Emit one normalized token per line for fast GNU-diff of two EDGAR extractions."""
import re
import sys

for path in sys.argv[1:]:
    text = open(path, encoding="utf-8", errors="replace").read().lower()
    text = text.replace("\u2019", "'").replace("\u2014", "-")
    tokens = re.findall(r"[a-z0-9'$%.+-]+", text)
    for t in tokens:
        print(t)
    print("\n\x00END-OF-DOC\x00\n")
