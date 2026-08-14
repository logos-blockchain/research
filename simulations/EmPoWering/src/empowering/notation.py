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
   the specification's own identifier inventory.

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
NOT_NOTATION = re.compile(
    r"\.py\b|\.toml\b|\.json\b|\.md\b|^make |^\w+/[\w./]+$|^--|^\w+\.\w+:\d+$"
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
