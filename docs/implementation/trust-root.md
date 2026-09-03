# F-03 trust-root design note

Status: design note only. This note records the proposed coordinator ruling for F-03 before implementation edits; it is not an implementation, trust decision, qualification result, promotion, support claim, or DONE signal. The verifier is scoped to the external signed-metadata boundary and never reads or operates on the human-produced opaque boot-artifact source repository.

## Contract and boundary

F-03 supplies the trusted terminal that F-02 deliberately leaves unopened. It accepts bounded bytes for a signed F-02 envelope, a trust-root bundle, an optional artifact byte stream, and a caller-supplied replay snapshot. It returns either a closed trusted view or one deterministic typed error. It does not fetch, upload, execute, install, select a disk, change boot state, write a replay store, or mutate any input. A caller may persist the returned replay proposal only as a separate explicitly authorized operation.

For every F-02 payload with a closed artifact member (`platform-manifest/v1`, `installer-plan/v1`, or the DTB artifact digest), the caller must provide an exact ID-to-stream map. Every declared ID is verified once against its signed SHA-256 digest and bounded byte stream; missing, extra, duplicate, short, long, and mismatched streams reject before a trusted result. Paths are never used to infer an ID.

The F-02 vocabulary remains exactly eight payload types. The trust-root bundle and its signature proof are policy metadata, not a ninth F-02 payload and not a consumer-owned schema. Every F-02 payload is first structurally and semantically validated by F-02, then verified by F-03. A valid F-02 shape, digest, or signature is never trusted before F-03 completes.

The release trust graph is:

```text
immutable root anchors
        |
        v
signed root bundle and role delegations
        |
        v
targets -> snapshot -> timestamp
   |          |
   v          v
artifact   package-index
   |
   v
emergency/recovery (explicit exceptional path)
```

`snapshot` and `timestamp` can establish freshness and consistency only. They cannot authorize a target, artifact, package, board, installer mutation, or rollback that is not already authorized by a delegated release role. `emergency/recovery` can authorize only the bounded recovery and incident operations explicitly listed in its signed statement.

## Signed bytes and key identity

The implementation uses the `cryptography` Ed25519 backend, not a signature-shaped acceptance stub. It decodes exactly 32 raw public-key bytes and exactly 64 raw signature bytes, verifies with `Ed25519PublicKey.verify`, and rejects every other algorithm, encoding, key length, signature length, or trailing input. F-02's `algorithm: ed25519` and `signature_format: raw-ed25519/v1` remain mandatory.

Every public key has the stable ID `ed25519:sha256:<64 lowercase hexadecimal characters>`, computed over its raw 32-byte public key. The key ID is recomputed and compared; it is never a lookup-only label. A key record contains only the key ID, raw public key, role binding, activation interval, and status. Private keys and seed material are never in the repository, bundle, fixture, logs, CLI arguments, environment, or Python objects returned to consumers.

For an F-02 envelope, the signed preimage is exactly:

```text
UTF-8("omarchy-auth-preimage/v1") || 0x00 || JCS({
  "format": envelope.format,
  "payload_type": envelope.payload_type,
  "payload_version": envelope.payload_version,
  "domain": envelope.domain,
  "context": envelope.context,
  "schema_set_digest": envelope.schema_set_digest,
  "payload": envelope.payload
})
```

The `signatures` member is excluded from the preimage. JCS is RFC 8785 over UTF-8 JSON, with no alternate serializer, whitespace, numeric spelling, field omission, or Unicode normalization. The verifier recomputes the payload digest and schema-set digest before returning a trusted view, and binds the envelope domain, context, payload type, expected F-02 signer role, trust bundle sequence, and repository/channel scope.

When a signed payload carries `channel`, that value is authoritative and must equal any caller-requested channel exactly. A caller cannot relabel a stable document as edge, including when a delegation uses a wildcard scope. Payloads without a channel remain bound to the concrete root-bundle channel; a wildcard root channel cannot supply an unstated channel.

The trust-root bundle has a distinct domain-separated preimage:

```text
UTF-8("omarchy-trust-root-preimage/v1") || 0x00 || JCS(bundle_without_signatures)
```

The bundle has a fixed `format`, `version`, `sequence`, `issued_at`, `expires_at`, repository scope, channel scope, role definitions, delegations, revocations, freeze state, and optional explicit rollback/recovery authorization. Its proof contains independently signed copies of that exact preimage. A proof cannot sign a digest while the verifier signs a different projection, and signatures cannot be nested as data in the preimage.

## Roles, custody, and thresholds

The following initial role policy is intentionally explicit. Key IDs in the policy are opaque values such as `ed25519:sha256:<digest>` and are generated only during the controlled key ceremony.

| Role | Authority | Threshold | Custody | Maximum metadata lifetime |
| --- | --- | --- | --- | --- |
| `root` | trust-root bundle, delegations, revocations, freeze/unfreeze, role policy | 3 of 5 | all offline hardware tokens, split across two controlled locations | 365 days |
| `targets` | release targets, board registry, platform manifest, qualification references | 2 of 3 | two offline release keys and one constrained online relay | 90 days |
| `snapshot` | exact snapshot of target metadata and digests | 2 of 3 | short-lived constrained online keys | 24 hours |
| `timestamp` | freshness timestamp for a previously published snapshot | 2 of 3 | short-lived constrained online keys | 6 hours |
| `artifact` | component, boot, firmware, image, and evidence artifact digest records | 2 of 3 | two offline artifact keys and one constrained build relay | 30 days |
| `package-index` | immutable package index and package-to-artifact mapping | 2 of 3 | two offline package keys and one constrained build relay | 30 days |
| `emergency/recovery` | freeze, incident recovery bundle, and explicitly named rollback | 3 of 5 | offline hardware tokens, separate from routine targets custody | 7 days |

No key is reused across roles. A constrained online key may sign only the exact role, repository, channel, and path prefix in its delegation; it cannot add a key, change a threshold, authorize a new board, or sign an artifact body. Root and emergency keys are never present in CI, a release builder, an installer, or an online mirror. Threshold counts distinct non-revoked key IDs, not duplicate signatures or repeated public-key bytes.

The F-02 signer-role to delegated-role mapping is closed:

| F-02 `signer_role` | Delegated role | Allowed payload scope |
| --- | --- | --- |
| `board-admission` | `targets` | `board-registry/v1` only |
| `manifest-release` | `targets` | `platform-manifest/v1` only |
| `qualification-lab` | `targets` | `qualification-record/v1` only |
| `installer-planner` | `targets` | `installer-plan/v1` only; no release authority |
| `boot-runtime` | `artifact` | `boot-health/v1` only, runtime scope |
| `boot-success-marker` | `artifact` | `boot-success-mark/v1` only, runtime scope |
| `dtb-authority` | `artifact` | `dtb-mutation-envelope/v1` only, named artifact scope |
| `owner-authorization` | `emergency/recovery` | `owner-approval/v1` only, exact plan and operation scope |

An F-02 envelope has one signature by contract. To satisfy a threshold, F-03 receives a proof set of independently signed, byte-identical envelope copies and verifies each against the same canonical preimage. It rejects duplicate key IDs, mixed payloads, mixed schema-set digests, mixed role/context/scope, and fewer than the delegated threshold. No consumer may interpret one F-02 signature as a threshold result.

The artifact-to-role matrix is also closed:

| Artifact or metadata class | Required authority | Required binding |
| --- | --- | --- |
| board registry, manifest, qualification reference | `targets` | exact document ID, payload digest, schema-set digest, repository, channel |
| source/config/patch/toolchain/report lock | `targets` | exact component and manifest projection |
| kernel, DTB, boot stack, firmware bundle, image, SBOM, evidence bytes | `artifact` | exact artifact ID, size, content digest, source digest, manifest digest |
| package database and package index | `package-index` | exact index digest and package-to-artifact digest mapping |
| snapshot and timestamp metadata | their named roles | exact target or snapshot digest and channel |
| recovery image and recovery runbook bundle | `emergency/recovery` | exact board scope, image digest, recovery version, incident or routine release ID |
| opaque human-produced boot artifact envelope | `artifact` | declared identity, digest, license/notice, redistribution decision, and interface attestation only |

The verifier checks artifact bytes supplied by a caller against the signed size and SHA-256 digest. It does not inspect source repositories, infer provenance, or treat a URI or successful transport as content proof.

## Delegation and verification order

Root delegation is the only authority that can create or change a role, key set, threshold, allowed scope, lifetime, or custody classification. Delegations are path-scoped, non-transitive unless explicitly named, and cannot delegate `root`, `emergency/recovery`, freeze, revocation, or rollback authority. A role proof must resolve through the current root bundle and the exact repository/channel/path scope; consumer-local owner tables are forbidden.

The deterministic verification order is:

1. Read at most the configured metadata limit from a caller-owned byte source, reject invalid UTF-8, duplicate JSON keys, excessive depth/arrays/strings, trailing bytes, and non-canonical JSON.
2. Validate the closed trust-bundle shape and F-02 envelope shape without returning a partial object; verify exact format, type, version, domain, context, and schema-set identity.
3. Load only the immutable packaged root anchors, recompute every public-key ID, verify the root threshold, and verify root sequence, scope, expiry, revocation, and freeze state.
4. Resolve the delegated role and scope; verify every distinct Ed25519 signature over the exact canonical preimage; then enforce the threshold and required F-02 signer role.
5. Enforce key activation/revocation intervals, bundle and payload expiry, future-issued skew, channel/repository/path scope, and required cross-document digest bindings.
6. Verify snapshot/timestamp consistency and freshness; verify each declared artifact's exact byte count and SHA-256 from a bounded caller stream when bytes are supplied. Missing required bytes reject rather than defer.
7. Compare sequence and release version against the caller's replay snapshot; reject replay, freeze, and rollback before constructing a trusted view. An explicit emergency rollback must name the prior digest, board/channel scope, incident ID, and recovery policy and must itself satisfy the emergency threshold.
8. Return one immutable `Trusted` view plus an uncommitted monotonic replay proposal. Any failure returns only the first stable error in this order.

Signature validity is necessary but never sufficient: the verifier does not trust an issuer string, key ID, digest, expiry, role, or artifact path until the authority chain and all bindings above succeed.

## Expiry, replay, freeze, rollback, rotation, and revocation

Production uses a trusted UTC clock supplied by the host authority context. `issued_at` may be at most five minutes in the future, `expires_at` must be strictly in the future, and each lifetime must be within the role maximum above. Test clocks are private adapters and cannot be selected by the production CLI. Expired timestamp metadata rejects even if its underlying snapshot remains valid; timestamp freshness never extends target or artifact expiry.

The replay key is `(repository, channel, role, scope)`. The on-disk `omarchy-replay-state/v1` object is closed: it has exactly `format`, `version`, and a sorted `entries` array; every entry has exactly `scope`, nonnegative bounded `sequence`, `version`, canonical `metadata_digest`, and canonical `lineage_digest`. Malformed, divergent, unsorted, duplicated, or oversized state returns `TRUST_REPLAY_STATE_UNAVAILABLE` before trust evaluation. The monotonic state stores the highest accepted trust-bundle sequence, target metadata sequence, release version, snapshot sequence, timestamp sequence, and accepted digest lineage. A candidate is acceptable only when every relevant sequence and version is strictly greater than the stored value, or is the same sequence and exact digest already recorded. Lower values, changed bytes at an already accepted sequence, duplicate lineage, and a new version that points to an older artifact all return typed replay or rollback errors. Replay state is bounded to 1,024 scopes and 4,096 digest-lineage entries; overflow is a hold, never eviction.

Root freeze state blocks all new target, artifact, package, and recovery acceptance for the named scope. Unfreeze requires a new root bundle, root threshold, fresh incident ID, and explicit scope; role signatures cannot clear a freeze. Normal rollback is always denied. Only an emergency/recovery threshold may authorize a rollback to a previously accepted exact digest, with a named incident, reason, board/channel scope, expiry no longer than seven days, and a recovery image/runbook digest. It cannot authorize an unqualified board, a new artifact, a mutable URI, or a lower schema set.

Rotation is an overlap ceremony: the current root threshold signs a next-root bundle, the next root threshold signs an acknowledgement over the exact next-root bundle projection (with both signature arrays excluded), at least two old root IDs remain in the new threshold during the overlap, and activation is at a strictly higher sequence. The acknowledgement carries every new root public key and requires the root threshold of distinct active new IDs; an unanchored new root or missing acknowledgement is rejected. Role rotation follows the same higher-sequence rule and retains a valid old threshold until cutover. Revocation is root-signed, names an exact key ID and effective time, and is checked before threshold counting; a revoked key never satisfies a threshold after its effective time. A compromised role is frozen first, its scope is revoked, replacement keys are rotated, and only then may an emergency bundle unfreeze the affected scope. Revoked keys and private key material never appear in public fixtures.

Offline recovery uses the packaged root anchors, the last accepted replay snapshot, and a signed recovery bundle copied through a user-selected local medium. It requires no network, mirror, package manager, or mutable branch. Recovery verifies the same root chain, artifact bytes, board/manifest bindings, and expiry rules; it never silently resets replay state. If the snapshot is missing or divergent, the result is `TRUST_REPLAY_STATE_UNAVAILABLE` and a typed hold, not an assumed zero state.

## Bounded I/O and deterministic errors

The hard limits are: trust metadata 1 MiB; one JSON string 4 KiB; aggregate strings 256 KiB; depth 32; object properties 128; array items 1,024; proof signatures 16; keys 64; delegations 128; revocations 256; replay scopes 1,024; and artifact content 8 GiB with a signed exact byte count. Artifact readers consume fixed chunks, stop after declared size plus one byte, and reject short or long streams. Paths are never opened by the verifier; the CLI opens regular local files with bounded reads and never follows network URLs. There is no recursion or unbounded `read()` on untrusted input.

The closed error vocabulary is `TRUST_INPUT_TOO_LARGE`, `TRUST_IO_LIMIT`, `TRUST_UTF8_INVALID`, `TRUST_JSON_INVALID`, `TRUST_DUPLICATE_KEY`, `TRUST_NONCANONICAL`, `TRUST_SCHEMA_INVALID`, `TRUST_ANCHOR_MISMATCH`, `TRUST_KEY_ID_INVALID`, `TRUST_UNKNOWN_ROLE`, `TRUST_SCOPE_MISMATCH`, `TRUST_DELEGATION_INVALID`, `TRUST_SIGNATURE_INVALID`, `TRUST_THRESHOLD_UNMET`, `TRUST_CONTEXT_MISMATCH`, `TRUST_DIGEST_MISMATCH`, `TRUST_ARTIFACT_MISSING`, `TRUST_ARTIFACT_SIZE`, `TRUST_ARTIFACT_DIGEST`, `TRUST_NOT_YET_VALID`, `TRUST_EXPIRED`, `TRUST_REVOKED_KEY`, `TRUST_FROZEN`, `TRUST_REPLAY`, `TRUST_ROLLBACK`, `TRUST_ROTATION_INVALID`, `TRUST_RECOVERY_REQUIRED`, `TRUST_REPLAY_STATE_UNAVAILABLE`, and `TRUST_INTERNAL`. Errors contain only `code`, canonical JSON path, and a stable detail from a closed table. No backend exception, key material, raw artifact bytes, filesystem path, or partial trusted value is emitted.

## Implementation inventory and gates

The implementation is limited to new `src/omarchy_trust/` modules, `policy/trust/` policy and anchors, `fixtures/trust/` vectors, `tools/trust/` drift/fixture tooling, `tests/test_trust_root.py`, `.github/workflows/trust.yml`, `docs/implementation/trust-root.md`, and the minimal `pyproject.toml` package/dependency/resource integration. Existing F-02/F-06 code and `PROGRAM.md` remain untouched.

The exact proposed runtime dependency is `cryptography==44.0.2`; existing `jsonschema==4.26.0` and `rfc8785==0.1.4` remain the canonical parser/canonicalizer inputs. CI pins `pytest==8.3.5` for tests. No vendored cryptography, network client, signing service, or private-key package is allowed. Setuptools must package the immutable `policy/trust/root-anchors.json`, role-policy schema/lock, and public generated fixture manifest as data; a wheel test must load them from the installed package rather than the checkout.

The read-only CLI is `omarchy-platform trust verify --root-bundle FILE --document FILE [--proof FILE] [--artifact ID=FILE ...] --replay-state FILE`. It reads local bounded inputs and emits canonical JSON with `decision: TRUSTED` or `decision: REJECT`, the typed code/path, document and artifact digests, and an uncommitted replay proposal. Every `--artifact ID=FILE` is matched exactly once against the signed document artifact set. Exit status 0 means trusted, 2 means deterministic rejection, and 3 means bounded I/O/tooling failure. It has no network mode, no state-write flag, no key-generation command, and no mutation authority.

Fixtures are immutable and named by expected result: `accepted-envelope.json`, `accepted-threshold-set.json`, `accepted-offline-recovery.json`, `hostile-invalid-signature.json`, `hostile-threshold-shortfall.json`, `hostile-duplicate-signer.json`, `hostile-expired.json`, `hostile-future-issued.json`, `hostile-replay.json`, `hostile-rollback.json`, `hostile-frozen-scope.json`, `hostile-revoked-key.json`, `hostile-rotation-gap.json`, `hostile-unanchored-new-root.json`, `hostile-artifact-byte-mismatch.json`, `hostile-artifact-short-read.json`, `hostile-artifact-long-read.json`, `hostile-cross-role-laundering.json`, and `compromise-drill-role-key.json`. Every fixture records its expected typed code, canonical preimage digest, and required verification phase. The compromise drill demonstrates key compromise, freeze, revocation, overlap rotation with new-root acknowledgement, offline recovery, and post-recovery replay denial without network access.

`tests/test_trust_root.py` must exercise real Ed25519 signing and verification, canonical-preimage mutation, threshold counting, role/path scope, all temporal and replay rules, exact artifact bytes, bounded readers, no-network/no-write behavior, wheel resource loading, and every listed hostile fixture. `.github/workflows/trust.yml` runs formatting, type/static checks, the focused tests, the full existing test battery, `git diff --check`, conflict-marker and secret scans, trust fixture drift, and an isolated wheel install/smoke test. CI output must distinguish `TRUSTED` from `STRUCTURAL_ONLY`; a structural F-02 result never opens this trust gate.

Residuals after this slice remain root key ceremony and custody assignment by the project owner, an independently reviewed cryptographic implementation, F-05 candidate assembly and consumer guards, F-07 promotion, artifact/source byte acquisition policy, human-produced opaque boot artifacts, physical qualification, and installer/recovery integration. No release or board support claim follows from F-03 alone.

## Coordinator ruling required before implementation

1. Confirm whether the trust-root bundle is approved as a separate non-F-02 policy envelope as proposed, or require it to use one of the eight F-02 authenticated payload types. Adding a ninth F-02 payload is not compatible with the frozen vocabulary without an explicit F-02 change.
2. Confirm the proposed role names, signer-role mapping, thresholds, and online/offline custody split, especially whether routine `targets`, `artifact`, and `package-index` signatures must include an offline signer on every publication.
3. Confirm that threshold proofs may be represented as byte-identical F-02 envelope copies, since the current F-02 envelope permits exactly one signature, and approve the bounded proof-set limits.
4. Confirm the five-minute future-clock skew, role lifetime limits, monotonic replay key/state limits, and emergency-only rollback semantics.
5. Provide the owner-approved public key ceremony/custody record and decide whether root anchors are checked-in package data or an independently provisioned release input. No implementation can create or infer private keys.
6. Confirm the `cryptography==44.0.2` dependency and the proposed CLI/resource/fixture/CI surface, or provide the project's approved Ed25519 backend and version before implementation begins.
