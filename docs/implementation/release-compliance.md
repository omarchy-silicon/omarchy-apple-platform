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
match the bundle references exactly. A digest is a non-null lowercase `sha256:`
value with 64 hexadecimal characters. Source URIs are immutable HTTPS URIs
with lowercase DNS, no userinfo/port/query/fragment, no dot or empty segments,
and exact digest-token path segments. Artifact/source URLs use a dedicated
source-digest segment followed by a digest-only content filename with a closed
archive extension; SBOM URLs use the same digest-only filename rule.

Each artifact contains exactly: `artifact_id`, `component_id`,
`content_digest`, `source_digest`, `upstream_digest`, `fork_digest`,
`source_uri`, `artifact_class`, `spdx_expression`, `copyright_notice`,
`source_offer`, `redistribution`, `owner_decision`, `firmware_policy`,
`generated`, `build_provenance`, `sbom_ref`, `candidate_ref`, `manifest_ref`,
and `schema_set_ref`. Upstream identity is required for every artifact; fork
identity is additionally required for fork artifacts and is never inferred from
two null values. Classes, SPDX expressions, firmware/asset policy,
redistribution states, source-offer states, provenance versions, SBOM formats,
and record versions are closed vocabularies in `policy/vocabulary.json`.

Legal decisions are residual inputs, not invented by this evaluator. An owner
decision has `decision_id`, `evidence_digest`, `decided_at`, and `expires_at`.
Redistributed artifacts require `allowed`, a present non-expired decision,
copyright/NOTICE text, and a source offer. `prohibited`, `unknown`, and
`direct-fetch-only` all reject a release bundle. Source-offer-required classes
must provide an immutable URI, digest, and future expiry.

Every artifact requires a closed build-provenance record whose builder,
toolchain, and digest refs exactly match the packaged immutable
`omarchy_release_compliance/provenance_lock.py` resource; the lock is
repository-owned and cannot be replaced by a bundle field. Generated
artifacts additionally require a closed SBOM reference. Firmware and asset
classes additionally require the corresponding policy classification. All
identifiers are non-empty ASCII strings, unique, and sorted. Empty or
incomplete bundles reject rather than defaulting.

## Evaluation and attestation

`evaluate(bundle)` returns a closed result with `decision` (`allow` or
`reject`), `code`, `path`, and deterministic `bundle_digest`. The first failure
in the documented lexical order wins; no warning is a success. All parsing and
validation is pure and read-only. `attest(bundle, result)` produces canonical
bytes containing the exact inventory, policy, candidate, manifest, and
schema-set digests plus `signed: false`, `trusted: false`, `clock_trusted: false`,
and `promotable: false`. It is an evidence projection only. Production uses an
internal UTC clock; only the private test adapter can replace it.

The candidate consumer guard has no attestation constructor in F-06 and
intentionally rejects every input with `ATTESTATION_TRUST_UNAVAILABLE`; F-03
must provide signature/trust verification before this seam can open. It is not
a promotion terminal. F-07 remains the sole promotion terminal.

The module CLI is `PYTHONPATH=src python -m omarchy_release_compliance` with
`validate`, `evaluate`, and `attest` subcommands. It reads one JSON document
from a file or stdin and writes structured JSON to stdout; failures are
structured JSON on stderr with stable exit codes. It performs no network I/O;
the evaluator reads its packaged immutable provenance resource.

## Gates and fixtures

`fixtures/compliance/accepted.json` is the sole accepted fixture. The hostile
fixture set covers incomplete/unknown fields, duplicate and unsorted IDs,
unknown/prohibited/direct-fetch-only redistribution, absent and expired owner
decisions, missing NOTICE/source/SBOM/provenance, mutable URI, digest mismatch,
fork/upstream ambiguity, and candidate/manifest/schema-set transplant. Tests
also mutate the accepted object in memory so fixtures cannot become decorative.
`tools/compliance/drift.py` verifies the vocabulary, exact fixture manifest,
hardcoded hostile-code oracle, canonical SHA-256 hashes, generated outputs, and
hostile-code coverage without network access. `tools/compliance/generate.py`
materializes consolidated NOTICE and public source-offers projections; both,
like the unsigned attestation, are untrusted and non-promotable until F-03.
