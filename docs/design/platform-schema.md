# F-02 platform schema design

Status: DESIGN NOTE ONLY — proposed contract, awaiting coordinator ruling and implementation

This note defines the execution contract for the five F-02 documents. It does not implement schemas, validators, bindings, signing, or installer behavior. It does not alter the program status or make a hardware-support claim. The coordinator must approve the open decisions in the final section before implementation begins.

## 1. Contract and design goals

F-02 owns the canonical data contract connecting exact Apple board identity, a release tuple, a read-only installation plan, physical qualification evidence, and boot-slot health. The contract must make the safe path easy to call and the ambiguous path impossible to mistake for success.

The five wire identifiers are fixed for this design wave:

| Document | Identifier | Producer | Primary consumers | Authority it does not have |
| --- | --- | --- | --- | --- |
| Board registry | 'board-registry/v1' | 'omarchy-apple-platform' | installer, product/control plane, release tooling | It cannot qualify a board or select a component version by itself |
| Platform manifest | 'platform-manifest/v1' | release tooling in 'omarchy-apple-platform' | installer, boot/update tooling, product diagnostics | It cannot replace physical qualification or artifact verification |
| Installer plan | 'installer-plan/v1' | macOS installer planner | installer UI, transaction executor, diagnostics | It cannot authorize a mutation without fresh revalidation and owner approval |
| Qualification record | 'qualification-record/v1' | hardware lab / qualification tooling | release promotion, public-ledger generator, diagnostics | It cannot grant support merely because a record parses |
| Boot health | 'boot-health/v1' | boot/runtime health reporter | boot-slot selector, rollback code, diagnostics | It cannot promote a board, release, or capability |

Every consumer receives a typed, validated value plus an explicit trust state. 'Parsed' means only that the bytes obey the wire schema. 'Canonical' means the value has one canonical byte representation. 'Trusted' means the signature and policy checks passed. 'Admitted' means the cross-document and local safety policy passed. These states are not interchangeable.

The design preserves the program's distinction between intake/lifecycle evidence and support. The only board lifecycle state that may be used by a stable install admission rule is 'full', and even that state is insufficient unless the selected manifest and qualification record agree on the same exact board and manifest digest. No state in these schemas is a user-facing support announcement.

## 2. Evidence from consumer repositories

The interfaces below are based on read-only inspection of the actual available consumers, not on a green-field model.

### 2.1 Existing macOS installer

The current 'omarchy-mac-installer' checkout is a Python Asahi installer. 'src/system.py:31-50' extracts an ordered IORegistry compatibility list, lowercases the device class, and separately extracts product type, 32-bit board ID, 32-bit chip ID, system firmware, product name, and SoC name. 'src/main.py:39-89' keeps the chip-to-minimum-macOS table and the device-class table as in-process dictionaries. 'src/main.py:971-979' admits a device when those local tables recognize it, and 'src/main.py:995-998' applies a local minimum macOS version.

The same installer uses mutable 'diskutil' plist maps. 'src/diskutil.py:47-71' indexes whole-disk and APFS structures, while 'src/diskutil.py:127-145' retains a partition UUID, APFS container reference, volume roles, and the device identifier. 'src/main.py:280-404' chooses an OS template and an IPSW, and 'src/osinstall.py:67-199' turns a template's partition/image/extras fields into disk mutations and boot-object variables. Those values are useful observations and execution inputs, but they are not a safe canonical release authority.

F-02 therefore defines adapters from these fields rather than requiring the existing Python dictionaries or Asahi 'installer_data.json' to become the canonical format. The adapter must preserve the raw observation for diagnostics, normalize only documented fields, and refuse to produce an admission decision when a required identity field is missing or inconsistent.

### 2.2 Existing product/control plane

The available 'omarchy-mac' checkout's 'tests/test-asahi-compatibility.sh:34-46' treats 'uname -m', the presence of '/proc/device-tree/compatible', and an 'apple' substring as diagnostic checks; it explicitly passes for an aarch64 non-Apple board or no device tree. 'install/preflight/arm-mirrors.sh:5-20' likewise branches on 'uname -m', and 'manual/44-mac-support.md:5-15' still describes M-series installation as unsupported and a whole-disk flow.

That behavior is appropriate historical compatibility logic but is not sufficient for the F-02 admission path. The future product integration must call a generated contract API or the stable CLI defined here. It must not parse a registry with 'jq', 'JSON.parse', line-oriented shell logic, or a second SoC map, and it must not turn an architecture match into an install-success result.

### 2.3 Opaque repository boundary

The 'm1n1-omarchy' repository was not inspected because the coordinator explicitly declared its 'AGENTS.md' an AI/LLM-prohibited boundary. This note makes no claim about that repository or its contents. The platform manifest still names boot components abstractly and leaves that repository's implementation and integration contract to its authorized human/coordinator workflow.

## 3. Schema language and repository layout

### 3.1 Wire language

All five F-02 payloads use UTF-8 JSON validated against JSON Schema Draft 2020-12. JSON is the interchange format because the installer already consumes structured plist/JSON-like data, the product has existing JSON process boundaries, and release tooling needs inspectable signed metadata. JSON Schema is a validation language, not a trust mechanism; signature verification and cross-document policy remain separate gates.

The implementation must use a parser that rejects duplicate object names before schema validation. It must not use a permissive JSON parser whose last-key-wins behavior can make the bytes signed by one component differ from the object interpreted by another. The parser must also reject invalid UTF-8, a UTF-8 BOM, NaN/Infinity extensions, non-finite numbers, unbounded depth, and resource-limit violations before constructing a typed value.

The canonical repository layout is:

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
fixtures/
  accepted/<document>/
  hostile/<document>/
  canonicalization/
bindings/
  manifest/<generator-version>/
  lock.json
tools/schema/
  schema.lock
  generator/
  cli/
docs/design/platform-schema.md
~~~

Each public schema has a stable '$id' of the form 'https://schemas.omarchy.dev/<document>/v1', a '$schema' of 'https://json-schema.org/draft/2020-12/schema', a closed root object, and definitions imported only by digest-pinned local references. The eventual implementation may choose a different hosting domain, but the '$id' must not move after v1 is published without a new major schema identifier.

'common.schema.json' owns lexical types and shared envelope fields. 'vocabularies.schema.json' owns the finite capability, lifecycle, operation, failure, status, and source-kind vocabularies. The five document schemas own their semantic shapes. No consumer repository copies a field list into a hand-maintained schema.

### 3.2 Common lexical types

These lexical rules are part of v1 and must be generated into every binding:

| Type | Rule |
| --- | --- |
| 'schema_id' | One of the five exact strings above; no aliases and no implicit version coercion |
| 'document_id' | Lowercase ASCII identifier, ^[a-z0-9][a-z0-9._:-]{0,127}$, stable for the document's lifetime |
| 'board_id' | Lowercase 'apple:<board-class>' identifier, where '<board-class>' is a bounded ASCII token; examples in fixtures may use 'apple:j413ap' but do not imply support |
| 'soc_id' | Lowercase 'apple:<soc-token>' identifier; a SoC ID is diagnostic and never a board substitute |
| 'uuid' | Lowercase RFC 4122 textual UUID with hyphens |
| 'digest' | 'sha256:' followed by exactly 64 lowercase hexadecimal characters |
| 'git_commit' | Lowercase hexadecimal commit ID of 40 or 64 characters; short hashes are rejected |
| 'timestamp' | RFC 3339 UTC timestamp ending in 'Z', millisecond precision permitted, no timezone offsets |
| 'uri' | Absolute URI string with bounded length; policy separately allows only configured HTTPS origins and rejects userinfo, fragments, branch-like references, and unapproved hosts |
| 'version' | Bounded opaque release/component version string; consumers do not guess ordering from it unless the relevant schema declares an ordering rule |
| 'bytes_u32' | JSON integer from 0 through 4,294,967,295; no string/hex alternative |
| 'base64url' | Unpadded RFC 4648 base64url with bounded decoded length |
| 'path_token' | Bounded non-empty token with no '/', '\\', '..', NUL, or control characters; this is not an OS path |

All object properties are explicitly listed. 'additionalProperties: false' or an equivalent 'unevaluatedProperties: false' rule is mandatory at every object boundary, including nested status and measurement objects. Arrays that represent sets must be unique and sorted by the key stated in the document section. Human text is bounded and never interpreted as a command, path, URL, selector, or policy expression.

## 4. Shared signed-document envelope

The payload is the signed contract. A transport envelope wraps it without becoming part of the payload digest:

~~~
{
  "format": "omarchy-signed/v1",
  "payload": { "schema": "board-registry/v1", "...": "..." },
  "signatures": [
    {
      "key_id": "platform-release-2026-01",
      "role": "release",
      "algorithm": "ed25519",
      "signature": "<unpadded-base64url>"
    }
  ]
}
~~~

The envelope schema requires 'format', 'payload', and a non-empty 'signatures' array. 'signatures' are unique and sorted by 'key_id', then 'role'. v1 accepts only 'ed25519'; adding another algorithm requires a new envelope version or a coordinator-approved compatibility rule. The envelope does not contain a caller-controlled 'trusted' or 'support' boolean.

The payload digest is 'sha256:' plus the lowercase hexadecimal SHA-256 of the RFC 8785 JSON Canonicalization Scheme (JCS) bytes of 'payload'. The signature preimage is:

~~~
ASCII("omarchy-signature/v1") || 0x00 || ASCII(payload.schema) || 0x00 || JCS(payload)
~~~

Signatures do not cover the outer 'signatures' array recursively. A verifier first parses the envelope strictly, canonicalizes the payload, computes the payload digest, checks every signature's cryptographic validity, and then applies the external trust policy for the key ID and role. A valid cryptographic signature from an unknown or disallowed key is not trusted.

F-03 owns the trust root, key custody, role membership, threshold, expiry grace, rotation, revocation, and offline recovery policy. F-02 fixes the envelope shape and digest/signature preimage so that F-03 cannot create a second wire format. An unsigned local installer-plan proposal is allowed before owner approval; it is not eligible for remote publication or execution.

### 4.1 Canonicalization rules

JCS is applied to the complete payload, including 'schema', identity, timestamps, and all arrays. Producers must emit compact UTF-8 JCS bytes for digest/signature operations. Pretty-printed JSON is display-only and must be re-parsed and canonicalized before verification. Object key order is determined by JCS; array order is semantic and therefore fixed by the schemas.

The following are required golden properties:

- Reordering object properties does not change canonical bytes or the payload digest.
- Reordering an array that is declared sorted is rejected, not silently repaired.
- Changing any value, array element, or schema identifier changes the payload digest.
- Numbers are finite, within declared bounds, and represented according to JCS; '-0', overflows, and alternate numeric spellings are rejected by the parser or canonicalizer where they would not have one stable representation.
- A signature generated over one payload cannot verify after whitespace, Unicode, array-order, or value changes.

The implementation must not canonicalize by 'jq -S', language-default map serialization, plist serialization, or a custom pretty-printer. The canonicalization test suite must include independent implementations or a checked-in reference vector so that one runtime cannot define the format by accident.

## 5. board-registry/v1

### 5.1 Payload shape

Required top-level fields:

~~~
schema, document_id, issuer, issued_at, expires_at, registry_revision, boards
~~~

'boards' is a non-empty array sorted by 'board_id'. Every entry contains:

| Field | Required shape and semantics |
| --- | --- |
| 'board_id' | Exact stable board identity used in all other documents |
| 'identity_match' | Required exact predicates for macOS IORegistry and Linux device tree; missing required observations produce 'unknown', never a match |
| 'soc' | 'soc_id', optional bounded display name, and exact chip-ID values where known; SoC is supporting evidence only |
| 'firmware' | 'firmware_schema', accepted system-firmware/boot-firmware predicates, and required Apple firmware provenance class |
| 'physical_capabilities' | One entry for every capability physically present or explicitly absent on the board; entries sorted by capability ID |
| 'lifecycle' | One of 'intake', 'detected', 'bringup', 'experimental', 'daily_driver', 'full', 'retired' |
| 'qualification_profile' | Profile ID and sorted required qualification check IDs; this is the required test contract, not a result |
| 'install_policy' | Allowed channels, minimum macOS/firmware predicates, encryption options, recovery requirements, and immutable policy revision |
| 'notes' | Optional bounded human text; never consumed as policy |

'identity_match' has this shape:

~~~
macos: {
  compatible: [exact ordered strings],
  device_class: exact lowercase string,
  product_type: exact string,
  board_id_u32: exact integer,
  chip_id_u32: exact integer
}
linux: {
  compatible: [exact ordered strings],
  model: optional exact string
}
~~~

The source adapters may record additional raw observations in local diagnostics, but the signed registry has no open-ended raw-property map. 'product_name' and 'soc_name' may be retained as display metadata in 'labels'; they are never sufficient match predicates. A board matcher must require every predicate declared for its source and must reject disagreement between sources. There is no 'any_board', family wildcard, marketing-name wildcard, architecture-only, or “closest match” rule.

'physical_capabilities' entries have 'capability_id', 'physical_presence' ('present' or 'absent'), 'support_requirement' ('required', 'optional', or 'not_applicable'), 'policy_id', and 'qualification_check_ids'. An omitted capability is unknown. A present capability marked 'not_applicable' is invalid. 'optional' means a product may expose a constrained behavior only when the platform manifest and qualification record explicitly agree; it does not mean a missing required capability can be downgraded to a warning.

The capability vocabulary is finite and names the program's applicable domains, including CPU/topology, memory, internal display/backlight, external display, GPU, media, audio/speakersafety, camera, keyboard/trackpad, Touch ID/SEP, Wi-Fi, Bluetooth, USB, Thunderbolt, NVMe, SD, Ethernet, charging/battery, thermal/fan, suspend/resume, virtualization, and recovery. The coordinator must approve the initial vocabulary and the meaning of 'optional'; no consumer may invent a new capability string.

### 5.2 Registry invariants

- 'board_id', 'device_class', 'product_type', 'board_id_u32', and 'chip_id_u32' are not interchangeable. A matching record requires the exact fields the record declares.
- A 'full' record must name a qualification profile whose required checks are non-empty. The registry alone cannot make those checks pass.
- 'retired' records remain parseable for historical evidence but are not install-admissible.
- Registry entries cannot share a 'board_id' or have duplicate identity predicates that make two records match the same complete observation.
- 'expires_at' must be after 'issued_at'; registry consumption rejects expired data according to the F-03 policy and never silently uses an old cache for a new install.
- A registry revision is immutable once signed. Corrections publish a new document ID/revision and retain the old record for evidence lookup.

## 6. platform-manifest/v1

### 6.1 Payload shape

Required top-level fields:

~~~
schema, document_id, issuer, issued_at, expires_at, channel, release_version,
board_registry_digest, board_targets, board_qualifications, firmware_schema,
components, artifacts, package_set, compatibility, rollback
~~~

'channel' is one of 'edge', 'rc', or 'stable'. 'board_targets' is a unique sorted array of explicit 'board_id' values. A manifest never targets a SoC family or an architecture without board IDs.

'components' is a sorted array of component lock entries:

~~~
component_id, source.repository, source.commit, source.upstream_commit(optional),
build.recipe_digest, build.toolchain_digest, artifact_ids, abi_contract
~~~

'source.repository' is a canonical repository identifier from an allowlist, not a mutable URL. 'source.commit' is a full commit ID. 'build.recipe_digest' and 'build.toolchain_digest' are content digests. 'artifact_ids' are sorted and unique. 'abi_contract' is a bounded identifier interpreted by a compatibility table, never an evaluated expression.

'artifacts' contains one entry per selected output:

~~~
artifact_id, kind, component_id, media_type, size_bytes, digest, locator,
artifact_signature_policy
~~~

'kind' is a finite vocabulary for the stage-1/stage-2 boot payloads, U-Boot/UEFI payload, device tree, kernel, initramfs, firmware bundle, Mesa/userspace artifact, installer image, package index, and recovery artifact. 'locator' is only a fetch hint. The consumer must enforce origin allowlists, verify the artifact digest, and apply the artifact-signature policy before writing or executing it. The manifest signature is not an artifact signature.

'package_set' names an immutable repository snapshot digest and contains sorted package records with package name, architecture, exact version, artifact digest, and signature policy. It cannot contain a floating mirror, branch, range, or unconstrained dependency expression. Package-manager resolution is a verification step against this set, not a version-selection authority.

'compatibility' contains typed relations only:

~~~
boot_protocol, kernel_abi, firmware_schema, package_architecture,
component_relations: [{left_id, relation, right_id}],
consumer_schema_set, minimum_consumer_api
~~~

'relation' is one of a finite set such as 'requires_exact', 'requires_same', or 'requires_at_least' whose operands are typed by the relation definition. There is no shell, regex, Python, JavaScript, or package-manager expression in a manifest.

'rollback' contains 'last_known_good_required', sorted 'compatible_previous_manifest_ids', 'minimum_retention', and 'failure_attempt_limit'. Rollback compatibility is explicit; a consumer must not infer that any older manifest is safe.

### 6.2 Manifest-to-board qualification binding

'board_targets' and 'board_qualifications' are both required. Each 'board_qualifications' entry is '{board_id, qualification_record_id, required_outcome}' and is sorted by 'board_id'. The manifest references qualification record IDs, not record digests, to avoid a cyclic digest relationship: the qualification record contains the manifest ID and manifest payload digest; the verifier checks that its signed record names the currently verified manifest digest.

For a stable manifest, 'required_outcome' is 'pass', every target board must be 'full' in the referenced registry digest, and every referenced qualification record must be complete, physically identified, signed by an allowed lab role, and bound to the same manifest payload digest. Edge and RC may carry narrower lifecycle states only under coordinator-approved release policy; they are not stable support claims.

The manifest must include exact firmware schema and exact artifact digests for the complete compatibility tuple. It may include diagnostic labels for SoC family or product class, but those labels never widen 'board_targets'.

## 7. installer-plan/v1

### 7.1 Plan is a proposal plus a checked approval

The plan is produced after a read-only inventory and before privileged or destructive work. It is not a command script. Required top-level fields are:

~~~
schema, document_id, issuer, issued_at, expires_at, inventory,
selection, mutations, rollback_boundaries, recovery_requirements, approval
~~~

'selection' contains 'board_id', 'board_registry_digest', 'manifest_id', 'manifest_digest', and 'plan_policy_revision'. All references are exact and must be reloaded from verified signed documents. It cannot contain an independently chosen component version, URL, package range, or firmware file.

'inventory' contains:

| Group | Required fields |
| --- | --- |
| Observation | 'observed_at', source adapter version, macOS version/build, boot mode, system firmware, recovery firmware, and network/power readiness |
| Board | exact macOS identity predicates, optional Linux identity predicates if already available, and the resulting 'board_id' only after registry matching |
| Storage | whole-disk stable identifier, disk size, physical/internal flags, GPT identity, APFS container UUIDs, volume UUIDs, roles, sizes, free ranges, and a topology digest |
| Security | FileVault/boot-policy state and the required owner-authentication/recovery boundary, never the password, token, recovery secret, or encryption material |
| Existing OS | boot/default volume UUIDs, detected OS/recovery relationships, and whether an existing alternative-OS object is Omarchy-owned |
| Network | readiness and selected verified origin class, not credentials or arbitrary proxy configuration |

Stable storage identifiers are typed object references, not paths. A 'storage_ref' is '{object_kind, stable_id, expected_parent_id, expected_role, expected_size_bytes}'. The schema rejects '/dev/disk*', '/', glob patterns, raw environment-variable substitutions, filesystem paths, and user-provided device names in a mutation target. The executor may derive an OS path only after resolving the stable ID through the current system API and revalidating it immediately before use.

### 7.2 Mutation and approval shape

'mutations' is a non-empty array sorted by sequence. Each entry is:

~~~
sequence, step_id, operation, target_refs, preconditions, expected_effect,
rollback_boundary, owner_visible_summary
~~~

'operation' is a finite vocabulary limited to approved APFS/Recovery/LocalPolicy provisioning, artifact placement, slot preparation, and verification operations. It is not a command line. Each target reference must occur in 'inventory' and match its stable object kind, parent, role, and expected identity. Each precondition is declarative and bounded. The expected effect names the postcondition and the next journal state; it never asserts success merely because a subprocess returned zero.

The plan must contain a topology digest over the canonical inventory storage subset. Before every durable step the executor obtains fresh inventory, recomputes the digest, and compares each target object. Any changed, missing, ambiguous, or newly appearing target fails closed. Unrelated APFS containers are represented as protected observations and may not appear in a mutation target.

'approval' is either 'null' for a display-only proposal or:

~~~
{ plan_digest, scope_digest, approved_at, actor_kind, approval_method }
~~~

The approval is valid only when 'plan_digest' equals the canonical payload digest and 'scope_digest' covers the exact mutation sequence and targets. It contains no credential. Owner authentication is performed by the platform/Apple mechanism outside this document; its success is recorded as a typed result, never as a password field. A plan with missing approval, stale expiry, or changed digest is not executable.

### 7.3 Plan privacy and lifecycle

The local executor may retain a protected inventory for recovery, but exported diagnostics must redact serials, owner identifiers, boot tokens, credentials, encryption material, and device IDs not necessary for support. Redaction is a separate projection with its own tests; it must not be implemented by deleting fields before signature verification.

Plans are single-transaction proposals. Reuse after a process death requires reading the durable journal and producing a new plan or explicit resume record bound to the same verified selection and current topology. F-02 does not define the transaction journal; I-01 owns that state machine.

## 8. qualification-record/v1

### 8.1 Physical evidence contract

Required top-level fields are:

~~~
schema, document_id, issuer, issued_at, expires_at, board, manifest,
qualification_profile_id, test_results, outcome, residuals, operator, lab, evidence
~~~

'board' contains the lab asset ID, exact board identity observations, board ID, SoC ID, RAM/storage configuration class, product topology, and firmware/macOS baseline. A lab asset ID is not a serial number in public output. Private evidence systems may retain the serial under their own access controls, but the schema has no unconstrained private blob.

'manifest' contains 'manifest_id', 'manifest_digest', and 'board_registry_digest'. The record is invalid if the manifest digest does not match the verified manifest under test. The board identity must match exactly one registry entry; SoC-only or architecture-only records are invalid.

'test_results' is sorted by 'test_id'. Every result contains:

~~~
test_id, capability_id, applicability, required, status, started_at,
completed_at, evidence_ids, measurements, failure_code, notes
~~~

'applicability' is 'present', 'absent', or 'unknown'; 'unknown' cannot be 'pass'. 'status' is 'pass', 'fail', 'blocked', 'not_run', or 'not_applicable'. 'required' is copied from the qualification profile and cannot be downgraded by the operator. Measurements are typed '{name, value, unit, criterion_id}' with bounded numeric ranges; raw logs live behind immutable evidence references.

'evidence' entries contain 'evidence_id', 'digest', 'media_type', 'captured_at', 'retention_class', and 'privacy_class'. A locator is optional metadata and never proof of retrieval. Evidence is accepted only after the bytes at the locator are fetched from an authorized store and their digest matches. Missing or mismatched evidence is a record failure, not an empty evidence list.

'outcome' is 'pass', 'fail', or 'incomplete'. It may be 'pass' only when every applicable required test has status 'pass', every required evidence reference verifies, no required measurement violates its criterion, and all residuals are explicitly non-blocking under the qualification policy. A record with a critical residual can parse but cannot satisfy a stable promotion gate. The record does not contain 'support: true' or a public marketing status.

'operator' contains a non-secret operator identity reference and role. 'lab' contains a lab identity, harness version, host/toolchain digests, power/capture topology class, and clock source. These fields make evidence reproducible without embedding credentials or uncontrolled host data.

### 8.2 Requalification rules

Any change to board identity, firmware schema, manifest digest, qualification profile revision, required capability criterion, or evidence integrity invalidates the old pass for promotion. A new record is required. A newer record does not delete an older record; the public ledger chooses the applicable immutable record according to signed release policy.

Qualification records are physical evidence. Static schema validation, a VM, a mocked device tree, a recognized chip string, a successful compile, or a booting desktop can be a lower-level test result but cannot satisfy the physical board evidence requirement.

## 9. boot-health/v1

### 9.1 Bounded runtime contract

Boot health is deliberately small and bounded to 4 KiB for the v1 payload. Required top-level fields are:

~~~
schema, document_id, issuer, issued_at, expires_at, board_id,
manifest_id, manifest_digest, slot, attempt, checks, success, fallback
~~~

'slot' contains a stable slot token ('slot-a', 'slot-b', or 'recovery'), 'slot_generation', and the boot artifact digest. It is not a path, device name, or arbitrary boot argument. 'attempt' contains a non-negative monotonic counter, 'started_at', 'finished_at', and the previous slot token. Counters must not move backward for the same slot-generation lineage.

'checks' is a sorted array of bounded check results. Each has 'check_id', 'class' ('required' or 'advisory'), 'status' ('pass', 'fail', or 'unknown'), 'observed_at', and an optional bounded measurement/evidence digest. Unknown required checks are failures for success evaluation. Check IDs come from the manifest/qualification vocabulary; a producer cannot make a new required check disappear by omitting it.

'success' is a boolean with a semantic invariant: it may be 'true' only if every required check declared by the selected manifest's boot-health profile appears exactly once with 'pass', the board and manifest digests match the selected slot, and the attempt counter is valid. 'success_mark' is required when 'success' is true and absent when false; it contains the canonical payload digest and mark time. A JSON Schema 'if/then' rule handles shape, and a cross-document validator handles the required-check set.

'fallback' contains 'decision' ('none', 'hold', 'switch', or 'recovery'), an optional target slot, and a bounded failure code. A 'switch' target must be a last-known-good slot whose manifest digest is in the explicit rollback compatibility set. A failed or malformed marker causes the boot-slot policy to retain or select a verified fallback; it never treats corruption as success.

### 9.2 Boot/runtime boundary

The bootloader and the Linux health reporter share this JSON contract. The bootloader must consume only the bounded generated boot-health parser and the documented atomic transport; it must not accept arbitrary environment strings or a line-oriented success flag. The Linux reporter must verify the boot context (slot, attempt, board, and manifest digest) before writing a marker. The marker must be written atomically, with a torn/truncated file treated as absent.

The runtime producer is not automatically a project trust root. Its provenance and transport authenticity are checked by the boot/update policy. A boot-health pass permits slot success and rollback accounting only; it is not a qualification result and cannot update the board registry or manifest. B-03/B-04 own the boot-slot implementation and must not introduce a second private success format.

## 10. Trust boundaries and authority flow

| Boundary | Input | Required checks | Output authority |
| --- | --- | --- | --- |
| Hardware observation adapter | IORegistry, device tree, 'diskutil', firmware APIs, runtime probes | strict parser, source-specific normalization, exact field presence, conflict detection | untrusted 'Observation' only |
| Registry loader | signed registry bytes/cache | schema, JCS digest, signature, F-03 key/expiry policy, duplicate-match analysis | trusted board policy data |
| Manifest loader | remote/local release metadata | schema, signature, origin allowlist, expiry, registry digest, exact board targets, artifact/package constraints | trusted release selection, not installed artifacts |
| Artifact/package fetcher | locators and bytes | allowlisted origin, TLS policy, byte digest, artifact/package signature, size/type limits | verified bytes for a selected manifest only |
| Plan builder | observations plus trusted registry/manifest | read-only mode, exact identity, topology digest, declarative mutation grammar | unapproved proposal |
| Owner approval | UI/CLI confirmation and Apple authorization result | exact plan/scope digest, freshness, actor boundary, no credential persistence | executable approval for that plan only |
| Plan executor | approved plan and fresh observations | stable-ID revalidation before every mutation, journal transition, postcondition | durable mutation within declared scope |
| Qualification ingestion | lab record and evidence references | schema, board/manifest binding, evidence digests, required-result completeness | candidate physical evidence, not support |
| Boot-health reader/writer | boot context and bounded marker | atomic transport, slot/attempt/manifest match, required checks, rollback policy | slot success/fallback only |
| Public ledger generator | trusted registry, manifest, qualification records | all cross-document gates and redaction projection | derived publication, never an input authority |

No remote response, package index, user path, architecture string, operator note, or generated binding can cross directly into a privileged/destructive operation. Each boundary must name its rejection code and retain enough non-secret context for diagnosis.

## 11. Generated bindings and API boundaries

### 11.1 Generation model

'omarchy-apple-platform' publishes the canonical schema bundle and a generator lock. The lock records the schema commit/digest, JSON Schema metaschema version, generator version/digest, and each generated output's source-schema digest. Generated bindings are outputs, not a second source of truth. A consumer's CI fails if generated output is stale or changed by a generator that is not in the lock.

The first required targets are:

| Consumer | Generated output | Required behavior |
| --- | --- | --- |
| macOS installer Python | strict dataclasses/value objects plus parser/validator and canonical digest helpers | reject unknown fields and duplicate IDs; expose typed stable disk refs; never return a partially valid dictionary |
| native macOS installer/control plane | strict Swift 'Codable' models plus unknown-key checking, canonicalization, and trust-state wrappers | do not rely on default 'Codable' unknown-key tolerance in the admission path |
| product shell/QML boundary | a versioned 'omarchy-platform' helper protocol and generated JSON result types | shell/QML sees a small allowlisted result, never raw signed metadata or an ad hoc 'jq' traversal |
| boot/update helper | bounded C/Rust boot-health binding as approved by B-03/B-04 | fixed limits, no unbounded allocation, no arbitrary environment fallback |
| release/qualification tooling | strict Rust or Python binding selected by the tooling owner | canonical output, cross-document validation, evidence-digest checking |

Bindings must include 'parse', 'validate', 'canonical_bytes', 'payload_digest', and explicit conversion from 'Parsed' to 'Trusted'/'Admitted' after the caller supplies a trust context. They must not expose a mutable generic map as the primary API. An escape hatch for diagnostics may return a redacted tree, but privileged code cannot use it.

The generator emits compile-time constants for schema IDs, vocabulary values, maximum sizes, and source-schema digest. It emits tests for required fields, unknown-field rejection, enum rejection, bounds, sorted arrays, and cross-document reference hooks. It does not emit a trust root or embed private keys.

### 11.2 Stable library API

The language-neutral API surface is:

~~~
parse(document_type, bytes) -> Parsed<T> | SchemaError
canonical_bytes(Parsed<T>) -> bytes | CanonicalizationError
digest(Parsed<T>) -> Digest
verify(Parsed<T>, TrustContext, Clock) -> Trusted<T> | TrustError
admit_board(Observation, Trusted<BoardRegistry>, Trusted<PlatformManifest>, QualificationSet, Policy, Clock) -> AdmittedBoard | AdmissionError
validate_plan(Trusted<BoardRegistry>, Trusted<PlatformManifest>, Observation, Parsed<InstallerPlan>, Policy, Clock) -> PlanDecision
evaluate_boot_health(Trusted<PlatformManifest>, Parsed<BootHealth>, BootContext, Clock) -> SlotDecision
~~~

'verify' never implies board support. 'admit_board' requires exact source predicates, one registry match, a verified manifest target, matching firmware schema, expiry validity, and the manifest's board qualification policy. 'validate_plan' has no disk-writing capability. 'evaluate_boot_health' returns a slot decision and never a release/support decision. APIs return structured stable error codes and a JSON-safe redacted explanation; they never include passwords, signature private material, or raw secret-bearing command output.

### 11.3 Package boundaries

The proposed package boundaries are:

- 'omarchy-platform-schemas': immutable schema/fixture bundle, no privileged operations and no network trust decisions.
- 'omarchy-platform-schema-cli': validation, canonicalization, digest, verification, fixture, and generated-binding commands; usable in CI and diagnostics.
- 'omarchy-platform-contracts-python', 'OmarchyPlatformContracts' (Swift), and the approved boot-helper binding: generated consumer libraries pinned to the schema lock.
- Consumer-specific adapters in 'omarchy-mac-installer' and 'omarchy-mac': source observation, UI, storage APIs, and transaction control remain in the consumer. They may not add registry entries, version maps, or alternate signatures.
- Release/promotion tooling: manifest assembly, artifact verification, qualification correlation, and channel policy remain in 'omarchy-apple-platform'; package managers and installers only consume the selected result.

The product's existing shell/QML runtime must not become a cryptographic verifier. It asks the helper for typed/redacted decisions and displays stable error codes. The helper must accept only file/descriptor inputs selected by the caller's trusted staging layer, not arbitrary URLs from a menu or user text.

## 12. CLI shape

The CLI is a diagnostic and CI interface, not a privilege escalator. The command name is proposed as 'omarchy-platform' and remains subject to coordinator approval. Commands are deterministic and produce human output by default or one JSON result with '--json':

~~~
omarchy-platform schema list
omarchy-platform validate --type board-registry/v1 --input FILE
omarchy-platform canonicalize --type platform-manifest/v1 --input FILE --output FILE
omarchy-platform digest --type qualification-record/v1 --input FILE
omarchy-platform verify --input SIGNED_FILE --trust-bundle FILE --at TIME
omarchy-platform admit board --observation FILE --registry SIGNED_FILE --manifest SIGNED_FILE --at TIME
omarchy-platform plan validate --plan FILE --registry SIGNED_FILE --manifest SIGNED_FILE --observation FILE --at TIME
omarchy-platform boot-health evaluate --health FILE --manifest SIGNED_FILE --context FILE --at TIME
omarchy-platform fixtures run [--type TYPE] [--case CASE]
omarchy-platform bindings check --lock bindings/lock.json
~~~

'validate' is syntax/semantic validation only and labels its result 'UNTRUSTED'. 'verify' requires an explicit trust bundle and has no '--trust-all', network-fetch, key-generation, or private-key option. 'admit' and 'plan validate' refuse unsigned inputs, expired documents, unknown boards, missing fields, and digest mismatches before returning an allow decision. All commands read bytes without mutating the target; only a future separately authorized installer owns durable operations.

Proposed exit classes are stable and non-overlapping: '0' accepted decision, '10' parse/schema failure, '11' canonicalization/digest failure, '12' signature or trust failure, '13' expired/not-yet-valid/replay failure, '14' cross-document mismatch, '15' unsupported/ambiguous identity, '16' plan safety or approval failure, '17' boot-health/fallback failure, and '20' CLI usage/internal error. The JSON result includes 'ok', 'decision', 'code', 'path', and a redacted 'message'; it never emits a success result with warnings standing in for a required failure.

## 13. Compatibility and evolution

### 13.1 Versioning rule

'board-registry/v1', 'platform-manifest/v1', 'installer-plan/v1', 'qualification-record/v1', and 'boot-health/v1' are exact major contracts. A consumer must select a schema by exact identifier and reject every other major version. There is no “best effort v1 parser” and no silent conversion from v0 or a future version.

Because security consumers fail closed on unknown fields, a shape change that adds a field, changes an enum, changes array ordering, changes canonicalization, or changes signature semantics requires a new major document/envelope version unless the coordinator explicitly approves a compatible v1 revision and all consumers are regenerated together. Documentation-only changes may not change the '$id', digest, or generated source digest.

Each generated package reports the exact schema-set digest it was built from. A manifest's 'consumer_schema_set' and 'minimum_consumer_api' prevent a new release from reaching a consumer too old to enforce its required fields. Consumer CI runs a compatibility matrix of the current supported schema set, the previous pinned set where rollback requires it, and deliberately rejected future/unknown versions.

### 13.2 Data migration

No migration is performed during privileged installation, boot selection, or qualification evaluation. A migration tool may read an older document, produce a new document through a reviewed explicit adapter, and require new signing/approval. It must retain the source digest and migration version. A failed migration yields no output eligible for execution.

Registry corrections, requalification, revoked manifests, and expired keys are append-only publications. Historical records remain verifiable; they are never rewritten to appear current. Cache use requires an explicit offline policy from F-03 and a bounded expiry/grace decision, not a generic “last known good” fallback.

## 14. Fail-closed parsing and admission checklist

The strict parser rejects:

- wrong or missing 'schema', unknown fields, nulls where a value is required, duplicate keys, duplicate IDs, duplicate array members where uniqueness is declared, malformed UTF-8, BOMs, control characters, non-finite numbers, overlong strings, excessive depth, oversized arrays, and integer overflow;
- unknown enums, invalid lower-case/UUID/digest/commit/timestamp forms, unsorted semantic arrays, unsupported signature algorithms, malformed base64url, invalid URI policy, and path-like tokens;
- missing cross-document references, mismatched registry/manifest/board/firmware/qualification/slot digests, duplicate registry matches, unknown capability IDs, omitted required checks, and a present capability incorrectly marked not applicable;
- expired or not-yet-valid signed documents, clock-policy violations, replayed attempts, stale plan topology, and a plan whose approval or scope digest is not exact;
- manifests with branch/ref URLs, non-allowlisted repositories, floating versions, missing artifact/package digests, unsigned artifacts, incompatible component relations, incomplete rollback declarations, or targets broader than explicit board IDs;
- qualification records with unknown board identity, missing physical evidence, failed/blocked/not-run required checks, mismatched manifest digest, stale firmware/profile, measurement violations, or unexplained critical residuals;
- boot-health records with wrong board/manifest/slot context, counter rollback, a required check missing/unknown/failed, a success mark without complete required passes, a fallback target outside the rollback set, or a torn/truncated marker;
- installer plans with raw device paths, glob/environment substitutions, missing stable identifiers, changed APFS topology, unrelated-container targets, unapproved operations, missing owner approval, expired selection, or any mutation not present in the signed manifest/policy.

The parser returns no usable partial object after a rejection. The admission APIs do not call a default record, select the newest available record, infer a SoC from 'uname -m', accept the first compatible entry, or turn 'unknown' into 'optional'. If a consumer cannot evaluate a required condition, its decision is reject/hold with a stable error code.

## 15. Hostile fixture corpus

The implementation must check in fixtures before consumer integration. Every accepted fixture has a canonical byte file, payload digest, and (where applicable) signature vector. Every hostile fixture states the rejection code and JSON path.

### 15.1 Parser and canonicalization fixtures

Include duplicate keys at root and nested levels, invalid UTF-8, BOM, unpaired surrogate, NUL/control characters, NaN/Infinity, '-0', exponent/overflow values, huge depth, huge string/array/object counts, unknown fields, null substitutions, duplicate IDs, unsorted arrays, alternate UUID/digest case, invalid base64url, signature bytes with padding, and object-property reorderings. Include Unicode normalization variants to prove that the contract does not silently normalize signed strings.

### 15.2 Identity and registry fixtures

Include unknown device class, unknown chip ID, same SoC with a different board, board/product mismatch, swapped board/chip IDs, missing IORegistry field, missing device-tree field, conflicting macOS/Linux observations, duplicate board matches, family-only observation, 'uname -m' without a board, omitted capability, present capability marked not applicable, 'full' without a complete profile, expired registry, retired board, and a record whose display name differs but exact predicates match.

### 15.3 Manifest and supply-chain fixtures

Include a valid signature over changed payload, wrong key ID, valid signature from a wrong role, threshold shortfall, expired/not-yet-valid envelope, replayed old manifest, branch/tag/ref locator, unallowlisted repository, mutable package range, wrong architecture, missing artifact digest, changed artifact bytes, package/index digest mismatch, incompatible firmware schema, component relation contradiction, board target omitted from registry, stable target without pass qualification, and rollback target not in the compatibility set.

### 15.4 Plan and storage fixtures

Include '/dev/disk*', '/', '..', glob, environment substitution, symlink-like path tokens, whole-disk/volume confusion, duplicate APFS UUID, APFS parent change, changed partition size, new unrelated container, disappeared target, stale topology digest, mutation sequence gap, mutation outside manifest policy, no owner approval, approval for a different plan, expired plan, interrupted step, and a successful subprocess with a failed postcondition.

### 15.5 Qualification and boot fixtures

Include a missing raw evidence object, evidence digest mismatch, wrong lab role, unknown board, wrong manifest digest, missing required test, required test marked optional, required test skipped, stale firmware baseline, measurement just outside a threshold, critical residual on an otherwise passing record, wrong slot, wrong attempt counter, counter rollback, missing required boot check, success with an advisory-only pass, success mark digest mismatch, torn marker, fallback to an unqualified slot, and boot-health data that tries to update registry/manifest state.

## 16. Test and gate plan

### 16.1 F-02 implementation gates

The implementation cannot enter consumer integration until all of these are green:

1. Every schema validates against the Draft 2020-12 metaschema and the repository's closed-object/resource-limit rules.
2. Accepted and hostile fixtures pass/fail with the declared code and path. The failure census contains zero unexpected accepts and zero unexpected rejects.
3. Canonicalization vectors match the independent reference implementation. Map reorder invariance, sorted-array rejection, digest mutation, and signature mutation properties pass.
4. Generated bindings are deterministic from the locked schema/generator inputs, compile in every required target, reject unknown fields, and expose no untyped admission escape hatch.
5. Cross-document tests prove registry/manifest/qualification/plan/boot-health digest and identity relationships, stable-vs-edge policy, expiry, replay, rollback, and exact board matching.
6. Resource-limit, fuzz, and differential parser tests run with bounded CPU/memory/time. Fuzz findings are fixed or explicitly rejected by coordinator ruling; they are not waived as malformed user input.
7. Redaction tests prove that exported plan/qualification/boot-health diagnostics omit credentials, owner tokens, encryption material, unnecessary device identifiers, and private evidence bytes while preserving verification-relevant digests.
8. CLI golden tests cover every command, exit class, JSON output shape, no-network validation mode, and refusal of '--trust-all'/arbitrary privileged operations.
9. A read-only consumer contract test runs against the actual installer identity/plist fixtures and product helper boundary. It proves that current dictionary/'uname' behavior is an adapter input, not a source of support authority.
10. Repository gates include 'git diff --check', conflict-marker scan, secret scan, generated-artifact drift check, dependency/license/provenance review, and exact base/tip census.

### 16.2 Cross-repository gates before implementation is accepted

The coordinator must require:

- installer tests over versioned macOS IORegistry and 'diskutil' plist fixtures, including no mutation during inventory/plan and stable-ID revalidation before each step;
- product tests proving unknown/ambiguous board and missing required capability fail before privileged action and that UI/reporting cannot convert a required failure into install success;
- release tests proving every artifact/package byte is digest/signature checked and component selection comes only from one manifest;
- boot/update tests proving attempts, atomic markers, last-known-good retention, automatic fallback, and downgrade rules use the boot-health contract without a private success format;
- physical-lab tests proving qualification records reference immutable evidence and a static/mock/VM result cannot produce a physical qualification pass;
- adversarial review with planted unknown-board, duplicate-key, stale-plan, changed-disk, bad-signature, missing-capability, and success-after-failure cases. A bug-level finding blocks integration.

F-02 itself does not run consumer or physical suites. It defines their required fixtures and contract gates so that later slices cannot claim that schema compilation or a recognized Apple chip is acceptance evidence.

## 17. Explicit deferrals

- F-03 decides the trust root, key roles, thresholds, custody, expiry/grace, revocation, rotation, mirror compromise response, and offline recovery. This note defines only the envelope and signature preimage.
- F-04 decides reproducible builders, artifact/provenance/SBOM formats, immutable storage, channel promotion, and independent-build evidence. The manifest fields reserve their references without implementing those systems.
- F-05 decides assembled-system compatibility validation and promotion automation.
- I-01/I-03/I-04/I-06 decide the transaction journal, APFS/Recovery state machine, destructive-operation implementation, resume, uninstall, and DFU recovery runbook.
- P-01/P-02/P-04/P-05 decide product admission UX, required/optional capability presentation, diagnostics/support-bundle implementation, and update/rollback UX.
- B-03/B-04 decide the bootloader transport, bounded boot-health implementation, slot layout, success-marker storage, fallback, and bootloader resource budget. The opaque m1n1 repository boundary is respected.
- Q-01/Q-02 decide the lab controller, evidence store, redaction pipeline, and public ledger generation. This note defines the wire record consumed by those systems.
- Actual board inventory, firmware schema values, hardware thresholds, support states, and qualification evidence are not filled in by this design note.
- No binary/CBOR/CBOR-signing alternate for boot-health is defined. If the bootloader cannot meet the bounded JSON contract, the coordinator must rule on a new version rather than accept an undocumented second encoding.
- No APFS writer, firmware extractor, package manager integration, telemetry endpoint, database, or UI is implemented here.
- No generated binding, schema file, fixture, key, release manifest, qualification record, or support ledger is published by this design-only change.

## 18. Questions requiring coordinator ruling

The proposed defaults below make implementation possible, but these decisions are intentionally left for the coordinator:

| # | Question | Proposed default | Why the ruling matters |
| --- | --- | --- | --- |
| 1 | Is JSON Schema Draft 2020-12 plus RFC 8785 JCS the canonical wire/crypto base? | Yes; all five payloads use strict JSON and JCS | Changing this changes every parser, generated binding, digest, fixture, and signature vector |
| 2 | Is the 'omarchy-signed/v1' envelope with Ed25519 and the stated domain-separated preimage acceptable, or must F-02 use DSSE/COSE? | Keep the stated envelope in v1; F-03 supplies trust policy | The envelope choice is a compatibility boundary before any key is issued |
| 3 | Which roles and signature threshold should F-03 assign to registry, manifest, qualification, and runtime artifacts? | F-03 defines roles; F-02 requires role-bearing signatures and never embeds a threshold | This controls whether a cryptographically valid document is trusted |
| 4 | Should 'apple:<device-class>' be the permanent board ID, or should the organization allocate an opaque board ID while retaining device class as a predicate? | Use the readable ID in this note, with exact predicates preserved | Board IDs are referenced by every repository and public evidence record |
| 5 | Must a board match require all available macOS and Linux predicates, or may a source-specific predicate set qualify when the other source is unavailable? | Require every predicate declared by the selected record; missing required source data is unknown/reject | This determines behavior in macOS-only installer and Linux first-boot contexts |
| 6 | Which capability vocabulary and 'optional' semantics are approved for v1? | Start with the finite program domains listed here; omission means unknown and required failures cannot downgrade | Capability names become an API and drive physical qualification completeness |
| 7 | Can boot-health remain bounded JSON at the bootloader boundary? | Yes, 4 KiB payload and generated bounded parser; a binary alternative requires a new version | A private boot marker would create an unreviewed second authority and rollback hole |
| 8 | Which generated language targets are mandatory in F-02, especially Swift and C/Rust for boot health? | Python, Swift, product helper protocol, and one bounded boot binding | This determines generator scope, package ownership, and CI toolchain requirements |
| 9 | Should generated bindings be checked into consumers or fetched as pinned packages? | Generate in consumer CI from the schema lock and check in the reproducible output where review requires it | This controls supply-chain review, offline builds, and drift detection |
| 10 | What is the owner-approval authenticity boundary for 'installer-plan/v1'? | Approval binds exact plan/scope digests and records method/result; credential handling remains outside the document | A plan must not be executable merely because its JSON is signed by a project key |
| 11 | What offline cache/expiry grace is permitted for registry and manifest use? | Reject by default; F-03 may define a bounded signed offline recovery mode | An installer cannot silently downgrade to stale support metadata |
| 12 | Does stable manifest publication require qualification record IDs to be present in the manifest, or should a separate signed promotion index bind them? | Keep record IDs in the manifest and avoid cyclic record digests | This determines release assembly and immutable evidence lookup |

## 19. F-02 implementation handoff

After coordinator ruling, the implementation slice should proceed in this order: land the canonical schemas and common vocabulary; implement strict parse/canonicalize/digest; add signed-envelope verification hooks without hard-coding the F-03 trust root; generate and compile the required bindings; land accepted/hostile/canonical fixtures; implement pure cross-document admission functions; expose the CLI; then run the consumer contract and adversarial gates.

The implementation handoff must preserve the following non-negotiables: exact board identity is not SoC or architecture; a registry is not a qualification record; a manifest is not artifact proof; a plan is not approval; boot health is not hardware qualification; generated bindings are not trust roots; and no unknown, stale, mismatched, or partially verified value may be used to claim success or authorize mutation.
