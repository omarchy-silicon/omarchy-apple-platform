# F-06 release-compliance implementation

This note records the executable seam implemented in this branch. F-06 is an
evidence-only, fail-closed evaluator. It does not fetch, sign, redistribute,
promote, upload, or mutate an artifact. F-07 remains the only promotion
terminal; this implementation emits an explicitly unsigned attestation for
later trust processing.

## Versioned input grammar

The accepted top-level bundle is exactly `release-compliance/v1` with the
following keys, in canonical JSON order when serialized: `version`, `policy`,
`candidate`, `manifest`, `schema_set`, and `artifacts`. Every object has a
closed key set and every list is deterministically sorted by its identifier.

`candidate`, `manifest`, and `schema_set` each contain `id`, `version`, and
`digest`; the three references are copied into every artifact record and must
match the bundle references exactly. A digest is a lowercase `sha256:` value
with 64 hexadecimal characters. Source URIs are immutable HTTPS URIs whose
path contains a pinned digest or version and which have no query or fragment.

Each artifact contains exactly: `artifact_id`, `component_id`,
`content_digest`, `source_digest`, `upstream_digest`, `fork_digest`,
`source_uri`, `artifact_class`, `spdx_expression`, `copyright_notice`,
`source_offer`, `redistribution`, `owner_decision`, `firmware_policy`,
`generated`, `build_provenance`, `sbom_ref`, `candidate_ref`, `manifest_ref`,
and `schema_set_ref`. The digest fields are explicit even when a value is
`null`; upstream and fork are mutually exclusive unless the fork record
explicitly names its upstream digest. Classes, SPDX expressions, firmware
policy, redistribution states, and source-offer states are closed vocabularies
in `policy/vocabulary.json`.

Legal decisions are residual inputs, not invented by this evaluator. An owner
decision has `decision_id`, `evidence_digest`, `decided_at`, and `expires_at`.
Redistributed artifacts require `allowed`, a present non-expired decision,
copyright/NOTICE text, and a source offer. `prohibited`, `unknown`, and
`direct-fetch-only` all reject a release bundle. Source-offer-required classes
must provide an immutable URI, digest, and future expiry.

Generated artifacts require a non-empty build provenance object and SBOM
reference. Firmware and asset classes additionally require the corresponding
policy classification. All identifiers are non-empty ASCII strings, unique,
and sorted. Empty or incomplete bundles reject rather than defaulting.

## Evaluation and attestation

`evaluate(bundle, now=...)` returns a closed result with `decision` (`allow` or
`reject`), `code`, `path`, and deterministic `bundle_digest`. The first failure
in the documented lexical order wins; no warning is a success. All parsing and
validation is pure and read-only. `attest(bundle, result)` produces canonical
bytes containing the exact inventory, policy, candidate, manifest, and
schema-set digests plus `signed: false`, `trusted: false`, and
`promotable: false`. It is an evidence projection only.

The module CLI is `PYTHONPATH=src python -m omarchy_release_compliance` with
`validate`, `evaluate`, and `attest` subcommands. It reads one JSON document
from a file or stdin and writes structured JSON to stdout; failures are
structured JSON on stderr with stable exit codes. It performs no network I/O.

## Gates and fixtures

`fixtures/compliance/accepted.json` is the sole accepted fixture. The hostile
fixture set covers incomplete/unknown fields, duplicate and unsorted IDs,
unknown/prohibited/direct-fetch-only redistribution, absent and expired owner
decisions, missing NOTICE/source/SBOM/provenance, mutable URI, digest mismatch,
fork/upstream ambiguity, and candidate/manifest/schema-set transplant. Tests
also mutate the accepted object in memory so fixtures cannot become decorative.
`tools/compliance/drift.py` verifies the vocabulary, fixture manifest, and
hostile-code coverage without network access.

