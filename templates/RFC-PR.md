# [RFC] Specification Change Template

## How to Use This Template

<aside>

These conventions apply to **every** section below. They are stated once here so the individual sections stay short.

- **Title.** The document's top-level heading is the RFC title, prefixed `[RFC]`. Set the GitHub PR title to exactly this heading.
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

**Single source of truth — so the filled-in PR contains no redundancy.** Each kind of content has exactly one home. Every other section *links or points* to it in one line rather than restating it. When two sections would carry the same content, the more specific one below owns the detail and the broader one gives a pointer.

| Content | Its one home | What every other section does |
| --- | --- | --- |
| Full specification of each change | **Details** | Summarize or link; never re-specify |
| Prioritized reading order, priority & focus | **Reviewer Orientation** | One line per entry, linking into Details and Affected Specifications |
| Inventory of affected documents | **Affected Specifications** | Reviewer Orientation links to these entries, not re-list them |
| Why the change is needed | **Motivation** | — |
| Tradeoffs, rationale, alternatives | **Discussion** | — |
| Editorial / non-normative cleanup | **Chores** | Details excludes it |
| Engineering tasks | **Implementation** | States work to do, not the change itself |

</aside>


## Reviewer Orientation

<aside>

**Purpose:** In one place, tell reviewers *what matters most* and *the order to read it*, so they can start reviewing immediately. This section replaces a separate change summary and reading guide, and is the canonical home for the priority labels used elsewhere in the template.

**Include:** a single ordered table of the changes a reviewer should work through, in recommended reading sequence (dependencies first — not diff or alphabetical order), with these columns:

- **#** — reading order
- **Priority** — Critical / High / Medium / Low (see guidance below)
- **Document / Change** — link to its entry in **Affected Specifications** and **Details**; put a **Start here** marker on the 1–2 highest-risk entries a time-constrained reviewer must not skip
- **What to look for** — the one or two things to scrutinize (a new state transition, a changed serialization format, a removed rule, a cross-spec dependency), or "skim" for editorial / non-normative documents

Note any prerequisite context needed before the first entry (e.g., "read Motivation first", or a background spec that is unchanged but assumed).

**Priority guidance** (maps the impact dimensions from *How to Use This Template*):

- **Critical:** consensus, safety, liveness, cryptographic validity, serialization compatibility, data availability, slashing, asset loss, or hard-fork behavior
- **High:** externally visible protocol behavior, validator/node behavior, public APIs, storage formats, cross-specification dependencies, or migration requirements
- **Medium:** internal algorithms, parameters, verification criteria, performance-sensitive behavior, or implementation requirements
- **Low:** wording, examples, formatting, terminology cleanup, typo fixes, or non-normative clarifications

**Avoid:**

- Diff order or alphabetical order instead of dependency/impact order
- Giving every entry equal weight, or hiding compatibility/security/consensus/migration impact
- Re-describing *what* changed in detail (that is **Details**) or re-listing **Affected Specifications** — link to them and keep each row to one line

**Output style:** Use a single ordered table, one line per row, linking each entry to its **Details** and **Affected Specifications** entries rather than restating them. If one document contains changes at different priorities, give it a row per change (same document link, different priority and focus) rather than collapsing them under one priority. For a single-document PR, replace the table with one line (e.g., "Single-document change — read [spec] top to bottom; focus on [X].").

**Example:**

| # | Priority | Document / Change | What to look for |
| --- | --- | --- | --- |
| 1 | Critical | **Start here** — [Core spec] | new *X* state transition; removed *Y* concept |
| 2 | High | [Dependent spec A] | updated validation rules and serialization format |
| 3 | High | [Dependent spec B] | externally visible behavior; backwards-compatibility |
| 4 | Low | [Editorial spec] | skim — terminology alignment only |

</aside>


## Status tracker

- [ ]  🚧 **Raw (make sure that all below is completed)**
    -  Template applied
    -  Authors filled in
    -  Authors agree on the RFC content
- [ ]  📘 **Draft (make sure that all below is completed)**
    -  All dependent specifications added (Notion backlinks checked)
    -  Specifications to deprecate added, if applicable
    -  Specifications to retire added, if applicable
    -  Research Lead assigned, or Project Lead assigned if the Research Lead is an author
    -  Relevant Research Domain Experts assigned (cannot be authors)
- [ ]  ⚙️ **Verified (make sure that all below is completed)**
    -  Researchers’ comments addressed
    -  All logical changes documented
    -  All Research reviewers approve the latest version
    -  Engineering Lead assigned
    -  Relevant Engineering Domain Experts assigned
- [ ]  🔀 **Merged (make sure that all below is completed)**
    -  Engineers’ comments addressed
    -  Every change added to the change log
    -  All Engineering reviewers approve the latest version
    -  Specification version numbers assigned
    -  Implementation reviewed and merged
    -  Branch updated to master and all conflicts resolved
    -  PR merged

</details>

## Change log

| **Revision** | **Description** | **Date** |
| --- | --- | --- |
| v1 | Initial PR description | YYYY-MM-DD |
|  | Description of what changed in this revision | YYYY-MM-DD |
| v2 | Description of what changed in this revision | YYYY-MM-DD |
|  | Description of what changed in this revision | YYYY-MM-DD |
| vN | Description of what changed in this revision | YYYY-MM-DD |

# Motivation

<aside>

**Purpose:** Explain why this PR is needed.

**Include:**

- The problem, limitation, or opportunity being addressed
- The affected protocol, product, or system component
- Why the change matters
- Any measurable evidence, analysis, or observed issue supporting the change
- The expected benefit if the PR is accepted

**Avoid:**

- Implementation details
- Vague claims such as “improves performance” without explanation
- Repeating the Proposal section

**Output style:** Write 1–3 concise paragraphs in formal specification-change language.

</aside>

# Proposal

<aside>

**Purpose:** Summarize the proposed change at a high level.

**Include:**

- The core idea of the change and the specifications or protocol components affected
- The main behavioral or architectural change
- Any new concepts, parameters, or mechanisms introduced
- Any change along an impact dimension (see *How to Use This Template*)

**Avoid:**

- Full implementation details
- Long discussion of tradeoffs
- Repeating the Motivation section
- Enumerating every change one by one (that is **Details**) — convey the idea, then let Details specify it

**Output style:** Write a concise technical summary understandable to reviewers before they read the Details section.

</aside>

# Discussion

<aside>
💡

**Purpose:** Analyze consequences, tradeoffs, and rationale for the proposed change.

**Include:**

- Effects on relevant system properties (the impact dimensions, plus performance, reliability, scalability, decentralization, or user experience)
- Important alternatives considered, if any
- Rationale for chosen parameters, constants, or thresholds
- Risks, open questions, and assumptions
- Backwards compatibility impact and any required migration path

**Avoid:**

- Restating the Proposal without analysis
- Unsupported claims
- Implementation minutiae unless they affect the analysis
- Omitting backwards compatibility analysis for externally visible changes

**Output style:** Use clear subsections when the discussion covers multiple topics. Omit the section entirely (don't leave an empty heading) when the proposal is self-evident and has no meaningful tradeoffs.

</aside>

# Details

<aside>

**Purpose:** Specify the concrete changes required to implement the proposal across all affected specifications.

**Include:**

- All normative changes required by the PR, ordered from highest to lowest review impact
- New, modified, or removed protocol rules
- New, modified, or removed data structures, algorithms, parameters, or validation rules
- Cross-specification dependencies
- Any migration, compatibility, or rollout requirements
- Test vectors, simulation parameters, or verification criteria introduced
- Use code snippets while discussing code changes, following the *Readable code snippets* convention in *How to Use This Template*

**Avoid:**

- High-level motivation already covered above
- Omitting small but required changes
- Mixing unresolved design questions with accepted specification changes
- Editorial or non-normative cleanup (that belongs in **Chores**)

**Output style:** Use precise specification language, starting with the changes highest along the impact dimensions. This section is optional only when the Proposal section fully captures every required change.

</aside>

## Chores

<aside>

**Purpose:** The single home for all small, non-normative changes that do not require detailed explanation.

**Include:**

- Naming or terminology updates
- Formatting, rendering, or editorial updates that are part of the PR
- Minor cleanup tasks required by the proposal
- Minor specification corrections (e.g., typo fixes, bound tightening, variable renames)

**Avoid:**

- Normative protocol changes that belong in Details
- Unrelated cleanup tasks
- Presenting chores as the main contribution of the PR when substantive specification changes exist

**Output style:** Use a short bullet list at the end of Details, chores grouped and clearly lower priority than normative changes. Omit the section entirely when there are no chores.

</aside>

# Implementation

<aside>

**Purpose:** Enumerate the concrete engineering tasks required to implement this specification, as a single trackable checklist. This section absorbs verification: tests, test vectors, benchmarks, and spec-implementation agreement checks are listed as tasks here rather than in a separate Testing and Verification section.

**Include:**

- One actionable task per discrete unit of engineering work, ordered by implementation sequence where possible
- Tasks for new, modified, or removed data structures, algorithms, validation rules, and serialization
- Tasks for removing or migrating deprecated mechanisms
- Tasks for tests, test vectors, simulations, or benchmarks that exercise the change
- A final task that verifies the implementation matches this specification
- Links to implementation PRs, issues, commit ranges, or CI runs as they become available

**Avoid:**

- Vague tasks that cannot be checked off (e.g., "implement the protocol")
- Restating the Details section verbatim instead of stating the work to be done
- Claiming verification without a corresponding task or evidence
- Listing tasks unrelated to this specification

**Output style:** Use a GitHub-compatible task list — one `- [ ] task` per line (GitHub renders `- [ ]` as unchecked and `- [x]` as checked). For an editorial-only specification change, use a single task such as `- [ ] No implementation required (specification-only change)` and briefly state why.

</aside>

- [ ]  <Engineering task 1>
- [ ]  <Engineering task 2>
- [ ]  <…>
- [ ]  Add or extend tests / test vectors that exercise the change
- [ ]  Verify the implementation matches this specification

# Affected Specifications

<aside>

**Purpose:** Identify every specification affected by this PR.

**Guidance:** For PRs, this is the most critical section. Reviewers must verify the list is complete before approving. Derive the list from the current diff every time the description is updated: a document appears only if the diff changes it. Drop any document the current diff leaves untouched — including one an earlier revision of the branch changed. A document that was read, consulted, or depended on is not affected.

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

**Output style:** Use a single table, one linked specification per row, omitting statuses that don't apply (no empty "None" rows). Every modified specification must be branched from master.

| Specification | Status | Note |
| --- | --- | --- |
| [Spec link] | Created / Modified / Deprecated / Retired | optional one-line note |

</aside>
