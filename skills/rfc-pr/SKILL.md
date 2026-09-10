---
name: rfc-pr
description: "Draft a Logos specification-change submission from the current branch: a short PR description (Motivation, Proposal, Status tracker) pushed to GitHub, and an RFC document (Reviewer Orientation, Discussion, Details, Implementation, Affected Specifications) committed under the spec domain's raw/rfc/ and numbered by the PR. Self-updates itself and the template from logos-blockchain/research on every run. Trigger: /rfc-pr."
---

# /rfc-pr

Turn the changes on the current branch into a Logos specification-change submission. The
submission is **two artifacts**, and this skill produces both:

| Artifact | Sections | Destination |
| --- | --- | --- |
| PR description | Motivation, Proposal, Status tracker | the GitHub PR body |
| RFC document | Change log, Reviewer Orientation, Discussion, Details, Chores, Implementation, Affected Specifications | `docs/<domain>/raw/rfc/RFC-<pr>-<subsystem>-<title>.md`, committed on the branch |

The canonical template defines both. This skill applies it.

## Usage

```
/rfc-pr                      # draft both artifacts from current branch vs master, then push
/rfc-pr <PR-number>          # target a specific PR instead of the current branch's PR
/rfc-pr --base <ref>         # diff against a base other than origin/master
/rfc-pr --no-push            # write both files only; do not touch GitHub or commit
/rfc-pr --ref <branch|tag>   # fetch the skill and template from a ref other than master
/rfc-pr --no-self-update     # skip step 0; run the skill exactly as installed
```

## Configuration (defaults)

- **Source repo** (for both the skill and the template): `logos-blockchain/research`
- **Skill path:** `skills/rfc-pr/SKILL.md`
- **Template path:** `templates/RFC-PR.md`
- **Base branch for the diff:** `origin/master`
- **RFC document directory:** `docs/<domain>/raw/rfc/` in the repo the PR targets, where
  `<domain>` is the `docs/` directory holding the specs the change touches

If invoked in a repo whose template lives elsewhere, adjust the paths and ask the user
when unsure.

## Procedure

Run these in order. Keep intermediate files in the session scratchpad (`$SCRATCH`).

### 0. Update this skill from the repo

Do this **first, on every invocation**, unless `--no-self-update` was given. The copy of
this skill already in context may be stale; the repo is the source of truth.

```bash
gh api repos/logos-blockchain/research/contents/skills/rfc-pr/SKILL.md \
  -H "Accept: application/vnd.github.raw" > "$SCRATCH/SKILL.remote.md"
diff -q "$SCRATCH/SKILL.remote.md" ~/.claude/skills/rfc-pr/SKILL.md
```

Add `?ref=<ref>` to the path if `--ref` was given, and use the same ref in step 1 so the
skill and the template always come from one commit.

**Install it only if all three hold**, so a failed fetch can never blank the skill:

1. the fetch exited 0 and the file is non-empty;
2. it begins with a `---` frontmatter block containing `name: rfc-pr`;
3. it differs from `~/.claude/skills/rfc-pr/SKILL.md`.

Then copy it over `~/.claude/skills/rfc-pr/SKILL.md`, **read the installed file, and
follow that version for the rest of this run** — not the one loaded into context at the
start. Tell the user the skill updated itself and summarize what changed.

If the fetch fails, 404s, or fails a check: keep the installed copy, say so in one line,
and carry on. A 404 means this skill has not landed on the source ref yet.

### 1. Fetch the template (every invocation — never rely on a local copy)

```bash
gh api repos/logos-blockchain/research/contents/templates/RFC-PR.md \
  -H "Accept: application/vnd.github.raw" > "$SCRATCH/RFC-PR.template.md"
```

Fallbacks, in order, only if the `gh api` call fails:

1. `git show origin/master:templates/RFC-PR.md` (if inside the research repo)
2. the local working-tree file `templates/RFC-PR.md`

If every source fails, stop and report — never invent a template structure.

Run this even when only updating an existing submission. Validate whatever already
exists against the just-fetched template and apply what the template changed since:
title convention, section structure, table formats, which artifact owns which section.
**Where this skill and the fetched template disagree, the template wins.**

### 2. Establish branch and PR context

```bash
git rev-parse --abbrev-ref HEAD          # must NOT be master/main
gh pr view --json number,title,url,body,baseRefName,headRefName 2>/dev/null
```

- With a PR number as argument, use `gh pr view <number> ...` instead.
- No PR yet is fine — you will create one in step 6. Note it as "no PR yet → will create".
- If a PR exists, note whether its body is non-empty; you will confirm before overwriting.
- A branch with no upstream must be pushed before a PR can be opened.

### 3. Gather the change content from git

```bash
BASE=$(git merge-base HEAD origin/master)
git diff --stat "$BASE"...HEAD           # inventory of changed files
git diff "$BASE"...HEAD -- '*.md'        # full diff of the spec changes
git log --format='%s%n%b' "$BASE"..HEAD  # intent, from the commit messages
```

- Changed specification documents are the **Affected Specifications**. Classify each from
  the diff: added file → Created, deleted → Retired, otherwise Modified.
- Read the changed files wherever the diff alone is ambiguous.
- Exclude the RFC document itself from the Affected Specifications table — the RFC
  document is the submission, not a specification it changes.

### 4. Draft both artifacts

Parse the template's structure, then write real content under each heading. The
template's `<aside>` blocks are authoring guidance — **they never appear in the output**.
Drop the "How to Use This Template" section and the "Part A" / "Part B" scaffolding
headings too; they organize the template, not the artifacts.

**Prose rules — these are the point of the exercise, not decoration.** Write for a
competent engineer who does not work on this subsystem.

- Short sentences, one idea each. Prefer the ordinary word where it is just as exact:
  `use` not `utilize`, `so` not `hence`, `about` not `approximately`.
- Keep the terms the specification defines (`epoch`, `slot`, `note`); define any other
  term of art in a clause the first time it appears.
- Cut filler: "it should be noted that", "in order to", "is able to", "leverage",
  "seamless", "robust".
- Active voice, actor named: "the leader validates the block", not "the block is
  validated".
- No adjective in place of a number: "12% slower", never "significantly slower".
- **Say it once.** Each fact has one home; everywhere else links to it. If two sections
  would carry the same sentence, the more specific one keeps it.
- Scale to size: a one-line change gets a one-sentence Motivation and a one-task
  Implementation. Length is not thoroughness.

**Artifact A — PR description.** Only these, in order:

1. `# [RFC] <Subsystem>: <Title>` — per the template's Title convention.
2. One line linking the RFC document.
3. **Motivation** — 1–3 short paragraphs: the problem, why it matters, what improves.
4. **Proposal** — 1–2 short paragraphs, optionally up to five bullets: the core idea and
   what it lands in. Not an enumeration of changes.
5. **Status tracker** — the template's checklist verbatim, all unchecked, including the
   approvals table beneath it.

Nothing else. No Details, no Implementation, no Affected Specifications.

**Artifact B — RFC document.** In template order:

1. `# [RFC] <Subsystem>: <Title>` — the same string as the PR title.
2. One line linking back to the PR for motivation and proposal.
3. **Change log** — oldest-first, `v1 | Initial RFC | <today>`. Take the date from
   `date +%F`; never hardcode it. On an update, append a row saying what actually moved,
   and run the template's change-log order check before pushing.
4. **Reviewer Orientation** — the ordered reading table in dependency order, one line per
   change, Priority per the template's guidance, **Start here** on the 1–2 highest-risk
   entries.
5. **Discussion** — tradeoffs, alternatives, rationale for thresholds, compatibility.
   Omit the heading entirely when there is nothing to say.
6. **Details** — every normative change, highest impact first, with snippets following
   the template's *Readable code snippets* convention.
7. **Chores** — non-normative cleanup as bullets. Omit the heading when empty.
8. **Implementation** — a GitHub task list, ending with a test task and a
   "verify the implementation matches this specification" task.
9. **Affected Specifications** — one row per changed spec, rebuilt from the current diff
   per the template's standing check.

**Faithfulness.** Draft only from what the diff, the files, and the commit messages
support. Where something genuinely cannot be inferred — the underlying motivation, why a
threshold is what it is, a tradeoff nobody wrote down — insert
`> **TODO (author):** …` rather than inventing it. Never fabricate measurements, numbers,
or rationale.

**On an update, re-draft rather than append.** Both artifacts state what the branch
changes *now*. Delete rationale for abandoned approaches, snippets that no longer match,
answered `TODO (author)` placeholders, and Affected Specifications rows the current diff
no longer touches. Record the removals in the Change log.

### 5. Write the files

- **RFC document** → `docs/<domain>/raw/rfc/RFC-<pr>-<subsystem>-<title>.md` in the
  target repo. `<domain>` is the `docs/` directory holding the specs the change touches;
  where it spans several, take the one with the largest normative change. `<pr>` is the
  PR number — see step 6, which opens the PR first when there is none, because the
  number has to exist before the file can be named. The rest is the lower-cased
  hyphenated RFC title, so `[RFC] Mantle: Remove the concept of a session` against a
  blockchain spec on PR #412 becomes
  `docs/blockchain/raw/rfc/RFC-412-mantle-remove-the-concept-of-a-session.md`. Create the
  `rfc/` directory if the domain does not have one.
- Where the RFC document already exists under a **different** PR number or slug — the
  title changed, or an earlier run guessed — `git mv` it rather than adding a second
  copy, and note the rename in the Change log.
- **PR description** → `$SCRATCH/RFC-PR-body.md`. It is not committed: its content lives
  in the PR body, and a second copy in the repo would be one more thing to keep in step.
- If a root-level `RFC-PR-*.md` from the older single-artifact convention is present,
  point it out and offer to remove it. Do not delete it unprompted.

Under `--no-push` there may be no PR and so no number. Write the RFC document as
`RFC-TBD-<subsystem>-<title>.md` and say in the report that the name needs the number
once the PR is opened; never invent one.

Show the user both drafts, or a summary of each, before anything is pushed.

### 6. Get the PR number, then commit the RFC document

Skip this whole step under `--no-push`.

**The PR number is part of the RFC document's file name, so the PR has to exist before
the file can be named.** That fixes the order below: get a number first, write the file
with it, commit, then set the body. Committing and opening a PR are outward-facing, so
**confirm with the user before the first of them.**

**Case A — no PR exists.** Push the branch and open the PR with the drafted body. The RFC
link line in that body points at the path the file *will* have; it resolves once the next
push lands.

```bash
git push -u origin <branch>
gh pr create --base master --head <branch> \
  --title "[RFC] <Subsystem>: <Title>" --body-file "$SCRATCH/RFC-PR-body.md"
```

`gh pr create` prints the PR URL; its trailing number is `<pr>`. Never guess it in
advance — GitHub numbers issues and PRs from one sequence, so the next number is not
predictable.

The PR title must match the `# ` heading of both artifacts exactly. Ask the user for the
subsystem when the diff does not make it obvious; fall back to the branch name or commit
subject for `<Title>` only, never for `<Subsystem>`.

**Cases B and C — a PR already exists.** The number is known, so no first push is needed.
Set the body once the RFC document is committed:

```bash
gh pr edit <number> --body-file "$SCRATCH/RFC-PR-body.md"
```

Under **Case C** the PR has a non-empty body, and this overwrites author-written content —
ask the user to confirm before running it.

**Then, in every case,** name the RFC document with `<pr>`, fix the back-link in its
header and the forward link in the PR body to match, and push:

```bash
mkdir -p docs/<domain>/raw/rfc
git add docs/<domain>/raw/rfc/RFC-<pr>-<slug>.md
git commit -m "docs(rfc): add the RFC document for <title>"
git push
```

Report the PR URL, the committed RFC path, and anything left as `TODO (author)`.

## Notes

- The skill and the template are both fetched fresh on every run, from the same ref, so a
  convention that changes upstream takes effect on the next invocation without anyone
  reinstalling anything. Step 0 rewrites `~/.claude/skills/rfc-pr/SKILL.md` in place.
- Self-update is skipped by `--no-self-update`, and never proceeds on a failed or
  malformed fetch.
- `$SCRATCH` is the session scratchpad directory; substitute the actual path.
- Never overwrite a non-empty PR body without explicit confirmation.
