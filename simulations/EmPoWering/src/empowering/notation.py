"""The report's notation contract, enforced.

Section 1.0 promises that symbols and self-describing names are strictly
interchangeable: a backtick span holds only names, a ``$…$`` span only symbols, and
section 1.0's table maps each to exactly one of the other. That promise is easy to
state and easy to erode -- one substitution that leaves ``T`` inside a code span, one
new quantity named in prose but never declared, and a reader can no longer follow one
form into the other.

So it is checked rather than trusted. Three directions, all of which must hold:

A. no symbol -- Greek, or a lone Latin letter -- inside a code span;
B. no symbol loose in prose, outside math;
C. every name used in a code span traceable to section 1.0, the config, the model, or
   the specification's own identifier inventory;
D. no *bare* symbol in prose even when wrapped in math -- ``$\rho$`` mid-sentence beside
   ``distribution_rate`` is the mixing this contract exists to prevent. Inline
   *relations* are welcome, and each is paired with its code sibling; a lone symbol is
   not a relation.

Run as ``make notation``. Failure prints the offending spans, not just a count, because
the fix is always to rewrite one of them.
"""
from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

GREEK = r"[σφψβρΦλκΔΣ]"
LEFTOVER = r"⌊|⌋|·|−|≤|≥|∧|∈|≫|√|÷|\^|dem̂|R₀|σₑ|Φ̂|S_tge|N_b|n_tx"
LONE_LETTER = r"(?<![\w.\-])[A-Za-z](?![\w])"

# Spans that are not model notation at all: spec constants, file paths, make targets.
SPEC_CONST = re.compile(r"^[A-Z_0-9]+$")
# A path needs a real extension or a known directory -- matching any `a/b` shape once let
# `p/2²²` through as if it were a file, hiding a bare field-modulus symbol for months.
NOT_NOTATION = re.compile(
    r"\.py\b|\.toml\b|\.json\b|\.md\b|\.png\b|^make |^--|^\w+\.\w+:\d+$"
    r"|^(?:simulations|reports|tools|src|web|configs|figures)/"
)

# Identifiers quoted from the proposal's own inventory (report section 1.5). They belong
# to the specification, not to this model, and are declared as such in section 1.0.
SPEC_IDENTIFIERS = {
    "pow_reward_pool", "epoch_pow_reward", "distribute_block_reward", "get_block_rewards",
    "pol_epoch_nonce", "epoch_nonce", "pow_nonce", "public_key", "difficulty_blend",
    "difficulty_reward", "pow_quota", "b_exec", "r_b", "r_max", "d_blend", "blend_target",
    "block_reward_blend_share", "block_reward_leader_share", "block_reward_pow_share",
    "blend_ops_per_message", "block_rewards", "unwired_placeholder",
}


def code_spans(text: str) -> list[str]:
    """Backtick spans that carry model notation, stripped of the ones that do not."""
    out = []
    for m in re.finditer(r"`([^`\n]+)`", text):
        span = m.group(1).strip()
        if SPEC_CONST.match(span) or NOT_NOTATION.search(span):
            continue
        out.append(span)
    return out


def declared_names(text: str) -> set[str]:
    """Every name section 1.0's two tables map to a symbol."""
    start = text.index("### 1.0 Notation")
    end = text.index("\n### ", start + 10)
    names: set[str] = set()
    for row in re.findall(r"^\|\s*(.+?)\s*\|", text[start:end], re.M):
        names.update(re.findall(r"`([a-z_][a-z0-9_]*)`", row))
    return names


def prose_math(text: str) -> list[tuple[int, str]]:
    """Every inline ``$…$`` span in running prose, with its line number.

    Skips fences, table rows and display equations -- all of which may legitimately hold
    symbols -- and section 1.0 itself, which is the mapping. Currency is not math: an
    unescaped ``$5`` would otherwise pair with the next dollar sign and read as a formula,
    so the report escapes those and this skips what is left.
    """
    lines = text.split("\n")
    lo = next(i for i, l in enumerate(lines) if l.startswith("### 1.0 Notation"))
    hi = next(i for i in range(lo + 1, len(lines)) if lines[i].startswith("### "))
    # Section 0 warns that two documents write the same letter for different quantities.
    # It is the one place where the letter itself is the subject, so it must show it.
    w0 = next(i for i, l in enumerate(lines) if l.startswith("## 0. A warning about the letter"))
    w1 = next(i for i in range(w0 + 1, len(lines)) if lines[i].startswith("## "))
    out, in_fence = [], False
    for i, line in enumerate(lines):
        if w0 <= i < w1:
            continue
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or line.lstrip().startswith("|") or line.strip().startswith("$$"):
            continue
        if lo <= i < hi:
            continue
        for m in re.finditer(r"(?<!\\)\$([^$\n]+?)(?<!\\)\$", line):
            out.append((i + 1, m.group(1)))
    return out


def prose_only(text: str) -> str:
    """The document with code spans, math, fences and tables removed."""
    body = re.sub(r"```.*?```", "", text, flags=re.S)
    body = re.sub(r"`[^`\n]*`", "", body)
    body = re.sub(r"\$\$?.+?\$\$?", "", body, flags=re.S)
    return re.sub(r"^\s*\|.*$", "", body, flags=re.M)


def run(report: Path, config: Path) -> int:
    text = report.read_text()
    failures: list[str] = []
    checks = 0

    # --- A. symbols must not appear inside code spans ---------------------------------
    offenders = {}
    for span in code_spans(text):
        found = re.findall(GREEK, span) + re.findall(LONE_LETTER, span) + re.findall(LEFTOVER, span)
        if found:
            offenders.setdefault(span, set()).update(found)
    checks += 1
    if offenders:
        for span, syms in sorted(offenders.items()):
            failures.append(f"symbol {''.join(sorted(syms))!r} inside a code span: `{span}`")
    else:
        print(f"  PASS  no symbols inside any of {len(code_spans(text))} code spans")

    # --- B. symbols must not appear loose in prose ------------------------------------
    loose = re.findall(GREEK + r"|R₀|σₑ|Φ̂|S_tge|\bN_b\b|\bn_tx\b", prose_only(text))
    checks += 1
    if loose:
        failures.append(f"symbols loose in prose, outside math: {sorted(set(loose))}")
    else:
        print("  PASS  no symbols loose in prose -- every one is wrapped in math")

    # A Latin symbol is harder to spot than a Greek one, because a lone letter in English
    # is usually not notation: "128 B", "(a) and (b)", "i.e.", and every possessive. So this
    # looks only where a letter is doing an equation's work -- beside a relational operator,
    # or inside a tuple next to a name. That is where `(T, `pow_share`) = (11, 11 %)` hid.
    latin = []
    for ln, line in enumerate(text.split("\n"), 1):
        stripped = re.sub(r"`[^`\n]*`", "⟦⟧", line)
        stripped = re.sub(r"(?<!\\)\$[^$\n]+?(?<!\\)\$", "⟦⟧", stripped)
        if stripped.lstrip().startswith("|") or stripped.startswith("```"):
            continue
        for m in re.finditer(r"(?<![\w`$\\/§#.\-–—’'*])([A-Za-z])(?![\w’'])", stripped):
            if m.group(1) not in "TRFPHNLSvhdqspmxcEek":
                continue
            head, tail = stripped[max(0, m.start() - 3):m.start()], stripped[m.end():m.end() + 4]
            if re.match(r"^\s*(LGO|of|per|$)", tail) and re.search(r"[\d.,]\s*$", head):
                continue                                   # a unit: "128 B", "2.05 M LGO"
            if head.endswith("(") and tail.startswith(")"):
                continue                                   # an enumeration label: "(a)"
            if re.match(r"^\s*[=<>≈≤≥,)]", tail) or re.search(r"[=(,]\s*$", head):
                latin.append(f"line {ln}: bare `{m.group(1)}` doing an equation's work -- use its name")
    checks += 1
    if latin:
        failures.extend(latin)
    else:
        print("  PASS  no bare Latin symbol standing in for a name in prose")

    # --- C. every name must be traceable ----------------------------------------------
    declared = declared_names(text)
    cfg = set(re.findall(r"^\s*([a-z_]+)\s*=", config.read_text(), re.M))
    core = (Path(__file__).parent / "core.py").read_text()
    from_model = set(re.findall(r"def ([a-z_]+)", core)) | set(re.findall(r"p\.([a-z_]+)", core))

    used: set[str] = set()
    for span in code_spans(text):
        used.update(re.findall(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b", span))
    untraceable = sorted(used - declared - cfg - from_model - SPEC_IDENTIFIERS)
    checks += 1
    if untraceable:
        failures.append(
            "names used but not declared in §1.0, the config, core.py or the spec "
            f"inventory: {untraceable}"
        )
    else:
        print(f"  PASS  all {len(used)} names traceable ({len(declared)} declared in §1.0)")

    # --- D. inline math in prose must be a relation, never a lone symbol ---------------
    RELATION = re.compile(r"[=<>≤≥]|\\iff|\\Longrightarrow|\\ast\s*=|[+\-/]")
    bare = [(ln, x) for ln, x in prose_math(text) if not RELATION.search(x)]
    checks += 1
    if bare:
        for ln, x in bare:
            failures.append(f"line {ln}: bare symbol ${x}$ in prose -- use its name")
    else:
        total = len(prose_math(text))
        print(f"  PASS  all {total} inline math spans in prose are relations, not lone symbols")

    # A dollar amount left unescaped pairs with the next dollar sign and renders the prose
    # between them as a formula. Cheap to check, and invisible until someone reads the page.
    money = [
        m.group(0)
        for line in text.split("\n")
        if not line.lstrip().startswith("|")
        for m in re.finditer(r"(?<!\\)\$\d[\d.,]*", line)
    ]
    checks += 1
    if money:
        failures.append(f"unescaped currency would render as math: {money} -- write \\$")
    else:
        print("  PASS  every dollar amount escaped, so none of it renders as math")

    # LaTeX outside math delimiters renders as literal backslashes. Easy to introduce when
    # building an equation table programmatically, and invisible in the source.
    naked = []
    for ln, line in enumerate(text.split("\n"), 1):
        body = re.sub(r"(?<!\\)\$[^$\n]+?(?<!\\)\$", "", line)
        body = re.sub(r"`[^`\n]*`", "", body)
        if re.search(r"\\(varphi|sigma|rho|beta|psi|Phi|lambda|kappa|Delta|dfrac|ast|text)\b", body):
            naked.append(f"line {ln}: LaTeX outside math -- {body.strip()[:60]}")
    checks += 1
    if naked:
        failures.extend(naked)
    else:
        print("  PASS  no LaTeX left outside math delimiters")

    # An equation buried mid-sentence is hard to see. A defining relation -- one whose right
    # side is an expression rather than a bare value -- gets its own line, the same treatment
    # the math forms get. Two contexts legitimately keep one inline: a relation quoted from
    # elsewhere, and one used as a paragraph's bold label, where it is already prominent.
    def is_equation(sp: str) -> bool:
        rel = re.search(r"(<=|>=|==|=|<|>)", sp)
        return bool(rel and re.search(r"[*/+]|sqrt|ceil|min\(|max\(", sp[rel.end():])
                    and len(sp) > 30)

    buried = []
    for ln, line in enumerate(text.split("\n"), 1):
        if line.lstrip().startswith("|") or line.startswith(("#", "*Fig")):
            continue
        stripped = line.strip()
        if stripped.startswith("`") and stripped.endswith("`") and stripped.count("`") == 2:
            continue                                          # already on its own line
        for m in re.finditer(r"`([^`\n]+)`", line):
            if not is_equation(m.group(1)):
                continue
            before = line[:m.start()]
            if before.count('"') % 2 == 1:
                continue                                      # quoted from elsewhere
            if before.strip() in ("**", ""):
                continue                                      # the paragraph's bold label
            buried.append(f"line {ln}: equation buried in prose -- give it its own line: "
                          f"`{m.group(1)[:56]}`")
    checks += 1
    if buried:
        failures.extend(buried)
    else:
        print("  PASS  every defining equation sits on its own line")

    print()
    if failures:
        for f in failures:
            print(f"  BROKEN  {f}")
        print(
            f"\n{len(failures)} notation break(s). §1.0 promises the two forms are "
            "interchangeable;\nrewrite the span, or declare the name in §1.0."
        )
        return 1
    print(f"notation coherent: {checks} checks, symbols and names never mix")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--config", type=Path, required=True)
    a = ap.parse_args()
    print(f"notation contract: {a.report}\n")
    sys.exit(run(a.report, a.config))


if __name__ == "__main__":
    main()
