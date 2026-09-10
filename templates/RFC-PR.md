# [RFC] Specification Change Template

## How to Use This Template

<aside>

A specification change is submitted as **two artifacts**, and this template covers both. Each one has its own part below.

| Artifact | What it holds | Where it lives |
| --- | --- | --- |
| **Pull request description** (Part A) | Motivation, Proposal, Status tracker — nothing else | the GitHub PR body |
| **RFC document** (Part B) | Change log, Reviewer Orientation, Discussion, Details, Chores, Implementation, Affected Specifications | `docs/<domain>/raw/rfc/RFC-<pr>-<subsystem>-<title>.md`, committed on the branch |

The split has one purpose: the PR body answers *why this, and what is it* for someone deciding whether to read further, and the RFC document holds everything a reviewer needs to actually review. Keep them disjoint. The PR body never restates the RFC document, and the RFC document never re-argues the motivation — it links back.

These conventions apply to **every** section of both artifacts. They are stated once here so the individual sections stay short.

- **Title.** The RFC title is `[RFC] <Subsystem>: <Title>`. `<Subsystem>` names the part of the specification the change lands in, taken from the `bedrock-*` document(s) it touches — strip the `bedrock-` prefix and any version segment, then Title-Case the remainder, keeping its hyphens (`bedrock-v1.1-block-construction.md` → `Block-Construction`). When a change spans several subsystems, name the one whose normative change is largest; when it touches no `bedrock-*` document, use the closest subsystem the change is about. `<Title>` is a short sentence-case phrase, e.g. `[RFC] Mantle: Remove the concept of a session`. The GitHub PR title, the PR body's top heading, and the RFC document's top heading are all exactly this string.
- **Plain language.** Write for a competent engineer who does not work on this subsystem. Short sentences, one idea each. Prefer the ordinary word wherever it is just as exact — `use` not `utilize`, `so` not `hence`, `about` not `approximately`, `enough` not `sufficient`. Keep the terms the specification itself defines, such as `epoch`, `slot`, or `note`; define any other term of art in a clause the first time it appears. Cut filler outright: "it should be noted that", "in order to", "is able to", "leverage", "seamless", "robust". Prefer the active voice and name the actor — "the leader validates the block", not "the block is validated". Never let an adjective stand in for a number: write "12% slower", not "significantly slower".
- **Say it once.** Every fact has one home (see the table below) and one statement. Everywhere else, link to it. If two sections would carry the same sentence, the more specific one keeps it and the other gets a pointer. Length is not thoroughness: a section that says the same thing twice is a section a reviewer stops trusting.
- **Every update re-drafts both artifacts; neither is a log.** They state what the branch changes *now*, so on every revision re-derive each section from the current diff and **delete what no longer holds** — rationale for an approach since abandoned, changes reverted or moved out of scope, snippets that no longer match the spec, `TODO (author)` placeholders already answered, and every **Affected Specifications** row the current diff leaves untouched. Stale content is worse than missing content: it sends reviewers to read things that are not there, and it hides the parts that need attention. Three checks run on **every** update, before pushing — the **Change log** order (see that section), the removal of superseded content (this rule), and the **Affected Specifications** table against the current diff (see that section). Record the removals themselves as a Change log entry.
- **Order by review impact.** In every section, put the highest-impact normative change first and group minor/editorial changes last. Never let cleanup obscure protocol changes.
- **Impact dimensions** (referenced throughout as "impact dimensions"): consensus / safety / liveness, cryptographic validity, serialization & compatibility, data availability, slashing / economics, migration, and externally visible node / validator / user / API behavior. The **Reviewer Orientation** priority labels below define how these map to Critical / High / Medium / Low.
- **Scale ceremony to size.** For a minor correction, **Motivation** may be a single sentence and **Implementation** a single task.
- **Readable code snippets.** Tag every fenced block with its language (e.g. ` ```python `) so it syntax-highlights. Show only the lines that change plus the minimal surrounding context, eliding the rest with `# ...` — never paste a whole structure to touch one field. Make the edit legible: use a ` ```diff ` block with `+` / `-` lines, or annotate changed lines with a trailing comment (e.g. `# new`, `# was: 0`); show before → after when the change alters semantics. Keep every snippet syntactically valid and consistently indented so it renders and parses cleanly. For example, changing one field of a structure:

    ```diff
     class DeclarationInfo:
         service: ServiceType
    -    active: EpochNumber       # 0 until the first active message
    +    active: EpochNumber | None  # None until the first active message
         # ... unchanged fields elided
    ```

**Where each kind of content lives.** Each row has exactly one home. Every other section links to it in one line rather than restating it.

| Content | Its one home | Artifact | What every other section does |
| --- | --- | --- | --- |
| Why the change is needed | **Motivation** | PR body | RFC document links back; never re-argues it |
| What the change is, in short | **Proposal** | PR body | Details specifies it; never re-summarizes it |
| Review lifecycle state | **Status tracker** | PR body | — |
| Revision history | **Change log** | RFC document | — |
| Prioritized reading order, priority & focus | **Reviewer Orientation** | RFC document | One line per entry, linking into Details and Affected Specifications |
| Tradeoffs, rationale, alternatives | **Discussion** | RFC document | — |
| Full specification of each change | **Details** | RFC document | Summarize or link; never re-specify |
| Editorial / non-normative cleanup | **Chores** | RFC document | Details excludes it |
| Engineering tasks | **Implementation** | RFC document | States work to do, not the change itself |
| Inventory of affected documents | **Affected Specifications** | RFC document | Reviewer Orientation links to these entries, not re-list them |

</aside>


---

# Part A — Pull request description

<aside>

**Purpose:** Give a reader deciding whether to engage the two things they need — why the change exists and what it is — plus the lifecycle state. Nothing else belongs in the PR body.

**Include:** the title as the top heading, a one-line link to the RFC document, then **Motivation**, **Proposal**, and the **Status tracker**, in that order.

**Avoid:**

- Any of Part B's sections. A reviewer who wants Details opens the RFC document; a PR body that carries them means two copies to keep in step, and one of them will go stale
- Restating the Proposal inside the Motivation, or the reverse
- A wall of text. The whole body should be readable in under two minutes

</aside>

## Title and link

<aside>

**Output style:** The top heading is the RFC title (see *Title* in *How to Use This Template*). Directly beneath it, one line linking the RFC document, so a reviewer reaches it without scrolling.

**Example:**

```markdown
# [RFC] Mantle: Remove the concept of a session

**Full RFC:** [`docs/blockchain/raw/rfc/RFC-412-mantle-remove-the-concept-of-a-session.md`](docs/blockchain/raw/rfc/RFC-412-mantle-remove-the-concept-of-a-session.md)
```

</aside>

# Motivation

<aside>

**Purpose:** Explain why this PR is needed.

**Include:**

- The problem, limitation, or opportunity being addressed
- The affected protocol, product, or system component
- Why it matters, and what improves if the PR is accepted
- Any measurement, analysis, or observed failure that supports the change

**Avoid:**

- Implementation details, and anything that belongs in the RFC document
- Vague claims such as "improves performance" without a number
- Repeating the Proposal section

**Output style:** One to three short paragraphs. Plain language, per *How to Use This Template*. If one sentence covers it, write one sentence.

</aside>

# Proposal

<aside>

**Purpose:** Say what the change is, at a level a reviewer can hold in their head before opening the RFC document.

**Include:**

- The core idea, and the specifications or protocol components it lands in
- The main behavioral or architectural change
- Any new concept, parameter, or mechanism introduced
- Any change along an impact dimension (see *How to Use This Template*)

**Avoid:**

- Enumerating every change one by one — that is **Details**, in the RFC document
- Full implementation detail, or a long discussion of tradeoffs
- Repeating the Motivation section

**Output style:** One or two short paragraphs, optionally followed by a bullet list of no more than five points. Convey the idea and stop; the RFC document specifies it.

</aside>

## Status tracker

- [ ]  🚧 **Raw (make sure that all below is completed)**
    -  Template applied
    -  RFC document added under the domain's `raw/rfc/`, numbered by this PR
    -  Authors filled in
    -  Authors agree on the RFC content
- [ ]  📘 **Draft (make sure that all below is completed)**
    -  All dependent specifications added (Notion backlinks checked)
    -  Specifications to deprecate added, if applicable
    -  Specifications to retire added, if applicable
    -  **Leads assigned** — Research Lead and Engineering Lead. Where the Research Lead is an author, the Project Lead stands in
- [ ]  ⚙️ **Verified (make sure that all below is completed)**
    -  **Domain experts assigned** — research and engineering, as the change requires; cannot be authors
    -  Reviewers' comments addressed
    -  All logical changes documented
    -  **Required approvals collected on the latest revision** (see below)
- [ ]  🔀 **Merged (make sure that all below is completed)**
    -  Every change added to the change log, and the change log's order checked
    -  Specification version numbers assigned
    -  Implementation reviewed and merged
    -  Branch updated to master and all conflicts resolved
    -  PR merged

**Required approvals — two in both cases, and both on the latest revision.**

| If the author is… | Required approvals |
| --- | --- |
| anyone other than the Research Lead | the **lead**, plus **one** domain expert or implementer |
| the Research Lead | **two** domain experts or implementers — the lead approval is unavailable, so a second reviewer takes its place |

Nobody approves their own RFC. An approval binds only the revision it was given on: if a later revision changes anything normative, collect them again and say so in the **Change log**.


---

# Part B — RFC document

<aside>

**Purpose:** Hold everything a reviewer needs in order to review — the reading order, the reasoning, the specification of every change, the work it implies, and the documents it touches.

**Filing:** commit it at `docs/<domain>/raw/rfc/RFC-<pr>-<subsystem>-<title>.md` as part of the branch.

- `<domain>` is the `docs/` directory holding the specifications the change touches — `blockchain`, `anoncomms`, `storage`, and so on. `raw` is the same Raw lifecycle stage the Status tracker names, so the RFC files beside the specifications it changes. When a change spans several domains, use the one whose normative change is largest, the same tie-break as `<Subsystem>`. Create the `rfc/` directory if the domain does not have one yet.
- `<pr>` is the number of the pull request carrying the submission, so the document is identifiable on its own and sorts by age. The number does not exist until the PR does: **open the PR first, then name the file.** For a submission whose PR is not yet open, create it with the title and the PR body, take the number it is assigned, and commit the RFC document in the next push.
- `<subsystem>-<title>` is the lower-cased, hyphenated form of the rest of the RFC title.

So `[RFC] Mantle: Remove the concept of a session`, changing a blockchain specification on PR #412, files at `docs/blockchain/raw/rfc/RFC-412-mantle-remove-the-concept-of-a-session.md`. The document is part of the submission and is reviewed with it.

**Output style:** The top heading is the RFC title, identical to the PR title. Directly beneath it, one line linking back to the PR. Then the sections below, in order. Do not repeat Motivation or Proposal here — link to the PR body once, in that same line.

**Example header:**

```markdown
# [RFC] Mantle: Remove the concept of a session

**Motivation and proposal:** [PR #412](https://github.com/logos-co/logos-lips/pull/412)
```

</aside>

## Change log

<aside>

**Purpose:** Let a reviewer who has already read an earlier revision see exactly what moved since, and let an approver tell whether the revision they approved is still the current one.

**Include:** one entry per revision, **oldest first** — `v1` at the top, the newest revision on the last row. A revision needing several lines keeps its number on its first row and leaves the **Revision** cell blank on the continuation rows beneath it. Dates are `YYYY-MM-DD`, and each entry says what actually moved — including content **removed** under *Every update re-drafts both artifacts*, and any re-collection of approvals.

**Check the order on every update, before pushing.** This is a standing check, not a one-off:

- revisions read `v1, v2, … vN` — no gaps, no duplicates, none out of sequence;
- the newest entry is **last**, and describes the update being pushed;
- every date is well-formed, and no date is earlier than one above it;
- every continuation row sits directly under the revision it belongs to, with the Revision cell blank;
- nothing changed since the previous revision is missing an entry.

**Avoid:**

- Appending new revisions to the **top** — the table reads oldest-first, and reversing it silently misdates the history
- Renumbering or rewording an existing revision to cover a later change; add a new row instead
- Entries such as "addressed comments" or "minor fixes" that do not say what moved

</aside>

| **Revision** | **Description** | **Date** |
| --- | --- | --- |
| v1 | Initial RFC | YYYY-MM-DD |
|  | Description of what changed in this revision | YYYY-MM-DD |
| v2 | Description of what changed in this revision | YYYY-MM-DD |
|  | Description of what changed in this revision | YYYY-MM-DD |
| vN | Description of what changed in this revision | YYYY-MM-DD |

## Reviewer Orientation

<aside>

**Purpose:** In one place, tell reviewers *what matters most* and *the order to read it*, so they can start reviewing immediately. This is the canonical home for the priority labels used elsewhere in the template.

**Include:** a single ordered table of the changes a reviewer should work through, in recommended reading sequence (dependencies first — not diff or alphabetical order), with these columns:

- **#** — reading order
- **Priority** — Critical / High / Medium / Low (see guidance below)
- **Document / Change** — link to its entry in **Affected Specifications** and **Details**; put a **Start here** marker on the 1–2 highest-risk entries a time-constrained reviewer must not skip
- **What to look for** — the one or two things to scrutinize (a new state transition, a changed serialization format, a removed rule, a cross-spec dependency), or "skim" for editorial / non-normative documents

Note any prerequisite context needed before the first entry (e.g., "read the PR's Motivation first", or a background spec that is unchanged but assumed).

**Priority guidance** (maps the impact dimensions from *How to Use This Template*):

- **Critical:** consensus, safety, liveness, cryptographic validity, serialization compatibility, data availability, slashing, asset loss, or hard-fork behavior
- **High:** externally visible protocol behavior, validator/node behavior, public APIs, storage formats, cross-specification dependencies, or migration requirements
- **Medium:** internal algorithms, parameters, verification criteria, performance-sensitive behavior, or implementation requirements
- **Low:** wording, examples, formatting, terminology cleanup, typo fixes, or non-normative clarifications

**Avoid:**

- Diff order or alphabetical order instead of dependency/impact order
- Giving every entry equal weight, or hiding compatibility/security/consensus/migration impact
- Re-describing *what* changed in detail (that is **Details**) or re-listing **Affected Specifications** — link to them and keep each row to one line

**Output style:** One ordered table, one line per row, linking each entry to its **Details** and **Affected Specifications** entries rather than restating them. If one document contains changes at different priorities, give it a row per change (same document link, different priority and focus) rather than collapsing them under one priority. For a single-document RFC, replace the table with one line (e.g., "Single-document change — read [spec] top to bottom; focus on [X].").

**Example:**

| # | Priority | Document / Change | What to look for |
| --- | --- | --- | --- |
| 1 | Critical | **Start here** — [Core spec] | new *X* state transition; removed *Y* concept |
| 2 | High | [Dependent spec A] | updated validation rules and serialization format |
| 3 | High | [Dependent spec B] | externally visible behavior; backwards-compatibility |
| 4 | Low | [Editorial spec] | skim — terminology alignment only |

</aside>

# Discussion

<aside>
💡

**Purpose:** Analyze consequences, tradeoffs, and rationale.

**Include:**

- Effects on relevant system properties (the impact dimensions, plus performance, reliability, scalability, decentralization, or user experience)
- Important alternatives considered, if any
- Rationale for chosen parameters, constants, or thresholds
- Risks, open questions, and assumptions
- Backwards compatibility impact and any required migration path
- A specification the change *should* have modified but did not — raise it here as a review finding

**Avoid:**

- Restating the Proposal without analysis
- Unsupported claims
- Implementation minutiae unless they affect the analysis
- Omitting backwards compatibility analysis for externally visible changes

**Output style:** Use clear subsections when the discussion covers several topics. Omit the section entirely (don't leave an empty heading) when the proposal is self-evident and has no meaningful tradeoffs.

</aside>

# Details

<aside>

**Purpose:** Specify the concrete changes required across all affected specifications. This is the only place the change is specified in full.

**Include:**

- All normative changes required by the PR, ordered from highest to lowest review impact
- New, modified, or removed protocol rules
- New, modified, or removed data structures, algorithms, parameters, or validation rules
- Cross-specification dependencies
- Any migration, compatibility, or rollout requirements
- Test vectors, simulation parameters, or verification criteria introduced
- Code snippets, following the *Readable code snippets* convention in *How to Use This Template*

**Avoid:**

- Motivation, which lives in the PR body
- Omitting small but required changes
- Mixing unresolved design questions with accepted specification changes
- Editorial or non-normative cleanup (that belongs in **Chores**)

**Output style:** Precise specification language, highest impact first. Plain language still applies: precise is not the same as ornate.

</aside>

## Chores

<aside>

**Purpose:** The single home for small, non-normative changes that need no explanation.

**Include:**

- Naming or terminology updates
- Formatting, rendering, or editorial updates that are part of the PR
- Minor cleanup required by the proposal
- Minor specification corrections (e.g., typo fixes, bound tightening, variable renames)

**Avoid:**

- Normative protocol changes that belong in Details
- Unrelated cleanup tasks
- Presenting chores as the main contribution when substantive changes exist

**Output style:** A short bullet list at the end of Details, clearly lower priority than the normative changes. Omit the section entirely when there are no chores.

</aside>

# Implementation

<aside>

**Purpose:** Enumerate the engineering tasks this specification requires, as one trackable checklist. Verification lives here too: tests, test vectors, benchmarks, and spec-implementation agreement checks are tasks in this list, not a separate section.

**Include:**

- One actionable task per discrete unit of engineering work, in implementation order where possible
- Tasks for new, modified, or removed data structures, algorithms, validation rules, and serialization
- Tasks for removing or migrating deprecated mechanisms
- Tasks for tests, test vectors, simulations, or benchmarks that exercise the change
- A final task that verifies the implementation matches this specification
- Links to implementation PRs, issues, commit ranges, or CI runs as they become available

**Avoid:**

- Tasks that cannot be checked off, such as "implement the protocol"
- Restating **Details** instead of stating the work to be done
- Claiming verification without a corresponding task or evidence
- Tasks unrelated to this specification

**Output style:** A GitHub task list — one `- [ ] task` per line. For an editorial-only change, use a single task such as `- [ ] No implementation required (specification-only change)` and say why in the same line.

</aside>

- [ ]  <Engineering task 1>
- [ ]  <Engineering task 2>
- [ ]  <…>
- [ ]  Add or extend tests / test vectors that exercise the change
- [ ]  Verify the implementation matches this specification

# Affected Specifications

<aside>

**Purpose:** Identify every specification this PR changes.

**Guidance:** This is the section reviewers must verify is complete before approving. A document appears only if the diff changes it: one that was read, consulted, or depended on is not affected. The RFC document itself is the submission rather than a specification the submission changes, so it never appears in this table even though the diff adds it.

**Rebuild the table from the current diff on every update, before pushing.** This is a standing check, not a one-off — the table is derived from the diff, never edited by hand into agreement with it:

- every row corresponds to a document the **current** diff changes;
- every document the current diff changes has a row;
- each row's Status still matches what the diff does to that document — a spec first modified and later deleted on the same branch becomes Retired, not Modified;
- **rows for documents the current diff no longer touches are deleted**, including ones an earlier revision of the branch did change. Note the removal in the **Change log**.

**Include:** one row per affected specification, tagged with its **Status**:

- **Created** — newly created by this PR (not a modified existing spec)
- **Modified** — existing spec changed by this PR (mark the changes using the agreed change-tracking convention)
- **Deprecated** — superseded but not yet removed
- **Retired** — removed by this PR
- A spec the change *should* have modified but did not is a review finding, not a table row — raise it in **Discussion**

**Avoid:**

- Leaving the table empty when the PR changes existing behavior
- Listing broad areas instead of linking the specific specifications
- Listing documents the diff does not change — related, read, consulted, or depended on. An unchanged entry spends reviewer attention on nothing and hides the entries that need it

**Output style:** One table, one linked specification per row, omitting statuses that don't apply (no empty "None" rows). Every modified specification must be branched from master.

| Specification | Status | Note |
| --- | --- | --- |
| [Spec link] | Created / Modified / Deprecated / Retired | optional one-line note |

</aside>
