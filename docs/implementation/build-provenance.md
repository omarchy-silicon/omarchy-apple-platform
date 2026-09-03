# F-04 reproducible build and provenance design note

Status: design-note only. This note is the proposed executable increment for F-04 and is not an implementation, qualification record, trust decision, release, support claim, or DONE ruling.

## Boundary and ownership

F-04 consumes the closed F-02 platform-manifest records, their canonical payload and schema-set digests, and the opaque human-produced boot-artifact envelope. It does not add an authenticated payload type, copy a consumer schema, inspect the fenced `m1n1-omarchy` source, or infer a board or component identity from a repository name. The boot envelope is validated only for its declared identity, digest, signature metadata, license/notice inventory, redistribution decision, source-offer statement, and interface attestation.

F-04 owns builder declarations, source and toolchain closure, deterministic build execution, independent-result comparison, SBOM/provenance evidence, the content-addressed artifact store, and digest-only edge/RC promotion primitives. F-03 remains the authority for key material, signatures, threshold and role policy, expiry, replay, freeze, and revocation. F-07 remains the only terminal allowed to assemble and write a stable release after recomputing the complete program closure.

The first executable increment uses small local fixtures and fake builders with the same contracts as production builders. It proves the guards and metadata shape without pretending that a fixture is a Linux, firmware, Mesa, boot, or physical qualification build.

## Pinned builder and input closure

Each builder definition is an immutable JSON document under `builders/<builder-id>/definition.json`, selected by an exact builder ID. The definition records the base image digest, host/guest architecture, isolated execution backend, toolchain package digests, environment policy digest, network policy, reproducibility controls, resource limits, and the allowed recipe entrypoint. A lock document records the definition digest; a branch, tag, image name without a digest, or repository owner is never a builder identity.

Each recipe has a canonical source-lock document and a recipe digest. Every source input records an allowlisted repository URI, exact commit, content digest, media type, and extraction digest. Generated inputs, patches, submodules, toolchain archives, build scripts, configuration, and opaque boot envelopes are listed in the same closure. A source commit is not accepted as a substitute for its fetched bytes. The closure digest is recomputed from canonical JSON before execution and is copied into every result, attestation, and package-index entry.

The runner fetches only immutable, allowlisted inputs before entering the build sandbox. The sandbox denies network access, host-path reads, undeclared environment variables, clock-dependent output, and writes outside its bounded output directory. A traced read or dependency not present in the closure is a hard `UNDECLARED_INPUT` failure. Mutable fetches, redirects to mutable locations, missing digest pins, and a changed byte stream are hard `MUTABLE_INPUT` or `INPUT_DIGEST_MISMATCH` failures before the recipe runs.

Build output is normalized according to the builder definition: stable file ordering and metadata, fixed locale/timezone, declared source date, and deterministic archive settings. The result records each output path, media type, byte count, content digest, and the aggregate artifact-set digest. Host identity, credentials, absolute paths, and raw unredacted environment are excluded from evidence.

## Independent comparison

`compare` accepts two complete build-result records produced by different builder IDs and independently verified input closures. It requires equal source, recipe, toolchain, environment-policy, and input-closure digests, equal output path sets, equal bytes, and equal aggregate digests. A repeated run in one builder is useful diagnostics but never satisfies the high-trust two-builder requirement.

Any missing result, builder reuse, input-closure divergence, output-path divergence, byte mismatch, or digest mismatch returns one deterministic rejection code and no release result. The comparison evidence records both builder IDs, result digests, and the exact mismatch path; it does not select one output as authoritative. High-trust components cannot proceed on a warning or a matching aggregate digest whose member bytes were not checked.

## SBOM and provenance evidence

Every build result has a canonical provenance record containing the builder-definition digest, toolchain digest, recipe digest, source/input closure digest, environment-policy digest, output-set digest, and redacted build-log digest. Each generated output has a corresponding SBOM reference. The SBOM must enumerate every emitted file and every resolved build/runtime dependency with stable identity, version, digest where available, and declared license/notice reference; omitted output files, unresolved dependencies, and duplicate or unsorted identities reject the result.

F-04 emits unsigned canonical evidence. A package/index record references the exact platform-manifest document ID and payload digest, schema-set digest, component and artifact IDs, artifact digests, provenance and SBOM digests, source-offer/notice references supplied by F-06, channel, and the complete last-known-good rollback set. F-04 never treats a `signed`, `trusted`, or `promotable` field in input JSON as proof.

## F-03 signing and package-index seam

The implementation exposes one narrow adapter boundary for F-03: submit canonical metadata bytes, the expected schema-set digest, requested signer role, channel, expiry, and replay identity; receive either a verified `Trusted<TrustContext>` result containing the accepted role/key/threshold decision or a typed rejection. The adapter owns signature verification and any signing operation. F-04 has no private-key path, local role table, fallback key, or boolean trust shortcut. Until the F-03 adapter is present, metadata remains explicitly unsigned, untrusted, and non-promotable.

The signed package/index envelope is immutable and digest-addressed. It binds the package/index digest to the exact artifact set, platform manifest, provenance and SBOM records, builder policy, channel, and rollback set. Consumers verify the F-03 trust result and then recompute all referenced bytes; a valid signature over a substituted digest, missing object, stale expiry, replay identity, or wrong role rejects before use.

## Immutable store, promotion, and rollback

The artifact store is content-addressed by lowercase `sha256:<hex>` and implements `put-if-absent`. Writing new bytes to an occupied digest, overwriting an existing index, deleting an object referenced by any channel, or replacing a digest with a same-named object is rejected. Repeating a write with identical bytes is an idempotent no-op. Store verification rehashes bytes and checks the recorded media type, size, provenance, SBOM, and package/index references.

Edge, RC, and stable use separate immutable namespace records. Promotion copies an already verified artifact/index digest and its complete rollback set from the source namespace; it never invokes a builder, resolves a branch, refreshes a dependency, or changes bytes. A target release record already exists only if its digest and complete metadata are identical; otherwise promotion rejects. Direct stable writes, including a direct F-04 CLI call, reject with `STABLE_PROMOTION_REQUIRES_F07`.

Rollback is a digest-only copy of the previously recorded last-known-good tuple and index into the target recovery namespace. The exercise must prove that the old boot/kernel/firmware/Mesa/userspace objects remain present, that rollback does not rebuild or fetch, and that a missing member rejects with `ROLLBACK_ARTIFACT_MISSING`. A rollback record is append-only and binds the failed candidate, restored digest set, reason, and F-03-authorized metadata.

## Bounded CLI and CI contract

The future `omarchy-build` CLI is read-only with respect to source trees and network state and has bounded input bytes, list lengths, recursion, subprocess count, and output size. Its commands are `lock check`, `build`, `compare`, `store verify`, `metadata verify`, `promote`, and `rollback`. Each command reads explicit paths, never executes command text supplied by a document, emits one canonical JSON result on stdout, emits stable redacted error JSON on stderr, and uses a fixed exit-code table. `promote` and `rollback` are dry-run by default and require an explicit operation token supplied by the F-03/F-07 seam; no CLI flag can bypass trust or stable-channel policy.

The CI workflow runs from a clean checkout and verifies builder-definition drift, closure and generated-output drift, positive two-builder comparison, store immutability, metadata/index references, and the full hostile fixture matrix. It runs without network access after fixture acquisition and records the exact base and tip SHAs, tool versions, and gate census. CI results are evidence only until F-03 trust and F-07 candidate assembly consume them.

## Hostile and positive probes

The first test matrix includes positive matching independent builders, repeatable canonical metadata, same-byte idempotent store insertion, digest-only edge-to-RC promotion, and rollback with a retained prior tuple. It also plants and must reject:

- a recipe reading a file absent from the source closure (`UNDECLARED_INPUT`);
- a branch, moving tag, mutable URL, redirect, or changed fetch (`MUTABLE_INPUT` / `INPUT_DIGEST_MISMATCH`);
- one changed output byte, changed output path, or aggregate/member digest disagreement (`ARTIFACT_MISMATCH`);
- a promotion that calls the builder or substitutes a newly rebuilt result (`PROMOTION_REBUILD_FORBIDDEN`);
- an SBOM missing an emitted file, dependency, digest, or notice mapping (`INCOMPLETE_SBOM`);
- an unsigned, wrong-role, expired, replayed, or schema-transplant package index (`INDEX_TRUST_REJECTED`);
- a rollback set missing any required artifact or pointing at a different manifest (`ROLLBACK_ARTIFACT_MISSING` / `ROLLBACK_BINDING_MISMATCH`); and
- two builders that emit different bytes despite matching declared inputs (`NONREPRODUCIBLE_OUTPUT`).

Every hostile case checks both the deterministic code and the absence of an artifact, channel copy, or success result. The probes remain outside the fenced source repository and use only declared opaque metadata for any boot artifact.

## Local/CI boundary and later work

Local execution can prove canonical locking, sandbox input tracing, deterministic fixture builds, byte-level comparison, SBOM completeness, content-addressed no-overwrite behavior, and digest-only promotion/rollback. CI can repeat those checks on clean runners and exercise the F-03 adapter contract with explicit signed and rejected fixtures.

Actual component builds require pinned source repositories, dedicated isolated builders, license and source-offer records, and the component owners' build contracts. Human-owned m1n1 artifacts require a human-signed opaque envelope before they enter the closure. Production signing, key custody, rotation/revocation, offline recovery, and release authorization remain F-03/F-07 work. Physical qualification, boot behavior, and all-board support remain Q and component work; this note provides none of that evidence.

## Coordinator questions before implementation

1. Which exact F-03 adapter and `Trusted<TrustContext>` serialization should the F-04 package/index verifier consume, including the signer roles for artifact metadata and package indexes?
2. Should the first store implementation use a local filesystem layout for the CI contract, or is an existing immutable object-store API already authoritative for digest-addressed namespace copies?
3. Which two isolated builder backends are required for the first high-trust fixture and later component builds (for example, two OCI-based definitions), and what artifact classes must be classified high-trust at F-04 launch?
