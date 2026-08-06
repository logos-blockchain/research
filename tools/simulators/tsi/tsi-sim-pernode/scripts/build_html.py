"""Render the TSI report markdown to standalone, print-friendly HTML.

Markdown is the source of truth; the HTML is a build artifact (not committed). Code blocks are
syntax-highlighted (codehilite + Pygments), and `.md` links are rewritten to `.html` so the
index and the report navigate to each other.

The report lives in reports/tsi/ (not in this simulator folder) as a SINGLE document, named
README.md so it renders as the directory landing page; figure links are relative to that
directory, so paths resolve as-is.

Run:  python scripts/build_html.py --all            # the report
      python scripts/build_html.py <file.md> ...     # specific docs (paths relative to reports/tsi)
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import markdown
from pygments.formatters import HtmlFormatter

# The report set lives in the repo's reports/ tree, not alongside the simulator.
HERE = Path(__file__).resolve().parents[5] / "reports" / "tsi"
DOCS = ["README.md"]   # the report IS the directory README (renders at reports/tsi/)

CSS_BASE = r"""
@page { size: A4; margin: 18mm 16mm 20mm 16mm; }
html { -webkit-print-color-adjust: exact; }
body { font-family: -apple-system, "Helvetica Neue", "Arial Unicode MS", sans-serif;
       font-size: 9.5pt; line-height: 1.45; color: #1a1a1a; max-width: 100%; margin: 0; }
h1 { font-size: 17pt; line-height: 1.25; border-bottom: 2px solid #333; padding-bottom: 6px; }
h2 { font-size: 13.5pt; margin-top: 22px; border-bottom: 1px solid #999; padding-bottom: 3px;
     page-break-after: avoid; }
h3 { font-size: 11pt; margin-top: 16px; page-break-after: avoid; }
p, li { text-align: justify; }
code { font-family: "SF Mono", Menlo, monospace; font-size: 8.5pt;
       background: #f4f4f4; padding: 0 2px; border-radius: 2px; }
pre { background: #f4f4f4; padding: 8px 10px; border-radius: 4px; overflow-x: hidden;
      white-space: pre-wrap; page-break-inside: avoid; }
pre code { background: none; font-size: 8pt; }
table { border-collapse: collapse; width: 100%; font-size: 8pt; margin: 10px 0; }
th, td { border: 1px solid #bbb; padding: 3px 5px; text-align: left; vertical-align: top; }
th { background: #ececec; }
tr { page-break-inside: avoid; }
img { max-width: 100%; height: auto; }
figure { margin: 12px 0; text-align: center; page-break-inside: avoid; }
figcaption { font-size: 8pt; color: #444; text-align: justify; margin-top: 4px; padding: 0 8mm; }
blockquote { border-left: 3px solid #999; margin-left: 0; padding-left: 12px; color: #333; }
hr { border: none; border-top: 1px solid #ccc; margin: 18px 0; }
em { color: inherit; }
"""


def render(md_path: Path) -> Path:
    body = markdown.markdown(
        md_path.read_text(),
        extensions=["tables", "fenced_code", "sane_lists", "codehilite", "md_in_html"],
        extension_configs={"codehilite": {"guess_lang": False}},
    )
    # rewrite intra-set links so the rendered HTML navigates to .html, not .md
    body = re.sub(r'(href="[^"]*?)\.md(#|")', r"\1.html\2", body)
    pyg = HtmlFormatter(style="default").get_style_defs(".codehilite")
    style = (CSS_BASE + "\n.codehilite{background:#f4f4f4;border-radius:4px;}\n"
             ".codehilite pre{background:none;margin:0;}\n" + pyg)
    html = (f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<title>{md_path.stem}</title><style>{style}</style></head><body>\n"
            f"{body}\n</body></html>")
    out = md_path.with_suffix(".html")
    out.write_text(html)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Render the TSI report markdown set to HTML")
    ap.add_argument("docs", nargs="*", help="specific .md files (default: the whole set)")
    ap.add_argument("--all", action="store_true", help="render the index + 4 parts")
    args = ap.parse_args()
    targets = DOCS if (args.all or not args.docs) else args.docs
    for d in targets:
        p = HERE / d
        if not p.exists():
            print(f"skip (missing): {d}")
            continue
        print(f"wrote {render(p).name}")


if __name__ == "__main__":
    main()
