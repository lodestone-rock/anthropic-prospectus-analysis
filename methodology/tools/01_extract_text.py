#!/usr/bin/env python3
"""Extract text from EDGAR HTML filings: block tags -> newlines, strip scripts/styles."""
import html
import re
import sys

from html.parser import HTMLParser

BLOCK = {
    "p", "div", "tr", "br", "li", "table", "td", "th", "h1", "h2", "h3", "h4",
    "h5", "h6", "hr", "ul", "ol", "dl", "dt", "dd", "section", "article", "header",
    "footer", "caption", "option", "blockquote", "pre", "form",
}
SKIP = {"script", "style", "title"}


class Extractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.out = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip_depth += 1
        if tag in BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in SKIP and self.skip_depth > 0:
            self.skip_depth -= 1
        if tag in BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if self.skip_depth == 0:
            self.out.append(data)

    def handle_entityref(self, name):
        if self.skip_depth == 0:
            self.out.append(html.unescape(f"&{name};"))

    def text(self):
        raw = "".join(self.out)
        raw = raw.replace("\xa0", " ")
        lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in raw.split("\n")]
        out = []
        blank = 0
        for ln in lines:
            if ln:
                out.append(ln)
                blank = 0
            else:
                blank += 1
                if blank <= 1:
                    out.append("")
        return "\n".join(out).strip() + "\n"


def main():
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8", errors="replace") as f:
        data = f.read()
    ex = Extractor()
    ex.feed(data)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(ex.text())
    print(f"{dst}: {len(ex.text())} chars")


if __name__ == "__main__":
    main()
