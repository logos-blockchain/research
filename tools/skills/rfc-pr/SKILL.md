---
name: rfc-pr
description: "Fill in a GitHub PR description for a Logos spec change using the canonical RFC-PR template. Fetches the up-to-date template from the logos-blockchain/research repo, drafts every section from the current branch's diff vs master, writes RFC-PR-<topic>.md, then sets it as the PR body — creating the PR with `gh pr create` if none exists, or updating it with `gh pr edit`. Trigger: /rfc-pr."
---

# /rfc-pr

Produce a filled-in PR description for a Logos specification-change PR by applying the
canonical **RFC-PR** template to the changes on the current branch, then set it as the
PR body on GitHub.

## Usage

```
/rfc-pr                      # draft from current branch vs master, write file, push to the branch's PR
/rfc-pr <PR-number>          # target a specific PR instead of the current branch's PR
/rfc-pr --base <ref>         # diff against a base other than origin/master
/rfc-pr --no-push            # write the Markdown file only; do not touch the GitHub PR
/rfc-pr --ref <branch|tag>   # fetch the template from a ref other than master
```

## Configuration (defaults)

- **Template source repo:** `logos-blockchain/research`
- **Template path:** `templates/RFC-PR.md`
- **Base branch for the diff:** `origin/master`

These are the defaults for the Logos research repo. If invoked in another repo whose
template lives elsewhere, adjust the repo/path accordingly (ask the user if unsure).

## Procedure

Follow these steps in order. Use the session scratchpad for all intermediate files.

### 1. Establish branch / PR context

```bash
git rev-parse --abbrev-ref HEAD          # current branch — must NOT be master/main
gh pr view --json number,title,url,body,baseRefName,headRefName 2>/dev/null
```

- If a PR number was passed as an argument, use `gh pr view <number> ...` instead.
- If no PR exists for the branch, that is fine — you will **create** one in step 6 using
  the drafted description as its body. Note it as "no PR yet → will create".
- If a PR does exist, note whether it **already has a non-empty body** — you will confirm
  before overwriting it in step 6.
- Ensure the branch is pushed to the remote before creating a PR
  (`git push -u origin <branch>` if it has no upstream); a PR cannot be opened otherwise.

### 2. Fetch the up-to-date template (do NOT rely on any local copy)

```bash
gh api repos/logos-blockchain/research/contents/templates/RFC-PR.md \
  -H "Accept: application/vnd.github.raw" > "$SCRATCH/RFC-PR.template.md"
```

Add `?ref=<ref>` to the path if `--ref` was given. Fallbacks, in order, only if the
`gh api` call fails:

1. `git show origin/master:templates/RFC-PR.md` (if inside the research repo)
2. the local working-tree file `templates/RFC-PR.md`

If every source fails, stop and report — do not invent a template structure.

### 3. Gather the change content from git

Compute the merge base and inspect the branch's changes against the base:

```bash
BASE=$(git merge-base HEAD origin/master)
git diff --stat "$BASE"...HEAD          # inventory of changed files
git diff "$BASE"...HEAD -- '*.md' '*.py' # full diff of spec/code changes
```

- Treat changed specification documents (Markdown/spec files) as the **Affected
  Specifications**. Classify each as Created / Modified / Deprecated / Retired from the
  diff (added file = Created, deleted = Retired, etc.).
- Read the changed files where the diff alone is ambiguous.
- Also read recent commit messages on the branch for intent:
  `git log --format='%s%n%b' "$BASE"..HEAD`.

### 4. Draft the filled-in description

Parse the template's section structure, then write real content for each section. The
template's `<aside>` blocks are **authoring guidance (Purpose / Include / Avoid / Output
style) — they must NOT appear in the output.** Likewise drop the top
"How to Use This Template" meta-section entirely. Keep the section **headings** and
produce content beneath each, honoring these template conventions:

- **Order by review impact** — highest-impact normative change first in every section;
  editorial/minor changes last.
- **Single source of truth** — the full spec of each change lives in **Details**; every
  other section links or points to it in one line rather than restating it.
- **Readable code snippets** — language-tagged fenced blocks; ` ```diff ` with `+`/`-`
  for edits; show only changed lines plus minimal context, eliding the rest with `# ...`.
- **Scale ceremony to size** — for a small change, Motivation may be one sentence and
  Implementation a single task. Omit **Discussion** and **Chores** entirely (no empty
  heading) when they have no content.

Sections to emit, in template order:

1. **Reviewer Orientation** — the ordered reading table (dependency order, not diff
   order), one line per change, Priority = Critical/High/Medium/Low per the template's
   priority guidance, with a **Start here** marker on the 1–2 highest-risk entries.
2. **Status tracker** — copy the template's checklist verbatim (all unchecked).
3. **Change log** — a single `v1 | Initial PR description | <today>` row. Get the date
   from `date +%F`; never hardcode it.
4. **Motivation** — 1–3 paragraphs; why the change is needed.
5. **Proposal** — high-level summary of the change.
6. **Discussion** — tradeoffs / alternatives / compatibility; omit if none.
7. **Details** — every normative change, ordered by impact, with code snippets.
8. **Chores** — non-normative cleanup as a bullet list; omit if none.
9. **Implementation** — GitHub task list (`- [ ] task`), one per unit of work, ending
   with a test task and a "verify implementation matches the spec" task.
10. **Affected Specifications** — one table row per changed spec with its Status and an
    optional note; link each spec.

**Faithfulness:** draft only from what the diff, files, and commit messages actually
support. For content that genuinely cannot be inferred (e.g. the underlying motivation,
rationale for a threshold, tradeoffs), insert a clearly marked
`> **TODO (author):** …` placeholder rather than fabricating evidence, numbers, or
rationale. Never invent measurements or claims.

### 5. Write the Markdown file

Write the filled description to `RFC-PR-<Topic>.md` at the repo root, where `<Topic>` is
a short kebab/Title-case slug derived from the branch name or PR title (match the
existing convention, e.g. `RFC-PR-Remove-Concept-of-a-Session.md`). Show the user the
draft (or a summary of it) before pushing.

### 6. Push to — or create — the GitHub PR

Skip this entire step if `--no-push` was given (write the file only).

**Case A — no PR exists for the branch:** create one, using the drafted description as its
body. Confirm with the user first (opening a PR is outward-facing), then:

```bash
git push -u origin <branch>          # only if the branch has no upstream yet
gh pr create --base master --head <branch> \
  --title "<PR title>" --body-file RFC-PR-<Topic>.md
```

Derive the title from the branch name / commit subject; ask the user if it is unclear.

**Case B — a PR exists with an empty body:** push directly:

```bash
gh pr edit <number> --body-file RFC-PR-<Topic>.md
```

**Case C — a PR exists with a non-empty body:** this would overwrite author-written
content — **ask the user to confirm** before running the `gh pr edit` command above.

Report the resulting PR URL and the written file path at the end.

## Notes

- The template is fetched fresh from GitHub on every run, so the skill always reflects
  the latest RFC-PR conventions even as they evolve — no local copy is trusted.
- `$SCRATCH` refers to the session scratchpad directory; substitute the actual path.
- Pushing a PR description is outward-facing: never overwrite an existing non-empty body
  without explicit confirmation.
