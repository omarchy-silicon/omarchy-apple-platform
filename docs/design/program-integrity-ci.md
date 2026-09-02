# Program-integrity CI design

Status: DESIGN NOTE ONLY. This document specifies a future validator, its hostile test
surface, and its GitHub Actions enforcement. It does not implement any workflow, validator,
test, fixture, schema, or production code. No slice or release is DONE from this note.

Declared base: origin/main at 58302d148f0e8b855578f9aa518ff1c5eb48c515.

Declared lane: factory/design-program-integrity-ci.

Declared worktree: /Users/simonbourdon/Documents/GitHub/Omarchy-Silicon/lanes/program-ci-design.

## 1. Scope, authorities, and boundaries

### Scope

The future system validates the coordinator-owned PROGRAM.md as a signed-plan integrity
input. It parses the canonical five-column slice ledger, computes its dependency graph,
checks the status census, proves dynamic F-07 closure and direct prerequisites, proves the
single stable-promotion writer seam, and verifies that decision and progress history is
append-only against the actual pull-request base commit. It emits deterministic JSON and a
human-readable fail census.

The future workflow runs that validator from a trusted base checkout against the proposed
merge tree as data. It also runs the standard-library hostile tests from a trusted checkout,
records clean-checkout and toolchain evidence, and uploads only redacted validator output.

### Non-goals

This design does not validate platform behavior, signed artifact contents, board
qualification, physical evidence, installer behavior, release compliance, cryptographic
trust roots, or product wire errors. It does not replace F-02, F-03, F-05, F-06, or F-07.
It does not inspect or operate on the human-produced opaque boot-artifact source boundary.
It does not authorize a release, change a branch-protection rule, merge a pull request, or
mark a PROGRAM slice DONE.

The m1n1-omarchy repository and every m1n1 path are an opaque human-produced boundary for
this design. The only permitted description of that boundary is the external signed
artifact checks stated below; no source-level fact is inferred.

The opaque boundary is represented only by the external checks already required by
PROGRAM.md: a human-signed artifact identity, declared digest, signature, schema,
provenance, license and notice inventory, redistribution decision, source-offer statement
where applicable, and interface attestation. The future validator compares those declared
external values at the platform boundary; it never reads, traverses, characterizes, builds,
or tests the fenced source.

### Consumed authorities

The implementation consumes only these authorities at the declared base:

1. AGENTS.md, especially the coordinator-only DONE rule, append-only history rule,
   read-only reviewer rule, exact-base rule, and fail-closed unknown rule.
2. PROGRAM.md, especially Sections 6, 8, 10, 11, 12, 13, 17, 18, and 19; the canonical
   ledger, F-07 prerequisites, status vocabulary, decision history, and progress history
   are read as authority rather than copied into a second policy file.
3. GitHub pull-request event metadata and Git object identity for the canonical repository.
   Event fields are untrusted until repository, SHA, format, ancestry, and availability
   checks pass.

The current PROGRAM structure has no explicit machine-readable marker identifying which Q
rows are board-cohort qualification terminals. Before promotion-mode enforcement is
considered complete, the coordinator must add this exact paragraph under Section 12:

Q cohort rows are exactly ledger rows whose ID matches Q-[0-9]{2} and whose Deliverable cell begins with the exact case-sensitive verb Certify followed by one space. All other Q rows are intake, schema, lab-setup, or other non-cohort rows and are not Q cohorts.

The validator recognizes that paragraph byte-for-byte in the Section 12 authority text.
That sentence makes the classification part of the consumed coordinator authority without
creating a validator-owned list or a second authority. Until it exists in the actual
PROGRAM.md being validated, the validator fails closed with PI_POLICY_UNDECLARED for
promotion mode; it may not silently fall back to the current Q-04 through Q-08 spelling.

### Plan integrity is not release readiness

Plan integrity answers whether the written plan is structurally closed, historically
append-only, and governed by one declared promotion seam. Release readiness answers whether
the assembled candidate is signed, reproducible, legally distributable, compatible,
physically qualified, rollback-capable, and honestly represented. A green plan-integrity
check therefore does not establish a release, support level, hardware compatibility, or
qualification result. Conversely, a release gate may not waive a failed plan-integrity
check because its artifacts or physical tests look good.

## 2. Exact future ownership

The following paths are reserved for later work. Every path is named now, the ownership
sets are disjoint, and none of these files exists at the declared base or in this design
lane. This document is the only file owned by the current lane.

| Future path | Owner | Responsibility |
|---|---|---|
| src/release/stable_store.py | F-07 implementation lane | One immutable channel-copy sink; it accepts only an authenticated F07PromotionReceipt and never decides readiness |
| src/release/f07_promotion.py | F-07 implementation lane | The sole caller that may copy an already-built candidate digest to stable after recomputing closure |
| tools/program_integrity/validate.py | Program-integrity implementation lane | Standalone Python CLI, canonical parser, graph/history/policy checks, deterministic JSON, and human fail census |
| tests/program_integrity/test_validate.py | Program-integrity QA lane | Python standard-library unit tests and hostile tests; it invokes only the validator contract and temporary data |
| tests/program_integrity/fixtures/valid-program.md | Program-integrity QA lane | Positive ledger and history fixture |
| tests/program_integrity/fixtures/malformed-table.md | Program-integrity QA lane | Malformed five-column ledger fixture |
| tests/program_integrity/fixtures/duplicate-id.md | Program-integrity QA lane | Duplicate ledger ID fixture |
| tests/program_integrity/fixtures/unknown-dependency.md | Program-integrity QA lane | Missing or unknown dependency fixture |
| tests/program_integrity/fixtures/self-edge.md | Program-integrity QA lane | Self-dependency fixture |
| tests/program_integrity/fixtures/cycle.md | Program-integrity QA lane | Dependency-cycle fixture |
| tests/program_integrity/fixtures/missing-f07-closure.md | Program-integrity QA lane | F-07 reachability gap fixture |
| tests/program_integrity/fixtures/missing-direct-p03.md | Program-integrity QA lane | Removed F-07 to P-03 direct edge |
| tests/program_integrity/fixtures/missing-direct-p05.md | Program-integrity QA lane | Removed F-07 to P-05 direct edge |
| tests/program_integrity/fixtures/missing-direct-i09.md | Program-integrity QA lane | Removed F-07 to I-09 direct edge |
| tests/program_integrity/fixtures/missing-direct-b04.md | Program-integrity QA lane | Removed F-07 to B-04 direct edge |
| tests/program_integrity/fixtures/missing-direct-q04.md | Program-integrity QA lane | Removed F-07 to the Q-04 cohort edge |
| tests/program_integrity/fixtures/missing-direct-q05.md | Program-integrity QA lane | Removed F-07 to the Q-05 cohort edge |
| tests/program_integrity/fixtures/missing-direct-q06.md | Program-integrity QA lane | Removed F-07 to the Q-06 cohort edge |
| tests/program_integrity/fixtures/missing-direct-q07.md | Program-integrity QA lane | Removed F-07 to the Q-07 cohort edge |
| tests/program_integrity/fixtures/missing-direct-q08.md | Program-integrity QA lane | Removed F-07 to the Q-08 cohort edge |
| tests/program_integrity/fixtures/duplicate-progress-row.md | Program-integrity QA lane | Duplicated progress-history row fixture |
| tests/program_integrity/fixtures/rewritten-progress-row.md | Program-integrity QA lane | Rewritten retained progress-history row fixture |
| tests/program_integrity/fixtures/deleted-progress-row.md | Program-integrity QA lane | Deleted retained progress-history row fixture |
| tests/program_integrity/fixtures/reordered-decision-row.md | Program-integrity QA lane | Reordered decision-history row fixture |
| tests/program_integrity/fixtures/second-stable-writer.py | Program-integrity QA lane | AST input that adds a second stable sink caller |
| tests/program_integrity/fixtures/unknown-status.md | Program-integrity QA lane | Unknown status fixture |
| tests/program_integrity/fixtures/control-characters.md | Program-integrity QA lane | Control-character fixture |
| tests/program_integrity/fixtures/unicode-confusable-id.md | Program-integrity QA lane | Non-ASCII confusable ID fixture |
| tests/program_integrity/fixtures/warning-success.md | Program-integrity QA lane | Required failure relabeled as a warning fixture |
| .github/workflows/program-integrity.yml | Repository CI owner | Read-only PR and branch workflow, trusted-base execution, network isolation, and artifact upload |

The oversized-input, unavailable-base, and shallow-history cases are generated in temporary
directories by test_validate.py; they are deliberately not checked-in megabyte or Git
database fixtures. No future implementation file outside this table may be created as part
of this design.

## 3. Canonical validator contract

### Input and output

validate.py is a standalone Python 3.13.5 standard-library program. It runs with
python -I -S, imports no third-party package, reads only explicitly named paths and Git
metadata, and never executes a file from the candidate tree. The maximum input size is
1,048,576 bytes per PROGRAM.md and 10,000 ledger rows. UTF-8 decoding is strict. A
candidate exceeding either bound returns PI_INPUT_TOO_LARGE and cannot return success.

The JSON result uses UTF-8 with ensure_ascii=true, sorted keys, stable list ordering, and
one final newline. Success has exit status 0 and contains result PASS, the exact base SHA,
merge-base SHA, candidate tree identity, topological order, closure list, direct-edge
set, and status census. Failure contains result FAIL, one primary stable error code,
phase, path, line when known, a deterministic detail, and the complete fail census for
all failures observed after the primary phase. Human output contains one line in the form
FAIL code phase path detail for every failure and never reports a required failure as a
warning followed by success.

Unknown input, an unavailable required authority, an unsupported syntax variant, an
unhandled parser exception, or an unrecognized executable path is a hard failure. The
validator must return PI_UNKNOWN with exit status 70 for an internal or otherwise
uncategorized condition; it must not default, skip, warn, or synthesize a result.

### Five-column ledger parser

The parser locates exactly one heading named ## 12. Slice ledger and exactly one ledger
table after the Section 12.1 acceptance table. It does not search all Markdown tables and
does not use a grep pattern as a parser. The ledger header cells must be exactly ID,
Repository, Deliverable, Depends on, and Status, enclosed by the five outer pipe
boundaries. The delimiter cells must each contain exactly three hyphens.

Each data row must contain exactly five cells in the same order: ID, Repository,
Deliverable, Depends on, Status. A row is split on its six outer pipe boundaries, with
ASCII spaces trimmed from the cell edges. Tabs, embedded unescaped pipes, empty ID, empty
repository, empty deliverable, empty dependency expression, and empty status are rejected.
The parser stops only at the blank line or next structural heading that terminates this
table; a pipe-prefixed malformed line in the table region is PI_ROW_SHAPE, not an ignored
paragraph. The line number is carried into every row diagnostic.

The ID grammar is ASCII and case-sensitive: (B|F|G|I|K|P|Q)-[0-9]{2}. The complete ID
set is derived from the rows, not from a hard-coded list of current IDs. Status is also
ASCII and case-sensitive and must be exactly one of DONE, IN PROGRESS, REVIEW, TODO, or
HUMAN-ONLY BLOCKED. REVIEW is allowed by the factory lifecycle even though the exact base
ledger has no REVIEW row. No other status, prefix, width, separator, Unicode lookalike,
or normalization is accepted.

The dependency cell is either none or a comma-and-one-space separated sequence of exact
IDs and the two existing external prerequisite literals already present in PROGRAM.md:
shipping hardware and the human-owner qualifier. The external literals are opaque,
non-graph prerequisites; they are compared exactly and never resolved to a repository,
path, source, or executable. none cannot be combined with another token. Empty tokens,
duplicate tokens, unknown IDs, and unknown external literals fail closed.

The parser returns an immutable row record containing raw row bytes, line number, ID,
repository, deliverable, ordered dependency tokens, graph dependency IDs, external
prerequisites, and status. All downstream checks consume these records. No check reparses
the ledger or maintains a consumer-specific field list.

### Graph checks and traversal

After parsing all rows, the validator checks duplicate IDs, missing graph dependencies,
self-edges, duplicate dependency tokens, and cycles in that order. A missing dependency is
PI_DEP_UNKNOWN even when the missing token resembles a valid ID. A self-edge is
PI_DEP_SELF. A cycle is PI_DEP_CYCLE.

The deterministic topological traversal represents each declaration A depends on B as a
graph edge B to A, so dependencies precede their consumers. It uses Kahn's algorithm with
a min-heap ordered by the canonical ASCII ID string. The emitted order is therefore
independent of hash-table ordering or file-system order. For a cycle, the witness starts
at the lexicographically smallest unvisited node and follows lexicographically sorted
outgoing dependency edges; the closed cycle is rotated to its lexicographically smallest
first ID. The same input always emits the same order and witness.

The exact status census is computed only after lexical and graph validation succeeds. It
contains total, counts for all five allowed statuses including zero, and sorted ID lists
for every status. It does not infer state from decision history, progress history, branch
names, commit messages, or prose. For the exact base ledger, the expected census is
52 total rows: 1 DONE, 1 IN PROGRESS, 0 REVIEW, 44 TODO, and 6 HUMAN-ONLY BLOCKED. The
future test must recompute this value from the base rather than hard-code it as its only
assertion.

## 4. Dynamic F-07 policy and sole-writer proof

### Closure and direct edges

The validator requires exactly one row with ID F-07. It traverses only graph dependency
edges from F-07, recursively and deterministically, and requires the reachable set to
equal the complete parsed ledger ID set. Any missing ID is reported in sorted order as
PI_F07_CLOSURE at policy.f07.closure. This makes the closure dynamic: a newly added ledger
ID is automatically a required F-07 descendant without editing validator code.

The direct-edge policy is checked separately from transitive closure. F-07 must directly
depend on F-05 and on P-03, P-05, I-09, and B-04. It must also directly depend on every
Q cohort derived from the coordinator-owned classification amendment in Section 1. The
validator reports each missing edge separately as PI_F07_DIRECT_EDGE at
policy.f07.direct_edges.ID. A transitive path never satisfies a mandatory direct edge.
The Q set is computed from the parsed rows on every run; Q-04 through Q-08 are the
current expected result, not a validator-owned enumeration.

If the classification amendment is absent or cannot be parsed exactly, the validator
returns PI_POLICY_UNDECLARED at policy.q_cohorts before evaluating promotion-mode
closure. It never invents a second cohort list. If a future coordinator changes the
classification rule, the change is a PROGRAM authority change and must be reviewed as
such.

### Structural proof of the sole stable writer

The future F-07 production seam has exactly two reserved files. stable_store.py defines
the only low-level function named copy_immutable_digest_to_channel. f07_promotion.py is
the only permitted caller, and its only permitted channel argument is the literal stable.
The store accepts a verified F07PromotionReceipt and performs the atomic copy; it does
not calculate closure or accept a status override. The workflow in this design never
writes a channel.

The validator proves this with a syntax-aware AST and control-flow audit, not a vague grep:

1. Enumerate tracked files under src/release using Git's NUL-delimited file list. An
   unrecognized executable suffix, symlink, generated launcher, or unreadable file in that
   directory is PI_UNKNOWN.
2. Parse every Python source file with ast.parse under the pinned interpreter. Syntax
   errors, dynamic import constructs, eval, exec, getattr-based sink lookup, shell
   execution, subprocess calls, and network imports in the release seam are hard failures.
3. Resolve only direct, non-aliased imports of
   release.stable_store.copy_immutable_digest_to_channel. Count every call AST node to
   that resolved symbol and require exactly one call site.
4. Require that the one call site is in src/release/f07_promotion.py, passes the literal
   stable as its first argument, and is dominated on every control-flow path in that
   module by construction of an F07PromotionReceipt. A small standard-library control-flow
   and data-flow pass proves that the receipt cannot be replaced before the call; an
   unknown control-flow shape is PI_UNKNOWN.
5. Require that stable_store.py defines the sink and that no other production file defines
   a channel-copy primitive, calls the sink, or exposes a second stable channel. The audit
   enumerates every tracked production Python source file, and rejects any executable
   production file outside the two reserved release paths because its write capability is
   not closed. Test and fixture files are input data for this audit, not production
   writers. The audit reports the resolved module, symbol, call count, and call paths in
   JSON so a reviewer can reproduce the proof.

The hostile second-stable-writer fixture adds a direct call in another source file; the
test also covers an import alias and a dynamic lookup. Each must fail the AST contract.
The proof is bounded by the closed Python release seam. Unknown code shape or language
boundary is a failure, never an implied pass.

## 5. Append-only decision and progress history

### Trusted base selection

For a pull request, the workflow reads base.repo.full_name, base.sha, head.repo.full_name,
head.sha, and the pull-request number from the event. The base repository must equal
github.repository. The base and head SHA values must each be exactly 40 lowercase or
uppercase hexadecimal characters and must resolve to commit objects fetched from the
canonical GitHub repository and the declared head repository respectively. Fork heads
are permitted as data sources; fork credentials, secrets, and arbitrary URLs are not.

The workflow uses actions/checkout with fetch-depth 0, fetches no tags, submodules, or LFS,
and persists no credentials. It materializes the base tree at the actual base.sha, the
head tree at head.sha, and the synthetic pull-request merge commit from the event's
pull-request merge ref. It first verifies that git merge-base base.sha head.sha succeeds
and records that SHA. It requires the synthetic merge commit to exist, to be
conflict-free, and to have actual base.sha as its first parent; its tree is the candidate
tree. It does not require the head branch to contain the newest base commit, because a
pull request may be based on an older common ancestor. A missing base object, repository
mismatch, invalid SHA, missing merge-base, shallow repository, conflicting merge, or
unavailable pull-request merge context returns a base-trust failure before any candidate
code is executed.

The trusted validator and trusted test harness are loaded from the base tree. The
candidate tree is mounted read-only as input. No Python, shell, binary, workflow helper,
test, or build script from the candidate tree is executed. This is required for fork PRs
and for any event whose base cannot be proven trusted. If the validator is absent from the
base tree during bootstrap, the check returns PI_BASE_UNAVAILABLE; the rollout must
land the validator and its tests before the workflow is introduced.

For a branch push, the parent commit supplied by the push event is the base commit. An
all-zero before SHA, missing parent, shallow history, or failed merge-base is a hard
failure. Branch validation never substitutes the local checkout tip or origin/main for a
missing event parent.

### Exact append-only algorithm

The trusted validator extracts the raw UTF-8 table-row bytes under the decision-log and
progress-log headings from PROGRAM.md at the actual base tree and from the candidate merge
tree. The decision-log header cells must be exactly Date, Decision, and Reason. The
progress-log header cells must be exactly Timestamp, Event, and Evidence or result. Both
delimiter rows must have exactly three hyphens in each cell. Their data-row bytes are
otherwise opaque to the ledger parser. No whitespace, Unicode, line-ending, or Markdown
normalization is applied.

For each history:

1. Verify that every base row occurs byte-for-byte at the same index in the candidate
   sequence. The base sequence is an immutable prefix, not a set and not a sorted list.
2. If the candidate has the same length and row multiset as base but a different order,
   return PI_HISTORY_REORDER.
3. If the candidate has the same length but a different row multiset, return
   PI_HISTORY_REWRITE.
4. If the candidate is shorter than base, return PI_HISTORY_DELETE. If it is longer but
   does not contain the complete base-row multiset, return PI_HISTORY_DELETE.
5. For a retained prefix and appended rows, validate the exact table shape, reject control
   characters, and reject
   duplicate raw progress rows or duplicate decision identity keys. The first appended
   duplicate in byte order is PI_HISTORY_DUPLICATE.

The history checks use the actual base commit, not origin/main, a local branch name, a
checkout's default merge ref, or a contributor-provided base file. The JSON evidence
contains base.sha, merge_base, base row counts, candidate row counts, exact retained-prefix
digest, and appended-row digests. A failure contains the first differing index and the
base/candidate row digests without echoing secrets.

## 6. CI workflow and security contract

### Triggers and exact check

The future workflow path is .github/workflows/program-integrity.yml. It triggers on pull
request opened, synchronize, reopened, and ready_for_review events, and on pushes to main
and factory/** branches. It runs all gates in one job named validate under workflow name
program-integrity. The exact branch-protection check name is program-integrity / validate.
No alternate job, neutral conclusion, skipped required phase, or renamed check may satisfy
the handoff.

The workflow uses concurrency group program-integrity-${{ github.event.pull_request.number
|| github.ref }} with cancel-in-progress true. A superseded run is not a pass; the newest
uncancelled run must produce the required check.

### Permissions and actions

The job declares permissions contents: read and no other permission. It uses no repository
secrets, deployment token, write token, OIDC identity, artifact signing key, or
pull_request_target event. Fork pull requests therefore receive the same read-only path.
The only actions are pinned by immutable commit SHA:

- actions/checkout v4.2.2 at 11bd71901bbe5b1630ceea73d27597364c9af683.
- actions/upload-artifact v4.6.2 at ea165f8d65b6e75b540449e92b4886f43607fa02.

Checkout uses fetch-depth 0, fetch-tags false, submodules false, lfs false, and
persist-credentials false. Any action reference that is a tag, branch, shortened SHA, or
mutable container tag is a workflow failure.

### Pinned tools, network, and cache

The runner contract is ubuntu-24.04 with Git 2.47.2 and Docker Engine 27.5.1; a preflight
checks exact versions and returns PI_TOOLCHAIN_UNAVAILABLE if either is unavailable.
The isolated validator image is the amd64 Linux image
python:3.13.5-slim-bookworm@sha256:a7cb177dc60dfa77b223192cd0d9e6ce1aac7cf9a569023d68e7c91b6371a718.
The image reports Python 3.13.5 and is used with python -I -S. No pip, package index,
formatter, linter, compiler, or third-party module is needed.

Network is allowed only for the pinned GitHub checkout actions, the canonical GitHub
repository and permitted fork object fetch, the pinned Docker image digest from
registry-1.docker.io, and the final upload-artifact call. No contributor URL, submodule,
LFS endpoint, package index, arbitrary curl, arbitrary download, or release endpoint is
allowed. After the image is present, validator and test containers run with
--network=none, read-only source mounts, dropped capabilities, no-new-privileges, and a
small tmpfs for the JSON report. The workflow records the network-isolated command in its
evidence.

No actions/cache, pip cache, Docker layer cache, or cross-run workspace cache is used.
Cache reuse can launder contributor-controlled content into a structural check, so every
run uses a fresh checkout and an immutable image digest. The uploaded report and human
fail census are retained for 14 days and contain no credentials or raw environment.

### Clean-checkout and evidence requirements

The job fails unless the base and candidate directories are clean read-only checkouts,
the expected commit identities match the event, the merge-base evidence is present, and
the changed-file census is recorded. It runs git status --porcelain=v1 and
git diff --exit-code in each checkout, then runs git diff --check against the allowlisted
program-integrity paths. It checks conflict markers only in the allowlisted paths
PROGRAM.md, tools/program_integrity, tests/program_integrity, and
.github/workflows/program-integrity.yml; it never performs an unbounded repository
traversal across an opaque external source boundary.

The report must include exact base, merge-base, head, candidate-tree, validator-source,
runner, container-image, action-SHA, command, exit-status, and changed-file values. The
human section must include PASS count, FAIL count, and an explicit fail census by stable
code and path. A zero FAIL count with a missing phase, missing evidence item, unavailable
tool, or warning-success is itself PI_UNKNOWN.

## 7. Exit classes, error codes, and precedence

The validator's exit status is separate from F-02 product wire error codes. It emits no
F-02 error identifier and does not reuse a product error number. All validator codes have
the PI_ prefix and all failures are machine-readable.

| Exit status | Class | Stable codes |
|---|---|---|
| 0 | Valid plan-integrity result | PI_OK |
| 2 | Invocation or argument failure | PI_USAGE |
| 10 | UTF-8, control, table, row, ID, or status grammar | PI_INPUT_TOO_LARGE, PI_UTF8, PI_CONTROL_CHAR, PI_LEDGER_TABLE, PI_ROW_SHAPE, PI_ID_SYNTAX, PI_STATUS_UNKNOWN |
| 11 | Dependency graph failure | PI_DUPLICATE_ID, PI_DEP_UNKNOWN, PI_DEP_DUPLICATE, PI_DEP_SELF, PI_DEP_CYCLE |
| 12 | Promotion policy or stable-writer failure | PI_F07_MISSING, PI_POLICY_UNDECLARED, PI_F07_DIRECT_EDGE, PI_F07_CLOSURE, PI_SECOND_STABLE_WRITER, PI_WARNING_SUCCESS |
| 13 | Append-only history failure | PI_HISTORY_DELETE, PI_HISTORY_REWRITE, PI_HISTORY_REORDER, PI_HISTORY_DUPLICATE |
| 14 | Base, merge, trust, or toolchain failure | PI_BASE_REPOSITORY, PI_BASE_SHA, PI_BASE_UNAVAILABLE, PI_BASE_SHALLOW, PI_MERGE_BASE, PI_TOOLCHAIN_UNAVAILABLE |
| 70 | Unknown hard failure | PI_UNKNOWN |

The primary-error precedence is fixed and evaluated before any later phase can replace it:
PI_USAGE; PI_BASE_REPOSITORY; PI_BASE_SHA; PI_BASE_UNAVAILABLE; PI_BASE_SHALLOW;
PI_MERGE_BASE; PI_TOOLCHAIN_UNAVAILABLE; PI_INPUT_TOO_LARGE; PI_UTF8; PI_CONTROL_CHAR;
PI_LEDGER_TABLE; PI_ROW_SHAPE; PI_ID_SYNTAX; PI_STATUS_UNKNOWN; PI_DUPLICATE_ID;
PI_DEP_UNKNOWN; PI_DEP_DUPLICATE; PI_DEP_SELF; PI_DEP_CYCLE; PI_F07_MISSING;
PI_POLICY_UNDECLARED; PI_F07_DIRECT_EDGE; PI_F07_CLOSURE; PI_SECOND_STABLE_WRITER;
PI_WARNING_SUCCESS; PI_HISTORY_DELETE; PI_HISTORY_REORDER; PI_HISTORY_REWRITE;
PI_HISTORY_DUPLICATE; PI_UNKNOWN.

Within a code, diagnostics are sorted by phase, source path, one-based line number, and
canonical ID or raw digest. If multiple mandatory edges are missing, all missing edges
appear in the fail census but the first lexicographic edge controls the primary detail.
Warnings are informational only for non-required observations; a required failure labeled
warning is PI_WARNING_SUCCESS with exit 12. No unknown condition is downgraded.

## 8. Hostile test matrix

Every hostile test runs from a clean temporary copy of valid-program.md, applies exactly
the stated mutation, invokes the trusted validator, captures JSON and human output, and
asserts the stable code, path, phase, exit status, and evidence. The fixture name is the
checked-in input unless the row explicitly says runtime-generated. Positive tests also
assert the exact base census and deterministic topological order.

| Case | Input mutation | Expected code, path, and phase | Exit | Required evidence |
|---|---|---|---:|---|
| valid baseline | No mutation to valid-program.md | PI_OK; report.result; report | 0 | JSON PASS, 52-row census, closure contains every ledger ID, deterministic topological order, zero FAIL |
| malformed header | Change the exact ledger header cell text | PI_LEDGER_TABLE; ledger.header; parse | 10 | Expected header cells, actual header cells, source line, human FAIL, no PASS |
| malformed row shape | Remove one delimiter cell or add a sixth ledger cell | PI_ROW_SHAPE; ledger.rows.line; parse | 10 | First malformed line, expected five cells, actual count, human FAIL, no PASS |
| duplicate ID | Copy one ledger row and retain its ID | PI_DUPLICATE_ID; ledger.rows.ID; graph | 11 | Duplicate ID, both source lines, sorted ID census absent, no status-derived success |
| unknown dependency | Replace one dependency with Z-99 | PI_DEP_UNKNOWN; ledger.rows.ID.depends; graph | 11 | Raw token, source line, known-ID set not used as fallback, no topological order |
| self-edge | Add the row ID to its own dependency cell | PI_DEP_SELF; ledger.rows.ID.depends; graph | 11 | Self edge, row line, no cycle witness substituted |
| cycle | Change two dependency cells to form A to B and B to A | PI_DEP_CYCLE; graph.cycle; graph | 11 | Canonical closed witness, sorted traversal seed, no partial closure |
| missing F-07 closure | Remove G-05 from both applicable Q-cohort dependency rows so G-05 is unreachable from F-07 | PI_F07_CLOSURE; policy.f07.closure.G-05; policy | 12 | Sorted missing-ID list, complete ledger total, direct-edge evidence still present |
| missing direct P-03 | Remove only F-07 to P-03 | PI_F07_DIRECT_EDGE; policy.f07.direct_edges.P-03; policy | 12 | Transitive reachability shown separately, missing direct edge, no warning-success |
| missing direct P-05 | Remove only F-07 to P-05 | PI_F07_DIRECT_EDGE; policy.f07.direct_edges.P-05; policy | 12 | Transitive reachability shown separately, missing direct edge, no warning-success |
| missing direct I-09 | Remove only F-07 to I-09 | PI_F07_DIRECT_EDGE; policy.f07.direct_edges.I-09; policy | 12 | Transitive reachability shown separately, missing direct edge, no warning-success |
| missing direct B-04 | Remove only F-07 to B-04 | PI_F07_DIRECT_EDGE; policy.f07.direct_edges.B-04; policy | 12 | Transitive reachability shown separately, missing direct edge, no warning-success |
| missing direct Q-04 | Remove only F-07 to Q-04 | PI_F07_DIRECT_EDGE; policy.f07.direct_edges.Q-04; policy | 12 | Q-04 derived from PROGRAM classification, missing direct edge, no warning-success |
| missing direct Q-05 | Remove only F-07 to Q-05 | PI_F07_DIRECT_EDGE; policy.f07.direct_edges.Q-05; policy | 12 | Q-05 derived from PROGRAM classification, missing direct edge, no warning-success |
| missing direct Q-06 | Remove only F-07 to Q-06 | PI_F07_DIRECT_EDGE; policy.f07.direct_edges.Q-06; policy | 12 | Q-06 derived from PROGRAM classification, missing direct edge, no warning-success |
| missing direct Q-07 | Remove only F-07 to Q-07 | PI_F07_DIRECT_EDGE; policy.f07.direct_edges.Q-07; policy | 12 | Q-07 derived from PROGRAM classification, missing direct edge, no warning-success |
| missing direct Q-08 | Remove only F-07 to Q-08 | PI_F07_DIRECT_EDGE; policy.f07.direct_edges.Q-08; policy | 12 | Q-08 derived from PROGRAM classification, missing direct edge, no warning-success |
| duplicate progress row | Append an exact retained progress row after the base prefix | PI_HISTORY_DUPLICATE; history.progress.append; history | 13 | Base prefix digest unchanged, duplicate raw-row digest and appended line, human FAIL |
| rewritten progress row | Change one retained progress evidence cell without appending a correction row | PI_HISTORY_REWRITE; history.progress.prefix.index; history | 13 | First differing index, base and candidate row digests, no normalized comparison |
| deleted progress row | Delete one retained progress row | PI_HISTORY_DELETE; history.progress.prefix.index; history | 13 | Missing base row identity and base/candidate counts, no prefix truncation accepted |
| reordered decision row | Permute two retained decision rows | PI_HISTORY_REORDER; history.decision.order; history | 13 | Same row multiset with different order, first inversion, no sorted-set acceptance |
| second stable writer | Add a second direct sink call using second-stable-writer.py | PI_SECOND_STABLE_WRITER; policy.stable_writer.callers; policy | 12 | AST-resolved sink symbol, two call paths, allowed caller path, no grep-only evidence |
| unknown status | Replace TODO with BLOCKED | PI_STATUS_UNKNOWN; ledger.rows.ID.status; parse | 10 | Raw status, allowed-status grammar, no census or success |
| control characters | Insert U+0000, U+000B, or U+007F into a cell | PI_CONTROL_CHAR; input.bytes.offset; parse | 10 | Byte offset, Unicode code point, no terminal control emitted |
| Unicode confusable ID | Replace ASCII F-01 with a fullwidth or Cyrillic lookalike | PI_ID_SYNTAX; ledger.rows.line.id; parse | 10 | Escaped raw ID, ASCII grammar, no Unicode normalization |
| oversized input | Runtime-generate a file of 1,048,577 bytes | PI_INPUT_TOO_LARGE; input.size; preflight | 10 | Actual byte count, configured limit, no parse attempt |
| base unavailable | Omit the base commit object | PI_BASE_UNAVAILABLE; base.commit; trust | 14 | Event SHA, failed object check, no candidate code execution |
| base repository mismatch | Set base.repo.full_name to a repository other than github.repository | PI_BASE_REPOSITORY; base.repository; trust | 14 | Event repository values, canonical expected repository, no candidate code execution |
| shallow history | Set up a shallow temporary Git repository | PI_BASE_SHALLOW; base.history; trust | 14 | is-shallow result, fetch-depth evidence, no local-tip substitution |
| merge-base unavailable | Use unrelated base and head histories | PI_MERGE_BASE; base.merge_base; trust | 14 | Failed merge-base command, both commit identities, no candidate code execution |
| warning-success | Remove P-03 and label the required failure warning in the fixture text | PI_F07_DIRECT_EDGE; policy.f07.direct_edges.P-03; policy | 12 | Human FAIL, exit 12, no PASS, no success true, warning cannot downgrade |

The QA lane must add at least one simultaneous-failure assertion: a malformed table,
unknown status, missing direct edge, and rewritten history in one candidate must report
PI_LEDGER_TABLE as primary according to the precedence table and retain the later failures
in the JSON fail census. It must also assert that an unavailable base wins over every
candidate mutation and that an unavailable pinned tool is a limitation with exit 14,
never PASS.

## 9. Local and CI commands

These are future commands, not commands that pass in this design-only lane.

Local trusted-base validation after the validator is available:

    python3.13 -I -S tools/program_integrity/validate.py --program PROGRAM.md --base-ref origin/main --head-ref HEAD --json-out /tmp/program-integrity.json

Local standard-library tests:

    python3.13 -I -S -m unittest discover -s tests/program_integrity -p 'test_*.py' -v

Local hostile-only census:

    python3.13 -I -S -m unittest discover -s tests/program_integrity -p 'test_validate.py' -k HostileMatrix -v

CI preflight:

    git --version
    docker version --format '{{.Server.Version}}'
    git rev-parse --is-shallow-repository
    git merge-base "$BASE_SHA" "$HEAD_SHA"

CI isolated validator and tests:

    docker run --rm --network=none --read-only --cap-drop=ALL --security-opt=no-new-privileges -v "$BASE_DIR:/base:ro" -v "$CANDIDATE_DIR:/candidate:ro" -v "$REPORT_DIR:/report:rw" python:3.13.5-slim-bookworm@sha256:a7cb177dc60dfa77b223192cd0d9e6ce1aac7cf9a569023d68e7c91b6371a718 python -I -S /base/tools/program_integrity/validate.py --base-program /base/PROGRAM.md --candidate-program /candidate/PROGRAM.md --base-sha "$BASE_SHA" --merge-base "$MERGE_BASE" --candidate-root /candidate --json-out /report/program-integrity.json

    docker run --rm --network=none --read-only --cap-drop=ALL --security-opt=no-new-privileges -v "$BASE_DIR:/base:ro" -v "$FIXTURE_DIR:/fixtures:ro" -v "$REPORT_DIR:/report:rw" python:3.13.5-slim-bookworm@sha256:a7cb177dc60dfa77b223192cd0d9e6ce1aac7cf9a569023d68e7c91b6371a718 python -I -S -m unittest discover -s /base/tests/program_integrity -p 'test_*.py' -v

The local and CI commands must print a PASS/FAIL census, not just a process exit code.
The census includes every test case, every validator phase, every stable error code, and
every unavailable-tool limitation. A formatter or third-party static checker is not part
of this design because no concrete pinned formatter or checker is selected. Python
ast.parse under Python 3.13.5 is the only specified static syntax check. If a future
owner adds a formatter or checker, its exact version and immutable acquisition must be
recorded before a green result can be claimed; an unavailable tool is not PASS.

## 10. Rollout and ownership checkpoints

The rollout order is fixed:

1. Coordinator rules on this design and separately decides whether to add the minimum
   Q-cohort classification amendment to PROGRAM.md.
2. The implementation lane creates validate.py, test_validate.py, and the named fixtures;
   it proves the parser, graph, history, policy, AST writer, and exit-code contracts.
3. A read-only adversarial reviewer plants every listed violation, including a second
   stable writer, fork-style base failure, shallow history, warning-success, and combined
   failures. The default verdict is REJECT until the planted guard trips with the specified
   evidence.
4. After the validator and test surface are independently accepted, the CI owner creates
   program-integrity.yml with the pinned actions, runner/toolchain, trust-boundary, and
   network policy in this note.
5. The coordinator obtains GitHub run proof from valid PRs and hostile PRs, including a
   fork PR, an unavailable-base simulation, and a shallow-history simulation. The proof
   includes check name, exact tip, artifacts, exit status, and fail census.
6. The repository owner decides whether branch protection may require
   program-integrity / validate and whether workflow changes require an owner-approved
   review. Only that owner checkpoint can change repository policy.

No slice or release becomes DONE from this design. Even after the workflow is green,
PROGRAM.md remains a plan authority and F-07 remains responsible for release readiness.

## 11. Open questions

1. Coordinator ruling: will the exact Q-cohort classification sentence in Section 1 be
   added to PROGRAM.md before promotion-mode implementation begins?
2. Owner ruling: is the repository owner authorizing a branch-protection policy change
   that makes program-integrity / validate required on main? This design does not assume
   that authority.
3. Coordinator and CI-owner ruling: does the repository-hosted runner actually provide
   Git 2.47.2 and Docker Engine 27.5.1, or must an owner-approved immutable runner image
   provide them? An unavailable version remains a failed gate.
4. Coordinator ruling: are src/release/stable_store.py and
   src/release/f07_promotion.py the accepted F-07 production seam names, or should the
   same two-role seam receive different exact paths before implementation?
5. Owner ruling: is registry-1.docker.io an approved CI dependency for the pinned
   Python image, or must the image be mirrored under an owner-controlled immutable
   registry and its digest re-recorded?
6. Coordinator ruling: after validator/tests land, may the workflow run only trusted-base
   test code on PRs, with candidate tests becoming executable only after merge? This
   design chooses the fail-closed trusted-base behavior to prevent contributor code
   execution during fork validation.
