"""One-time migration: split REPORT-tsi-parameter-selection.md into a thematic 4-part set + index.

The single report grew dense and heavily cross-referenced; this slices it into four cohesive parts
(kept in tsi-sim-pernode/ so all report-figures/ links stay valid) plus a short index that reuses the
canonical filename as the entry point. Section NUMBERS (§1-§9, A-C) are preserved as stable identifiers
across files; every §ref is rewritten into a clickable link to a portable `<a id="s6-5">` anchor,
same-file or cross-file as appropriate. Figure embeds and §9's config/script/run paths are untouched.

Run:  python scripts/split_report.py    (reads REPORT-...md, writes the 4 parts + overwrites the index)
"""

from __future__ import annotations

# ruff: noqa: E501  (one-time migration; index/nav strings are intentionally long prose)
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SRC = HERE / "REPORT-tsi-parameter-selection.md"
INDEX = "REPORT-tsi-parameter-selection.md"
P1 = "tsi-report-1-overview-and-recommendations.md"
P2 = "tsi-report-2-accuracy-and-design.md"
P3 = "tsi-report-3-robustness-and-incentives.md"
P4 = "tsi-report-4-reproducibility-and-appendices.md"

# top-level section id -> part filename, and the section order within each part
PART_SECTIONS = {
    P1: ["1", "7", "8"],
    P2: ["2", "3", "4", "5"],
    P3: ["6"],
    P4: ["9", "A", "B", "C"],
}
PART_TITLE = {
    P1: "Part 1 — Overview and recommendations",
    P2: "Part 2 — Accuracy and design",
    P3: "Part 3 — Robustness and incentives",
    P4: "Part 4 — Reproducibility and appendices",
}
SEC_TO_FILE = {s: f for f, secs in PART_SECTIONS.items() for s in secs}


def top_id(line: str) -> str | None:
    m = re.match(r"^##\s+Appendix\s+([A-C])\b", line)
    if m:
        return m.group(1)
    m = re.match(r"^##\s+(\d+)\.", line)
    return m.group(1) if m else None


def header_anchor(line: str) -> str | None:
    """Anchor id for a section/subsection header line, e.g. §6.5 -> s6-5, App B.2 -> sB-2."""
    m = re.match(r"^##\s+Appendix\s+([A-C])\b", line)
    if m:
        return "s" + m.group(1)
    m = re.match(r"^##\s+(\d+)\.", line)
    if m:
        return "s" + m.group(1)
    m = re.match(r"^###\s+([0-9A-C]+)\.(\d+)", line)
    if m:
        return f"s{m.group(1)}-{m.group(2)}"
    return None


def make_ref_rewriter(current_file: str):
    """Rewrite §N/§N.M and 'Appendix X' refs into links to their anchor (same- or cross-file)."""
    def link(top: str, sub: str | None, label: str) -> str:
        anchor = "s" + top + (f"-{sub}" if sub else "")
        tgt = SEC_TO_FILE.get(top)
        if tgt is None:
            return label  # unknown target: leave as text
        dest = f"#{anchor}" if tgt == current_file else f"{tgt}#{anchor}"
        return f"[{label}]({dest})"

    def sec_sub(m: re.Match) -> str:
        top, sub = m.group(1), m.group(2)
        return link(top, sub, m.group(0))

    def appendix(m: re.Match) -> str:
        return link(m.group(1), None, m.group(0))

    sec_re = re.compile(r"§\s?(\d+)(?:\.(\d+))?")
    app_re = re.compile(r"\bAppendix\s+([A-C])\b")

    def rewrite(text: str) -> str:
        return app_re.sub(appendix, sec_re.sub(sec_sub, text))

    return rewrite


def render_lines(lines: list[str], current_file: str) -> list[str]:
    """Inject anchors before headers and rewrite §refs, skipping fenced code blocks."""
    rewrite = make_ref_rewriter(current_file)
    out: list[str] = []
    in_fence = False
    for ln in lines:
        if ln.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append(ln)
            continue
        if in_fence:
            out.append(ln)  # never touch code (refs there stay plain text)
            continue
        aid = header_anchor(ln)
        if aid is not None:
            out.append(f'<a id="{aid}"></a>')
            out.append(ln)  # header title kept verbatim (no links inside headers)
            continue
        out.append(rewrite(ln))
    return out


def part_header(fname: str, units_note: str) -> list[str]:
    nav = (f"*[Part 1 — Overview & recommendations]({P1}) · [Part 2 — Accuracy & design]({P2}) · "
           f"[Part 3 — Robustness & incentives]({P3}) · [Part 4 — Reproducibility & appendices]({P4}) · "
           f"[Index]({INDEX})*")
    where = ("*Sections live across the set: §1/§7/§8 in Part 1, §2–§5 in Part 2, §6 in Part 3, "
             "§9 and Appendices A–C in Part 4.*")
    return [
        f"# Total-Stake-Inference parameter selection — {PART_TITLE[fname].split('— ')[1]}",
        "",
        units_note,
        "",
        nav,
        "",
        where,
        "",
        "---",
        "",
    ]


def build_index(units_note: str) -> str:
    lines = [
        "# Total-Stake-Inference parameter selection",
        "",
        units_note,
        "",
        "This analysis selects and justifies the TSI parameters for Cryptarchia, from a per-node "
        "network simulation (`tsi-sim-pernode`). It is split into four parts:",
        "",
        f"1. **[Overview and recommendations]({P1})** — the executive summary, the per-knob parameter "
        "reference (§7), and the safest selection with residual risks and the recommendation-vs-spec "
        "deltas (§8).",
        f"2. **[Accuracy and design]({P2})** — the model and counting rule (§2), the seven findings and "
        "their evidence (§3), and the design equations / selection algorithm (§4–§5).",
        f"3. **[Robustness and incentives]({P3})** — jitter, grinding, withholding, selfish mining, the "
        "reward design, fork/reorg depth, and organic churn (§6).",
        f"4. **[Reproducibility and appendices]({P4})** — how to re-run every study (§9), the residual "
        "f-rounding offset (App A), the per-epoch noise floor (App B), and consensus detail (App C).",
        "",
        f"**Headline recommendation** (Cryptarchia baseline f = 1/30): security `k = 2160`, uncle "
        f"window `W = 300` slots, uncle cap `U = ⌈ρ⌉ + 1` (2 at the Blend target), learning rate "
        f"`β = 1`, peering degree ≥ 6 at scale, soft uncle rewards with `w_u + w_n < 1`, and operate "
        f"at load `ρ = f·D_vis < 1`. The full recommended-configuration table and rationale are in "
        f"**[Part 1 →]({P1})**.",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    text = SRC.read_text()
    if "## 6. Robustness" not in text:
        sys.exit("Source has already been split (no '## 6. Robustness' found in "
                 f"{SRC.name}, which is now the index). This one-time migration is complete; "
                 "re-run against the pre-split backup only.")
    raw = text.split("\n")

    # frontmatter (title + units note) is everything before the first "## " header
    first_h = next(i for i, l in enumerate(raw) if l.startswith("## "))
    units_note = raw[2]  # the italic "*Per-node network simulation ... 1 slot = 1 s.*" line

    # slice into top-level sections
    sections: dict[str, list[str]] = {}
    cur: str | None = None
    for l in raw[first_h:]:
        tid = top_id(l)
        if tid is not None:
            cur = tid
            sections[cur] = []
        if cur is not None:
            sections[cur].append(l)

    # update the reading-order note (in §1) to describe the 4-part structure
    ro_old_prefix = "The rest of the report, in reading order:"
    ro_new = ("This report is split into four parts (see the [index](" + INDEX + ")): "
              "**Part 1** — the recommended configuration, the per-knob parameter reference (§7) and "
              "the safest selection with residual risks and spec deltas (§8); **Part 2** — the model "
              "and counting rule (§2), the evidence behind each finding (§3), and the design equations "
              "and selection algorithm (§4–§5); **Part 3** — robustness against noise, attacks and the "
              "incentive design (§6); **Part 4** — reproducibility (§9) and the appendices (the residual "
              "~1 % f-rounding offset, the ±0.9 % per-epoch noise floor, and consensus detail).")
    sections["1"] = [
        ro_new if l.startswith(ro_old_prefix) else l for l in sections["1"]
    ]

    # assemble each part
    for fname, sec_ids in PART_SECTIONS.items():
        body: list[str] = list(part_header(fname, units_note))
        for sid in sec_ids:
            body.extend(sections[sid])
            body.append("")  # spacer between sections
        rendered = render_lines(body, fname)
        (HERE / fname).write_text("\n".join(rendered).rstrip() + "\n")
        print(f"wrote {fname} ({len(rendered)} lines)")

    # index last (overwrites the source-name file)
    (HERE / INDEX).write_text(build_index(units_note))
    print(f"wrote {INDEX} (index)")


if __name__ == "__main__":
    main()
