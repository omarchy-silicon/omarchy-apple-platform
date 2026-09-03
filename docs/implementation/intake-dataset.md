# Q-00 cited Apple Silicon intake dataset design

Status: design note only. This note defines the executable Q-00 dataset boundary; it is not an intake dataset, board-registry publication, qualification record, support claim, release input, or DONE claim.

## Purpose and boundary

Q-00 produces an offline-verifiable, append-only observation dataset for Apple Silicon board intake. It preserves what an authoritative source said, when it was retrieved, and exactly which bytes were used. It does not infer compatibility from a chip family, promote a board to Omarchy support, perform hardware qualification, verify signatures, or authorize an installer mutation. Q-01 owns the qualification criteria and records; F-03 owns trust and signing; F-05 owns candidate assembly. A consumer may use a Q-00 projection only after validating its dataset digest and the exact `board-registry/v1` binding.

The first implementation is deliberately bounded to the candidate inventory named by the program: M1 through M4 rows plus the separately identified A18 Pro MacBook Neo, M5, and announced M6 candidates. It imports only rows for which every asserted identity has an accepted immutable citation. Rows with unresolved selectors, contradictory identity evidence, announced-but-not-shipping lifecycle, or absent physical evidence remain explicit `unknown` observations and cannot enter an admission allowlist. The initial release records residual coverage for newer boards and every capability not evidenced by the imported sources; it does not fill gaps from a neighboring model or SoC family.

## Closed dataset grammar

The canonical top-level value is `intake-dataset/v1` and has exactly `dataset_id`, `dataset_revision`, `schema_set_digest`, `generated_at`, `sources`, `records`, `contradictions`, and `projections`. Objects are RFC 8785 JCS canonical UTF-8 before hashing. Every object has a closed key set; identifiers are non-empty ASCII, unique, and lexicographically sorted in arrays. Unknown facts are represented only by the typed `unknown` state or null fields where the field permits null. Missing required evidence is an error, not an unknown default.

### Immutable source records

Each source record has exactly `source_id`, `authority_class`, `canonical_url`, `revision`, `retrieved_at`, `content_digest`, `media_type`, `locator`, and `snapshot_path`. `content_digest` is a lowercase `sha256:` digest of the exact snapshot bytes. `retrieved_at` is an RFC 3339 UTC timestamp and is evidence metadata, not a claim date. `revision` is a closed tagged value: `commit:<40-hex>`, `tag:<immutable-tag>@<40-hex>`, `document:<publisher-version>`, or `snapshot:<sha256:...>`. The canonical URL must be HTTPS, contain no credentials, query, fragment, or mutable branch/ref segment, and resolve to the cited immutable artifact represented by the digest. A moving page, branch, `latest`, search result, redirect-only URL, or unpinned tag is rejected even when its bytes look correct.

`authority_class` is closed to `apple-official`, `asahi-upstream`, and `linux-upstream`. Apple product/support/developer publications are acceptable only under `apple-official`; Asahi-owned documentation or repository commits under `asahi-upstream`; and Linux kernel or subsystem upstream records under `linux-upstream`. Blogs, forums, mirrors, vendor summaries, social posts, uncited local observations, and any future authority class are rejected until the schema is deliberately versioned. The source snapshot is stored at `snapshot_path` under `data/intake/sources/` using its content digest; the validator never fetches `canonical_url`.

### Normalized board records and claims

Each record has exactly `record_id`, `record_revision`, `marketing_product`, `marketing_year`, `apple_model_identifiers`, `apple_board_selectors`, `device_tree_compatibles`, `soc_identities`, `lifecycle`, `evidence_tier`, `claims`, `source_refs`, `contradiction_refs`, and `unknowns`. `record_revision` is append-only and a correction creates a new record revision; it never rewrites the prior observation. Model identifiers, board selectors, compatible strings, and SoC identities are separately typed arrays, sorted and semantically unique. A string that merely shares a family prefix cannot satisfy an exact board selector.

`claims` is a closed discriminated union. Each claim has `claim_id`, `claim_type`, `subject`, `state`, `normalized_value`, `source_refs`, and `observed_at`; `state` is `confirmed`, `unknown`, or `disputed`. A `confirmed` or `disputed` claim requires at least one source reference; an `unknown` claim has no invented value and must carry a residual reason. `normalized_value` is closed per claim type, never an arbitrary JSON object:

- `board-identity`: exact Apple model identifier, board selector, and device-tree compatible tuple, with each member independently cited.
- `soc-identity`: exact SoC identifier, die variant, core topology, and memory/package facts only when separately evidenced.
- `firmware-schema`: firmware family/schema identifier, supported boot input state, and lifecycle of the firmware evidence.
- `boot-capability`: exact boot component or behavior, source/revision, and evidence state; this is not a boot-success or qualification result.
- `kernel-capability`: exact kernel/driver capability, required kernel interface, and evidence state; source availability is not physical support.
- `device-tree-capability`: exact compatible node or DT binding and the referenced board selector; a generic compatible is never promoted to a board claim.
- `graphics-capability`: exact GPU/display/media capability, required firmware/driver context, and evidence state; architecture recognition or compilation is insufficient.

The normalized claim subject must equal the containing `record_id` and, for board/DT claims, the exact board selector named by that record. A source reference names a source ID and the validator checks that the source exists, is accepted, and is digest-addressed. Assertions without citations, citations to a different board, or claims that use a source only for a neighboring family fail closed.

`evidence_tier` is closed to `source-identity`, `upstream-implementation`, `observed-intake`, and `omarchy-qualified`. Q-00 may emit the first three only; it must reject an `omarchy-qualified` claim unless a later Q-01 qualification record is explicitly bound. No Q-00 row is support evidence by itself. `lifecycle` is closed to `shipping`, `announced`, `discontinued`, and `unknown`; announced hardware is retained for intake but is never admitted as supported.

### Contradictions and supersession

Each contradiction has exactly `contradiction_id`, `record_id`, `claim_refs`, `kind`, `description`, `source_refs`, `status`, `opened_at`, and `supersedes`. `kind` is closed to `identity`, `selector`, `lifecycle`, `firmware`, `boot`, `kernel`, `device-tree`, and `graphics`; `status` is `open`, `superseded`, or `resolved-by-authority`. At least two cited claims from distinct sources are required. The validator rejects a record with an open contradiction in an identity, selector, or lifecycle claim and emits the contradiction rather than selecting a winner. `resolved-by-authority` requires a new cited claim and a superseding record revision; it is not a silent field replacement. A later correction references the prior record digest, preserving both historical observations.

## Digest-addressed manifest and projections

The dataset manifest is itself addressed by a separately computed `dataset_digest = sha256(JCS(manifest))`; `dataset_id` is stable metadata and is never used as a digest. Each source, record, contradiction, and projection entry carries its content digest. The manifest contains a sorted `records` index of `record_id`, `record_revision`, and `record_digest`, plus a sorted source index and the exact `schema_set_digest`. A record digest is recomputed from the complete record, not trusted from an index or projection.

Q-00 may generate a `board-registry/v1` projection, but the projection is not an independent source of truth. Every projection carries exactly one `dataset_digest`, `record_digest`, and `record_revision` binding. The validator regenerates the projection from the cited record and compares canonical bytes and digest; a stale projection, record transplant, board/SoC mismatch, missing source reference, extra unbound source, or projection with a duplicate semantic ID rejects. A projection never converts `unknown`, `disputed`, `announced`, or unqualified evidence into an accepted board.

The proposed repository layout is:

- `src/omarchy_intake/`: closed models, canonical hashing, offline validation, projection, and deterministic CLI.
- `data/intake/sources/`: immutable source snapshots addressed by digest.
- `data/intake/records/`: append-only normalized record revisions.
- `data/intake/manifest.json`: the checked-in dataset manifest and its expected digest lock.
- `fixtures/intake/`: one bounded accepted dataset plus hostile mutations.
- `tools/intake/`: schema-lock, digest, projection, and no-network drift checks.
- `tests/test_intake.py`: validator, manifest, hostile, and CLI tests.
- `docs/implementation/intake-dataset.md`: this design ruling.
- `.github/workflows/intake.yml`: offline validation with network access disabled.

## Validator, CLI, and CI contract

The validator accepts only local paths or bytes and has no network-capable dependency. It parses with duplicate-key rejection, validates the closed schema, recomputes every source/record/contradiction/projection digest, checks sorted semantic uniqueness, validates all citations and contradiction edges, verifies append-only supersession, and compares every projection against regenerated canonical output. It returns no partially validated record. The first failure is deterministic by `(object kind, identifier, path, error code)` and includes a stable code and JSON path.

The deterministic CLI is `python -m omarchy_intake validate --manifest data/intake/manifest.json --root data/intake --offline` and `python -m omarchy_intake project --record <record-id> --manifest ... --offline`. It writes canonical structured JSON to stdout, diagnostics to stderr, uses stable nonzero exit codes for malformed, untrusted, stale, contradictory, and tooling-invalid input, and never contacts a URL. `--offline` is mandatory in CI and is a policy assertion, not a promise inferred from a successful command.

CI runs the validator from a clean checkout with network sockets denied, verifies the manifest digest lock, checks that every referenced snapshot exists and hashes exactly, regenerates all projections, runs accepted and hostile mutation tests, and runs schema/binding drift checks. Missing optional tools or an unavailable network sandbox are `TOOLING_BLOCK`, never a pass. The CI job must fail if a new source, record, contradiction, projection, schema, or fixture is not represented in the manifest lock.

## Required hostile probes

The initial fixture and tests must mutate the accepted dataset to prove rejection of: an uncited claim; a source with a mutable URL; a source with a missing or unpinned revision; a source content-digest mismatch; duplicate source, record, claim, or semantic selector IDs; reverse-sorted arrays; conflicting claims presented as one resolved fact; unsupported authority class; stale or transplanted projection; a projection that launders one board's qualification or selector into another board; an open contradiction omitted from the record; a supersession edge that does not point to the prior digest; a digest index altered without changing content; unknown values filled from a chip-family sibling; and a network-only source with no local snapshot. Each probe must assert the stable rejection code and that no projection or admission object is returned.

The positive fixture is intentionally small: it contains one fully cited shipping board record with independently cited board, SoC, firmware, boot, kernel, DT, and graphics observations, one announced candidate retained as non-admissible, and one contradiction record retained as unresolved. It is not a claim that these examples constitute hardware qualification or complete program coverage. The fixture manifest also lists explicit residuals for every candidate row and capability not yet supported by immutable citations.

## Initial authoritative source plan and residuals

The first source bundle is limited to immutable Apple publications for product/model identity and lifecycle, immutable Asahi documentation or repository revisions for board selectors and device-tree identity, and immutable Linux upstream revisions for kernel/DT capability context. Source authority is assigned per assertion, not per row. Marketing summaries may locate a candidate but cannot be cited as authority. The import process records the exact URL, revision, retrieval time, snapshot digest, and locator before normalization.

The initial release intentionally leaves unresolved selector gaps in newer candidates, contradictory M5 identity observations, the M3 Ultra model-identifier contradiction, incomplete M4 Pro/Max device-tree evidence, all physical Omarchy qualification, and any capability requiring unverified firmware, artifacts, or hardware behavior. These residuals are first-class dataset output and fail closed in downstream board admission. Q-00 is complete only when the executable validator, immutable snapshots, bounded manifest, hostile tests, projection lock, and no-network CI are implemented and independently reviewed; this note alone does not satisfy that condition.
