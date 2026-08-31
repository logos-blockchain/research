"""The machinery for checking a report's quoted numbers against the model that produced them.

`validate` ties the model to its closed forms. Between the model and the *document* there was
nothing: every published table was pinned by a literal inside `validate.py`, which is a second
copy of the number rather than a check on the first. Edit a table in the report and nothing
failed -- the two could disagree indefinitely, and the only reason they did not is that
someone remembered to change both.

This closes that gap the way the tokenomics simulator already does. Each claim names a
section, a pattern that locates the number inside it, and the value the model says it must be.

The engine lives here so the de-novo simulator can use it too: it already imports this package
(`PYTHONPATH=src:../strategies/src`), so the two reports are gated by one implementation
rather than by two that drift apart.

**A pattern that stops matching is a failure, not a pass.** Silently losing coverage when
someone rewords a sentence is the failure mode a gate like this exists to prevent, so a
pattern matching zero times -- or more than once, which means it is not anchored to the number
it claims -- fails the run.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

NUM = r"[-+]?[\d,]+(?:\.\d+)?"


@dataclass(frozen=True)
class Claim:
    """One quoted number: where it appears, how to find it, and what the model says."""
    section: str            # a section key, or "*" for the whole document
    pattern: str            # regex with exactly one capture group around the number
    expected: float
    rel: float = 5e-3       # the report rounds, so compare relatively by default
    note: str = ""


def parse_number(raw: str) -> float:
    return float(raw.replace(",", "").replace("−", "-").strip())


def split_sections(text: str) -> dict[str, str]:
    """Map each numbered section to its own text, so a claim is checked where it is stated.

    Scoping matters: `| 50 |` occurs in half a dozen tables across a report this size, and an
    unscoped pattern would match whichever one came first rather than the one being asserted.
    """
    heads = list(re.finditer(r"^#{2,4} +(\d+(?:\.\d+)*)[. ]", text, re.M))
    out: dict[str, str] = {}
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        out[m.group(1)] = text[m.start():end]
    return out


def run(report: Path, claims: list[Claim], *, elsewhere: set[str] | None = None,
        check_figures: bool = True) -> int:
    """Check every claim, the figure references, and the section cross-references.

    ``elsewhere`` names section numbers that belong to some *other* document -- a
    specification or a proposal -- and so must not be counted as dangling here.
    """
    try:
        text = report.read_text()
    except OSError as e:
        print(f"cannot read report: {e}", file=sys.stderr)
        return 2

    sections = split_sections(text)
    failures: list[str] = []
    missing: list[str] = []
    checked = 0
    print(f"report numbers: {report}\n")

    for c in claims:
        scope = text if c.section == "*" else sections.get(c.section)
        if scope is None:
            missing.append(c.pattern)
            print(f"  MISS  §{c.section:<5} no such section in the report")
            continue
        # MULTILINE throughout: most claims anchor on `^|` to pin themselves to one table row.
        found = re.findall(c.pattern, scope, re.M)
        if len(found) != 1:
            missing.append(c.pattern)
            print(f"  MISS  §{c.section:<5} pattern matched {len(found)}x (want 1): "
                  f"{c.pattern[:52]}")
            continue
        checked += 1
        got = parse_number(found[0])
        ok = (got == c.expected if c.rel == 0
              else abs(got - c.expected) <= c.rel * max(abs(c.expected), 1e-12))
        if not ok:
            failures.append(f"§{c.section} {c.note or c.pattern[:40]}")
        print(f"  {'PASS' if ok else 'FAIL'}  §{c.section:<5} report {got:,.6g} vs model "
              f"{c.expected:,.6g}" + (f"   -- {c.note}" if c.note else ""))

    # An unreferenced figure is a section that lost its picture in an edit. The check is
    # against every report sharing the directory, not just this one: the de-novo set has four
    # documents drawing on one `figures/`, and asserting each figure against a single report
    # would fail on figures that simply belong to a sibling.
    if check_figures:
        fig_dir = report.parent / "figures"
        if fig_dir.is_dir():
            print()
            siblings = "\n".join(p.read_text(errors="replace")
                                 for p in sorted(report.parent.glob("*.md")))
            for f in sorted(fig_dir.glob("*.png")):
                here = f"figures/{f.name}" in text
                anywhere = f"figures/{f.name}" in siblings
                if not anywhere:
                    failures.append(f"figure {f.name} referenced by no report")
                where = "" if here else "   -- by a sibling report"
                print(f"  {'PASS' if anywhere else 'FAIL'}  figure {f.name} referenced{where}")

    # A section deleted wholesale takes its numbers with it, so no claim is left to mismatch.
    # Only the cross-references can see that, which is why they are checked here too.
    print()
    cited = {m.group(1) for m in re.finditer(r"§(\d+(?:\.\d+)*)", text)}
    dangling = sorted(c for c in cited - (elsewhere or set()) if c not in sections)
    if dangling:
        failures.append(f"{len(dangling)} dangling cross-reference(s)")
        print(f"  FAIL  cited but absent: {', '.join('§' + d for d in dangling)}")
    else:
        print(f"  PASS  all {len(cited & set(sections))} cited sections resolve; "
              f"{len(sections)} present")

    print()
    if missing:
        print(f"{len(missing)} pattern(s) did not match exactly once -- the report's wording "
              f"moved,\nso the gate can no longer find the number. Re-anchor it or fix the text.")
    if failures:
        print(f"{len(failures)} number(s) drifted from the model:")
        for f in failures:
            print(f"    {f}")
    if not missing and not failures:
        print(f"all {checked} quoted numbers match the model")
    return 1 if (failures or missing) else 0
