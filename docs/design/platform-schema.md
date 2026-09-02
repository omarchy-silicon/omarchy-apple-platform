# F-02 platform schema design

Status: DESIGN NOTE ONLY — corrected contract proposal; no implementation, compatibility claim, support claim, or DONE claim

This note defines the design-only contract for the five F-02 documents and the two auxiliary authenticated objects used by the installer and boot boundary. It does not implement schemas, validators, bindings, signing, storage operations, boot transport, or installer behavior. It does not change PROGRAM.md, program status, or hardware qualification. The boot implementation boundary remains opaque and is not inspected, described, or depended on here.

## 1. Contract and non-negotiables

F-02 defines the canonical data contract connecting exact Apple board identity, a release tuple, a read-only installation plan, physical qualification evidence, and boot-slot health. Every authority-bearing API consumes a value that crossed exactly one verification seam. Parsing, canonicalization, signature validity, trust policy, cross-document admission, and durable execution are separate gates.

The five wire payload types are fixed for this design wave:

| Payload type | Producer | Primary consumers | Authority it does not have |
| --- | --- | --- | --- |
| 'board-registry/v1' | platform registry tooling | installer, product helper, release tooling | It cannot qualify a board or select a component version by itself |
| 'platform-manifest/v1' | release tooling | installer, update tooling, diagnostics | It cannot replace physical qualification or artifact verification |
| 'installer-plan/v1' | read-only installer planner | approval UI, transaction executor, diagnostics | It cannot authorize mutation without a separate owner receipt |
| 'qualification-record/v1' | hardware lab tooling | promotion, ledger generation, diagnostics | It cannot grant support merely because it parses |
| 'boot-health/v1' | bounded runtime reporter | slot selector, rollback code, diagnostics | It cannot promote a board, release, or capability |

The boot-success marker and owner-authorization receipt are separate authenticated object types. They are not fields that are hashed into the object they authorize. Stable identifiers identify objects; content digests identify bytes. Neither is substituted for the other.

The only stable install-admission lifecycle state is 'full', and it is insufficient unless the selected registry, manifest, and qualification record agree on the same exact board and manifest content digest. No field in these schemas is a user-facing support announcement.

## 2. Wire language, canonicalization, and bounds

All payloads and auxiliary objects use UTF-8 JSON validated against JSON Schema Draft 2020-12 and canonicalized with RFC 8785 JSON Canonicalization Scheme (JCS). JSON Schema is a shape constraint, not a trust mechanism. Signature verification and cross-document policy are separate gates.

The parser must reject duplicate object names before schema validation. It must reject invalid UTF-8, a UTF-8 BOM, unpaired surrogates, NaN/Infinity extensions, non-finite numbers, negative zero, control characters, non-canonical numeric spellings, unbounded depth, and resource-limit violations before constructing a typed value. A parser that silently keeps the last duplicate key is not conforming.

The schema-set layout is:

~~~
schemas/
  common/v1/common.schema.json
  common/v1/vocabularies.schema.json
  board-registry/v1/board-registry.schema.json
  platform-manifest/v1/platform-manifest.schema.json
  installer-plan/v1/installer-plan.schema.json
  qualification-record/v1/qualification-record.schema.json
  boot-health/v1/boot-health.schema.json
  signed-document/v1/signed-document.schema.json
  owner-approval/v1/owner-approval.schema.json
  boot-success-mark/v1/boot-success-mark.schema.json
fixtures/
  accepted/<type>/
  hostile/<type>/
  canonicalization/
bindings/
  python/1.0.0/
  swift/1.0.0/
  rust-boot/1.0.0/
  lock.json
tools/schema/
  schema.lock
  generator/
  cli/
docs/design/platform-schema.md
~~~

Each schema has a closed root and closed nested objects. Every '$id' is 'https://schemas.omarchy.dev/<type>/v1', every schema declares the Draft 2020-12 metaschema, and local references are digest-pinned. A schema-set digest is the SHA-256 digest of the canonical lock object defined in section 11; a consumer must not substitute a compatible-looking schema set.

The common lexical rules are:

| Type | Rule |
| --- | --- |
| 'schema_id' | Exactly one of the five payload identifiers above |
| 'document_id' | Lowercase ASCII '^[a-z0-9][a-z0-9._:-]{0,127}$'; stable for that document revision |
| 'board_id' | Lowercase 'apple:<board-class>' with a bounded ASCII token; it is not a SoC ID |
| 'soc_id' | Lowercase 'apple:<soc-token>'; diagnostic only |
| 'uuid' | Lowercase RFC 4122 textual UUID with hyphens |
| 'digest' | 'sha256:' followed by exactly 64 lowercase hexadecimal characters |
| 'git_commit' | Lowercase hexadecimal commit ID of exactly 40 or 64 characters |
| 'timestamp' | RFC 3339 UTC timestamp ending in 'Z'; millisecond precision is allowed |
| 'version' | Bounded exact version token; ordering is allowed only where a field declares it |
| 'api_version' | Exactly three numeric components 'major.minor.patch', all bounded unsigned integers, with no prerelease text |
| 'bytes_u32' | JSON integer from 0 through 4,294,967,295; no string or hexadecimal alternative |
| 'base64url' | Unpadded RFC 4648 base64url with a declared decoded-length bound |
| 'path_token' | Bounded non-empty token with no slash, backslash, '..', NUL, or control character; it is not an OS path |
| 'stable_id' | One of the typed storage grammars in section 6; it is never a path or content digest |

The normative non-boot limits are maximum input 1 MiB, maximum nesting depth 32, maximum object properties 128 at every object, maximum array length 1,024, maximum string length 4,096 UTF-8 bytes, maximum total string bytes 256 KiB, and maximum integer magnitude 2^63-1 unless a narrower field rule applies. The boot marker has the stricter limits in section 8. A boundary value is valid only when the field's inclusive bound says so; a parser never truncates or repairs input.

## 3. Authentication model and exact preimages

### 3.1 Common signed-document envelope

A signed document carries a payload and one or more independent signature entries. The signature bytes and the signatures array are not recursively included in the payload digest. The conceptual wire shape is:

~~~json
{
  "format": "omarchy-signed/v1",
  "payload_type": "platform-manifest",
  "payload_version": "v1",
  "domain": "omarchy-platform-document",
  "context": "manifest-publication",
  "schema_set_digest": "sha256:<64 lowercase hex>",
  "payload": { "schema": "platform-manifest/v1", "...": "..." },
  "signatures": [
    {
      "key_id": "platform-release-2026-01",
      "signer_role": "release",
      "algorithm": "ed25519",
      "signature_format": "raw-ed25519/v1",
      "signature": "<unpadded-base64url>"
    }
  ]
}
~~~

The envelope requires all fields shown, a non-empty signatures array, and no other fields. The payload's required 'schema', 'document_id', and 'schema_set_digest' must agree with the envelope's 'payload_type', 'payload_version', and 'schema_set_digest'. v1 accepts only Ed25519 with raw 64-byte signatures encoded as unpadded base64url. Signatures are sorted and unique by '(key_id, signer_role, algorithm, signature_format)'.

For a payload 'P', define 'payload_digest = sha256(JCS(P))'. For each signature entry 'S', the exact authenticated preimage is the UTF-8 bytes of:

~~~
ASCII("omarchy-auth-preimage/v1") || 0x00 || JCS(A)
~~~

where 'A' is the following closed object, with values copied from the envelope and payload and with no signature bytes:

~~~json
{
  "envelope_format": "omarchy-signed/v1",
  "signature_format": "raw-ed25519/v1",
  "key_id": "<S.key_id>",
  "signer_role": "<S.signer_role>",
  "algorithm": "ed25519",
  "domain": "<envelope.domain>",
  "context": "<envelope.context>",
  "payload_type": "<envelope.payload_type>",
  "payload_version": "v1",
  "schema_set_digest": "<envelope.schema_set_digest>",
  "payload_digest": "<sha256(JCS(P))>",
  "anti_transplant": {
    "document_id": "<P.document_id>",
    "schema": "<P.schema>",
    "payload_type": "<envelope.payload_type>",
    "payload_version": "v1",
    "schema_set_digest": "<envelope.schema_set_digest>",
    "domain": "<envelope.domain>",
    "context": "<envelope.context>"
  },
  "payload": "<P as a JSON value>"
}
~~~

The format, signature format, key ID, signer role, algorithm, domain, context, payload type, payload version, schema-set digest, payload digest, and anti-transplant binding are therefore all inside the signature preimage. A verifier rejects any mismatch before asking trust policy whether the key and role are allowed. A valid Ed25519 signature from an unknown, expired, revoked, or wrong-role key yields no 'Trusted<T>'. The envelope does not contain a caller-controlled 'trusted', 'support', or 'success' boolean.

The payload digest is computed from 'P' only. It is not a field in 'P', so putting it in 'A' does not create a digest cycle. The signature itself is outside 'A' and is never signed recursively.

Unless a field explicitly names a domain-specific digest such as 'D_plan', 'D_scope', 'D_core', 'D_mark', or 'D_topology', a signed-document content digest such as 'manifest_digest' means this unprefixed 'payload_digest'. Domain-specific digests are never silently interchangeable with content digests or stable IDs.

### 3.2 Owner-authorization envelope

An installer plan is a proposal body, not an approval-bearing payload. The canonical plan body 'P_plan' has no 'approval', 'plan_digest', or 'approval_digest' field. Define:

~~~
D_plan = sha256(ASCII("omarchy-plan-body/v1") || 0x00 || JCS(P_plan))
~~~

The owner receipt body 'R_approval' is a separate 'owner-approval/v1' payload. It contains the exact 'D_plan', exact 'D_scope', actor and role, expiry, target identities, topology, registry/manifest/schema-set digests, and operation set specified in section 7. It does not contain a receipt digest. The common authentication construction is used with fixed 'domain = omarchy-owner-authorization' and 'context = installer-plan-execution'. Its authenticated preimage is:

~~~
ASCII("omarchy-auth-preimage/v1") || 0x00 || JCS(A_approval)
~~~

where 'A_approval' has the common fields from section 3.1 and its payload is 'R_approval'. The receipt signature is normally made by the owner-authorization service with signer role 'owner-authorization'; the actor role inside the receipt must be 'owner'. 'authorization_method' and 'authorization_result' record the external platform mechanism without storing a credential, assertion secret, password, recovery secret, or private key.

The receipt is authenticated against 'D_plan' and 'D_scope'; it is not inserted into 'P_plan' before calculating 'D_plan'. 'D_plan' is never the digest of 'R_approval', and 'plan_digest' may occur in the receipt preimage only as a reference to the already canonicalized plan, never in the plan's own preimage. An execution bundle may transport the verified plan envelope and verified approval envelope together, but the two digests remain separate. If a legacy or hostile input places 'plan_digest' under the plan payload or approval field, it fails with 'PLAN_DIGEST_CYCLE' rather than being normalized.

### 3.3 Boot-health core and success marker

'boot-health/v1' is the signed boot-health core 'C'. Its canonical payload contains board, manifest, slot, attempt, checks, success, and fallback state, but it contains no 'success_mark', 'canonical_payload_digest', 'success_mark_digest', or marker signature field. Define:

~~~
D_core = sha256(ASCII("omarchy-boot-health-core/v1") || 0x00 || JCS(C))
~~~

The success marker is a separate 'boot-success-mark/v1' payload 'M' with 'core_digest = D_core', board/manifest/slot/attempt binding, marker generation, and mark time. It contains no field containing its own digest. Its content digest, if needed for journal diagnostics, is:

~~~
D_mark = sha256(ASCII("omarchy-boot-success-mark/v1") || 0x00 || JCS(M))
~~~

The marker is authenticated in a separate envelope using 'domain = omarchy-boot-runtime' and 'context = boot-success-marker'. The common preimage contains the digest of 'M' as the outer payload digest but does not place 'D_mark' inside 'M'. The core digest is the only core reference in 'M'; it points one way from marker to the already-complete core. Neither the core preimage nor the marker preimage contains the digest of the object whose bytes it hashes.

The boot-success marker is written atomically. A torn, truncated, over-bound, unsigned, wrongly contextualized, or stale marker is absent for success evaluation. A boot-health failure or fallback decision can be represented by a signed core without a success marker; it never becomes success by omission.

### 3.4 Verification seam

The only constructor for 'Trusted<T>' is the verifier. The constructor is private to the contract library; generated bindings expose no cast, unchecked initializer, mutable trust flag, generic-map admission method, or deserialization path that can produce 'Trusted<T>'. 'Parsed<T>' means only strict parse and semantic schema validation. 'Canonical<T>' means canonical bytes are available. 'Trusted<T>' means the exact envelope, context, signature, schema-set digest, key policy, and validity window passed. 'Admitted<T>' means cross-document and local policy passed.

The sequence is:

~~~
strict_parse(bytes) -> Parsed<T> or ParseError
canonicalize(Parsed<T>) -> Canonical<T> or CanonicalizationError
verify(Parsed<T>, TrustContext, Clock, ExpectedContext) -> Trusted<T> or TrustError
admit(Trusted<...>) -> Admitted<T> or AdmissionError
~~~

No trust API accepts a parsed authority-bearing object. In particular, boot-health evaluation accepts 'Trusted<BootHealthCore>' and an optional 'Trusted<BootSuccessMark>', never 'Parsed<BootHealth>'. A missing marker is represented by 'None', not a parsed or laundered object. Verification or admission failure returns a stable code and JSON path, releases no authority-bearing partial value, and cannot be converted to allow by a caller. An indeterminate required condition is 'hold/reject', not success.

## 4. Cross-document identity and directionality

The registry contains exact board predicates and a finite capability vocabulary. A board match requires every predicate declared for the selected source and rejects conflicting source observations. There is no architecture-only, SoC-family, marketing-name, wildcard, first-match, or closest-match rule. SoC identity supports diagnostics but never substitutes for board identity.

The manifest contains explicit 'board_targets', an exact 'board_registry_digest', exact firmware schema, component locks, artifact/package content digests, rollback compatibility, and a 'qualification_bindings' array. Each binding contains '{board_id, qualification_record_id, required_outcome}' and references the stable qualification document ID only. The manifest never embeds a qualification content digest.

A qualification record contains its own stable 'document_id' and content digest when signed, plus 'manifest_id', 'manifest_digest', and 'board_registry_digest'. The record's 'manifest_digest' must equal the verified manifest payload digest, and its board ID must be one of the manifest's explicit targets. This is intentionally one-way:

~~~
manifest payload --board_id + qualification_record_id--> qualification record
qualification record --manifest_id + manifest_digest--> manifest payload
~~~

The manifest digest does not contain the qualification digest, while the qualification content digest contains the manifest digest. The stable record ID is not a content digest and never changes into one. A stable ID revision is immutable; a correction publishes a new ID/revision. A resolver rejects an ID that maps to zero, multiple, expired, or digest-mismatched records.

For a stable manifest, every target board must be 'full', every binding must have 'required_outcome = pass', and every referenced record must have complete physical evidence, an allowed lab role, and the exact manifest digest. Edge and RC may use narrower lifecycle policy only as an explicit non-support policy; they never widen targets or turn incomplete evidence into stable support.

## 5. Document payload contracts

Every payload has the common fields 'schema', 'schema_set_digest', 'document_id', 'issuer', 'issued_at', and 'expires_at'. All timestamps and digests are covered by the payload digest. Additional properties are forbidden at every nesting level.

### 5.1 board-registry/v1

Required additional top-level fields are 'registry_revision' and 'boards'. 'boards' is sorted by 'board_id'. A board contains 'board_id', exact 'identity_match', 'soc', 'firmware', 'physical_capabilities', 'lifecycle', 'qualification_profile', 'install_policy', and optional bounded 'labels'. The labels are display-only.

'identity_match' has explicit macOS and Linux predicate objects. The macOS object may contain an ordered exact 'compatible' list, exact lowercase 'device_class', exact 'product_type', exact 'board_id_u32', and exact 'chip_id_u32'. The Linux object may contain an ordered exact 'compatible' list and optional exact 'model'. Missing required predicates produce unknown, never a match. Raw open-ended property maps are not part of the signed registry.

'physical_capabilities' contains one entry per finite capability ID with 'physical_presence' ('present' or 'absent'), 'support_requirement' ('required', 'optional', or 'not_applicable'), 'policy_id', and non-empty sorted 'qualification_check_ids'. Omission means unknown. A present capability cannot be 'not_applicable'. Optional means only a constrained behavior explicitly agreed by the manifest and qualification record; it cannot downgrade a missing required capability.

The v1 capability vocabulary is exactly: 'cpu-topology', 'memory', 'internal-display', 'backlight', 'external-display', 'gpu', 'media', 'audio', 'camera', 'keyboard', 'trackpad', 'touch-id-sep', 'wifi', 'bluetooth', 'usb', 'thunderbolt', 'nvme', 'sd', 'ethernet', 'charging-battery', 'thermal-fan', 'suspend-resume', 'virtualization', and 'recovery'. No consumer may invent an ID in a signed record.

### 5.2 platform-manifest/v1

Required additional top-level fields are 'channel' ('edge', 'rc', or 'stable'), 'release_version', 'board_registry_digest', 'board_targets', 'qualification_bindings', 'firmware_schema', 'components', 'artifacts', 'package_set', 'compatibility', 'consumer_schema_set', 'minimum_consumer_api', and 'rollback'. 'board_targets' is a unique sorted list of explicit board IDs; it never names only a SoC or architecture.

Each component lock contains 'component_id', canonical repository ID, full source commit, optional full upstream commit, recipe digest, toolchain digest, sorted artifact IDs, and an exact ABI contract ID. Each artifact contains 'artifact_id', finite 'kind', component ID, media type, byte size, content digest, locator hint, and artifact signature policy. Locator is never proof. Package records contain package name, architecture, exact version, content digest, and signature policy; no range, branch, floating mirror, or unconstrained dependency expression is allowed.

'compatibility' contains only typed relations for boot protocol, kernel ABI, firmware schema, package architecture, and component relations. Relation operands are typed by the relation vocabulary. No shell, regular expression, package-manager expression, script, or evaluated policy appears in a manifest. Rollback contains 'last_known_good_required', sorted explicit previous manifest IDs, minimum retention, and a bounded failure attempt limit.

### 5.3 installer-plan/v1 proposal body

The plan payload has required additional fields 'inventory', 'selection', 'scope', 'mutations', 'rollback_boundaries', and 'recovery_requirements'. It does not have an approval field. 'selection' contains exact board ID, registry digest, manifest ID, manifest digest, schema-set digest, and policy revision. The planner cannot select an independent component, URL, package range, or firmware file.

'inventory' is a read-only observation. Storage uses the typed stable IDs and topology digest in section 6; it never uses a raw '/dev/disk*' path, filesystem path, glob, environment substitution, or user-provided device name as a mutation target. The executor may derive a volatile OS path only after resolving and revalidating the stable ID immediately before a step.

Each storage target is the closed reference '{object_kind, stable_id, expected_parent_id, expected_role, expected_size_bytes, object_generation}'. The reference is checked against the fresh topology object before every step; no omitted field is inferred from a path or current selection.

'mutations' is non-empty and contains declarative entries with 'sequence', 'step_id', finite 'operation', sorted 'target_refs', bounded 'preconditions', 'expected_effect', 'rollback_boundary', and bounded owner-visible summary. Every target must occur in inventory with the same kind, parent, role, size, object generation, and stable identity. A subprocess exit code is never an expected postcondition.

Before every durable step, a fresh topology snapshot is canonicalized and its digest and generation are compared with the plan. Changed, missing, ambiguous, or newly appearing targets fail closed. Protected unrelated containers may be observed but cannot be mutation targets.

### 5.4 qualification-record/v1

Required additional top-level fields are 'board', 'manifest', 'qualification_profile_id', 'test_results', 'outcome', 'residuals', 'operator', 'lab', and 'evidence'. The board contains exact identity observations, board ID, SoC ID, configuration class, topology class, and firmware/macOS baseline. A lab asset ID is not a public serial number.

'test_results' contains test ID, capability ID, applicability ('present', 'absent', or 'unknown'), immutable required flag copied from the profile, status ('pass', 'fail', 'blocked', 'not_run', or 'not_applicable'), timestamps, sorted evidence IDs, sorted typed measurements, failure code, and bounded notes. Unknown applicability cannot pass. Required status cannot be downgraded by an operator. A pass requires every applicable required test to pass, every required evidence digest to verify, all criteria to pass, and every residual to be explicitly non-blocking under policy.

'evidence' contains evidence ID, content digest, media type, capture time, retention class, privacy class, and optional locator. A locator is only a fetch hint. An authorized evidence store must return bytes whose digest matches before evidence is accepted. Raw evidence is not a public payload blob. Static validation, a VM, a mocked device tree, a recognized chip string, a successful compile, or a booting desktop cannot satisfy the physical evidence requirement.

### 5.5 boot-health/v1 core

Required additional top-level fields are 'board_id', 'manifest_id', 'manifest_digest', 'slot', 'attempt', 'checks', 'success', and 'fallback'. 'slot' contains only 'slot-a', 'slot-b', or 'recovery', a bounded slot generation, and a boot artifact content digest. 'attempt' contains a non-negative monotonic counter, start/finish times, previous slot, and boot context generation. Counter state is per board/manifest/slot-generation lineage; rollback, reset, reuse after unknown persistence, and wrap fail closed.

'checks' is sorted by check ID. Each check has check ID from the manifest profile, class ('required' or 'advisory'), status ('pass', 'fail', or 'unknown'), observed time, and optional bounded measurement/evidence digest. Every required declared check must appear exactly once for success. 'success' is true only when all required checks pass, identity and manifest digests match the verified slot context, the attempt is valid, and a separately verified success marker matches 'D_core'. The core has no success-marker field.

'fallback' has decision ('none', 'hold', 'switch', or 'recovery'), optional target slot, and bounded failure code. A switch target must be in the explicit rollback set and have a verified last-known-good record. Corruption is never treated as success.

## 6. Disk stable IDs and topology digest

### 6.1 Typed stable-ID grammars

Stable IDs are generated by a source adapter from a current authoritative storage observation. They are identity references, not OS paths, not locator strings, and not content digests. The exact grammars are:

~~~
whole_disk stable_id = disk:v1:sha256:<64 lowercase hex>
gpt_partition stable_id = partition:v1:sha256:<64 lowercase hex>
apfs_container stable_id = container:v1:sha256:<64 lowercase hex>
apfs_volume stable_id = volume:v1:sha256:<64 lowercase hex>
~~~

The hexadecimal suffix is the lowercase hexadecimal encoding of the identity digest bytes and has a kind-specific domain; the suffix contains no second 'sha256:' label. It must never be accepted as an artifact, evidence, manifest, or payload content digest. Unknown prefixes, uppercase hex, short hashes, paths, 'diskN' tokens, and a syntactically valid ID supplied without its source tuple and provenance are rejected. A caller cannot manufacture a stable ID from an unrelated content digest.

The exact identity preimages are:

~~~
I_disk = {"identity_schema":"disk-identity/v1", "object_kind":"whole_disk", "source_kind":..., "gpt_disk_guid":..., "capacity_bytes":..., "transport":..., "model_token":..., "serial_token":...|null, "physical_location":...|null}
I_partition = {"identity_schema":"partition-identity/v1", "object_kind":"gpt_partition", "parent_stable_id":..., "partition_guid":..., "type_guid":..., "first_lba":..., "last_lba":...}
I_container = {"identity_schema":"container-identity/v1", "object_kind":"apfs_container", "parent_stable_id":..., "container_uuid":..., "capacity_bytes":..., "physical_extents":[...]}
I_volume = {"identity_schema":"volume-identity/v1", "object_kind":"apfs_volume", "parent_stable_id":..., "volume_uuid":..., "role":..., "capacity_bytes":...}

stable_id = kind_prefix || sha256(ASCII("omarchy-storage-identity/v1") || 0x00 || JCS(I_kind))
~~~

The identity object is closed and its fields are normalized by the adapter before JCS. Paths, mount names, user labels, observation times, free-space values, and mutable display names are excluded. A whole disk requires a GPT disk GUID, capacity, transport, and at least one independent immutable anchor from serial token or physical location. A partition requires parent ID, partition GUID, type GUID, and both LBAs. A container requires parent ID, container UUID, capacity, and a non-empty physical extent list. A volume requires parent container ID, volume UUID, role, and capacity. Sparse identity is not assigned an ID.

### 6.2 Provenance and generation

Every storage object carries provenance outside the identity preimage: 'source_kind' (exactly one of 'macos-diskutil/v1', 'macos-iokit/v1', or 'linux-sysfs/v1'), exact adapter API version, source field names used, source observation digest, and source generation. The provenance must be sufficient to reproduce the normalized identity without exposing raw serials in exported diagnostics. A path is never provenance.

The source adapter maintains a persisted unsigned 64-bit 'source_generation' beginning at 1. It increments only when a committed topology snapshot differs from the previous canonical topology and remains unchanged for repeated observations of the same topology. It is never reset, reused, or wrapped. A missing persistence anchor, lower-than-previous value, or impending wrap is an unknown topology and fails closed. Each object also has an unsigned 'object_generation' assigned when first seen and incremented when its authoritative identity tuple or parent changes. A disappeared object may not silently resume an old plan; reappearance has a new object generation. A source that cannot provide these rules is not eligible for durable plan execution.

Replacement resistance requires the full typed identity tuple, parent stable ID, object generation, expected role, expected size, and source provenance class to match immediately before each step. Replacing a disk while retaining a volatile path, changing a parent, changing a partition extent, changing a UUID/role, or changing provenance fails. If two observations produce one stable ID with different tuples, if one tuple produces two stable IDs, or if a source reports multiple candidates for a requested ID, the result is 'AMBIGUOUS_IDENTITY' and no first match is selected. A physically identical replacement that is observationally indistinguishable cannot be proven safe; the adapter must report ambiguity or require a new plan rather than claim replacement detection.

### 6.3 Exact topology digest

The topology object 'T' is a closed object with 'topology_schema = storage-topology/v1', 'source_kind', 'adapter_api_version', 'source_generation', and sorted 'objects'. Each object contains kind, stable ID, parent stable ID or null, object generation, expected role, size, immutable identity anchors, and protected/mutation-target flags. It contains no raw path, mount point, free-space value, password, serial, or content bytes. A repeated observation with unchanged canonical objects keeps the same source and object generations, so a plan can be revalidated without treating a read itself as a topology change.

The exact digest is:

~~~
D_topology = sha256(ASCII("omarchy-storage-topology/v1") || 0x00 || JCS(T))
~~~

'D_topology' is not a field in 'T'. It is stored in the plan selection/scope and recomputed from a fresh snapshot. Bounds are at most 64 objects, maximum parent depth 4, maximum 64 physical extents per container, LBA and size values from 0 through 2^63-1, and the section 2 string/object limits. Exactly the same canonical topology bytes produce exactly the same topology digest; any field mutation changes it. A changed source generation, duplicate object, duplicate stable ID, parent cycle, unknown object kind, contradictory provenance, or ambiguous match rejects the snapshot.

## 7. Scope digest and owner approval

The plan's 'scope' object 'S' is a closed object containing exactly:

~~~json
{
  "scope_schema": "installer-scope/v1",
  "board_id": "<exact board ID>",
  "board_registry_digest": "<digest>",
  "manifest_id": "<stable manifest ID>",
  "manifest_digest": "<manifest payload digest>",
  "schema_set_digest": "<exact schema-set digest>",
  "topology_digest": "<D_topology>",
  "target_ids": ["<typed stable IDs, sorted>"],
  "operations": [
    {"sequence": 1, "step_id": "...", "operation": "...", "target_ids": ["..."]}
  ]
}
~~~

'S' contains neither 'scope_digest' nor 'plan_digest'. The exact scope digest is:

~~~
D_scope = sha256(ASCII("omarchy-installer-scope/v1") || 0x00 || JCS(S))
~~~

The plan body digest covers the complete plan body, including the exact scope object and full mutations, but not an approval receipt:

~~~
D_plan = sha256(ASCII("omarchy-plan-body/v1") || 0x00 || JCS(P_plan))
~~~

The owner receipt body 'R_approval' contains exactly these authorization bindings in addition to its common fields: 'schema = owner-approval/v1', 'plan_digest = D_plan', 'scope_digest = D_scope', 'schema_set_digest', 'board_id', 'board_registry_digest', 'manifest_id', 'manifest_digest', 'actor_id', 'actor_role = owner', 'approved_at', 'expires_at', 'topology_digest', sorted complete 'target_ids', sorted complete 'operations', 'authorization_method', and 'authorization_result = success'. The receipt's target IDs, topology digest, schema-set digest, registry/manifest digests, and operation set must byte-for-byte agree with the plan's scope and canonical mutation projection. It may contain an authorization evidence digest but never a credential.

The signed owner receipt is accepted only when its approval envelope has the fixed owner domain/context, the signer role is 'owner-authorization', the actor is authorized for the target account, current time is within both plan and receipt expiry, the receipt's 'D_plan' equals the verified plan body digest, and its 'D_scope' equals the recomputed scope digest. An approval for a changed plan, changed topology, changed target, changed operation, different board, different registry/manifest/schema set, expired receipt, or different actor is rejected. Approval does not grant support or release authority.

## 8. Boot binding and bounded runtime contract

The boot binding is frozen here and is not deferred to a dependent boot slice. The generated boot consumer handles only 'boot-health/v1' core and 'boot-success-mark/v1' marker values and their exact envelopes. It uses no private success format, line-oriented flag, arbitrary environment value, mutable path, or unbounded allocator. The transport must preserve the canonical bytes and atomic replacement semantics described in section 3.3.

The complete canonical UTF-8 success-marker envelope, including its payload, envelope fields, signature entry, and no trailing newline, has an inclusive maximum of exactly 4,096 bytes. Exactly 4,096 bytes is valid if all semantic checks pass; 4,097 bytes is 'RESOURCE_LIMIT'. The core payload is at most 3,072 bytes, the marker payload is at most 3,072 bytes, and its optional non-authoritative 'diagnostic_note' is at most 2,048 UTF-8 bytes. Maximum boot nesting depth is 8, maximum boot object properties is 32, maximum boot arrays are 32, and at most 32 checks are allowed. The signature remains a fixed 64-byte Ed25519 value before base64url encoding. These are parser and transport limits, not suggestions; 'diagnostic_note' is authenticated but never interpreted or used for authority.

The boot consumer verifies, before evaluating success, the trusted manifest context, board ID, manifest digest, slot, slot generation, attempt lineage, required-check set, core digest, outer marker payload digest, signature domain/context, source generation, and atomic-record length. It accepts a success marker only for the exact core digest and slot attempt it names. It retains last-known-good only from the explicit rollback set. A marker failure returns 'BOOT_MARKER_AUTH_FAILURE', 'BOOT_CONTEXT_MISMATCH', 'BOOT_COUNTER_FAILURE', 'BOOT_REQUIRED_CHECK_FAILURE', or 'BOOT_FALLBACK_FAILURE' as applicable and selects hold/recovery; it never returns success with a warning.

## 9. Trust boundaries and failure behavior

| Boundary | Input | Required checks | Output |
| --- | --- | --- | --- |
| Observation adapter | IORegistry, device-tree, firmware, storage, and runtime observations | strict parse, source normalization, complete identity, conflict and ambiguity rejection | untrusted observation only |
| Schema parser | bytes | encoding, duplicate keys, closed schema, canonical form, bounds | 'Parsed<T>' or stable parse error |
| Document verifier | parsed signed envelope | exact preimage, signature, role/key policy, time, replay, exact schema-set digest | 'Trusted<T>' or no value |
| Board admission | trusted registry and manifest plus observation | exact predicates, one match, expiry, registry/manifest/qualification directionality | 'AdmittedBoard' or reject/hold |
| Plan validator | trusted plan, registry, manifest, approval receipt, fresh observation | exact scope, stable IDs, topology, expiry, actor, operation policy | executable-scope decision or reject |
| Qualification ingestion | trusted record and evidence store | board/manifest binding, evidence digest, required-result completeness, lab role | candidate physical evidence, not support |
| Boot evaluator | trusted core, optional trusted success marker, trusted manifest, boot context | bounded parse, exact digest/slot/attempt/context, required checks, rollback policy | slot decision only |
| Redaction projection | verified trusted value | field-class policy and projection version | public/private projection, never a trust input |
| Executor | admitted plan plus fresh inventory | stable-ID revalidation before every mutation, journal/postconditions | durable mutation only within scope |

Failure codes are stable symbolic codes and never overlap; the parenthetical number is their broad CLI exit class: 'ACCEPT' (0), 'PARSE_SCHEMA_FAILURE' (10), 'UNKNOWN_FIELD' (10), 'DUPLICATE_SEMANTIC_KEY' (10), 'CANONICALIZATION_FAILURE' (11), 'SIGNATURE_CONTEXT_MISMATCH' (12), 'TRUST_FAILURE' (13), 'TRUST_BOUNDARY_FAILURE' (13), 'EXPIRY_OR_REPLAY_FAILURE' (14), 'CROSS_DOCUMENT_MISMATCH' (15), 'IDENTITY_INCOMPLETE' (16), 'AMBIGUOUS_IDENTITY' (16), 'PLAN_SCOPE_OR_APPROVAL_FAILURE' (17), 'PLAN_DIGEST_CYCLE' (17), 'BOOT_MARKER_OR_FALLBACK_FAILURE' (18), 'BOOT_MARKER_AUTH_FAILURE' (18), 'BOOT_CONTEXT_MISMATCH' (18), 'BOOT_COUNTER_FAILURE' (18), 'BOOT_REQUIRED_CHECK_FAILURE' (18), 'BOOT_FALLBACK_FAILURE' (18), 'BOOT_DIGEST_CYCLE' (18), 'RESOURCE_LIMIT' (19), and 'CLI_USAGE_OR_INTERNAL_FAILURE' (20). A failure result is JSON-safe and redacted with fields 'ok:false', 'decision:reject' or 'hold', 'code', 'path', and bounded 'message'. It contains no password, token, raw secret-bearing command output, or private signature material.

The APIs are:

~~~
parse(type, bytes) -> Parsed<T> | ParseError
canonical_bytes(Parsed<T>) -> bytes | CanonicalizationError
payload_digest(Parsed<T>) -> Digest | CanonicalizationError
verify(Parsed<T>, TrustContext, Clock, ExpectedContext) -> Trusted<T> | TrustError
admit_board(Observation, Trusted<BoardRegistry>, Trusted<PlatformManifest>, Trusted<QualificationRecord>[], Policy, Clock) -> AdmittedBoard | AdmissionError
validate_plan(Trusted<InstallerPlan>, Trusted<BoardRegistry>, Trusted<PlatformManifest>, Trusted<OwnerApproval>, Observation, Policy, Clock) -> PlanDecision
evaluate_boot_health(Trusted<BootHealthCore>, Trusted<BootSuccessMark>|None, Trusted<PlatformManifest>, BootContext, Clock) -> SlotDecision
project_public(Trusted<T>, ProjectionPolicy) -> PublicProjection
~~~

'evaluate_boot_health' deliberately has no 'Parsed<BootHealth>' parameter. 'admit_board', 'validate_plan', 'evaluate_boot_health', and every API that can authorize a release, slot, capability, approval, or mutation accept only trusted values after the one verifier seam. The public projection is not accepted by any trust API.

## 10. Sorted collections and duplicate rejection

Every array that is a set or ordered semantic collection has one declared key. Producers must emit that order; validators reject a wrong order and reject duplicate keys/IDs. They never sort, deduplicate, keep the first, or keep the last. These are the complete v1 rules:

| Collection | Required order and uniqueness key |
| --- | --- |
| signatures | '(key_id, signer_role, algorithm, signature_format)' |
| source compatible lists | exact source order; unique exact string |
| registry boards | 'board_id' |
| capability entries | 'capability_id' |
| qualification check IDs | 'check_id' |
| manifest board targets | 'board_id' |
| components | 'component_id' |
| component artifact IDs | 'artifact_id' |
| artifacts | 'artifact_id' |
| package records | '(package_name, architecture)' |
| component relations | '(left_id, relation, right_id)' |
| rollback manifest IDs | 'manifest_id' |
| qualification bindings | 'board_id' |
| plan target references | '(object_kind, stable_id)' |
| plan mutations | 'sequence' and independently 'step_id' |
| mutation target references | '(object_kind, stable_id)' |
| mutation preconditions | 'predicate_id' |
| topology objects | '(object_kind, stable_id)' |
| physical extents | '(start_lba, length_lba)' |
| qualification test results | 'test_id' |
| test evidence IDs | 'evidence_id' |
| measurements | '(criterion_id, name)' |
| residuals | 'residual_id' |
| evidence entries | 'evidence_id' |
| boot checks | 'check_id' |
| schema-set entries | '(schema_id, schema_version)' |
| required payload types | 'payload_type' |
| supported payload types | 'payload_type' |
| consumer supported entries | '(schema_set_digest, payload_type, consumer_api)' |
| scope target IDs | 'stable_id' (the typed prefix is part of the key) |
| scope operations | 'sequence' and independently 'step_id' |
| scope operation target IDs | 'stable_id' (the typed prefix is part of the key) |
| approval target IDs | 'stable_id' (the typed prefix is part of the key) |
| approval operations | 'sequence' and independently 'step_id' |
| rollback boundaries | 'sequence' |
| recovery requirements | 'requirement_id' |

Within a sorted collection, a duplicate semantic key, duplicate stable ID, duplicate board match, duplicate JSON object name, or duplicate operation sequence fails closed with 'DUPLICATE_SEMANTIC_KEY' at the second member's JSON path. Nested objects are closed too; an unknown nested property is never ignored.

## 11. Schema-set negotiation and comparable consumer API

The canonical 'schema.lock' object contains exact schema IDs and source digests, local reference digests, Draft 2020-12 identifier, RFC 8785 identifier, vocabulary digest, generator API/version/source digest, parser API/version/source digest for each language, toolchain versions, limits, and generated artifact digests. Its digest is:

~~~
schema_set_digest = sha256(ASCII("omarchy-schema-set/v1") || 0x00 || JCS(schema.lock))
~~~

The digest is computed without a digest field in 'schema.lock'. The same exact digest must be present in every payload, every signed envelope preimage, the owner receipt, the manifest's 'consumer_schema_set', and every 'Trusted<T>' metadata record. A verifier compares it byte-for-byte with the local supported lock; it does not negotiate individual fields from a mixed set.

'consumer_schema_set' contains the exact required schema-set digest and sorted required payload types. A consumer advertises sorted supported entries of '(schema_set_digest, supported_payload_types, consumer_api)'. Negotiation succeeds only on an exact digest and complete payload-type set. Unknown, future, partial, or mixed schema sets reject. A rollback consumer may advertise a previous exact set only when the manifest explicitly names that set and the local policy permits it; it cannot silently choose an older schema.

'minimum_consumer_api' is a numeric object '{major, minor, patch}' and is compared numerically, not as strings. Consumer API 'a' satisfies minimum 'b' exactly when 'a.major > b.major', or the majors equal and 'a.minor > b.minor', or major and minor equal and 'a.patch >= b.patch'. A lower major, missing component, overflow, prerelease, or malformed version rejects. The manifest's minimum is checked against the exact consumer API before any release or plan decision.

## 12. Bounded Python, Swift, and Rust handoff

The following handoff is frozen for v1. It is a design contract, not generated implementation. No dependent slice may reopen the boot binding or substitute a different parser.

| Target | Pinned toolchain | Pinned generator/parser/API | Required artifact and behavior |
| --- | --- | --- | --- |
| Python consumer | CPython 3.12.8, packaging API 1.0.0 | generator 'omarchy-schema-gen' 1.0.0, strict-json-python 1.0.0, contract API 'OmarchyPlatformContracts-Python/1.0.0' | deterministic typed models, duplicate-key rejection, JCS vectors, no mutable-map admission path |
| Swift consumer | Swift 6.0.3, macOS SDK 15.2, Swift API 1.0.0 | generator 'omarchy-schema-gen' 1.0.0, strict-json-swift 1.0.0, contract API 'OmarchyPlatformContracts-Swift/1.0.0' | strict unknown-key decoding, typed trust wrappers, canonical bytes and digest helpers |
| Rust boot consumer | rustc 1.84.1 stable, target 'aarch64-unknown-none', no-std profile 1.0.0 | generator 'omarchy-schema-gen' 1.0.0, strict-json-rust-no-std 1.0.0, boot API 'OmarchyBootHealthBinding/1.0.0' | only bounded core/marker parser, fixed storage, no heap, no arbitrary environment fallback |

The lock must contain concrete source and artifact SHA-256 digests for every generator, parser, schema input, toolchain image, and generated output. A placeholder, floating package, network fetch at build time, current-date stamp, absolute path, locale-dependent output, map-iteration order, or compiler nondeterminism is a lock failure. Generators emit only files listed in the lock, with stable line endings and stable file order; a clean rebuild must reproduce every artifact digest byte-for-byte.

Generated bindings expose parse, canonical bytes, payload digest, verify, and typed conversion only through the private trust seam. They generate the limits, schema IDs, enum values, sorted-key checks, error paths, and schema-set digest. They do not generate trust roots, private keys, privileged operations, or a generic unchecked value constructor. Python, Swift, and Rust must pass the same accepted/hostile/canonical vectors and cross-language digest/signature vectors. Consumer conformance requires compile, type/API surface, unknown-field, duplicate-key, bounds, schema-set, trust-wrapper, redaction, and no-laundering tests. CI rejects stale generated output and any consumer-local schema copy.

The Rust boot binding additionally requires: complete-marker 4,096-byte inclusive limit, exact 4,097-byte rejection, maximum nesting 8, maximum checks 32, bounded stack/heap accounting recorded in the lock, constant-time signature comparison, atomic-record validation, no path or environment input, and typed rejection for counter reset/wrap, context transplant, marker/core mismatch, and torn records. This binding is approved by this F-02 contract; B-03/B-04 own only later transport/storage integration against it.

## 13. Field classification, projections, and evidence access

Every field is classified in the schema registry as one of:

| Class | Examples | Public projection |
| --- | --- | --- |
| A: public contract | schema IDs, versions, lifecycle, capability IDs, content digests, bounded failure codes | copied when policy permits |
| B: restricted operational identifier | typed disk stable IDs, topology object IDs, lab asset IDs, actor references | replaced with versioned opaque tokens or omitted |
| C: private identifier | serials, physical locations, owner account identifiers, raw IORegistry identifiers | omitted; never used as public labels |
| D: secret/auth material | passwords, recovery keys, owner tokens, private keys, bearer assertions, encryption material | never accepted, stored, logged, or projected |
| E: evidence bytes | raw logs, captures, device-tree dumps, lab artifacts | metadata and digest only unless an authorized evidence reader requests bytes |

Public, private-redacted, and evidence-authorized projections are named versioned functions. Projection runs only after verification; deleting a field before signature verification is not redaction. Public projections preserve the relevant verification digests and a projection version, but do not claim that a redacted object is independently trusted. Restricted stable IDs are pseudonymous operational identifiers; if a public correlation token is needed it is derived with a versioned keyed HMAC, never a bare serial hash, and the key is not in the document.

Evidence access requires an authorized role, evidence ID, exact expected content digest, privacy-class policy, purpose, and expiry. The store returns bytes only after digest verification; callers receive a read receipt without credentials. Diagnostics redact raw evidence, serials, paths, tokens, credentials, and unnecessary device identifiers. Error messages use stable codes and JSON paths, not secret values. Notes and labels are bounded human text and are never interpreted as commands, selectors, paths, URLs, or policy expressions.

## 14. CLI and package boundaries

The proposed CLI is diagnostic and CI-only, not a privilege escalator:

~~~
omarchy-platform schema list
omarchy-platform validate --type board-registry/v1 --input FILE
omarchy-platform canonicalize --type platform-manifest/v1 --input FILE --output FILE
omarchy-platform digest --type qualification-record/v1 --input FILE
omarchy-platform verify --input SIGNED_FILE --trust-bundle FILE --at TIME
omarchy-platform admit board --observation FILE --registry SIGNED_FILE --manifest SIGNED_FILE --at TIME
omarchy-platform plan validate --plan SIGNED_FILE --approval SIGNED_FILE --registry SIGNED_FILE --manifest SIGNED_FILE --observation FILE --at TIME
omarchy-platform boot-health evaluate --health SIGNED_FILE --marker SIGNED_FILE --manifest SIGNED_FILE --context FILE --at TIME
omarchy-platform fixtures run --type TYPE --case CASE
omarchy-platform bindings check --lock bindings/lock.json
~~~

'validate' returns only 'UNTRUSTED' parsed/canonical information. 'verify' requires an explicit trust bundle and expected context; it has no trust-all, key-generation, private-key, network-fetch, or arbitrary privileged-operation option. Admission commands refuse unsigned, expired, unknown, mismatched, ambiguous, over-bound, or schema-set-incompatible inputs before an allow decision. All commands are read-only.

The package boundaries are: immutable schema/fixture bundle; schema CLI; generated Python/Swift/Rust contracts; consumer-specific observation/storage/UI adapters; release and qualification tooling; and the separately authorized transaction executor. A product shell or QML surface receives only typed redacted helper results and cannot become a cryptographic verifier or parse signed metadata with an ad hoc JSON traversal.

## 15. Named hostile fixtures

Before consumer integration, every fixture has a canonical input, expected code, and JSON path. The following fixtures are mandatory; 'ACCEPT' means code 0 and is included to pin an exact bound.

| Fixture | Hostile or boundary mutation | Expected code | Expected JSON path |
| --- | --- | --- | --- |
| 'signature-context-transplant' | valid signature moved from 'manifest-publication' to 'boot-success-marker' | 'SIGNATURE_CONTEXT_MISMATCH' | '$.context' |
| 'approval-plan-digest-cycle' | legacy 'plan_digest' inserted into the plan payload/approval field | 'PLAN_DIGEST_CYCLE' | '$.payload.plan_digest' |
| 'boot-success-mark-cycle' | marker contains 'canonical_payload_digest' or 'success_mark_digest' | 'BOOT_DIGEST_CYCLE' | '$.payload.canonical_payload_digest' |
| 'boot-forged-success-marker' | marker signature changed or signer role forged | 'BOOT_MARKER_AUTH_FAILURE' | '$.signatures[0].signature' |
| 'boot-counter-reset' | attempt counter lower than trusted lineage | 'BOOT_COUNTER_FAILURE' | '$.payload.attempt.counter' |
| 'boot-counter-wrap' | attempt counter wraps from max to zero | 'BOOT_COUNTER_FAILURE' | '$.payload.attempt.counter' |
| 'boot-marker-exact-4096' | complete canonical marker is exactly 4,096 bytes and otherwise valid | 'ACCEPT' | '$' |
| 'boot-marker-over-4096' | complete canonical marker is 4,097 bytes | 'RESOURCE_LIMIT' | '$' |
| 'disk-sparse-identity' | disk has only volatile path and model, no immutable anchors | 'IDENTITY_INCOMPLETE' | '$.inventory.storage.objects[0].stable_id' |
| 'duplicate-board-id' | second board has the first board's semantic key | 'DUPLICATE_SEMANTIC_KEY' | '$.payload.boards[1].board_id' |
| 'duplicate-nested-test-id' | second nested result repeats a test ID | 'DUPLICATE_SEMANTIC_KEY' | '$.payload.test_results[1].test_id' |
| 'capability-laundering-parsed-boot-health' | caller passes parsed health or public projection to evaluator | 'TRUST_BOUNDARY_FAILURE' | '$' |
| 'nested-closure-bypass' | unknown property appears under a nested storage object | 'UNKNOWN_FIELD' | '$.payload.inventory.storage.objects[0].unexpected' |
| 'topology-stable-id-collision' | two objects share one stable ID with different parent/tuple | 'AMBIGUOUS_IDENTITY' | '$.payload.inventory.storage.objects[1].stable_id' |
| 'approval-target-substitution' | receipt target differs from plan scope target | 'PLAN_SCOPE_OR_APPROVAL_FAILURE' | '$.payload.target_ids[0]' |
| 'manifest-qualification-reverse-cycle' | manifest embeds qualification content digest | 'CROSS_DOCUMENT_MISMATCH' | '$.payload.qualification_bindings[0].record_digest' |

The broader corpus must also cover duplicate keys at root and nested levels, invalid encoding, BOM, controls, numeric overflow, unknown enums, unsorted arrays, wrong board/chip predicates, changed artifacts, branch/ref locators, wrong roles, stale topology, raw paths, changed parent/size/UUID, missing evidence, required test omission, wrong slot, torn marker, fallback outside the rollback set, and success-after-failure. Every such case names its exact expected code and path; a case without a declared expectation is not a gate.

## 16. Verification and acceptance gates

The implementation cannot enter consumer integration until it proves:

1. Every schema validates against the Draft 2020-12 metaschema and all closed-object and resource-limit rules.
2. Every accepted and hostile fixture produces its declared code and JSON path, with zero unexpected accepts or rejects.
3. Independent JCS vectors prove object-order invariance, sorted-array rejection, digest mutation, signature-context binding, and both digest-cycle refusals.
4. Python, Swift, and Rust generated artifacts reproduce exact lock digests and pass the common vector and trust-wrapper conformance suite.
5. Cross-document tests prove one-way manifest/qualification binding, exact board identity, schema-set negotiation, API ordering, expiry, replay, rollback, plan scope, approval, and topology replacement resistance.
6. Fuzz, differential-parser, CPU, memory, depth, array, string, and boot-size tests remain within the frozen limits.
7. Redaction tests prove public/private/evidence projections omit secrets and unnecessary identifiers while preserving required verification digests.
8. CLI golden tests cover all exit classes, JSON result shape, no-network validation, and refusal of trust-all/private-key/arbitrary-operation options.
9. Read-only consumer contract tests prove current installer/plist/device-tree observations are adapter inputs and cannot become support authority.
10. Repository gates include conflict-marker scan, secret scan, generated-artifact drift, dependency/provenance review, and exact changed-file/base/tip census.

No schema compilation, recognized Apple chip, generated binding, booting desktop, or green focused test is implementation, release, hardware qualification, or F-02 DONE evidence. F-02 remains design-only until separately approved and implemented.

## 17. Resolved coordinator decisions

The former open questions are resolved for this design revision:

| Topic | Binding decision |
| --- | --- |
| Canonical wire/crypto base | Strict JSON, Draft 2020-12, RFC 8785 JCS, and the exact domain-separated Ed25519 envelope in section 3; no DSSE/COSE alternate in v1 |
| Envelope fields | Format, signature format, key ID, signer role, algorithm, domain, context, type/version, schema-set digest, payload digest, and anti-transplant fields are authenticated in one exact preimage; signature bytes are outside it |
| Trust policy | F-03 owns trust roots, key custody, role membership, thresholds, expiry grace, revocation, rotation, mirror compromise, and offline recovery, but cannot alter the F-02 envelope, role vocabulary, domain, or preimages |
| Board IDs | Readable exact 'apple:<board-class>' IDs remain stable references; source predicates remain mandatory; SoC and architecture are never IDs for admission |
| Storage IDs | Typed identity IDs in section 6 are separate from content digests and paths; sparse, colliding, ambiguous, or replacement-uncertain identities reject |
| Capabilities | The finite v1 vocabulary and optional semantics in section 5.1 are fixed; omission is unknown and required failure cannot downgrade |
| Boot format and bounds | Core plus separately authenticated success marker, atomic transport, frozen Rust binding, inclusive 4,096-byte complete marker limit, and 4,097-byte rejection; no private alternate format |
| Binding targets | Python, Swift, and Rust boot targets, exact versions, parser/generator APIs, lock digests, deterministic artifacts, and conformance requirements in section 12 are mandatory |
| Generated output | Generated artifacts are lock-pinned and reproducible; consumers may check in outputs or regenerate only from the exact lock, never fetch an unpinned package or maintain a second schema |
| Owner approval | A separately authenticated owner receipt binds exact plan/scope, actor/role, expiry, target IDs, topology, registry/manifest/schema-set digests, and operation set; it contains no credential |
| Cache and expiry | Expired or not-yet-valid registry, manifest, plan, receipt, qualification, or boot objects reject; no generic last-known-good cache or offline grace exists without a separate signed F-03 policy context |
| Qualification binding | Manifest references stable qualification IDs only; qualification records point back with manifest ID and manifest content digest; no reciprocal content-digest field is allowed |
| Schema negotiation | Exact schema-set digest and complete payload-type set are required; minimum consumer API uses numeric semantic ordering and never string comparison |

## 18. Owned residuals and explicit non-scope

These are named handoffs, not unanswered design questions and not silent prerequisites:

| Residual | Owner | Boundary and gate |
| --- | --- | --- |
| Trust root/key lifecycle and threshold configuration | F-03 owner | Must supply a TrustContext before trusted integration; cannot change F-02 wire/preimage rules |
| Artifact builder/provenance/SBOM and immutable promotion storage | F-04 owner | Must provide the manifest-referenced digests and signatures before release acceptance; F-02 does not implement builders |
| Assembled-system compatibility and promotion automation | F-05 owner | Must consume exact manifest/qualification directionality; no schema change is implied |
| APFS/Recovery transaction journal, destructive executor, resume, and recovery runbook | I-01/I-03/I-04/I-06 owners | Must revalidate section 6 IDs and section 7 scope before every mutation; no writer is implemented here |
| Product admission UX, diagnostics, redaction delivery, and update UX | P-01/P-02/P-04/P-05 owners | Must use typed/redacted results and preserve reject/hold semantics; no UI is implemented here |
| Boot transport, atomic storage integration, slot layout, and fallback implementation | B-03/B-04 owners | Must implement the frozen section 8 binding without introducing a second format; this note makes no claim about any opaque boot repository |
| Lab controller, evidence store, private/public projection, and ledger generation | Q-01/Q-02 owners | Must enforce evidence access and digest checks; no physical result is created here |
| Concrete board inventory, firmware values, measurement thresholds, and qualification evidence | platform qualification owner | Must be supplied as signed data and tested against the fixed shapes before any support or release claim |
| Concrete lock source/artifact digests and generated files | F-02 implementation owner | Must be recorded in 'schema.lock' and verified reproducibly before code integration; this design note publishes none |

The following remain explicitly outside this change: production code, generated bindings, schema files, fixtures, keys, release manifests, qualification records, support ledgers, APFS writers, firmware extractors, package-manager integrations, telemetry, databases, UI, boot transport, and any inspection or modification of the opaque boot artifact boundary. Their absence is not implementation evidence and does not authorize a compatibility or DONE claim.

## 19. Design-only handoff

After the resolved decisions above are accepted, the implementation sequence is: materialize the locked schemas and vocabularies; implement strict parse/canonicalize/digest; implement the single trust seam and separate owner/boot envelopes; generate Python, Swift, and Rust bindings from the lock; add the named fixtures and independent vectors; implement pure cross-document admission; expose the read-only CLI; then run consumer, storage, qualification, boot, and adversarial gates.

The handoff preserves these non-negotiables: exact board identity is not SoC or architecture; a registry is not qualification; a manifest is not artifact proof; a plan is not approval; a core digest is not a success-marker digest; stable IDs are not content digests; parsed data is not trusted data; boot health is not hardware qualification; generated bindings are not trust roots; and no unknown, stale, mismatched, laundered, or partially verified value may authorize mutation or claim success.
