# F-02 platform schema design

Status: DESIGN NOTE ONLY — corrected contract proposal; no implementation, compatibility claim, support claim, qualification claim, release claim, or DONE claim

This note defines the design-only contract for the five F-02 documents and the three auxiliary authenticated payloads used at the installer, release, boot, and device-tree boundaries. It does not implement schemas, validators, bindings, signing, storage operations, boot transport, device-tree mutation, or installer behavior. It does not change PROGRAM.md, program status, or hardware qualification. The boot implementation boundary is an opaque human-produced artifact boundary and is not inspected, described, tested, cloned, fetched, or depended on here.

## 1. Contract, vocabulary, and non-negotiables

F-02 connects exact Apple board identity, a release tuple, a read-only installation plan, physical qualification evidence, boot-slot health, owner authorization, and an authorized device-tree mutation record. Parsing, canonicalization, authentication, authority policy, cross-document admission, and durable execution are separate gates.

The authenticated payload vocabulary is exactly these eight values. The first five are the F-02 primary documents; the last three are auxiliary authenticated payloads. Auxiliary status does not exclude a value from the common envelope, schema-set, signature, canonicalization, negotiation, or fixture rules.

`OwnerProofReceipt`, `TargetAccount`, `Observation`, `AtomicBootRecord`, and
`VerifiedDtbInputs` are supporting verification-seam types only. Their `Trusted<T>` wrappers
are not authenticated payload vocabulary values, are not schema-input IDs, and do not add a
ninth payload or envelope variant.

~~~text
AUTHENTICATED_PAYLOAD_TYPES = {
  board-registry/v1,
  platform-manifest/v1,
  installer-plan/v1,
  qualification-record/v1,
  boot-health/v1,
  owner-approval/v1,
  boot-success-mark/v1,
  dtb-mutation-envelope/v1
}
F02_PRIMARY_TYPES = {
  board-registry/v1,
  platform-manifest/v1,
  installer-plan/v1,
  qualification-record/v1,
  boot-health/v1
}
AUXILIARY_AUTHENTICATED_TYPES = {
  owner-approval/v1,
  boot-success-mark/v1,
  dtb-mutation-envelope/v1
}
~~~

| Payload type | Producer | Primary consumers | Authority it does not have |
| --- | --- | --- | --- |
| `board-registry/v1` | platform registry tooling | installer, product helper, release tooling | it cannot qualify a board or select a component version by itself |
| `platform-manifest/v1` | release tooling | installer, update tooling, diagnostics | it cannot replace physical qualification or artifact verification |
| `installer-plan/v1` | read-only installer planner | approval service, transaction executor, diagnostics | it cannot authorize mutation without a separate owner receipt |
| `qualification-record/v1` | hardware lab tooling | promotion, ledger generation, diagnostics | it cannot grant support merely because it parses |
| `boot-health/v1` | bounded runtime reporter | slot selector, rollback code, diagnostics | it cannot promote a board, release, or capability |
| `owner-approval/v1` | owner-authorization service | plan validator, transaction executor | it cannot grant release, board, or boot authority |
| `boot-success-mark/v1` | bounded runtime reporter | boot evaluator, rollback code | it cannot qualify hardware or authorize mutation |
| `dtb-mutation-envelope/v1` | locked DTB policy tool | DTB consumer, boot integration | it cannot authorize a board, release, or storage operation |

`payload.schema` is the `payload_schema_id` and `payload_type` is the authenticated type; each accepts exactly one member of `AUTHENTICATED_PAYLOAD_TYPES`. A schema-input `schema_id` is instead one of the eleven closed schema-input IDs listed in section 3. There is no owner-specific ninth payload value, no seven-value replacement vocabulary, and no private alternate payload type. The common envelope has one canonical `payload_type` property; all older aliases are removed and rejected as unknown fields.

The only stable install-admission lifecycle state is `full`. It is insufficient unless the selected registry, manifest, qualification record, artifact set, and policy agree on exact content digests and exact board identity. No field in these schemas is a user-facing support announcement. Nothing in this note is implementation, compatibility, support, qualification, release, or DONE evidence.

## 2. Wire language, canonicalization, and validation phases

All eight payloads and their signed envelopes use UTF-8 JSON validated against JSON Schema Draft 2020-12 and canonicalized with RFC 8785 JSON Canonicalization Scheme (JCS). JSON Schema constrains shape; it does not establish trust. The parser rejects duplicate object names before schema validation. It rejects invalid UTF-8, a UTF-8 BOM, unpaired surrogates, NaN, Infinity, non-finite numbers, negative zero, non-canonical numeric spellings, unbounded depth, and resource-limit violations before constructing a typed value. A parser that keeps the last duplicate key is non-conforming.

The normative validation order is:

| Phase | Validation | First failure behavior |
| --- | --- | --- |
| P0 transport | byte encoding, UTF-8, BOM, control characters, duplicate JSON names, complete input | return `PARSE_SCHEMA_FAILURE` or `DUPLICATE_SEMANTIC_KEY` at the second JSON name; do not inspect cross-document references |
| P1 shape | root schema, required fields, closed objects, closed arrays, enum values, scalar bounds, exact API grammar, declared collection order | return `UNKNOWN_FIELD`, `PARSE_SCHEMA_FAILURE`, `RESOURCE_LIMIT`, or the declared shape code at the exact field |
| P2 canonical | JCS encoding, negative-zero rejection, digest recomputation, canonical byte equality | return `CANONICALIZATION_FAILURE` or the domain digest-cycle code |
| P3 authentication | envelope equality, signature preimage, signer role, key authority, issued/expiry window, replay identity | return `SIGNATURE_CONTEXT_MISMATCH`, `TRUST_FAILURE`, or `EXPIRY_OR_REPLAY_FAILURE` |
| P4 local identity | source normalization, stable-ID tuple, topology generation, mutation allowlist, required local fields | return `IDENTITY_INCOMPLETE`, `AMBIGUOUS_IDENTITY`, `BOOT_COUNTER_FAILURE`, or a domain failure |
| P5 cross-document | board, manifest, qualification, artifact, firmware, schema-set, plan, marker, and DTB bindings | return `CROSS_DOCUMENT_MISMATCH` or the more specific domain failure |
| P6 policy and execution | sealed authority, non-downgradeable gates, expiry at decision time, scope, rollback, evidence, and durable preconditions | return `TRUST_BOUNDARY_FAILURE`, `PLAN_SCOPE_OR_APPROVAL_FAILURE`, or a hold/reject decision |

P0 through P2 always precede P5. An unknown property is never treated as a possible cross-document mismatch. Within a collection, the second member with an identical semantic key fails at that member. Reusing one `stable_id` with a different normalized identity tuple or parent fails `AMBIGUOUS_IDENTITY` at the second `stable_id` path. Reusing one stable ID with the same tuple fails `DUPLICATE_SEMANTIC_KEY` at the second member. No validator sorts, deduplicates, keeps the first, or keeps the last member.

The non-boot limits are maximum input 1 MiB, maximum nesting depth 32, maximum object properties 128 at every object, maximum array length 1,024, maximum string length 4,096 UTF-8 bytes, maximum total string bytes 256 KiB, and maximum integer magnitude 2^63-1 unless a narrower field rule applies. The complete marker limit is in section 9. A boundary value is valid only when the inclusive bound says so; a parser never truncates or repairs input.

The common lexical grammar is closed:

| Type | Exact rule |
| --- | --- |
| `payload_schema_id` and `payload_type` | exactly one of the eight values in section 1 |
| schema-input `schema_id` | exactly one of the eleven IDs in `SCHEMA_INPUT_IDS` in section 3 |
| `document_id` | lowercase ASCII `^[a-z0-9][a-z0-9._:-]{0,127}$`, immutable for a revision |
| `board_id` | lowercase ASCII `apple:[a-z0-9][a-z0-9-]{0,63}` |
| `soc_id` | lowercase ASCII `apple-soc:[a-z0-9][a-z0-9-]{0,63}`, diagnostic only |
| `uuid` | lowercase RFC 4122 textual UUID with hyphens |
| `digest` | `sha256:` followed by exactly 64 lowercase hexadecimal characters |
| `git_commit` | lowercase hexadecimal commit ID of exactly 40 or 64 characters |
| `timestamp` | RFC 3339 UTC timestamp ending in `Z`, four-digit year, millisecond precision at most |
| `version` | three unsigned decimal components in `major.minor.patch`, each 0 through 65,535, with no prerelease text |
| `api_version` | the same three-component numeric grammar as `version` |
| `uint16` | JSON integer from 0 through 65,535 |
| `uint64` | JSON integer from 0 through 18,446,744,073,709,551,615 |
| `bytes_u32` | JSON integer from 0 through 4,294,967,295 |
| `base64url` | unpadded RFC 4648 base64url with the field’s declared decoded-length bound |
| `path_token` | non-empty ASCII token with no slash, backslash, `..`, NUL, control character, or URL delimiter |

The following identifiers are also closed grammar, not informal labels. Every
occurrence is validated at the named JSON path before any trust or cross-document decision:

~~~text
ProjectId = "project:" || LowerAsciiToken
RepositoryId = "repo:" || LowerAsciiToken
SliceId = "slice:" || LowerAsciiToken
ArtifactId = "artifact:" || LowerAsciiToken
PolicyId = "policy:" || LowerAsciiToken
KeyId = "key:" || LowerAsciiToken
ActorId = "actor:" || LowerAsciiToken
AccountId = "acct:" || LowerAsciiToken
CheckId = "check:" || LowerAsciiToken
MeasurementId = "measurement:" || LowerAsciiToken
EvidenceId = "evidence:" || LowerAsciiToken
InputId = "input:" || LowerAsciiToken
ComponentId = "linux-kernel" | "dtb-set" | "firmware-bundle" | "mesa-stack" | "boot-stack"
Operation = "inspect/v1" | "write/v1" | "replace/v1" | "remove/v1" | "rollback/v1"
Status = "pass" | "fail" | "not-run" | "unknown"
Applicability = "required" | "optional" | "not-applicable"
Timestamp = RFC3339 UTC ending in Z, millisecond precision at most, year 1970..9999
Generation = uint64, 0..18,446,744,073,709,551,615; no wrap or reset
JsonPointer = "" or "/" segment *("/" segment), 1..16 segments, each 1..64 ASCII
             bytes, RFC 6901 ~0/~1 escapes only, no URI fragment or array index
JsonPath = "$" or "$" *("." LowerAsciiToken / "[" 1*DIGIT "]"), max 512 ASCII bytes
ErrorMessage = one fixed template from the code table, ASCII, 1..256 bytes, no input value
PathToken = ASCII string 1..256 bytes with no slash, backslash, `..`, NUL, control character, or URL delimiter
SlotId = "slot-a" | "slot-b" | "recovery"
SourceKind = "macos-diskutil/v1" | "macos-iokit/v1" | "linux-sysfs/v1"
~~~

The grammar has no open object, arbitrary map, free-form enum, or unbounded string at a
trust boundary. A missing field, unknown field, duplicate object name, duplicate semantic
key, malformed identifier, out-of-order collection, out-of-range number, invalid status,
or invalid enum returns `PARSE_SCHEMA_FAILURE`, `UNKNOWN_FIELD`, `DUPLICATE_SEMANTIC_KEY`,
or `RESOURCE_LIMIT` at the exact JSON path shown by the error contract. The parser does not
coerce a string to a number, a number to a string, a null to a missing field, or an unknown
value to a default.

### 2.1 Closed nested grammar registry

This registry closes every nested grammar referenced below. `ExactObject<F>` means exactly
the listed properties, `SortedList<F,K>` means 0..1024 entries sorted and unique by `K`, and
`ExactList<F,K>` means the named finite members in the declared order with no missing,
duplicate, or extra member. A nullable field is nullable only where `| null` is written.
All object and array limits in section 2 apply recursively; the narrower bound wins.

~~~text
RegistryRevision = {revision_id: LowerAsciiToken, generation: Generation}
Board = {
  board_id: BoardId, identity_match: IdentityMatch, soc: SocRecord,
  firmware: FirmwareRecord, physical_capabilities: SortedList<PhysicalCapability, capability_id>,
  lifecycle: "active" | "deprecated" | "withdrawn", qualification_profile: ProfileId,
  install_policy: PolicyId, labels: SortedList<Label, label>
}
IdentityMatch = {
  macos: {compatible: ExactList<MacPredicate, value>, device_class: DeviceClass,
          product_type: ProductType, board_id_u32: uint32, chip_id_u32: uint32},
  linux: {compatible: ExactList<LinuxCompatible, value>, model: ModelToken}
}
MacPredicate = LowerAsciiToken; LinuxCompatible = LowerAsciiToken
DeviceClass = "desktop" | "laptop" | "tablet" | "unknown"
ProductType = "Mac" | "MacBook" | "MacBookAir" | "MacBookPro" | "Macmini" | "MacStudio"
SocRecord = {soc_id: SocId, family: LowerAsciiToken, revision: LowerAsciiToken}
FirmwareRecord = {firmware_schema_id: LowerAsciiToken, firmware_schema_version: Version,
                  firmware_schema_digest: Digest, bundle_id: LowerAsciiToken}
PhysicalCapability = {capability_id: CapabilityId, physical_presence: "present" | "absent",
                      support_requirement: "required" | "optional" | "not_applicable",
                      policy_id: PolicyId, qualification_check_ids: ExactList<CheckId, value>}
Label = ASCII string 1..64 bytes matching [a-z0-9][a-z0-9._-]{0,63}
CapabilityId = one exact member of the capability_vocabulary in section 6.1
ProfileId = "profile:" || LowerAsciiToken

ArtifactRecord = {artifact_id: ArtifactId, component_id: ComponentId,
                  kind: ArtifactKind, media_type: MediaType, size_bytes: uint64,
                  content_digest: Digest, artifact_version: Version, signature_policy_id: PolicyId}
ArtifactKind = "kernel-image/v1" | "dtb/v1" | "firmware/v1" | "mesa-package/v1" | "boot-image/v1"
MediaType = LowerAsciiToken
PackageRecord = {package_name: PackageName, architecture: Architecture, version: Version,
                 content_digest: Digest, signature_policy_id: PolicyId}
PackageName = ASCII string 1..128 bytes matching [a-z0-9][a-z0-9+._-]{0,127}
Architecture = "aarch64" | "arm64" | "noarch"
FirmwareSchema = {schema_id: LowerAsciiToken, schema_version: Version, schema_digest: Digest}
ManifestProjection = {projection_schema: "manifest-projection/v1", artifacts: SortedList<ArtifactRecord, artifact_id>,
                      package_set: SortedList<PackageRecord, (package_name, architecture)>,
                      compatibility: SortedList<TypedCompatibilityRelation, (left_component_id, relation, right_component_id)>,
                      firmware_schema: FirmwareSchema, rollback: RollbackProjection}
RollbackProjection = {last_known_good_required: true, manifest_ids: SortedList<DocumentId, document_id>,
                      artifact_ids: SortedList<ArtifactId, artifact_id>, minimum_retention: uint16,
                      failure_attempt_limit: uint16, projection_digest: Digest}

InstallerInventory = {topology: Topology, observed_at: Timestamp, observation_id: UUID}
PlanSelection = {board_id: BoardId, board_registry_digest: Digest, manifest_id: DocumentId,
                 manifest_digest: Digest, schema_set_digest: Digest, policy_id: PolicyId,
                 policy_digest: Digest, topology_digest: Digest, consumer_capability_digest: Digest}
Mutation = {sequence: uint16, step_id: LowerAsciiToken, operation: Operation,
            target_refs: SortedList<TargetRef, (object_kind, stable_id)>,
            preconditions: SortedList<Precondition, predicate_id>, expected_effect: ExpectedEffect,
            rollback_boundary: uint16, owner_summary: OwnerSummary}
TargetRef = {object_kind: ObjectKind, stable_id: StableId, identity_digest: Digest, object_generation: Generation}
Precondition = {predicate_id: LowerAsciiToken, kind: "identity-equals/v1" | "digest-equals/v1" | "generation-equals/v1",
               expected_digest: Digest, expected_generation: Generation}
ExpectedEffect = {effect_id: LowerAsciiToken, target_digest: Digest, topology_digest: Digest}
OwnerSummary = ASCII string 1..512 bytes; no control characters, secrets, or authority semantics
RollbackBoundary = {sequence: uint16, target_ids: SortedList<StableId, value>, required: true}
RecoveryRequirement = {requirement_id: LowerAsciiToken, kind: "offline-recovery/v1" | "last-known-good/v1" | "human-review/v1", required: true}
Scope = {scope_schema: "installer-scope/v1", project_id: ProjectId, repository_id: RepositoryId,
         slice_id: SliceId, board_id: BoardId, board_registry_digest: Digest,
         manifest_id: DocumentId, manifest_digest: Digest, schema_set_digest: Digest,
         policy_id: PolicyId, policy_digest: Digest, topology_digest: Digest,
         target_account_id: AccountId, target_account_binding: Digest,
         target_ids: SortedList<StableId, value>, target_identities: SortedList<TargetIdentity, stable_id>,
         operations: ExactList<ScopeOperation, sequence>}
TargetIdentity = {object_kind: ObjectKind, stable_id: StableId, identity_anchor_digest: Digest,
                  object_generation: Generation, source_identity_digest: Digest}
ScopeOperation = {sequence: uint16, step_id: LowerAsciiToken, operation: Operation,
                  target_ids: SortedList<StableId, value>}
QualificationManifestBinding = {manifest_id: DocumentId, manifest_digest: Digest,
                                board_registry_digest: Digest, required_outcome: "pass"}
QualificationOutcome = "pass" | "fail" | "blocked"
Slot = {slot_id: SlotId, slot_generation: Generation, boot_artifact_digest: Digest}
Attempt = {counter: Generation, started_at: Timestamp, finished_at: Timestamp | null,
           previous_slot: SlotId | null, boot_context_generation: Generation}
Fallback = {decision: "hold" | "recover", target_slot: SlotId, rollback_set_digest: Digest,
            failure_code: FailureCode | null}

QualificationProfile = {profile_id: ProfileId, board_id: BoardId, required_check_ids: ExactList<CheckId, value>,
                       measurement_rules: SortedList<MeasurementRule, (check_id, name)>,
                       failure_limit: uint16}
TestResult = {test_id: CheckId, capability_id: CapabilityId, applicability: Applicability, required: boolean,
             status: QualificationStatus, observed_at: Timestamp, evidence_ids: ExactList<EvidenceId, value>,
             measurements: SortedList<Measurement, (criterion_id, name)>, failure_code: FailureCode | null,
             notes: BoundedNote}
QualificationStatus = "pass" | "fail" | "not-run" | "blocked"
MeasurementRule = {check_id: CheckId, name: MeasurementName, unit: MeasurementUnit,
                   minimum: int64, maximum: int64, required: boolean}
Measurement = {criterion_id: LowerAsciiToken, name: MeasurementName, unit: MeasurementUnit, value: int64}
MeasurementName = "boot-time-ms" | "resume-time-ms" | "temperature-c" | "battery-percent" | "frame-rate-fps" | "error-count"
MeasurementUnit = "ms" | "celsius" | "percent" | "fps" | "count"
Evidence = {evidence_id: EvidenceId, content_digest: Digest, media_type: MediaType, captured_at: Timestamp,
            retention_class: "short" | "standard" | "long", privacy_class: "public" | "restricted" | "private" | "secret",
            locator: PathToken}
BoundedNote = ASCII or UTF-8 string 0..2048 bytes, no control character except space, tab, LF

BootCheckProfile = {profile_id: ProfileId, profile_digest: Digest, required_check_ids: ExactList<CheckId, value>,
                    allowed_classes: ExactList<BootCheckClass, value>, measurement_rules: SortedList<BootMeasurementRule, (check_id, name)>,
                    retry_limit: uint16, failure_limit: uint16, rollback_manifest_ids: SortedList<DocumentId, document_id>}
BootCheckClass = "board-identity/v1" | "manifest-integrity/v1" | "artifact-integrity/v1" | "firmware-abi/v1" | "dtb-integrity/v1" | "storage-topology/v1" | "display-ready/v1" | "userspace-ready/v1"
BootMeasurementRule = {check_id: CheckId, name: BootMeasurementName, unit: BootMeasurementUnit, minimum: int64, maximum: int64}
BootMeasurementName = "duration-ms" | "temperature-c" | "battery-percent" | "counter" | "generation" | "digest-match"
BootMeasurementUnit = "ms" | "celsius" | "percent" | "count" | "boolean"
BootCheck = {check_id: CheckId, class: BootCheckClass, status: BootStatus, observed_at: Timestamp,
             measurement: BootMeasurement, evidence_digest: Digest}
BootStatus = "pass" | "fail" | "not-run"
BootMeasurement = {name: BootMeasurementName, unit: BootMeasurementUnit, value: int64}
~~~

The registry’s finite names are normative. A measurement name must be permitted by the
manifest-declared profile for that check and its integer value must be within the inclusive
profile bounds; a wrong unit, missing measurement, extra measurement, or out-of-range value
is `BOOT_REQUIRED_CHECK_FAILURE` at `$.payload.checks[i].measurement`. A missing, unknown, or
duplicate check is `BOOT_REQUIRED_CHECK_FAILURE` at `$.payload.checks` or the second check’s
`check_id`; it never becomes an optional pass by default.

### 2.2 Reference-closure and rejection matrix

The shorthand types used by the closed records have these exact meanings. This table is
part of the schema contract, so an implementation may not fill an omitted definition from a
language default:

| Type | Syntax and semantics | Bound/order failure |
| --- | --- | --- |
| `BoardId` | `apple:` plus lowercase token, 1..64 suffix bytes; board identity, never SoC-only | `PARSE_SCHEMA_FAILURE` at the board ID |
| `SocId` | `apple-soc:` plus lowercase token, 1..64 suffix bytes; diagnostic only | `PARSE_SCHEMA_FAILURE` at the SoC ID |
| `SchemaId` | one of the eleven `SCHEMA_INPUT_IDS`, exact `name/v1` spelling | `UNKNOWN_FIELD` or `PARSE_SCHEMA_FAILURE` at the schema ID |
| `Domain` and `Context` | one exact row of the eight-row signing table | `SIGNATURE_CONTEXT_MISMATCH` at domain/context |
| `Version` and `ApiVersion` | three bounded unsigned components, numeric ordering only | `RESOURCE_LIMIT` or `PARSE_SCHEMA_FAILURE` at the component |
| `Digest` | `sha256:` plus 64 lowercase hexadecimal characters; digest is recomputed from its named preimage | `CANONICALIZATION_FAILURE` or `CROSS_DOCUMENT_MISMATCH` at the digest |
| `UUID` and `Nonce` | lowercase RFC 4122 UUID; nonce is unpadded base64url decoding to 16..32 bytes | `PARSE_SCHEMA_FAILURE` at the identifier |
| `PolicySource` | closed F-03 source record that can produce only `Trusted<PolicySource>` | `TRUST_BOUNDARY_FAILURE` at `$` |
| `SlotId` | exactly `slot-a`, `slot-b`, or `recovery`; slot generation is monotonic | `PARSE_SCHEMA_FAILURE` or `BOOT_COUNTER_FAILURE` at slot |
| `FailureCode` | exactly one code in section 13, never a free string | `PARSE_SCHEMA_FAILURE` at the code |
| `StableId` and `ObjectKind` | one matching typed prefix and object kind from section 7 | `AMBIGUOUS_IDENTITY` at the second identity |
| `GeneratedOutputLock`, `CompiledLock`, and `GeneratedBindingMetadata` | closed lock records from sections 3 and 11 with concrete digests and unique paths | `BINDING_INTEGRITY_FAILURE` at the first lock field |
| `Trusted<T>` | private nominal wrapper produced only by the named seam for `T` | `TRUST_BOUNDARY_FAILURE` at `$` |
| `PublicProjection` | one of three closed projection objects, no authority-bearing input | `UNKNOWN_FIELD` at the projection field |

For every closed object, missing required properties are `PARSE_SCHEMA_FAILURE` at the
missing property, unknown properties are `UNKNOWN_FIELD` at the unknown property, duplicate
object names and semantic keys are `DUPLICATE_SEMANTIC_KEY` at the second occurrence,
out-of-range numbers and byte/count/depth limits are `RESOURCE_LIMIT` at the value, and a
wrong declared order is `PARSE_SCHEMA_FAILURE` at the first out-of-order member. For every
cross-document relation, the first unequal canonical field is reported as
`CROSS_DOCUMENT_MISMATCH`; no relation is silently skipped. For every trust seam, absent,
unverifiable, stale, expired, replayed, or recomputation-inconsistent source material is
reported at the first source field with no trusted result.

The supporting source types referenced in constructor signatures are closed as follows:

~~~text
PolicySource = {source_schema: "policy-source/v1", policy: Policy,
                source: SourceEvidence, authority_digest: Digest}
GeneratedBindingMetadata = {metadata_schema: "generated-binding-metadata/v1",
                            language: "python" | "swift" | "rust-boot", binding_identity: BindingIdentity,
                            generated_artifact_id: ArtifactId, generated_output_digest: Digest,
                            compiled_lock_digest: Digest}
PublicProjection = {projection_version: "public/v1" | "private-support/v1" | "evidence-authorized/v1",
                    fields: ExactObject<ProjectionField>, projection_digest: Digest}
ProjectionField = one enumerated field from the selected projection allowlist
~~~

`PolicySource` and binding metadata are immutable source records whose digests are checked
against their trusted source and lock. `ProjectionField` is a schema-generator concept, not
a runtime map: each of the three projection IDs has an enumerated field set in section 12.

## 3. Exact schema-set layout and two-lock dependency

The directory layout has exactly two lock files. `schemas/schema-input.lock` is the sole preimage for `schema_set_digest`. `bindings/generated-output.lock` contains generated artifact digests and binds back to `schema_set_digest`; it is never part of the schema-set digest preimage. No third lock or compatibility alias is permitted.

~~~text
schemas/
  common/v1/common.schema.json
  common/v1/vocabularies.schema.json
  signed-document/v1/signed-document.schema.json
  board-registry/v1/board-registry.schema.json
  platform-manifest/v1/platform-manifest.schema.json
  installer-plan/v1/installer-plan.schema.json
  qualification-record/v1/qualification-record.schema.json
  boot-health/v1/boot-health.schema.json
  owner-approval/v1/owner-approval.schema.json
  boot-success-mark/v1/boot-success-mark.schema.json
  dtb-mutation-envelope/v1/dtb-mutation-envelope.schema.json
  schema-input.lock
bindings/
  generated-output.lock
  python/1.0.0/
  swift/1.0.0/
  rust-boot/1.0.0/
tools/schema/
  generator/
  cli/
fixtures/
  accepted/
  hostile/
  canonicalization/
docs/design/platform-schema.md
~~~

Fixture directories are named by the eight-value vocabulary with `/` replaced by `-`; the accepted and hostile directory sets are closed to those names. They are not lock preimage fields and do not permit arbitrary paths.

~~~text
SCHEMA_INPUT_IDS = {
  common/v1,
  vocabularies/v1,
  signed-document/v1,
  board-registry/v1,
  platform-manifest/v1,
  installer-plan/v1,
  qualification-record/v1,
  boot-health/v1,
  owner-approval/v1,
  boot-success-mark/v1,
  dtb-mutation-envelope/v1
}
~~~

The closed `schemas/schema-input.lock` grammar is:

~~~text
SchemaInputLock = {
  lock_schema: "schema-input-lock/v1",
  schema_set_id: "platform-schema-set/v1",
  schema_entries: SortedList<SchemaInputEntry, (schema_id, schema_version)>,
  vocabulary: {
    vocabulary_id: "authenticated-payload-vocabulary/v1",
    vocabulary_digest: Digest,
    payload_types: ExactList<PayloadType, payload_type>,
    primary_types: ExactList<PrimaryPayloadType, payload_type>,
    auxiliary_types: ExactList<AuxiliaryPayloadType, payload_type>
  },
  canonicalization: {
    standard: "RFC8785",
    implementation_id: "omarchy-jcs/v1",
    implementation_version: Version,
    implementation_source_digest: Digest,
    number_policy: "reject-negative-zero-and-nonfinite/v1"
  },
  limits: {
    max_input_bytes: 1048576,
    max_depth: 32,
    max_object_properties: 128,
    max_array_length: 1024,
    max_string_bytes: 4096,
    max_total_string_bytes: 262144,
    max_integer_magnitude: 9223372036854775807,
    complete_marker_max_bytes: 4096
  },
  generator_inputs: ExactList<ToolInput, input_id>,
  parser_inputs: ExactList<ToolInput, input_id>,
  toolchain_inputs: ExactList<ToolInput, input_id>
}
SchemaInputEntry = {
  schema_id: SchemaId,
  schema_version: "v1",
  source_path: RelativeSchemaPath,
  source_digest: Digest,
  reference_digests: SortedList<ReferenceDigest, reference_path>
}
ToolInput = {
  input_id: InputId,
  input_kind: "generator" | "parser" | "toolchain",
  name: LowerAsciiToken,
  version: Version,
  source_uri: ImmutableHttpsUri,
  source_digest: Digest,
  target: TargetToken,
  build_flags_digest: Digest
}
LowerAsciiToken = ASCII string matching [a-z0-9][a-z0-9._:-]{0,127}
InputId = "input:" || LowerAsciiToken
TargetToken = "python" | "swift" | "rust-boot" | "schema-cli"
RelativeSchemaPath = "schemas/" || ASCII path with slash-separated segments, no empty segment, no `..`, no backslash, and maximum length 256 bytes
RelativeBindingPath = "bindings/" || ASCII path with slash-separated segments, no empty segment, no `..`, no backslash, and maximum length 256 bytes
ImmutableHttpsUri = "https://" || lowercase DNS host || ASCII path with no query or fragment and maximum length 512 bytes
ReferenceDigest = {
  reference_path: RelativeSchemaPath,
  digest: Digest
}
~~~

`schema_entries` contains exactly the eleven schema IDs named in the layout: the two common schemas, the signed-document schema, and the eight payload schemas. Every input, vocabulary, canonicalization, limit, generator, parser, and toolchain field is present and has the exact type above. There are no generated-output digests, output paths, compiler outputs, current-date values, absolute paths, locale values, or `schema_set_digest` fields in this lock. The lock has no self-digest field.

The closed `bindings/generated-output.lock` grammar is:

~~~text
GeneratedOutputLock = {
  lock_schema: "generated-output-lock/v1",
  schema_set_digest: Digest,
  generated_entries: SortedList<GeneratedEntry, (language, artifact_id, output_role)>
}
GeneratedEntry = {
  language: "python" | "swift" | "rust-boot",
  artifact_id: ArtifactId,
  output_path: RelativeBindingPath,
  binding_identity: BindingIdentity,
  generator_input_id: InputId,
  parser_input_id: InputId,
  toolchain_input_id: InputId,
  source_schema_ids: ExactList<SchemaId, schema_id>,
  output_digest: Digest,
  line_endings: "LF",
  file_order_digest: Digest,
  bounded_memory_report_digest: Digest,
  consumer_api: ApiVersion,
  output_role: "parser" | "binding" | "schema-constants" | "boot-binding"
}
BindingIdentity = {
  binding_id: LowerAsciiToken,
  binding_version: Version,
  binding_source_digest: Digest,
  parser_id: LowerAsciiToken,
  parser_version: Version,
  parser_source_digest: Digest,
  api_id: LowerAsciiToken,
  api_version: ApiVersion,
  api_source_digest: Digest
}
ApiVersion = {major: uint16, minor: uint16, patch: uint16}
CompiledLock = {
  lock_schema: "compiled-binding-lock/v1", schema_set_digest: Digest,
  language: "python" | "swift" | "rust-boot", consumer_api: ApiVersion,
  binding_identity: BindingIdentity, parser_identity: BindingIdentity,
  toolchain_input_id: InputId, source_schema_ids: ExactList<SchemaId, schema_id>,
  generated_artifact_id: ArtifactId, generated_output_path: RelativeBindingPath,
  generated_output_digest: Digest, lock_digest: Digest
}
~~~

The lock graph is mechanically defined as `schema source bytes -> schema-input.lock fields -> schema_set_digest -> generated input selection -> generated-output.lock -> generated artifact bytes`. The output lock may contain `schema_set_digest`, but the input lock may not contain any output-lock field. Generated bindings may embed `schema_set_digest`; that embedded value creates no reverse edge. Thus every graph edge points from an input to a later digest or output and the graph is acyclic. A build fails closed if an entry is missing, duplicated, extra, stale, or digest-inconsistent.

The compiled lock is a per-consumer immutable record, not a third schema-set input. Its
preimage is `compiled_lock_digest = sha256(ASCII("omarchy-compiled-binding-lock/v1") ||
0x00 || JCS(CompiledLock without lock_digest))`; `generated_output_digest` is independently
`sha256(ASCII("omarchy-generated-output/v1") || 0x00 || LF-normalized output bytes)`. The
output lock has one and only one entry for each `(language, artifact_id, output_role)` and
each `output_path` is unique globally. A `(schema_set_digest, language, api_id, api_version,
output_role)` tuple cannot resolve to two artifact IDs or two output paths. The parser,
generator, API, toolchain, source schema IDs, output path, and output digest are all copied
into the compiled lock and compared exactly; a same-schema-set consumer with a different
generated or parser artifact is rejected as `BINDING_INTEGRITY_FAILURE`. There is no
fallback to a nearby binding, API downgrade, stale output, or consumer-local schema copy.

The digest is:

~~~text
schema_set_digest = sha256(ASCII("omarchy-schema-set/v1") || 0x00 || JCS(SchemaInputLock))
~~~

The exact `SchemaInputLock` object, including its sorted lists and all typed fields, is the only preimage. Reproduction uses the declared relative path, digest, URI, version, target, and build flag digest; implementation-specific map order and discovery are forbidden. Concrete source and artifact digests are an implementation-owner residual and are not published by this design note.

## 4. Common authenticated envelope and authority seam

Every authenticated payload is carried by a closed `omarchy-signed/v1` envelope with exactly these fields: `format`, `payload_type`, `payload_version`, `domain`, `context`, `schema_set_digest`, `payload`, and `signatures`. The payload object is closed and has the exact common fields `schema`, `schema_set_digest`, `document_id`, `issuer`, `issued_at`, and `expires_at`, followed by its type-specific required fields. `payload.schema`, `payload.document_id`, `payload.schema_set_digest`, `payload_type`, `payload_version`, and the envelope digest must agree.

The exact schema-set digest is required in every payload, every envelope preimage, every owner approval, the manifest consumer binding, every trusted metadata record, and both lock-direction checks. A consumer compares it byte-for-byte with the local input lock and never substitutes a compatible-looking schema set.

Each signature object is closed with exactly `key_id`, `signer_role`, `algorithm`, `signature_format`, and `signature`. v1 permits only `ed25519`, `raw-ed25519/v1`, and a fixed 64-byte signature encoded as unpadded base64url. Signatures are sorted and unique by `(key_id, signer_role, algorithm, signature_format)`. `key_id` and `signer_role` are authenticated values, not caller hints.

For payload `P`, `payload_digest = sha256(JCS(P))`. For signature entry `S`, define the closed object `A` with exactly these fields and no signature bytes:

~~~text
A = {
  envelope_format: "omarchy-signed/v1",
  signature_format: "raw-ed25519/v1",
  key_id: S.key_id,
  signer_role: S.signer_role,
  algorithm: "ed25519",
  domain: envelope.domain,
  context: envelope.context,
  payload_type: envelope.payload_type,
  payload_version: envelope.payload_version,
  schema_set_digest: envelope.schema_set_digest,
  payload_digest: sha256(JCS(P)),
  anti_transplant: {
    document_id: P.document_id,
    schema: P.schema,
    payload_type: envelope.payload_type,
    payload_version: envelope.payload_version,
    schema_set_digest: envelope.schema_set_digest,
    domain: envelope.domain,
    context: envelope.context
  },
  payload: P
}
auth_preimage = ASCII("omarchy-auth-preimage/v1") || 0x00 || JCS(A)
~~~

The format, key, role, algorithm, domain, context, type, version, schema-set digest, payload digest, anti-transplant binding, and complete payload are therefore signed together. The signature itself is outside `A` and is never signed recursively. A signature from an unknown, expired, revoked, or wrong-role key yields no `Trusted<T>`.

`TrustContext` is a closed, versioned, F-03-supplied value. It contains exactly `context_schema = "trust-context/v1"`, `context_id`, `authority_bindings`, `key_set_digest`, `revocation_epoch`, `issued_at`, and `expires_at`. Its `authority_bindings` are a non-empty sorted list of the following closed `AuthorityRoleBinding` records:

~~~text
AuthorityRoleBinding = {
  binding_schema: "authority-role-binding/v1",
  authority_id: LowerAsciiToken,
  role: "board-admission" | "manifest-release" | "installer-planner" | "owner-authorization" | "ci-conformance" | "qualification-lab" | "boot-runtime" | "dtb-authority" | "evidence-reader",
  actor_id: ActorId,
  account_id: AccountId,
  key_ids: SortedList<KeyId, key_id>,
  allowed_methods: ExactList<AuthorizationMethod, method>,
  service_policy_id: PolicyId,
  service_policy_digest: Digest,
  issued_at: Timestamp,
  expires_at: Timestamp,
  binding_digest: Digest
}
~~~

The binding digest covers the complete closed record except `binding_digest`, under the domain `omarchy-authority-role-binding/v1`. F-03 supplies and verifies the role membership, key custody, thresholds, revocation, rotation, expiry grace, mirror compromise, and offline recovery policy. Every release, CI, owner, board, qualification, evidence, boot, and DTB role resolution uses the matching `AuthorityRoleBinding`; a role string, key ID, account string, or caller-supplied policy cannot resolve authority by itself. There is no owner-specific payload type or owners-specific bypass.

`ExpectedContext` is a closed verifier input, supplied by the caller only as a typed value
whose constructor checks the selected operation and target. It contains exactly
`context_schema = "expected-context/v1"`, `payload_type`, `payload_version`, `domain`,
`context`, `project_id`, `repository_id`, `slice_id`, `operation`, `board_id`,
`manifest_id`, `manifest_digest`, `schema_set_digest`, `target_account_id`,
`target_account_binding`, `target_identity_digests`, and `policy_digest`. Null is allowed
only for fields marked `not-applicable` in the matrix below. The constructor derives the
scope from the verified document and rejects a caller value that cannot be exactly compared.

The exhaustive signing contract is the exact eight-row signing contract:

| Payload type | Signing domain | Context | Required signer role and exact scope |
| --- | --- | --- | --- |
| `board-registry/v1` | `omarchy-board-registry` | `board-registry-publication` | `board-admission`; `project_id`, `repository_id`, `slice_id`, and `operation = inspect/v1` are fixed; board target set is the registry board set |
| `platform-manifest/v1` | `omarchy-platform-manifest` | `manifest-publication` | `manifest-release`; exact project/repository/slice and `operation = inspect/v1`; board target set and manifest document ID are bound |
| `installer-plan/v1` | `omarchy-installer-plan` | `installer-plan-proposal` | `installer-planner`; exact project/repository/slice and the closed operation set in the plan scope; exact board, manifest, topology, target identities, and policy are bound |
| `qualification-record/v1` | `omarchy-qualification-record` | `qualification-result` | `qualification-lab`; exact project/repository/slice and `operation = inspect/v1`; exact board, manifest, profile, and evidence set are bound |
| `boot-health/v1` | `omarchy-boot-runtime` | `boot-health-core` | `boot-runtime`; exact project/repository/slice and `operation = inspect/v1`; exact board, manifest, slot, lineage, source generation, and attempt counter are bound |
| `owner-approval/v1` | `omarchy-owner-authorization` | `installer-plan-execution` | `owner-authorization`; exact project/repository/slice, closed operation set, actor, target account, policy, board, manifest, topology, and target identities are bound |
| `boot-success-mark/v1` | `omarchy-boot-runtime` | `boot-success-marker` | `boot-runtime`; exact project/repository/slice and `operation = inspect/v1`; exact board, manifest, slot, lineage, source generation, attempt counter, marker generation, and check set are bound |
| `dtb-mutation-envelope/v1` | `omarchy-dtb-authority` | `dtb-mutation-authorization` | `dtb-authority`; exact project/repository/slice and closed mutation operation, board, manifest, policy, tool, DTB artifact, firmware, DT schema, source generation, and ordered mutation set are bound |

The table is exhaustive and is enforced inside `verify` after envelope equality and before
authority resolution for every one of the eight values. `payload_type`, domain, context,
payload version, schema-set digest, and all non-null `ExpectedContext` fields must equal the
row; an unknown type, unknown domain or context, role from another row, wrong role scope,
missing required scope member, or transplanted signer returns `SIGNATURE_CONTEXT_MISMATCH`
at `$.payload_type`, `$.domain`, `$.context`, `$.signatures[i].signer_role`, or the first
mismatched scope path. There is no permissive role-only verification.

For avoidance of shorthand ambiguity, `Domain` is exactly the eight domain strings in the
table and `Context` is exactly the eight context strings in the table. The role field is
closed to the nine roles in `AuthorityRoleBinding`; `boot-runtime` is reused for the two
runtime payload rows only because their context and complete scope differ. `SchemaId` is one
of the eleven `SCHEMA_INPUT_IDS`; `PayloadType` is one of the eight payload values and is
never widened by a local schema file.

The only construction path is:

~~~text
strict_parse(bytes) -> Parsed<T> | ParseError
canonicalize(Parsed<T>) -> Canonical<T> | CanonicalizationError
verify(Canonical<T>, Trusted<TrustContext>, VerifiedClock, ExpectedContext) -> Trusted<T> | TrustError
admit(Trusted<T>, Admitted<Policy>) -> Admitted<T> | AdmissionError
~~~

The constructors for `Trusted<T>`, `Trusted<Observation>`, `VerifiedClock`,
`Trusted<AtomicBootRecord>`, `Trusted<VerifiedDtbInputs>`, `Trusted<BootContext>`,
`Admitted<Policy>`, `VerifiedOwnerAuthorizationContext`, `Trusted<TargetAccount>`,
`Trusted<OwnerProofReceipt>`, and `ConsumerCapabilities` are private to the contract
library and are all reached at one verification seam per source type. Generated bindings
expose no cast, unchecked initializer, mutable trust flag, generic-map admission method, or
deserialization path that produces one of these types. A failed step returns a stable
redacted error and releases no authority-bearing partial value.

### 4.1 One verification seam for local source records

The following are closed, non-payload records. They are supporting verification-seam types,
not values in `AUTHENTICATED_PAYLOAD_TYPES`, and none can be wrapped merely by copying JSON
fields. Each source adapter emits a closed `SourceEvidence` record containing immutable
source identity, the complete evidence-byte digest, a monotonically increasing source
generation, an adapter API version, capture and expiry times, a nonce, and a source record
digest. The seam checks the source signature or authenticated OS/hardware channel, exact
bytes and their digest, freshness, bounds, source-generation monotonicity, nonce/replay
reservation, and recomputes every derived digest before returning a trusted value.

~~~text
SourceEvidence = {
  evidence_schema: "source-evidence/v1", source_kind: LowerAsciiToken,
  source_id: LowerAsciiToken, adapter_id: LowerAsciiToken, adapter_api_version: Version,
  source_generation: Generation, evidence_digest: Digest, captured_at: Timestamp,
  expires_at: Timestamp, nonce: Nonce, source_record_digest: Digest
}
Observation = {
  observation_schema: "observation/v1", observation_id: UUID, project_id: ProjectId,
  repository_id: RepositoryId, slice_id: SliceId, board_id: BoardId,
  topology: Topology, board_predicates: IdentityMatch, source: SourceEvidence,
  observed_at: Timestamp, valid_until: Timestamp, replay_id: UUID,
  recomputation_digest: Digest
}
VerifiedClock = {
  clock_schema: "verified-clock/v1", clock_id: LowerAsciiToken, now: Timestamp,
  source_generation: Generation, monotonic_sequence: uint64, valid_until: Timestamp,
  attestation_digest: Digest
}
AtomicBootRecord = {
  record_schema: "atomic-boot-record/v1", record_id: UUID, project_id: ProjectId,
  repository_id: RepositoryId, slice_id: SliceId, board_id: BoardId, manifest_id: DocumentId,
  manifest_digest: Digest, lineage_id: UUID, slot_id: SlotId, slot_generation: Generation,
  attempt_counter: Generation, source_generation: Generation, commit_state: "committed",
  bytes_digest: Digest, source: SourceEvidence, replay_id: UUID
}
VerifiedDtbInputs = {
  inputs_schema: "verified-dtb-inputs/v1", project_id: ProjectId, repository_id: RepositoryId,
  slice_id: SliceId, board_id: BoardId, manifest_id: DocumentId, manifest_digest: Digest,
  policy_id: PolicyId, policy_digest: Digest, tool_id: LowerAsciiToken, tool_version: Version,
  tool_digest: Digest, dtb_artifact_id: ArtifactId, dtb_artifact_version: Version,
  dtb_artifact_digest: Digest, firmware_bundle_id: LowerAsciiToken,
  firmware_bundle_version: Version, firmware_bundle_digest: Digest, dt_schema_id: LowerAsciiToken,
  dt_schema_version: Version, dt_schema_digest: Digest, source_generation: Generation,
  source_dtb_bytes_digest: Digest, post_dtb_bytes_digest: Digest, source: SourceEvidence,
  replay_id: UUID, recomputation_digest: Digest
}
~~~

`make_trusted_observation` accepts only a complete authenticated `SourceEvidence` and a
closed adapter output; it rejects missing fields, stale `valid_until`, source-generation
rollback, duplicate observation/replay IDs, changed evidence bytes, unknown board
predicates, impossible topology bounds, or failed recomputation with `TRUST_BOUNDARY_FAILURE`
at `$.source` or the first source path. `verify_clock` accepts only a monotonic attested
clock sample and rejects a backward, expired, duplicated, or caller-time value with
`TRUST_BOUNDARY_FAILURE` at `$.now`. `make_trusted_atomic_boot_record` requires one complete
committed record, authenticated source bytes, exact digest recomputation, monotonic counter
and generation, and persistent replay reservation; partial, forged, stale, reset, wrapped,
or transplanted records produce `BOOT_COUNTER_FAILURE` or `TRUST_BOUNDARY_FAILURE` and no
record. `make_trusted_dtb_inputs` independently verifies the source and post-DTB bytes,
all manifest paths, policy/tool/artifact/firmware/schema tuple, source generation, and
recomputation digest; any missing, unverifiable, stale, mismatched, or replayed input
produces `DTB_INPUT_VERIFICATION_FAILURE` and no trusted inputs.

`Clock` and raw `Observation`, `AtomicBootRecord`, `VerifiedDtbInputs`, policy maps, target
identities, or proof bytes never appear in an authority API. `VerifiedClock`,
`Trusted<Observation>`, `Trusted<AtomicBootRecord>`, `Trusted<VerifiedDtbInputs>`, and
other `Trusted<T>` values are the only accepted forms.

The only source-boundary constructors are explicit and closed:

~~~text
verify_owner_proof(AuthenticatedOwnerProofSource) -> Trusted<OwnerProofReceipt> | TrustError
verify_target_account(AuthenticatedTargetAccountSource) -> Trusted<TargetAccount> | TrustError
make_trusted_observation(AuthenticatedObservationSource) -> Trusted<Observation> | TrustError
verify_clock(AttestedClockSample) -> VerifiedClock | TrustError
make_trusted_atomic_boot(AuthenticatedAtomicBootSource) -> Trusted<AtomicBootRecord> | TrustError
verify_dtb_inputs(Trusted<PlatformManifest>, Trusted<BootContext>, Admitted<Policy>,
                  Trusted<SourceEvidence>, VerifiedClock) -> Trusted<VerifiedDtbInputs> | DtbError
~~~

`AuthenticatedOwnerProofSource`, `AuthenticatedTargetAccountSource`,
`AuthenticatedObservationSource`, `AttestedClockSample`, and `AuthenticatedAtomicBootSource`
are private adapter-channel records with fixed fields, immutable source identity, complete
evidence bytes/digest, bounds, capture time, nonce, and source-generation. They are not
payload types and cannot be passed to `admit`, `validate_plan`, `evaluate_boot_health`, or a
mutation consumer. The constructor itself is the only place that reads their untrusted
bytes; it returns no partially trusted field on any failure.

## 5. Digest cycles and one-way document bindings

The installer plan body `P_plan` has no `approval`, `plan_digest`, or `approval_digest` property. Its digest is:

~~~text
D_plan = sha256(ASCII("omarchy-plan-body/v1") || 0x00 || JCS(P_plan))
~~~

The owner approval is a separate `owner-approval/v1` payload containing `D_plan` and `D_scope`. It is never inserted into `P_plan` before calculating `D_plan`. A `plan_digest` property under `P_plan` fails `PLAN_DIGEST_CYCLE` at `$.payload.plan_digest`; it is not normalized.

The boot-health payload is the signed core `C`. It contains no `success_mark`, `canonical_payload_digest`, `success_mark_digest`, or marker signature field. Its digest is:

~~~text
D_core = sha256(ASCII("omarchy-boot-health-core/v1") || 0x00 || JCS(C))
~~~

The separate `boot-success-mark/v1` payload `M` contains `core_digest = D_core` and never contains `D_mark`, its own digest, or a core self-reference. If a diagnostic marker digest is needed, it is external:

~~~text
D_mark = sha256(ASCII("omarchy-boot-success-mark/v1") || 0x00 || JCS(M))
~~~

The manifest references qualification records by stable `qualification_record_id` only. A qualification record points back with `manifest_id` and the verified manifest payload digest. A manifest never contains a qualification content digest. This one-way graph is:

~~~text
manifest payload --board_id + qualification_record_id--> qualification record
qualification record --manifest_id + manifest_digest--> manifest payload
~~~

A `document_id` has an immutable one-ID-to-one-payload-digest history. It is not a revision
counter and it is never reused for a correction. The closed local identity record and its
preimage are:

~~~text
DocumentIdRecord = {
  record_schema: "document-id-record/v1", document_id: DocumentId,
  payload_type: PayloadType, payload_version: "v1", schema: SchemaId,
  schema_set_digest: Digest, domain: Domain, context: Context,
  payload_digest: Digest, generation: Generation, lineage_id: UUID,
  first_seen_at: Timestamp, expires_at: Timestamp, replay_id: UUID,
  record_digest: Digest
}
DocumentIdLineage = {
  lineage_schema: "document-lineage/v1", lineage_id: UUID, payload_type: PayloadType,
  document_ids: ExactList<DocumentId, value>, predecessor_id: DocumentId | null,
  current_id: DocumentId, generation: Generation, lineage_digest: Digest
}
document_record_digest = sha256(ASCII("omarchy-document-id-record/v1") || 0x00 || JCS(DocumentIdRecord without record_digest))
lineage_digest = sha256(ASCII("omarchy-document-lineage/v1") || 0x00 || JCS(DocumentIdLineage without lineage_digest))
~~~

The first accepted envelope allocates exactly one record with `generation = 1`; a
retransmission is accepted only if every envelope field, signature tuple, payload digest,
lineage, and replay identity is byte-for-byte identical and the durable replay reservation
is already for that exact record. The same ID with a different payload digest, type, schema,
domain, context, generation, or lineage is `DOCUMENT_ID_REUSE` at `$.payload.document_id`.
The same payload digest under two IDs is not a correction and is rejected as
`DOCUMENT_ID_REUSE` unless the trusted lineage record explicitly identifies the second ID as
the next generation. Corrections create a new ID and a new generation, with exactly one
predecessor; a resolver follows the closed predecessor chain, verifies each record digest,
rejects cycles, missing predecessors, duplicate IDs, two children, two current IDs, expired
ambiguous records, or forked history, and never chooses first/last/default. A replayed nonce
or replay ID is `EXPIRY_OR_REPLAY_FAILURE`; an ambiguous ID graph is `DOCUMENT_ID_FORK`.

## 6. Primary payload contracts

Every payload uses the common fields from section 4 and forbids additional properties at every nesting level.

### 6.1 board-registry/v1

The additional top-level fields are exactly `registry_revision`, `boards`, and `capability_vocabulary`. `boards` is sorted by `board_id` and `capability_vocabulary` is the exact finite list:

~~~text
cpu-topology, memory, internal-display, backlight, external-display, gpu, media, audio, camera, keyboard, trackpad, touch-id-sep, wifi, bluetooth, usb, thunderbolt, nvme, sd, ethernet, charging-battery, thermal-fan, suspend-resume, virtualization, recovery
~~~

Each board has exactly `board_id`, `identity_match`, `soc`, `firmware`, `physical_capabilities`, `lifecycle`, `qualification_profile`, `install_policy`, and `labels`. `labels` is a sorted bounded display-only list and is never used for admission.

`identity_match` has exactly `macos` and `linux` predicate objects. `macos` has `compatible`, `device_class`, `product_type`, `board_id_u32`, and `chip_id_u32`; `linux` has `compatible` and `model`. A predicate object may use a declared `null` only for a field explicitly marked optional by the registry schema. Raw open-ended property maps are forbidden. Missing required predicates produce unknown, never a match. SoC identity is diagnostic and cannot substitute for board identity.

Each physical capability entry has exactly `capability_id`, `physical_presence`, `support_requirement`, `policy_id`, and `qualification_check_ids`. `physical_presence` is `present` or `absent`; `support_requirement` is `required`, `optional`, or `not_applicable`; check IDs are non-empty and sorted. Omission means unknown. A present capability cannot be `not_applicable`, and an optional capability cannot downgrade a missing required capability.

### 6.2 platform-manifest/v1 and canonical component tree

The additional top-level fields are exactly `channel`, `release_version`, `board_registry_digest`,
`board_targets`, `qualification_bindings`, `components`, `artifacts`, `package_set`,
`compatibility`, `firmware_schema`, `consumer_schema_set`, `minimum_consumer_api`, and
`rollback`. The five fields `artifacts`, `package_set`, `compatibility`, `firmware_schema`,
and `rollback` are signed `ManifestProjection` values only: they are recomputed from the
component tree and are not independent authorities. `channel` is `edge`, `rc`, or `stable`;
`board_targets` is a unique sorted list of explicit board IDs. It never names only a SoC or
architecture.

The `components` object is closed and has exactly these five property paths and no aliases:

~~~text
components.linux_kernel
components.dtb_set
components.firmware_bundle
components.mesa_stack
components.boot_stack
~~~

The path-to-ID mapping is exact: the five component `component_id` values are `linux-kernel`, `dtb-set`, `firmware-bundle`, `mesa-stack`, and `boot-stack` in the same order. Properties named `kernel`, `device_tree`, `firmware`, `mesa`, `boot`, `kernel_component`, `dtbs`, or `bootloader` are unknown fields and cannot be aliases.

Every component record is closed and has exactly `component_schema`, `component_id`, `source`,
`provenance`, `recipe_digest`, `abi_contract_id`, `config_inputs`, `policy_inputs`,
`patch_lock`, `toolchain_lock`, `report_lock`, `artifacts`, `packages`, `firmware_schema`,
`dt_schema`, `boot_check_profile`, `rollback`, and `compatibility_relations`. An empty lock
is represented only by `mode = "not-applicable/v1"` and `entries = []`; a required lock uses
`mode = "required/v1"` and a non-empty entry list. The component profile fixes the mode and
the nullable fields and cannot be changed by a manifest author:

| Component path | Config | Policy | Patch | Toolchain | Report |
| --- | --- | --- | --- | --- | --- |
| `components.linux_kernel` | required | required | required | required | required |
| `components.dtb_set` | required | required | required | required | required |
| `components.firmware_bundle` | required | required | not-applicable | required | required |
| `components.mesa_stack` | required | required | required | required | required |
| `components.boot_stack` | required | required | required | required | required |

The fixed component profile additionally requires `firmware_schema` only on
`components.firmware_bundle`, `dt_schema` only on `components.dtb_set`, and
`boot_check_profile` only on `components.boot_stack`; each other component carries `null`.
Package lists are empty except where the component produces packages. The relation list is
owned by exactly the lexicographically smaller component ID in each relation and is empty at
the other operand, preventing a second signed authority for the same relation.

The closed component grammar is:

~~~text
Component = {
  component_schema: "manifest-component/v1",
  component_id: ComponentId,
  source: {
    source_kind: "git-repository/v1" | "generated-from-locked-input/v1" | "immutable-bundle/v1",
    repository_id: RepositoryId,
    source_commit: GitCommit,
    upstream_commit: GitCommit | null,
    source_digest: Digest,
    provenance_report_digest: Digest
  },
  provenance: {
    provenance_schema: "component-provenance/v1",
    source_observation_digest: Digest,
    build_input_digest: Digest,
    attestation_digest: Digest,
    producer_binding_digest: Digest
  },
  recipe_digest: Digest,
  abi_contract_id: LowerAsciiToken,
  config_inputs: SortedList<ConfigInput, input_id>,
  policy_inputs: SortedList<PolicyInput, policy_id>,
  patch_lock: {
    mode: "required/v1" | "not-applicable/v1",
    entries: SortedList<PatchEntry, patch_id>,
    lock_digest: Digest
  },
  toolchain_lock: {
    mode: "required/v1",
    entries: SortedList<ToolchainEntry, toolchain_id>,
    lock_digest: Digest
  },
  report_lock: {
    mode: "required/v1",
    entries: SortedList<ReportEntry, report_id>,
    lock_digest: Digest
  },
  artifacts: SortedList<ComponentArtifact, artifact_id>,
  packages: SortedList<PackageRecord, (package_name, architecture)>,
  firmware_schema: FirmwareSchema | null,
  dt_schema: DtSchemaBinding | null,
  boot_check_profile: BootCheckProfile | null,
  rollback: RollbackCoordinates,
  compatibility_relations: SortedList<TypedCompatibilityRelation, (left_id, relation, right_id)>
}
ConfigInput = {
  input_id: LowerAsciiToken,
  input_kind: "config-file/v1" | "defconfig/v1" | "device-tree-source/v1",
  source_digest: Digest,
  normalized_content_digest: Digest,
  policy_digest: Digest
}
PolicyInput = {
  policy_id: PolicyId,
  policy_version: Version,
  policy_digest: Digest,
  source_digest: Digest
}
PatchEntry = {
  patch_id: LowerAsciiToken,
  source_digest: Digest,
  patch_digest: Digest,
  order: uint16
}
ToolchainEntry = {
  toolchain_id: LowerAsciiToken,
  toolchain_version: Version,
  toolchain_digest: Digest,
  flags_digest: Digest
}
ReportEntry = {
  report_id: LowerAsciiToken,
  report_kind: "build/v1" | "lint/v1" | "abi/v1" | "dt-schema/v1" | "compatibility/v1",
  report_digest: Digest,
  producer_toolchain_digest: Digest
}
ComponentArtifact = {
  artifact_id: ArtifactId,
  component_id: ComponentId,
  kind: "kernel-image/v1" | "dtb/v1" | "firmware/v1" | "mesa-package/v1" | "boot-image/v1",
  media_type: LowerAsciiToken,
  size_bytes: uint64,
  content_digest: Digest,
  artifact_version: Version,
  signature_policy_id: PolicyId
}
RollbackCoordinates = {
  coordinate_schema: "component-rollback/v1",
  previous_component_ids: SortedList<LowerAsciiToken, component_id>,
  previous_manifest_ids: SortedList<DocumentId, document_id>,
  artifact_ids: SortedList<ArtifactId, artifact_id>,
  retention_count: uint16,
  rollback_policy_id: PolicyId,
  rollback_policy_digest: Digest
}
TypedCompatibilityRelation = {
  relation_schema: "typed-compatibility-relation/v1",
  left_component_id: ComponentId,
  relation: "boot-protocol/v1" | "kernel-abi/v1" | "firmware-schema/v1" | "package-architecture/v1" | "component-interface/v1",
  right_component_id: ComponentId,
  contract_id: LowerAsciiToken,
  evidence_digest: Digest
}
DtSchemaBinding = {schema_id: LowerAsciiToken, schema_version: Version, schema_digest: Digest,
                   source_report_id: LowerAsciiToken}
~~~

`source` is never a branch, tag, floating URL, or mutable locator. `config_inputs`, `policy_inputs`, all lock entries, artifacts, rollback coordinates, and typed relations are authenticated by the manifest payload digest. A relation is accepted only for the declared typed operand pair. There is no raw shell expression, regular expression, package-manager expression, or evaluated policy in a manifest.

The manifest’s `qualification_bindings` entries have exactly `board_id`,
`qualification_record_id`, and `required_outcome = "pass"`. `components.firmware_bundle`
is the sole authority for `firmware_schema`; `components.<component>.artifacts` is the sole
authority for artifacts; `components.<component>.packages` is the sole authority for
packages; `components.<component>.compatibility_relations` is the sole authority for
compatibility; and each `components.<component>.rollback` is the sole authority for rollback
coordinates. The top-level `firmware_schema` equals the non-null firmware component binding;
top-level `artifacts` equals the exact sorted set union of all component artifacts;
top-level `package_set` equals the exact sorted set union of all component packages;
top-level `compatibility` equals the exact sorted set union of the component relation lists;
and top-level `rollback` equals the exact projection of all component rollback records,
including every ID, ordering, retention value, and policy digest. Equality includes object
shape, scalar values, and list order. A missing, extra, reordered, duplicate, or conflicting
projection is `MANIFEST_AUTHORITY_CONFLICT` at the first differing top-level path. There is
never a top-level winner, default, merge, or last-writer rule. `consumer_schema_set` and
`minimum_consumer_api` use section 11.

### 6.3 installer-plan/v1

The plan has exactly `inventory`, `selection`, `scope`, `mutations`, `rollback_boundaries`, and `recovery_requirements` after the common fields. It has no approval property. `selection` contains exact board ID, registry digest, manifest ID, manifest digest, schema-set digest, policy revision, topology digest, and consumer capability digest. It cannot select an independent component, URL, package range, or firmware file.

`inventory` is a read-only observation. Storage references use the typed records in section 7 and never use a raw `/dev/disk*` path, filesystem path, glob, environment substitution, or user-provided device name as a mutation target. The executor may derive a volatile OS path only after resolving and revalidating the stable ID immediately before a step.

Each mutation is a closed declarative record with exactly `sequence`, `step_id`, `operation`, `target_refs`, `preconditions`, `expected_effect`, `rollback_boundary`, and `owner_summary`. `operation` is a finite enum. Every target occurs in inventory with the same kind, parent, role, size, object generation, and stable identity. A subprocess exit code is never a postcondition. Before every durable step, a fresh topology is canonicalized and its digest and generation are compared with the plan. Changed, missing, ambiguous, or newly appearing targets fail closed.

### 6.4 qualification-record/v1

The additional fields are exactly `board`, `manifest`, `qualification_profile_id`, `test_results`, `outcome`, `residuals`, `operator`, `lab`, and `evidence`. `board` contains exact identity observations, board ID, SoC ID, configuration class, topology class, and firmware/macOS baseline. A lab asset ID is not a public serial number.

The closed `manifest` record is `QualificationManifestBinding` with exactly `manifest_id`,
`manifest_digest`, `board_registry_digest`, and `required_outcome = "pass"`.
`manifest_digest` must equal the verified manifest payload digest, `manifest_id` must equal
the verified manifest document ID, and the board ID must be an explicit manifest target. For
a stable manifest, every target board is `full`, every binding has `required_outcome =
"pass"`, and every referenced record has complete physical evidence, an allowed lab role,
and the exact manifest digest. Edge and RC records cannot widen targets or convert incomplete
evidence into stable support.

Each test result has exactly `test_id`, `capability_id`, `applicability`, `required`, `status`, `observed_at`, `evidence_ids`, `measurements`, `failure_code`, and `notes`. `status` is `pass`, `fail`, `not-run`, or `blocked`; record `outcome` is `pass`, `fail`, or `blocked`. Unknown applicability cannot pass. Required status is copied immutably from the profile and cannot be downgraded. A pass requires every applicable required test to pass, every required evidence digest to verify, all criteria to pass, and every residual to be explicitly non-blocking under the admitted policy.

Each evidence entry has exactly `evidence_id`, `content_digest`, `media_type`, `captured_at`, `retention_class`, `privacy_class`, and `locator`. A locator is a fetch hint only. The evidence store returns bytes only after matching the expected digest. Static validation, a VM, a mocked device tree, a recognized chip string, a successful compile, or a booting desktop cannot satisfy physical evidence.

The remaining qualification records are closed as follows:

~~~text
QualificationBoard = {board_id: BoardId, identity_observation_digest: Digest, soc_id: SocId,
                      configuration_class: LowerAsciiToken, topology_class: LowerAsciiToken,
                      firmware_baseline_digest: Digest, macos_baseline_digest: Digest}
Operator = {actor_id: ActorId, account_id: AccountId, role: "qualification-lab",
            binding_digest: Digest}
Lab = {lab_id: LowerAsciiToken, location_class: "internal" | "contracted", binding_digest: Digest}
Residual = {residual_id: LowerAsciiToken, severity: "informational" | "non-blocking" | "blocking",
            owner_id: LowerAsciiToken, immutable_input_digest: Digest,
            default_ruling: "reject" | "hold" | "allow", blocking_gate: LowerAsciiToken}
~~~

`QualificationBoard.identity_observation_digest` must resolve to a `Trusted<Observation>`
with the same complete board predicate and source tuple. `required`, `applicability`,
`status`, `failure_code`, measurement names/units/bounds, and evidence IDs are closed and
semantically unique. A required test can be `pass` only when its profile says required, its
status and all measurements satisfy the profile, and every evidence digest is verified by a
trusted evidence reader. An unassigned, unknown, blocking, stale, or unverifiable residual
forces `outcome = "fail"`; no notes field can override it. The operator and lab must resolve
through `Trusted<AuthorityRoleBinding>` with role `qualification-lab`.

### 6.5 boot-health/v1 core

The additional fields are exactly `board_id`, `manifest_id`, `manifest_digest`, `profile_id`,
`profile_digest`, `lineage_id`, `source_generation`, `slot`, `attempt`, `checks`,
`checks_digest`, `success`, and `fallback`. `profile_id` and `profile_digest` identify the
single `BootCheckProfile` at `$.payload.components.boot_stack.boot_check_profile` in the
verified manifest. `lineage_id` is a UUID. `source_generation` and `attempt.counter` are
unsigned 64-bit values with the exact bound in section 9. They are signed core fields, not
diagnostics.

`slot` contains exactly `slot_id`, `slot_generation`, and `boot_artifact_digest`; `slot_id` is `slot-a`, `slot-b`, or `recovery`. `attempt` contains exactly `counter`, `started_at`, `finished_at`, `previous_slot`, and `boot_context_generation`. `checks` is sorted by `check_id`; each check contains exactly `check_id`, `class`, `status`, `observed_at`, `measurement`, and `evidence_digest` using the closed `BootCheck` grammar. Every required declared check appears exactly once, no optional check may be unknown, and an empty, missing, extra, duplicate, unknown-class, or laundered check rejects. `checks_digest = sha256(ASCII("omarchy-boot-check-set/v1") || 0x00 || JCS(checks))`. `success` is true only if the manifest profile and its required check set, allowed classes, measurement names/units/bounds, retry limit, failure limit, board, manifest, slot, slot generation, lineage, source generation, counter, source record, and `checks_digest` all verify; every required check passes; the attempt is valid; and a separately verified marker matches `D_core`. The core contains no marker field.

`fallback` contains exactly `decision`, `target_slot`, `rollback_set_digest`, and `failure_code`. `decision` is `hold` or `recover`; `target_slot` is `slot-a`, `slot-b`, or `recovery`, and `failure_code` is null only for `hold` with a non-success core. A switch target must be in the exact rollback set derived from the manifest component rollback records and have a verified last-known-good record; `rollback_set_digest` is recomputed from that set. Corruption, an absent marker, a failed/not-run check, an indeterminate condition, an empty rollback set when recovery is required, or a reset/wrapped counter never becomes success.

`rollback_set_digest = sha256(ASCII("omarchy-boot-rollback-set/v1") || 0x00 ||
JCS({manifest_ids, artifact_ids, slot_ids, retention_count, failure_attempt_limit}))`, where
the lists are the exact sorted union of the component rollback records and `slot_ids` is a
closed projection of the corresponding last-known-good records. The boot evaluator
recomputes this digest from the trusted manifest and durable slot ledger before accepting a
marker; a marker that carries a different digest, an empty required set, an extra slot, or a
target not in the set is hold-only with `BOOT_FALLBACK_FAILURE`.

## 7. Typed storage identity and topology

Stable IDs are generated by one source adapter from a current authoritative storage observation. They are identity references, not paths, locators, content digests, or caller-created tokens. The exact typed forms are:

~~~text
whole_disk stable_id = ^disk:v1:sha256:[0-9a-f]{64}$
gpt_partition stable_id = ^partition:v1:sha256:[0-9a-f]{64}$
apfs_container stable_id = ^container:v1:sha256:[0-9a-f]{64}$
apfs_volume stable_id = ^volume:v1:sha256:[0-9a-f]{64}$
ObjectKind = "whole_disk" | "gpt_partition" | "apfs_container" | "apfs_volume"
StableId = DiskStableId | PartitionStableId | ContainerStableId | VolumeStableId
~~~

The `[0-9a-f]{64}` range is a grammar constraint, not an open template. The suffix is the kind-specific identity digest bytes encoded in lowercase hexadecimal and contains no second `sha256:` label. It is never accepted as an artifact, evidence, manifest, or payload digest. Unknown prefixes, uppercase hex, short hashes, paths, `diskN` tokens, and syntactically valid IDs without a source tuple and provenance are rejected.

The closed source normalization grammar is:

~~~text
SourceTuple = {
  source_kind: "macos-diskutil/v1" | "macos-iokit/v1" | "linux-sysfs/v1",
  adapter_id: LowerAsciiToken,
  adapter_api_version: Version,
  observation_digest: Digest,
  source_generation: uint64,
  logical_block_bytes: 512 | 4096,
  physical_block_bytes: 512 | 4096,
  source_identity_digest: Digest
}
NormalizedToken = lowercase ASCII token matching [a-z0-9][a-z0-9._:@+-]{0,127}
SerialToken = "serial:" || NormalizedToken
ModelToken = "model:" || NormalizedToken
PhysicalLocationToken = "location:" || NormalizedToken
PhysicalExtentList = SortedList<PhysicalExtent, (start_lba, length_lba)>, 1..64 entries
PhysicalExtent = {start_lba: uint64_63, length_lba: uint64_63}
~~~

The four exact identity preimages are closed objects:

~~~text
I_disk = {
  identity_schema: "disk-identity/v1",
  object_kind: "whole_disk",
  source: SourceTuple,
  gpt_disk_guid: UUID,
  capacity_bytes: uint64_63,
  transport: "internal-pcie" | "external-usb" | "external-thunderbolt" | "external-sata" | "virtual",
  model_token: ModelToken | null,
  serial_token: SerialToken | null,
  physical_location_token: PhysicalLocationToken | null
}
I_partition = {
  identity_schema: "partition-identity/v1",
  object_kind: "gpt_partition",
  source: SourceTuple,
  parent_stable_id: DiskStableId,
  partition_guid: UUID,
  type_guid: UUID,
  first_lba: uint64_63,
  last_lba: uint64_63
}
I_container = {
  identity_schema: "container-identity/v1",
  object_kind: "apfs_container",
  source: SourceTuple,
  parent_stable_id: DiskStableId | PartitionStableId,
  container_uuid: UUID,
  capacity_bytes: uint64_63,
  physical_extents: PhysicalExtentList
}
I_volume = {
  identity_schema: "volume-identity/v1",
  object_kind: "apfs_volume",
  source: SourceTuple,
  parent_stable_id: ContainerStableId,
  volume_uuid: UUID,
  role: "system" | "data" | "preboot" | "recovery" | "vm" | "update" | "other",
  capacity_bytes: uint64_63
}
stable_id(kind, I_kind) = kind_prefix(kind) || hex_lower(sha256(ASCII("omarchy-storage-identity/v2") || 0x00 || JCS({source: I_kind.source, identity: I_kind})))
identity_anchor_digest = sha256(ASCII("omarchy-storage-identity-anchor/v1") || 0x00 || JCS({source: I_kind.source, identity: I_kind}))
CapacityPreimage = {logical_block_bytes: 512 | 4096, value_lba: uint64_63, value_bytes: uint64_63}
value_bytes = exact(value_lba * logical_block_bytes)
~~~

`uint64_63` is an unsigned integer from 0 through 9,223,372,036,854,775,807. UUIDs are lower-case hyphenated RFC 4122 values. GUIDs use the same canonical textual form. Capacity is the authoritative byte capacity and is never rounded. Every LBA conversion uses the source tuple’s declared logical block size and the exact `CapacityPreimage`; multiplication must be integral, aligned, and <= `uint64_63`, otherwise `IDENTITY_INCOMPLETE` is returned at the offending capacity or extent path. A physical block size smaller than the logical size, a non-divisible byte capacity, zero extent length, inclusive-end overflow, unaligned byte offset, or LBA outside the parent range is rejected. Transport is one of the five values above. Model, serial, and physical-location tokens are normalized by Unicode-free ASCII lowercasing, are private inputs to the identity preimage, and never appear in exported topology, public projections, logs, or error messages. A null token is distinct from an empty token; empty tokens are invalid. A whole disk requires a GUID, capacity, transport, and at least one of serial or physical-location token. A partition requires a disk parent, GUID, type GUID, and `first_lba <= last_lba`. A container requires a valid parent and non-empty extents. A volume requires a container parent, UUID, role, and capacity. Sparse identity receives no ID.

`PhysicalExtent` is exactly `{start_lba: uint64_63, length_lba: uint64_63}` with
`length_lba >= 1`; extents are sorted by `(start_lba, length_lba)`, non-overlapping, and
their exclusive end `start_lba + length_lba` must not overflow and must be within the
parent capacity expressed in LBAs. A partition’s inclusive `last_lba` is converted with
`exclusive_end_lba = last_lba + 1` and the addition must not overflow. Every byte/LBA
conversion is recomputed from the same `logical_block_bytes`; no rounding or inferred sector
size is allowed. A partition parent resolves to a whole disk, a container parent resolves to
a disk or partition, and a volume parent resolves to a container. Each parent must be
present in the same topology. Parent depth is at most 4 and cycles fail before any matching
decision.

The adapter records provenance in the identity preimage and in the trusted relation as exactly `source_kind`, `adapter_id`, `adapter_api_version`, `source_field_names`, `observation_digest`, `source_generation`, `logical_block_bytes`, `physical_block_bytes`, and `source_identity_digest`. `source_field_names` is a sorted list from the closed field vocabulary for the object kind. The adapter is the only producer of a stable ID and must retain the source tuple, normalized tuple, evidence digest, and provenance needed to reproduce it without exporting private tokens. A same physical identifier observed through a different adapter, API version, evidence digest, source generation, field set, or block geometry produces a different stable-ID preimage and cannot silently preserve identity.

The topology `T` is closed and contains exactly `topology_schema = "storage-topology/v1"`,
`source_kind`, `adapter_id`, `adapter_api_version`, `observation_digest`,
`source_identity_digest`, `source_generation`, and `objects`. Each object contains exactly
`object_kind`, `stable_id`, `parent_stable_id`, `object_generation`, `expected_role`,
`size_bytes`, `identity_anchor_digest`, `protected`, `mutation_target`, and `provenance`.
There is no raw path, mount point, free-space value, serial, password, token, or content
bytes. The exact digest is:

~~~text
D_topology = sha256(ASCII("omarchy-storage-topology/v1") || 0x00 || JCS(T))
~~~

The closed topology object grammar is:

~~~text
TopologyObject = {
  object_kind: "whole_disk" | "gpt_partition" | "apfs_container" | "apfs_volume",
  stable_id: DiskStableId | PartitionStableId | ContainerStableId | VolumeStableId,
  parent_stable_id: DiskStableId | PartitionStableId | ContainerStableId | null,
  object_generation: uint64,
  expected_role: "system" | "data" | "preboot" | "recovery" | "vm" | "update" | "other",
  size_bytes: uint64_63,
  identity_anchor_digest: Digest,
  protected: boolean,
  mutation_target: boolean,
  provenance: {
    source_kind: SourceKind, adapter_id: LowerAsciiToken, adapter_api_version: Version,
    observation_digest: Digest, source_generation: Generation,
    source_identity_digest: Digest, source_field_names: SortedList<LowerAsciiToken, value>
  }
}
~~~

The `stable_id` prefix must match `object_kind`, `parent_stable_id` must have the exact parent type from the four identity preimages, and the object provenance must equal the topology source tuple. `mutation_target = true` is permitted only for an object present in the plan scope. `protected = true` and `mutation_target = true` cannot coexist. The topology root has no parent; every non-root parent is present exactly once.

The topology has at most 64 objects, maximum parent depth 4, and at most 64 physical extents per container. `source_generation` begins at 0 before any committed snapshot, becomes 1 on the first committed snapshot, remains unchanged for the same canonical topology, and increments once for each different committed canonical topology. It is never reset, reused, or wrapped. `object_generation` begins at 1 when an object is first seen, increments when its identity tuple or parent changes, and is never reused after disappearance. Reappearance receives a new generation.

Before every durable mutation, the executor resolves all planned stable IDs against a fresh
`Trusted<Observation>` and compares the complete typed identity tuple, parent, generation,
role, size, source provenance, adapter ID/API version, observation digest, source generation,
block geometry, and topology digest. A path replacement, parent change, extent change, UUID
change, role change, size change, source change, adapter change, clone, replacement, duplicate,
or ambiguous candidate fails closed. A replacement or clone gets a new source generation and
new stable ID even when a vendor identifier is unchanged; no continuity is inferred from a
matching serial or UUID alone. Two different tuples for one stable ID produce
`AMBIGUOUS_IDENTITY` at the second stable ID path. One tuple mapped to two stable IDs produces
`AMBIGUOUS_IDENTITY`; no first match is selected.

## 8. Scope, owner authorization, and policy inputs

The plan scope `S` is closed and contains exactly `scope_schema`, `project_id`,
`repository_id`, `slice_id`, `board_id`, `board_registry_digest`, `manifest_id`,
`manifest_digest`, `schema_set_digest`, `policy_id`, `policy_digest`, `topology_digest`,
`target_account_id`, `target_account_binding`, `target_ids`, `target_identities`, and
`operations`. `target_ids` and `target_identities` are sorted by typed stable ID. Each
operation contains exactly `sequence`, `step_id`, `operation`, and `target_ids`; sequences,
step IDs, and operation values are independently closed and unique. `target_identities`
contains exactly `{object_kind, stable_id, identity_anchor_digest, object_generation,
source_identity_digest}` and is copied from the `Trusted<Observation>` topology. The exact
scope digest is:

~~~text
D_scope = sha256(ASCII("omarchy-installer-scope/v1") || 0x00 || JCS(S))
~~~

`ProjectId`, `RepositoryId`, and `SliceId` are lowercase prefixed identifiers with maximum
128 bytes. The only v1 operation values are `inspect/v1`, `write/v1`, `replace/v1`,
`remove/v1`, and `rollback/v1`; `operations` must be sorted by sequence and the target IDs
inside each operation must be sorted and unique. A missing, unknown, duplicate, or reordered
operation or target identity fails at its exact path. Scope comparison is byte equality of
the complete canonical `S`, not equality of selected digests.

The owner approval body is a closed `owner-approval/v1` payload. In addition to the common
fields it contains exactly `plan_digest`, `scope_digest`, `project_id`, `repository_id`,
`slice_id`, `board_id`, `board_registry_digest`, `manifest_id`, `manifest_digest`,
`schema_set_digest`, `policy_id`, `policy_digest`, `actor_id`, `account_id`, `actor_role`,
`approved_at`, `topology_digest`, `target_ids`, `target_identities`, `operations`,
`authorization_method`, `authorization_result`, `external_proof_digest`,
`authorization_evidence_digest`, `service_policy_id`, `service_policy_digest`, `replay_id`,
`proof_receipt_id`, `target_account_record_id`, and `target_account_binding`. `actor_role` is exactly `owner`; `authorization_result` is
exactly `success`. Every field is a projection of the verified plan scope or the two trusted
records below. The target IDs, complete target identity tuples, topology, operation set,
project/repository/slice, board, registry, manifest, policy, and schema-set values must
byte-for-byte agree with the plan scope and mutation projection.

The exact authorization grammar is:

~~~text
ActorId = "actor:" || LowerAsciiToken
AccountId = "acct:" || LowerAsciiToken
AuthorizationMethod = "webauthn/v1" | "oidc-step-up/v1" | "hardware-token/v1"
AuthorizationResult = "success" | "denied" | "expired"
ReplayId = UUID
TargetAccountBinding = sha256(ASCII("omarchy-owner-target-account/v1") || 0x00 || JCS({project_id: ProjectId, repository_id: RepositoryId, slice_id: SliceId, operation: Operation, account_id: AccountId, plan_digest: Digest, scope_digest: Digest, policy_digest: Digest, manifest_digest: Digest, topology_digest: Digest, target_identity_digests: ExactList<Digest, value>}))
ProofReceiptId = "proof:" || LowerAsciiToken
TargetAccountRecordId = "target-account:" || LowerAsciiToken
OwnerAuthorizationContext = {
  context_schema: "owner-authorization-context/v1",
  project_id: ProjectId,
  repository_id: RepositoryId,
  slice_id: SliceId,
  actor_id: ActorId,
  account_id: AccountId,
  actor_role: "owner",
  operation: Operation,
  plan_digest: Digest,
  scope_digest: Digest,
  board_id: BoardId,
  manifest_id: DocumentId,
  manifest_digest: Digest,
  schema_set_digest: Digest,
  policy_id: PolicyId,
  policy_digest: Digest,
  topology_digest: Digest,
  target_identity_digests: ExactList<Digest, value>,
  authorization_method: AuthorizationMethod,
  authorization_result: "success",
  proof_receipt_id: ProofReceiptId,
  target_account_record_id: TargetAccountRecordId,
  service_policy_id: PolicyId,
  service_policy_digest: Digest,
  issued_at: Timestamp,
  expires_at: Timestamp,
  replay_id: ReplayId,
  target_account_binding: TargetAccountBinding
}
~~~

`OwnerProofReceipt` and `TargetAccount` are closed supporting records, not authenticated
payload types:

~~~text
OwnerProofReceipt = {
  receipt_schema: "owner-proof-receipt/v1", receipt_id: ProofReceiptId,
  project_id: ProjectId, repository_id: RepositoryId, slice_id: SliceId, operation: Operation,
  actor_id: ActorId, target_account_id: AccountId, plan_digest: Digest, scope_digest: Digest,
  board_id: BoardId, manifest_id: DocumentId, manifest_digest: Digest,
  schema_set_digest: Digest, policy_id: PolicyId, policy_digest: Digest,
  topology_digest: Digest, target_identity_digests: ExactList<Digest, value>,
  authorization_method: AuthorizationMethod, authorization_result: "success",
  assertion_digest: Digest, evidence_digest: Digest, source_identity: SourceEvidence,
  valid_from: Timestamp, expires_at: Timestamp, nonce: Nonce, replay_id: ReplayId,
  receipt_digest: Digest
}
TargetAccount = {
  account_schema: "target-account/v1", record_id: TargetAccountRecordId,
  account_id: AccountId, project_id: ProjectId, repository_id: RepositoryId, slice_id: SliceId,
  allowed_operations: ExactList<Operation, value>, target_identity_digests: ExactList<Digest, value>,
  board_id: BoardId, manifest_id: DocumentId, manifest_digest: Digest,
  schema_set_digest: Digest, policy_id: PolicyId, policy_digest: Digest,
  valid_from: Timestamp, expires_at: Timestamp, nonce: Nonce, replay_id: ReplayId,
  account_binding: Digest, record_digest: Digest
}
~~~

The proof seam verifies the immutable source identity and evidence bytes behind
`OwnerProofReceipt`; an `external_proof_digest` without that trusted receipt is not proof.
The target-account seam independently verifies account ownership, allowed project,
repository, slice, closed operation set, complete target identity set, board, manifest,
schema-set, policy, validity window, nonce, and replay state. It returns
`Trusted<OwnerProofReceipt>` and `Trusted<TargetAccount>` only after exact recomputation of
`receipt_digest`, `record_digest`, `assertion_digest`, and `TargetAccountBinding`.
Missing, unverifiable, stale, expired, replayed, transplanted, or conflicting records fail
with `OWNER_PROOF_VERIFICATION_FAILURE` at the first source field; no caller-declared actor,
account, digest, or role can construct either trusted value.

No credential, assertion, password, recovery secret, bearer token, private key, or raw proof
enters the plan, approval payload, journal, log, or projection. `external_proof_digest` and
`authorization_evidence_digest` are permitted in the payload only as exact projections of
the independently trusted receipt and evidence; changing either without changing the
trusted source is a hard rejection. `verify_owner_authorization` compares exact actor,
target account, project, repository, slice, operation, plan, complete scope, policy,
topology, schema set, manifest, validity/expiry, nonce/replay, and target identities before
returning the sealed `VerifiedOwnerAuthorizationContext`. A signed owner payload is never
approval authority until both trusted supporting records exist.

The approval envelope uses `domain = "omarchy-owner-authorization"`, `context = "installer-plan-execution"`, and signer role `owner-authorization`. It is accepted only
when the verified plan digest, complete scope digest and fields, current `VerifiedClock`,
target account record, owner proof receipt, role binding, and replay state agree. Expired,
not-yet-valid, changed-plan, changed-scope, changed-topology, changed-target identity,
changed-operation, changed-project, changed-repository, changed-slice, changed-board,
changed registry/manifest/policy/schema set, or different-actor/account receipts reject as
`PLAN_SCOPE_OR_APPROVAL_FAILURE` at the first differing path. There is never a winner between
payload, proof, target account, and plan values.

`Policy` is a closed versioned, non-downgradeable F-03 input with exactly `policy_schema =
"admission-policy/v1"`, `policy_id`, `policy_version`, `policy_digest`, `required_gates`,
`forbidden_downgrades`, `issued_at`, and `expires_at`. `required_gates` is a closed object
with exactly `board_identity`, `manifest_signature`, `qualification_pass`, `artifact_digest`,
`topology_revalidation`, `owner_authorization`, `schema_set_equality`, `boot_lineage`, and
`dtb_mutation_authority`, each fixed to `true` in v1. `forbidden_downgrades` is a sorted exact
list of those nine gate names. `admit_policy(Trusted<PolicySource>, Trusted<TrustContext>,
VerifiedClock)` is the one named seam that returns `Admitted<Policy>`; no API accepts an
unsealed policy map, boolean override, or caller-supplied gate set. `admit_board` and
`validate_plan` accept `Admitted<Policy>`.

The API signatures are:

~~~text
admit_board(Trusted<Observation>, Trusted<BoardRegistry>, Trusted<PlatformManifest>, Trusted<QualificationRecord>[], Admitted<Policy>, VerifiedClock) -> AdmittedBoard | AdmissionError
validate_plan(Trusted<InstallerPlan>, Trusted<BoardRegistry>, Trusted<PlatformManifest>, Trusted<OwnerApproval>, Trusted<OwnerProofReceipt>, Trusted<TargetAccount>, Trusted<Observation>, Admitted<Policy>, VerifiedClock) -> PlanDecision
verify_owner_authorization(Trusted<OwnerApproval>, Trusted<OwnerProofReceipt>, Trusted<TargetAccount>, Trusted<TrustContext>, VerifiedClock) -> VerifiedOwnerAuthorizationContext | AuthorizationError
~~~

## 9. Boot lineage, boot context, and DTB mutation envelope

### 9.1 Boot lineage and sealed BootContext

`attempt.counter` and `source_generation` are unsigned 64-bit values from 0 through exactly 18,446,744,073,709,551,615. Counter zero means `unstarted` in the durable lineage record. A signed core representing an executed attempt has counter 1 through the maximum; a counter-zero core is permitted only for `success = false` and `fallback.decision = hold` and can never have a success marker. The first attempt atomically changes durable counter 0 to 1. If the durable counter is the maximum, the producer returns `BOOT_COUNTER_FAILURE` before incrementing and never wraps.

Source generation zero means no topology snapshot has been committed. The first committed snapshot atomically changes it to 1. A different canonical topology increments it by one only when the new snapshot and generation are durably committed together. At the maximum, a changed snapshot fails before increment and leaves the prior snapshot and generation intact.

`lineage_id` is allocated once per board, manifest, and slot-generation lineage. It is in the signed core, in the success marker, and in `Trusted<BootContext>`. The durable lineage journal is closed with exactly `journal_schema`, `lineage_id`, `board_id`, `manifest_id`, `manifest_digest`, `slot_id`, `slot_generation`, `last_counter`, `source_generation`, `record_digest`, and `commit_state`. `commit_state` is `committed` or `uncommitted`; `record_digest` covers every other field under `omarchy-boot-lineage-record/v1`. A reboot resumes the committed lineage and next counter. A rollback to another manifest or slot generation creates a new lineage ID and permanently tombstones the old tuple. Reset, reuse, lower generation, missing persistence, torn record, or wrap is `BOOT_COUNTER_FAILURE` and selects hold or recovery.

The local `BootContext` is not an additional authenticated payload type. It is a closed sealed record:

~~~text
BootContext = {
  context_schema: "boot-context/v1",
  board_id: BoardId,
  manifest_id: DocumentId,
  manifest_digest: Digest,
  lineage_id: UUID,
  slot_id: "slot-a" | "slot-b" | "recovery",
  slot_generation: uint64,
  attempt_counter: uint64,
  source_generation: uint64,
  atomic_record_digest: Digest,
  lineage_source_digest: Digest,
  provenance: {
    source_kind: "atomic-boot-journal/v1",
    source_api_version: Version,
    storage_generation: uint64
  }
}
~~~

`verify_boot_context(Trusted<AtomicBootRecord>, Trusted<TrustContext>, VerifiedClock)` is
the only constructor. It strictly accepts one complete atomically read trusted record,
verifies the authenticated lineage source, exact bytes and `bytes_digest`, checks
board/manifest/slot binding, monotonic counter, source generation, commit state, expiry,
replay reservation, and role `boot-runtime`, then returns `Trusted<BootContext>`. A partial
read, caller-created record, unchecked constructor, mutable field, local default, reset,
reuse, lower value, missing authenticated source, or failed recomputation returns
`TRUST_BOUNDARY_FAILURE` or `BOOT_COUNTER_FAILURE` with no context value.

`evaluate_boot_health` has this exact signature and no caller-controlled `BootContext` parameter:

~~~text
evaluate_boot_health(Trusted<BootHealthCore>, Trusted<BootSuccessMark> | None, Trusted<PlatformManifest>, Trusted<BootContext>, VerifiedClock) -> SlotDecision
~~~

It verifies trusted manifest context, board ID, manifest digest, profile ID/digest, slot, slot
generation, lineage ID, attempt counter, source generation, required check set, every allowed
measurement and bound, `checks_digest`, `D_core`, marker payload digest, marker signature
domain/context/role, marker generation, `marked_at` through `VerifiedClock`, marker replay
reservation, exact rollback set, and atomic-record length before evaluating success. Missing
marker means no success. Empty, extra, unknown, duplicate, unsigned, laundered, stale, or
counter-reset/wrapped checks reject. A failure returns `BOOT_MARKER_AUTH_FAILURE`,
`BOOT_CONTEXT_MISMATCH`, `BOOT_COUNTER_FAILURE`, `BOOT_REQUIRED_CHECK_FAILURE`, or
`BOOT_FALLBACK_FAILURE` as the first applicable code and selects hold or recovery.

### 9.2 boot-success-mark/v1

The marker payload has exactly `schema`, `schema_set_digest`, `document_id`, `issuer`,
`issued_at`, `expires_at`, `core_digest`, `board_id`, `manifest_id`, `manifest_digest`,
`profile_id`, `profile_digest`, `lineage_id`, `source_generation`, `slot_id`,
`slot_generation`, `attempt_counter`, `marker_generation`, `marked_at`, `checks_digest`,
`rollback_set_digest`, `marker_replay_id`, and `diagnostic_note`. `diagnostic_note` is
authenticated, bounded to 2,048 UTF-8 bytes, and never interpreted for authority. The marker
uses `domain = "omarchy-boot-runtime"` and `context = "boot-success-marker"`.

The complete canonical UTF-8 marker envelope, including payload, envelope fields, signature
entry, and no trailing newline, has an inclusive maximum of exactly 4,096 bytes. Exactly
4,096 bytes is valid; 4,097 bytes returns `RESOURCE_LIMIT`. The core and marker payload
limits are each 3,072 bytes. Maximum boot depth is 8, maximum boot object properties is 32,
maximum boot arrays are 32, and checks are capped at 32. The fixed Ed25519 signature is 64
bytes before base64url encoding. The marker’s `marker_generation` is a strictly increasing
generation in the same board/manifest/slot/lineage tuple, and `marker_replay_id` is reserved
durably before acceptance. `marked_at` must be within the verified clock window and not ahead
of `VerifiedClock.now`. Atomic replacement is required; torn, truncated, unsigned, stale,
over-bound, replayed, or context-transplanted markers are absent for success evaluation.

### 9.3 dtb-mutation-envelope/v1

`dtb-mutation-envelope/v1` is the eighth and final auxiliary payload. Its payload is closed and has exactly the common fields plus `board_identity`, `source_identity`, `platform_manifest_document_id`, `platform_manifest_payload_digest`, `pre_mutation_dtb_digest`, `post_mutation_dtb_digest`, `policy_identity`, `tool_identity`, `artifact_identity`, `firmware_bundle_identity`, `dt_schema_identity`, `authorized_mutations`, `signer_authority`, `nonce`, and `replay_identity`. The common `issued_at` and `expires_at` fields occur once; the repeated names in this sentence describe the complete required set and are not duplicate wire properties.

The exact records are:

~~~text
BoardIdentity = {
  project_id: ProjectId,
  repository_id: RepositoryId,
  slice_id: SliceId,
  board_id: BoardId,
  board_registry_digest: Digest,
  identity_observation_digest: Digest,
  macos_predicate_digest: Digest,
  linux_predicate_digest: Digest,
  soc_id: SocId
}
SourceIdentity = {
  source_kind: "linux-device-tree/v1" | "macos-platform-registry/v1",
  source_adapter_id: LowerAsciiToken,
  source_api_version: Version,
  source_generation: uint64,
  source_observation_digest: Digest,
  source_identity_tuple_digest: Digest,
  source_bytes_digest: Digest,
  source_evidence_digest: Digest
}
PolicyIdentity = {
  policy_id: PolicyId,
  policy_version: Version,
  policy_digest: Digest
}
ToolIdentity = {
  tool_id: LowerAsciiToken,
  tool_version: Version,
  tool_digest: Digest
}
ArtifactIdentity = {
  artifact_id: ArtifactId,
  artifact_version: Version,
  artifact_digest: Digest
}
FirmwareBundleIdentity = {
  bundle_id: LowerAsciiToken,
  bundle_version: Version,
  bundle_digest: Digest,
  firmware_schema_id: LowerAsciiToken,
  firmware_schema_digest: Digest
}
DtSchemaIdentity = {
  schema_id: LowerAsciiToken,
  schema_version: Version,
  schema_digest: Digest
}
Nonce = base64url with decoded length from 16 through 32 bytes
AuthorizedMutation = {
  sequence: uint16,
  mutation_id: LowerAsciiToken,
  property_path: DtbPropertyPath,
  operation: "add" | "replace" | "remove",
  before_value_digest: Digest,
  after_value_digest: Digest,
  authorization_rule_id: LowerAsciiToken,
  before_preimage_digest: Digest,
  after_preimage_digest: Digest
}
SignerAuthority = {
  key_id: KeyId,
  signer_role: "dtb-authority",
  authority_binding_digest: Digest
}
ReplayIdentity = {
  replay_id: UUID,
  replay_domain: "omarchy-dtb-mutation/v1",
  issued_nonce_digest: sha256(ASCII("omarchy-dtb-nonce/v1") || 0x00 || Nonce)
}
ReplayReservation = {
  reservation_schema: "atomic-replay-reservation/v1", replay_domain: LowerAsciiToken,
  replay_id: UUID, nonce_digest: Digest, tuple_digest: Digest,
  state: "reserved" | "committed", created_at: Timestamp, record_digest: Digest
}
reservation_key = sha256(ASCII("omarchy-replay-key/v1") || 0x00 || JCS({replay_domain, replay_id, nonce_digest, tuple_digest}))
DtbMutationPolicy = {
  policy_schema: "dtb-mutation-policy/v1", board_id: BoardId,
  manifest_digest: Digest, policy_id: PolicyId, policy_digest: Digest,
  tool_id: LowerAsciiToken, tool_version: Version, tool_digest: Digest,
  dtb_artifact_id: ArtifactId, dtb_artifact_digest: Digest,
  firmware_bundle_id: LowerAsciiToken, firmware_bundle_digest: Digest,
  dt_schema_id: LowerAsciiToken, dt_schema_digest: Digest,
  source_generation: Generation, rules: ExactList<DtbMutationRule, authorization_rule_id>,
  policy_record_digest: Digest
}
DtbMutationRule = {authorization_rule_id: LowerAsciiToken, property_path: DtbPropertyPath,
                   operation: "add" | "replace" | "remove", allowed: true}
DtbPropertyPath = "/" node_segment "/" property_segment, max 256 ASCII bytes
node_segment = [a-z0-9][a-z0-9,._@+-]{0,63}
property_segment = [a-z][a-z0-9,._+-]{0,63}
DtbValue = closed JSON scalar, array, or object limited to 16 depth, 64 properties, 256 bytes;
           object keys are lowercase ASCII DT property names, sorted and unique
value_digest(v) = sha256(ASCII("omarchy-dtb-value/v1") || 0x00 || JCS(v))
absent_digest = sha256(ASCII("omarchy-dtb-absent/v1") || 0x00)
before_preimage(add) = absent_digest
after_preimage(remove) = absent_digest
before_preimage(replace) = value_digest(current_value)
after_preimage(add | replace) = value_digest(new_value)
pre_mutation_dtb_digest = sha256(ASCII("omarchy-dtb-pre/v1") || 0x00 || source_dtb_bytes)
post_mutation_dtb_digest = sha256(ASCII("omarchy-dtb-post/v1") || 0x00 || post_mutation_dtb_bytes)
~~~

`board_identity` is complete because it binds project, repository, slice, board ID, registry
digest, both source predicate digests, the identity observation digest, and the diagnostic
SoC ID. `source_identity` is complete because it binds source kind, adapter, API version,
source generation, observation bytes, source bytes, source evidence, and normalized identity
tuple. `DtbPropertyPath` is a normalized two-segment RFC 6901 pointer: the first segment is
an existing DT node and the second is an existing or policy-allowed property; `~0` and `~1`
are the only escapes, and empty segments, URI fragments, array indices, wildcards, prefixes,
regular expressions, `..`, backslashes, and paths outside the DT property tree reject at the
first path segment. `authorized_mutations` is a non-empty list of contiguous sequences 1
through its length, with unique mutation IDs and exact semantic keys `(sequence, mutation_id,
property_path, operation)`. `before_value_digest` and `after_value_digest` are recomputed
from the canonical source/post values. An `add` requires `before_value_digest = absent_digest`
and a real after value; a `replace` requires two real value digests; a `remove` requires a
real before value and `after_value_digest = absent_digest`. The corresponding
`before_preimage_digest` and `after_preimage_digest` must equal the formulas above. No
mutation is implied by a wildcard, prefix, regular expression, or free-form command.

The envelope is authenticated with the common preimage, `domain = "omarchy-dtb-authority"`,
`context = "dtb-mutation-authorization"`, signer role `dtb-authority`, and the exact
`authority_binding_digest`. Its producer is fail-closed: it accepts only a
`Trusted<PlatformManifest>`, a `Trusted<BootContext>`, an `Admitted<Policy>`, a
`Trusted<VerifiedDtbInputs>`, a lock-pinned tool and artifact, a verified firmware bundle,
and a verified DT schema. It performs mutation-policy lookup on the exact tuple
`(board_id, manifest_digest, policy_digest, tool_digest, dtb_artifact_digest,
firmware_bundle_digest, dt_schema_digest, source_generation)` at the manifest paths
`$.payload.components.dtb_set.policy_inputs`,
`$.payload.components.dtb_set.toolchain_lock.entries`,
`$.payload.components.dtb_set.artifacts`,
`$.payload.components.firmware_bundle.artifacts`, and
`$.payload.components.dtb_set.dt_schema`. It recomputes every source, artifact, rule,
preimage, and post-byte digest, emits no envelope on missing, stale, expired, mismatched, or
unverified input, and never invents a mutation.

Its consumer validates in this order: P0 through P3; expiry and persistent replay reservation;
board/project/repository/slice and source identity; manifest document ID and payload digest;
policy, tool, DTB artifact, firmware, and DT schema identities; exact source generation;
then each mutation’s path grammar, policy rule lookup, sequence, semantic key, operation,
before/after sentinel, preimage, and authorization; then direct recomputation of source DTB
bytes, every intermediate mutation result, post DTB bytes, `pre_mutation_dtb_digest`, and
`post_mutation_dtb_digest`. An unknown, missing, unauthorized, duplicate, or out-of-order
mutation fails `UNKNOWN_MUTATION` at the mutation path. A replayed nonce or replay ID fails
`EXPIRY_OR_REPLAY_FAILURE` before mutation. A cross-board, cross-project, cross-manifest,
cross-policy, cross-tool, cross-artifact, cross-firmware, wrong-schema, wrong-source,
wrong-before, wrong-after, source-digest, or post-digest mismatch fails closed with
`DTB_INPUT_VERIFICATION_FAILURE` or `CROSS_DOCUMENT_MISMATCH` at the first differing path.
The consumer performs no mutation unless every check passes, the atomic replay reservation
is durable, and the source/post result is atomically committed. A reservation conflict or
crash recovery re-reads the durable reservation and postcondition; it never retries by
guessing or silently applies the mutation twice.

## 10. Sorted collections and semantic uniqueness

Every set or ordered semantic collection declares one key. Producers emit the required order; validators reject wrong order and duplicate keys. The complete v1 collection table is:

| Collection | Order and uniqueness key |
| --- | --- |
| signatures | `(key_id, signer_role, algorithm, signature_format)` |
| source compatible lists | source order and unique exact string |
| registry boards | `board_id` |
| capability entries | `capability_id` |
| qualification check IDs | `check_id` |
| manifest board targets | `board_id` |
| components | `component_id` and exact path mapping |
| component config inputs | `input_id` |
| component policy inputs | `policy_id` |
| component patch entries | `patch_id` |
| component toolchain entries | `toolchain_id` |
| component report entries | `report_id` |
| component artifacts | `artifact_id` |
| artifacts | `artifact_id` |
| package records | `(package_name, architecture)` |
| component relations | `(left_component_id, relation, right_component_id)` |
| rollback manifest IDs | `manifest_id` |
| qualification bindings | `board_id` |
| plan target references | `(object_kind, stable_id)` |
| plan mutations | `sequence` and independently `step_id` |
| mutation target references | `(object_kind, stable_id)` |
| mutation preconditions | `predicate_id` |
| topology objects | `(object_kind, stable_id)` |
| physical extents | `(start_lba, length_lba)` |
| qualification test results | `test_id` |
| test evidence IDs | `evidence_id` |
| measurements | `(criterion_id, name)` |
| residuals | `residual_id` |
| evidence entries | `evidence_id` |
| boot checks | `check_id` |
| schema entries | `(schema_id, schema_version)` |
| required payload types | `payload_type` |
| supported payload types | `payload_type` |
| consumer supported entries | `(schema_set_digest, payload_type, consumer_api)` |
| scope target IDs | typed `stable_id` |
| scope operations | `sequence` and independently `step_id` |
| scope operation target IDs | typed `stable_id` |
| approval target IDs | typed `stable_id` |
| approval operations | `sequence` and independently `step_id` |
| rollback boundaries | `sequence` |
| recovery requirements | `requirement_id` |
| authorized DTB mutations | `sequence` and independently `mutation_id` |
| authority bindings | `(role, actor_id, account_id)` |

The table is exhaustive for every collection in the eleven schemas and supporting trusted
records. In addition, `manifest.artifacts`, `manifest.package_set`, `manifest.compatibility`,
`manifest.firmware_schema`, and `manifest.rollback` are checked as exact projections: the
validator computes the sorted union from the authoritative component paths and compares
length, key, order, and every closed field. `target_identities`, boot check measurements,
DTB mutation semantic keys, proof target identities, and document-lineage IDs are likewise
sorted or exact-ordered as their grammar states. A missing key, unknown member, duplicate,
conflicting duplicate, out-of-order member, or second map representation returns the
declared code at the second or first differing JSON path; no collection is deduplicated or
implicitly sorted.

The second identical member fails `DUPLICATE_SEMANTIC_KEY` at its JSON path. A different tuple or parent for an already-used stable ID fails `AMBIGUOUS_IDENTITY` at its second `stable_id` path. These rules apply before any cross-document comparison.

## 11. Exact set negotiation and ConsumerCapabilities

The manifest’s `consumer_schema_set` is closed with exactly `schema_set_digest`,
`required_payload_types`, `supported_payload_types`, `required_bindings`, and
`required_artifacts`. Both payload arrays must equal the exact eight-value set in section 1,
with no missing, duplicate, or extra value and the declared `payload_type` order. The
manifest-required binding and artifact lists are:

~~~text
ManifestConsumerBinding = {
  language: "python" | "swift" | "rust-boot", api_id: LowerAsciiToken,
  minimum_api: ApiVersion, binding_id: LowerAsciiToken, binding_version: Version,
  binding_source_digest: Digest, parser_id: LowerAsciiToken, parser_version: Version,
  parser_source_digest: Digest, generated_artifact_id: ArtifactId,
  generated_output_path: RelativeBindingPath, generated_output_digest: Digest
}
ManifestConsumerArtifact = {language: "python" | "swift" | "rust-boot",
                             artifact_id: ArtifactId, output_path: RelativeBindingPath,
                             output_digest: Digest, boot_required: boolean}
~~~

`required_bindings` is exactly one entry for each of Python, Swift, and Rust boot, sorted by
language; `required_artifacts` contains the matching generated outputs and exactly one
`boot_required = true` Rust boot binding. A manifest-required set and consumer-supported set
are not compatible if their set equality fails, even if their schema-set digest is equal.
Missing, extra, duplicate, conflicting, reordered, or mismatched binding/artifact entries
fail `BINDING_INTEGRITY_FAILURE` at the first differing path.

The closed `ConsumerCapabilities` input is:

~~~text
ConsumerCapabilities = {
  capabilities_schema: "consumer-capabilities/v1",
  consumer_id: LowerAsciiToken,
  language: "python" | "swift" | "rust-boot",
  consumer_api: {major: uint16, minor: uint16, patch: uint16},
  api_id: LowerAsciiToken,
  schema_set_digest: Digest,
  generated_binding_identity: {
    binding_id: LowerAsciiToken,
    binding_version: Version,
    binding_source_digest: Digest,
    parser_id: LowerAsciiToken,
    parser_version: Version,
    parser_source_digest: Digest,
    api_id: LowerAsciiToken,
    api_version: Version,
    api_source_digest: Digest
  },
  supported_payload_types: ExactList<PayloadType, payload_type>,
  compiled_lock_digest: Digest,
  generated_artifact_id: ArtifactId,
  generated_output_path: RelativeBindingPath,
  generated_output_digest: Digest,
  boot_artifact_id: ArtifactId | null,
  boot_artifact_digest: Digest | null
}
~~~

The only constructor is `load_consumer_capabilities(Trusted<CompiledLock>,
Trusted<GeneratedOutputLock>, Trusted<GeneratedBindingMetadata>)`. It verifies that the
output lock’s schema-set digest, language, binding/parser/API/toolchain identities,
generated artifact ID/path/digest, compiled-lock preimage, and exact eight-value supported
set agree. No public parser or caller-controlled constructor exists. `minimum_consumer_api`
in a manifest is exactly `{major: uint16, minor: uint16, patch: uint16}` and is compared
using total lexicographic numeric ordering `(major, minor, patch)`; a consumer satisfies it
if its tuple is greater than or equal to the required tuple. Missing, overflow, prerelease,
malformed, lower, or string-compared versions reject before release or plan admission.

Negotiation is:

~~~text
negotiate(required, capabilities) succeeds iff
  required.schema_set_digest == capabilities.schema_set_digest
  AND required.required_payload_types == capabilities.supported_payload_types
  AND required.required_bindings contains the exact capabilities binding for its language
  AND required.required_artifacts contains the exact capabilities output and digest
  AND each collection has no duplicate and the declared order is exact
  AND capabilities.generated_binding_identity matches generated-output.lock
  AND capabilities.consumer_api >= required.minimum_consumer_api by total tuple ordering
  AND (capabilities.language != "rust-boot" OR required boot artifact ID/digest matches)
~~~

There is no missing-type default, extra-type ignore, duplicate collapse, mixed-lock selection,
API string comparison, parser substitution, output-path substitution, boot-binding
substitution, downgrade, or older-lock fallback. Negotiation either selects the exact
manifest-required binding and artifact digest or rejects; a separately signed manifest may
name an exact previous set only in a future schema version, never by v1 fallback. The v1
required and supported sets remain the eight-value set. `ConsumerCapabilities` cannot claim
equality with a manifest unless language, API, output, boot artifact, parser, generator,
schema-set, and every required digest are equal.

## 12. Privacy, projections, evidence access, and errors

The schema registry classifies every field as one of five closed classes: A public contract, B restricted operational identifier, C private identifier, D secret/auth material, or E evidence bytes. A field not assigned one of these classes is a schema error. Classification is path-specific and inherited only where the registry explicitly lists the path.

The normative privacy registry is closed and covers the newly bound fields as follows:

| Path family | Class | Projection rule |
| --- | --- | --- |
| `$.payload.schema`, `schema_set_digest`, `document_id`, timestamps, public board/manifest/channel/version fields | A | public only after trusted verification |
| `$.payload.project_id`, `repository_id`, `slice_id`, policy IDs/digests, artifact IDs/digests, check IDs, operation and status | B | public only where the named projection allowlists the field |
| `$.payload.actor_id`, `account_id`, target account binding, stable IDs, source adapter/observation/generation, lab/operator IDs, serial/location/model tokens | C | omitted or field-path HMAC pseudonym only |
| signatures, key IDs, proof bytes/digests, credentials, private keys, bearer assertions | D | never projected or logged |
| evidence bytes, raw DTB bytes, raw source records, raw command output | E | evidence-authorized projection contains digest and receipt metadata only |

Every `OwnerProofReceipt`, `TargetAccount`, `Observation`, `AtomicBootRecord`, and
`VerifiedDtbInputs` path is explicitly assigned by this table or its closed record grammar;
an unclassified new path fails schema generation. Projection code accepts only
`Trusted<T>` plus `Trusted<ProjectionPolicy>` and `VerifiedClock`, applies the exact
allowlist, and recomputes `projection_digest`; it cannot promote a private field to public
by configuration. Error paths and messages contain no values from classes C, D, or E.

The public projection `public/v1` is closed and allowlists exactly: `schema`, `schema_set_digest`, `document_id`, `issued_at`, `expires_at`, `board_id`, `manifest_id`, `manifest_digest`, `channel`, `release_version`, `lifecycle`, `capability_id`, `support_requirement`, `content_digest`, `outcome`, `failure_code`, `projection_version`, and `projection_digest`. `issuer` is transformed to its public authority ID. `actor_id`, `account_id`, all stable storage IDs, lab asset IDs, source field names, serial tokens, physical-location tokens, raw paths, raw evidence, credentials, proofs, private keys, and bearer assertions are omitted. `soc_id` is omitted from public output. Arrays are re-keyed only by the declared public key and preserve their verified order.

The private-support projection `private-support/v1` is closed and contains every public field plus pseudonymized actor, account, storage, lab, source, and evidence references. Its allowlist is exactly `public/v1` plus `actor_token`, `account_token`, `storage_token`, `lab_token`, `source_token`, and `evidence_token`. Raw source, serial, location, path, credential, proof, and evidence bytes remain omitted. The evidence projection `evidence-authorized/v1` is closed and contains exactly `evidence_id`, `expected_content_digest`, `media_type`, `privacy_class`, `purpose`, `request_id`, `expires_at`, `bytes_digest`, `read_receipt_id`, and `projection_version`; it never embeds evidence bytes in a signed payload.

Each projection is generated only from a verified trusted value and a closed `ProjectionPolicy`:

~~~text
ProjectionPolicy = {
  policy_schema: "projection-policy/v1",
  policy_id: PolicyId,
  policy_version: Version,
  policy_digest: Digest,
  public_projection_id: "public/v1",
  private_projection_id: "private-support/v1",
  evidence_projection_id: "evidence-authorized/v1",
  hmac_key_domain: "omarchy-projection-pseudonym/v1",
  hmac_key_version: uint16,
  max_error_bytes: uint16,
  issued_at: Timestamp,
  expires_at: Timestamp
}
~~~

`ProjectionPolicy` is closed, versioned, and non-authoritative. It can select only the three named projections and the exact key version; it cannot authorize a board, release, boot, DTB mutation, owner approval, or storage mutation. `project_public`, `project_private_support`, and `project_evidence_authorized` reject an unknown policy version, expired policy, unknown path, or output over the policy bound.

Pseudonyms use exactly:

~~~text
HMAC_input = ASCII("omarchy-public-pseudonym/v1") || 0x00 || UTF8(field_path) || 0x00 || UTF8(normalized_private_value)
token = "pseudonym:v1:" || decimal(hmac_key_version) || ":" || base64url(HMAC-SHA256(K[hmac_key_domain, hmac_key_version], HMAC_input))
~~~

The key is supplied by the projection service and never enters a document. With one key version, the same field path and normalized private value produce the same token. Rotation switches all new output to the new version; old tokens are not reissued under the new version, and a revoked version cannot produce new output. No bare serial hash is permitted.

Evidence access uses closed, non-payload local records:

~~~text
EvidenceReadRequest = {
  request_schema: "evidence-read-request/v1",
  request_id: UUID,
  requester_actor_id: ActorId,
  requester_account_id: AccountId,
  evidence_id: LowerAsciiToken,
  expected_content_digest: Digest,
  privacy_class: "public" | "restricted" | "private" | "secret",
  purpose: "qualification-review" | "incident-review" | "release-audit",
  requested_at: Timestamp,
  expires_at: Timestamp
}
EvidenceReadAuthorization = {
  authorization_schema: "evidence-read-authorization/v1",
  request_id: UUID,
  decision: "allow" | "deny",
  reader_binding_digest: Digest,
  service_policy_id: PolicyId,
  service_policy_digest: Digest,
  issued_at: Timestamp,
  expires_at: Timestamp,
  replay_id: UUID
}
~~~

These local records are not members of the eight authenticated payload types and cannot be passed to the common payload verifier as a new type. An evidence reader must hold `Trusted<EvidenceReadAuthorization>` with role `evidence-reader`, exact request and account binding, current time, and replay state. The store verifies returned bytes against `expected_content_digest` before returning a read receipt.

The closed redacted error is exactly `{error_schema: "redacted-error/v1", ok: false,
decision: "reject" | "hold", code: FailureCode, path: JsonPath, message: ErrorMessage}`.
`JsonPath` uses the grammar in section 2, is at most 512 ASCII bytes, and is the exact
first-affected path recorded in the fixture catalog. `ErrorMessage` is one of the fixed
templates keyed by `code`, at most 256 ASCII bytes, and contains no input value. No error
includes passwords, tokens, raw command output, signatures, serials, paths, evidence bytes,
or private identifiers. `decision = "hold"` is allowed only for the six explicitly listed
boot/trust codes in the section 13 HOLD set; all other failures use `reject`.

## 13. Failure codes and APIs

Failure codes are unique normative strings; numeric display values are non-authoritative and
are not assigned. A code has exactly one JSON path family, phase, and decision below. A
duplicate code row, two meanings for one code, an unknown code, or an unknown hold-eligible
code is a schema/CI failure, not a runtime default.

| Code | Canonical path family | Phase | Decision |
| --- | --- | --- | --- |
| `ACCEPT` | `$` | P6 | allow |
| `PARSE_SCHEMA_FAILURE` | first malformed field or `$` | P0/P1 | reject |
| `UNKNOWN_FIELD` | unknown property | P1 | reject |
| `DUPLICATE_SEMANTIC_KEY` | second object name or collection key | P0/P1 | reject |
| `CANONICALIZATION_FAILURE` | `$` or first non-canonical scalar | P2 | reject |
| `SIGNATURE_CONTEXT_MISMATCH` | `$.payload_type`, `$.domain`, `$.context`, or `$.signatures[i]` | P3 | reject |
| `SIGNATURE_DOMAIN_BOARD_REGISTRY` | `$.domain` | P3 | reject |
| `SIGNATURE_CONTEXT_PLATFORM_MANIFEST` | `$.context` | P3 | reject |
| `SIGNATURE_ROLE_INSTALLER_PLAN` | `$.signatures[i].signer_role` | P3 | reject |
| `SIGNATURE_DOMAIN_QUALIFICATION` | `$.domain` | P3 | reject |
| `SIGNATURE_ROLE_BOOT_HEALTH` | `$.signatures[i].signer_role` | P3 | reject |
| `SIGNATURE_CONTEXT_OWNER_APPROVAL` | `$.context` | P3 | reject |
| `SIGNATURE_ROLE_BOOT_MARK` | `$.signatures[i].signer_role` | P3 | reject |
| `SIGNATURE_CONTEXT_DTB_ENVELOPE` | `$.context` | P3 | reject |
| `TRUST_FAILURE` | first authority/key/proof field | P3 | reject |
| `TRUST_BOUNDARY_FAILURE` | `$` or first untrusted local record field | P6 | hold |
| `EXPIRY_OR_REPLAY_FAILURE` | `$.payload.expires_at`, `$.replay_id`, or source replay path | P3/P6 | reject |
| `OWNER_EXPIRY_FAILURE` | `$.payload.expires_at` | P3 | reject |
| `DTB_EXPIRY_FAILURE` | `$.payload.expires_at` | P3 | reject |
| `REGISTRY_EXPIRY_FAILURE` | `$.payload.expires_at` | P3 | reject |
| `MANIFEST_EXPIRY_FAILURE` | `$.payload.expires_at` | P3 | reject |
| `QUALIFICATION_EXPIRY_FAILURE` | `$.payload.expires_at` | P3 | reject |
| `CROSS_DOCUMENT_MISMATCH` | first unequal bound field | P5 | reject |
| `IDENTITY_INCOMPLETE` | missing/invalid identity or capacity field | P4 | reject |
| `AMBIGUOUS_IDENTITY` | second stable ID or identity tuple path | P4 | reject |
| `PLAN_SCOPE_OR_APPROVAL_FAILURE` | first project/scope/account/approval field | P6 | reject |
| `PLAN_DIGEST_CYCLE` | `$.payload.plan_digest` | P2 | reject |
| `UNKNOWN_MUTATION` | `$.payload.authorized_mutations[i]` | P5 | reject |
| `MANIFEST_AUTHORITY_CONFLICT` | first differing manifest projection path | P5 | reject |
| `OWNER_PROOF_VERIFICATION_FAILURE` | first owner proof/target-account source path | P3/P6 | reject |
| `CAPABILITY_BOUNDARY_FAILURE` | `$.capabilities` | P6 | reject |
| `DTB_INPUT_BOUNDARY_FAILURE` | `$.dtb_inputs` | P6 | reject |
| `DOCUMENT_ID_REUSE` | `$.payload.document_id` | P3/P5 | reject |
| `DOCUMENT_ID_FORK` | document lineage record path | P5 | reject |
| `DTB_INPUT_VERIFICATION_FAILURE` | first DTB source/identity/preimage path | P4/P5 | reject |
| `BOOT_MARKER_AUTH_FAILURE` | `$.signatures[i]` or marker replay path | P3/P6 | hold |
| `BOOT_CONTEXT_MISMATCH` | first core/marker/context field | P5 | hold |
| `BOOT_COUNTER_FAILURE` | counter/generation/atomic record path | P4/P6 | hold |
| `BOOT_REQUIRED_CHECK_FAILURE` | check/profile/measurement path | P5 | hold |
| `BOOT_FALLBACK_FAILURE` | fallback or rollback-set path | P5/P6 | hold |
| `BOOT_DIGEST_CYCLE` | forbidden core/marker digest field | P2 | reject |
| `BOOT_MARKER_DIGEST_CYCLE` | `$.payload.canonical_payload_digest` | P2 | reject |
| `BINDING_INTEGRITY_FAILURE` | lock/binding/artifact/API path | P1/P5/P6 | reject |
| `RESOURCE_LIMIT` | first over-bound byte/depth/count/number path | P0/P1 | reject |
| `CLI_USAGE_OR_INTERNAL_FAILURE` | `$` | P0/P6 | reject |

The complete boot HOLD code set is exactly
`BOOT_MARKER_AUTH_FAILURE`, `BOOT_CONTEXT_MISMATCH`, `BOOT_COUNTER_FAILURE`,
`BOOT_REQUIRED_CHECK_FAILURE`, `BOOT_FALLBACK_FAILURE`, and `TRUST_BOUNDARY_FAILURE`.
`BOOT_DIGEST_CYCLE`, `EXPIRY_OR_REPLAY_FAILURE`, `CROSS_DOCUMENT_MISMATCH`, and every
other code are reject decisions even when encountered by a boot consumer. A failure code
may not be omitted, renamed, or reclassified by a producer.

The core API surface is:

~~~text
parse(type: PayloadType, bytes: Bytes) -> Parsed<T> | ParseError
canonical_bytes(Parsed<T>) -> Bytes | CanonicalizationError
payload_digest(Parsed<T>) -> Digest | CanonicalizationError
verify(Canonical<T>, Trusted<TrustContext>, VerifiedClock, ExpectedContext) -> Trusted<T> | TrustError
admit_policy(Trusted<PolicySource>, Trusted<TrustContext>, VerifiedClock) -> Admitted<Policy> | PolicyError
admit_board(Trusted<Observation>, Trusted<BoardRegistry>, Trusted<PlatformManifest>, Trusted<QualificationRecord>[], Admitted<Policy>, VerifiedClock) -> AdmittedBoard | AdmissionError
validate_plan(Trusted<InstallerPlan>, Trusted<BoardRegistry>, Trusted<PlatformManifest>, Trusted<OwnerApproval>, Trusted<OwnerProofReceipt>, Trusted<TargetAccount>, Trusted<Observation>, Admitted<Policy>, VerifiedClock) -> PlanDecision
verify_owner_authorization(Trusted<OwnerApproval>, Trusted<OwnerProofReceipt>, Trusted<TargetAccount>, Trusted<TrustContext>, VerifiedClock) -> VerifiedOwnerAuthorizationContext | AuthorizationError
verify_boot_context(Trusted<AtomicBootRecord>, Trusted<TrustContext>, VerifiedClock) -> Trusted<BootContext> | TrustBoundaryError
evaluate_boot_health(Trusted<BootHealthCore>, Trusted<BootSuccessMark> | None, Trusted<PlatformManifest>, Trusted<BootContext>, VerifiedClock) -> SlotDecision
verify_dtb_inputs(Trusted<PlatformManifest>, Trusted<BootContext>, Admitted<Policy>, Trusted<SourceEvidence>, VerifiedClock) -> Trusted<VerifiedDtbInputs> | DtbError
produce_dtb_mutation_envelope(Trusted<PlatformManifest>, Trusted<BootContext>, Admitted<Policy>, Trusted<VerifiedDtbInputs>, VerifiedClock) -> Trusted<DtbMutationEnvelope> | DtbError
consume_dtb_mutation_envelope(Trusted<DtbMutationEnvelope>, Trusted<VerifiedDtbInputs>, Admitted<Policy>, VerifiedClock) -> DtbMutationDecision
load_consumer_capabilities(Trusted<CompiledLock>, Trusted<GeneratedOutputLock>, Trusted<GeneratedBindingMetadata>) -> ConsumerCapabilities | CapabilityError
project_public(Trusted<T>, Trusted<ProjectionPolicy>, VerifiedClock) -> PublicProjection | ProjectionError
~~~

No trust API accepts parsed data, a public projection, caller-controlled policy, caller-controlled
boot context, raw stable ID, raw topology, raw observation, raw clock, raw atomic record, raw
DTB input, raw proof, raw target account, or unsigned local record. The public projection is
never accepted by an authority API. The executor receives only an admitted plan, a
`Trusted<Observation>`, and revalidated typed identities.

## 14. Mandatory hostile and boundary fixtures

Every fixture has one canonical input and exactly one mutation. The path is the first field affected by that mutation, and the phase is the first phase in section 2 that can observe it. `ACCEPT` is code 0 and pins a boundary. The table is the mandatory minimum; every row is required even when the same code occurs elsewhere.

| Blocker | Fixture | Single mutation | Expected code | Exact path | Phase |
| --- | --- | --- | --- | --- | --- |
| B1 | `payload-vocabulary-accepted-eight` | replace the accepted set with the exact eight values and no ninth value | `ACCEPT` | `$.payload_type` | P1 |
| B1 | `payload-vocabulary-missing-dtb` | remove `dtb-mutation-envelope/v1` from supported types | `CROSS_DOCUMENT_MISMATCH` | `$.payload.supported_payload_types` | P5 |
| B1 | `payload-vocabulary-extra-type` | append a ninth owner-specific value to supported types | `UNKNOWN_FIELD` | `$.payload.supported_payload_types[8]` | P1 |
| B1 | `payload-vocabulary-duplicate-type` | repeat `boot-health/v1` in supported types | `DUPLICATE_SEMANTIC_KEY` | `$.payload.supported_payload_types[7]` | P1 |
| B1 | `payload-schema-id-mismatch` | change payload `schema` from `dtb-mutation-envelope/v1` to `owner-approval/v1` | `PARSE_SCHEMA_FAILURE` | `$.payload.schema` | P1 |
| B1 | `component-path-alias` | rename `components.linux_kernel` to `components.kernel` | `UNKNOWN_FIELD` | `$.payload.components.kernel` | P1 |
| B2 | `parsed-boot-context-input` | pass `Parsed<BootHealth>` in the BootContext parameter | `TRUST_BOUNDARY_FAILURE` | `$.boot_context` | P6 |
| B2 | `caller-constructed-boot-context` | call the public BootContext constructor with a changed manifest digest | `TRUST_BOUNDARY_FAILURE` | `$.manifest_digest` | P6 |
| B2 | `downgraded-policy-gate` | set `required_gates.owner_authorization` to false | `TRUST_BOUNDARY_FAILURE` | `$.required_gates.owner_authorization` | P6 |
| B2 | `open-projection-policy` | add `allow_unknown_fields` to ProjectionPolicy | `UNKNOWN_FIELD` | `$.allow_unknown_fields` | P1 |
| B3 | `schema-input-lock-contains-output` | add `output_digest` to schema-input.lock | `UNKNOWN_FIELD` | `$.output_digest` | P1 |
| B3 | `output-lock-missing-schema-digest` | remove `schema_set_digest` from generated-output.lock | `PARSE_SCHEMA_FAILURE` | `$.schema_set_digest` | P1 |
| B3 | `lock-cycle-back-edge` | add generated-output.lock digest to schema-input.lock | `UNKNOWN_FIELD` | `$.generated_output_lock_digest` | P1 |
| B4 | `disk-identity-missing-guid` | remove `gpt_disk_guid` from I_disk | `IDENTITY_INCOMPLETE` | `$.gpt_disk_guid` | P4 |
| B4 | `disk-identity-empty-serial` | replace serial_token with an empty string | `IDENTITY_INCOMPLETE` | `$.serial_token` | P4 |
| B4 | `partition-parent-outside-topology` | replace partition parent_stable_id with an absent disk ID | `AMBIGUOUS_IDENTITY` | `$.parent_stable_id` | P4 |
| B4 | `topology-raw-path` | add `path` to a topology object | `UNKNOWN_FIELD` | `$.objects[0].path` | P1 |
| B4 | `topology-stable-id-collision` | give the second object the first stable ID and a different parent | `AMBIGUOUS_IDENTITY` | `$.objects[1].stable_id` | P4 |
| B4 | `topology-duplicate-object` | duplicate the first object without changing its tuple | `DUPLICATE_SEMANTIC_KEY` | `$.objects[1].stable_id` | P1 |
| B5 | `duplicate-root-json-name` | repeat the root `payload` JSON name | `DUPLICATE_SEMANTIC_KEY` | `$.payload` | P0 |
| B5 | `duplicate-nested-json-name` | repeat `board_id` in the nested board object | `DUPLICATE_SEMANTIC_KEY` | `$.payload.board_id` | P0 |
| B5 | `unknown-nested-field` | add `unexpected` under a storage object | `UNKNOWN_FIELD` | `$.payload.inventory.storage.objects[0].unexpected` | P1 |
| B5 | `duplicate-board-id` | set `boards[1].board_id` equal to `boards[0].board_id` | `DUPLICATE_SEMANTIC_KEY` | `$.payload.boards[1].board_id` | P1 |
| B5 | `duplicate-nested-test-id` | set `test_results[1].test_id` equal to `test_results[0].test_id` | `DUPLICATE_SEMANTIC_KEY` | `$.payload.test_results[1].test_id` | P1 |
| B5 | `stable-id-different-normalized-tuple` | reuse a stable ID with a changed UUID | `AMBIGUOUS_IDENTITY` | `$.payload.inventory.storage.objects[1].stable_id` | P4 |
| B5 | `invalid-utf8` | replace one payload byte with an invalid UTF-8 continuation byte | `PARSE_SCHEMA_FAILURE` | `$.transport.utf8` | P0 |
| B5 | `utf8-bom` | prepend a UTF-8 BOM | `PARSE_SCHEMA_FAILURE` | `$.transport.bom` | P0 |
| B5 | `control-character` | insert U+0001 into `owner_summary` | `PARSE_SCHEMA_FAILURE` | `$.payload.mutations[0].owner_summary` | P0 |
| B5 | `numeric-overflow` | set `minimum_consumer_api.major` to 65,536 | `RESOURCE_LIMIT` | `$.payload.minimum_consumer_api.major` | P1 |
| B5 | `unknown-enum` | set `slot.slot_id` to `slot-c` | `PARSE_SCHEMA_FAILURE` | `$.payload.slot.slot_id` | P1 |
| B5 | `unsorted-board-list` | swap `boards[0]` and `boards[1]` | `PARSE_SCHEMA_FAILURE` | `$.payload.boards[1].board_id` | P1 |
| B5 | `malformed-api` | set `minimum_consumer_api` to `1.2` | `PARSE_SCHEMA_FAILURE` | `$.payload.minimum_consumer_api` | P1 |
| B6 | `owner-actor-grammar` | replace actor_id with `actor:UPPER` | `PARSE_SCHEMA_FAILURE` | `$.payload.actor_id` | P1 |
| B6 | `owner-account-grammar` | replace account_id with `account:user` | `PARSE_SCHEMA_FAILURE` | `$.payload.account_id` | P1 |
| B6 | `owner-role-substitution` | replace actor_role `owner` with `operator` | `PARSE_SCHEMA_FAILURE` | `$.payload.actor_role` | P1 |
| B6 | `owner-method-unknown` | replace authorization_method with `email/v1` | `PARSE_SCHEMA_FAILURE` | `$.payload.authorization_method` | P1 |
| B6 | `owner-result-denied` | replace authorization_result `success` with `denied` | `PARSE_SCHEMA_FAILURE` | `$.payload.authorization_result` | P1 |
| B6 | `owner-proof-digest-mismatch` | change external_proof_digest without changing the trusted proof receipt | `OWNER_PROOF_VERIFICATION_FAILURE` | `$.payload.external_proof_digest` | P3 |
| B6 | `owner-service-policy-mismatch` | change service_policy_digest | `TRUST_FAILURE` | `$.payload.service_policy_digest` | P3 |
| B6 | `owner-expired` | set expires_at before verification time | `OWNER_EXPIRY_FAILURE` | `$.payload.expires_at` | P3 |
| B6 | `owner-replay` | reuse replay_id from an accepted receipt | `EXPIRY_OR_REPLAY_FAILURE` | `$.payload.replay_id` | P3 |
| B6 | `owner-target-account-mismatch` | change target_account_binding for the plan account | `PLAN_SCOPE_OR_APPROVAL_FAILURE` | `$.payload.target_account_binding` | P6 |
| B7 | `public-secret-field` | add private_key to public projection | `UNKNOWN_FIELD` | `$.private_key` | P1 |
| B7 | `public-serial-field` | add serial_token to public projection | `UNKNOWN_FIELD` | `$.serial_token` | P1 |
| B7 | `private-pseudonym-wrong-key-domain` | use a bare serial hash instead of the fixed HMAC preimage | `TRUST_FAILURE` | `$.storage_token` | P3 |
| B7 | `evidence-wrong-digest` | return bytes whose digest differs from expected_content_digest | `CROSS_DOCUMENT_MISMATCH` | `$.expected_content_digest` | P5 |
| B7 | `evidence-unauthorized-reader` | use an actor without an evidence-reader binding | `TRUST_FAILURE` | `$.reader_binding_digest` | P3 |
| B7 | `error-secret-message` | place a token value in the error message | `UNKNOWN_FIELD` | `$.message` | P1 |
| B8 | `reverse-cycle-record-digest` | add forbidden record_digest under the manifest qualification binding | `UNKNOWN_FIELD` | `$.payload.qualification_bindings[0].record_digest` | P1 |
| B8 | `cross-document-qualification-digest` | set qualification record manifest_digest to a different manifest digest | `CROSS_DOCUMENT_MISMATCH` | `$.payload.manifest_digest` | P5 |
| B8 | `signature-context-transplant` | change envelope context from `manifest-publication` to `boot-success-marker` | `SIGNATURE_CONTEXT_MISMATCH` | `$.context` | P3 |
| B8 | `approval-plan-digest-cycle` | add plan_digest to the plan payload | `PLAN_DIGEST_CYCLE` | `$.payload.plan_digest` | P2 |
| B8 | `boot-core-digest-cycle` | add canonical_payload_digest to the boot core | `BOOT_DIGEST_CYCLE` | `$.payload.canonical_payload_digest` | P2 |
| B8 | `boot-marker-canonical-digest-cycle` | add canonical_payload_digest to the success marker | `BOOT_MARKER_DIGEST_CYCLE` | `$.payload.canonical_payload_digest` | P2 |
| B8 | `boot-marker-success-digest-cycle` | add success_mark_digest to the success marker | `BOOT_DIGEST_CYCLE` | `$.payload.success_mark_digest` | P2 |
| B9 | `boot-counter-zero-start` | issue a success marker for counter zero | `BOOT_COUNTER_FAILURE` | `$.payload.attempt_counter` | P4 |
| B9 | `boot-counter-reset` | lower attempt counter from trusted value 4 to 3 | `BOOT_COUNTER_FAILURE` | `$.payload.attempt.counter` | P4 |
| B9 | `boot-counter-maximum` | request increment when durable counter is 18,446,744,073,709,551,615 | `BOOT_COUNTER_FAILURE` | `$.durable_lineage.last_counter` | P4 |
| B9 | `boot-counter-wrap` | replace maximum counter with zero | `BOOT_COUNTER_FAILURE` | `$.durable_lineage.next_counter` | P4 |
| B9 | `boot-source-generation-reset` | replace source_generation 9 with 0 after a committed snapshot | `BOOT_COUNTER_FAILURE` | `$.durable_lineage.source_generation` | P4 |
| B9 | `boot-lineage-transplant` | change marker lineage_id from the core lineage | `BOOT_CONTEXT_MISMATCH` | `$.payload.lineage_id` | P5 |
| B9 | `boot-source-generation-mismatch` | change marker source_generation from the core value | `BOOT_CONTEXT_MISMATCH` | `$.payload.source_generation` | P5 |
| B9 | `boot-torn-lineage-record` | truncate the durable lineage record after commit_state | `BOOT_COUNTER_FAILURE` | `$.atomic_record` | P0 |
| B9 | `boot-forged-success-marker-signature` | change the marker signature bytes | `BOOT_MARKER_AUTH_FAILURE` | `$.signatures[0].signature` | P3 |
| B9 | `boot-forged-success-marker-role` | change marker signer_role from `boot-runtime` to `release` | `BOOT_MARKER_AUTH_FAILURE` | `$.signatures[0].signer_role` | P3 |
| B9 | `boot-marker-exact-4096` | make the complete canonical marker exactly 4,096 bytes | `ACCEPT` | `$` | P1 |
| B9 | `boot-marker-over-4096` | make the complete canonical marker exactly 4,097 bytes | `RESOURCE_LIMIT` | `$` | P1 |
| B10 | `negotiation-missing-payload` | remove `dtb-mutation-envelope/v1` from supported set | `CROSS_DOCUMENT_MISMATCH` | `$.supported_payload_types` | P5 |
| B10 | `negotiation-extra-payload` | append a ninth owner-specific value to supported set | `UNKNOWN_FIELD` | `$.supported_payload_types[8]` | P1 |
| B10 | `negotiation-duplicate-payload` | repeat `platform-manifest/v1` in supported set | `DUPLICATE_SEMANTIC_KEY` | `$.supported_payload_types[1]` | P1 |
| B10 | `negotiation-mixed-schema-digest` | replace one capability schema_set_digest with a different digest | `CROSS_DOCUMENT_MISMATCH` | `$.schema_set_digest` | P5 |
| B10 | `negotiation-lower-api` | lower consumer major below manifest minimum | `CROSS_DOCUMENT_MISMATCH` | `$.consumer_api.major` | P5 |
| B10 | `negotiation-overflow-api` | set consumer patch to 65,536 | `RESOURCE_LIMIT` | `$.consumer_api.patch` | P1 |
| B10 | `negotiation-malformed-api` | set consumer_api to `1.0` | `PARSE_SCHEMA_FAILURE` | `$.consumer_api` | P1 |
| B10 | `negotiation-unsealed-capabilities` | pass a parsed capabilities map to negotiation | `CAPABILITY_BOUNDARY_FAILURE` | `$.capabilities` | P6 |
| B10 | `dtb-cross-board` | change board_identity.board_id from the manifest target | `CROSS_DOCUMENT_MISMATCH` | `$.payload.board_identity.board_id` | P5 |
| B10 | `dtb-cross-manifest` | change platform_manifest_payload_digest | `CROSS_DOCUMENT_MISMATCH` | `$.payload.platform_manifest_payload_digest` | P5 |
| B10 | `dtb-cross-firmware` | change firmware_bundle_identity.bundle_digest | `CROSS_DOCUMENT_MISMATCH` | `$.payload.firmware_bundle_identity.bundle_digest` | P5 |
| B10 | `dtb-wrong-tool` | change tool_identity.tool_digest | `CROSS_DOCUMENT_MISMATCH` | `$.payload.tool_identity.tool_digest` | P5 |
| B10 | `dtb-wrong-policy` | change policy_identity.policy_digest | `CROSS_DOCUMENT_MISMATCH` | `$.payload.policy_identity.policy_digest` | P5 |
| B10 | `dtb-wrong-artifact` | change artifact_identity.artifact_digest | `CROSS_DOCUMENT_MISMATCH` | `$.payload.artifact_identity.artifact_digest` | P5 |
| B10 | `dtb-unknown-mutation` | replace one authorized property_path with `/unlisted` | `UNKNOWN_MUTATION` | `$.payload.authorized_mutations[0].property_path` | P5 |
| B10 | `dtb-wrong-before-digest` | change before_value_digest for one property | `CROSS_DOCUMENT_MISMATCH` | `$.payload.authorized_mutations[0].before_value_digest` | P5 |
| B10 | `dtb-source-digest-failure` | change source_observation_digest | `CROSS_DOCUMENT_MISMATCH` | `$.payload.source_identity.source_observation_digest` | P5 |
| B10 | `dtb-post-digest-failure` | change post_mutation_dtb_digest | `CROSS_DOCUMENT_MISMATCH` | `$.payload.post_mutation_dtb_digest` | P5 |
| B10 | `dtb-expired` | set expires_at before consumer clock | `DTB_EXPIRY_FAILURE` | `$.payload.expires_at` | P3 |
| B10 | `dtb-replayed-nonce` | reuse nonce and replay_id after accepted envelope | `EXPIRY_OR_REPLAY_FAILURE` | `$.payload.replay_identity.replay_id` | P3 |

The following broader rows are also mandatory; each row has one mutation:

| Fixture | Single mutation | Expected code | Exact path | Phase |
| --- | --- | --- | --- | --- |
| `changed-artifact-content` | change one manifest artifact content_digest | `MANIFEST_AUTHORITY_CONFLICT` | `$.payload.artifacts[0].content_digest` | P5 |
| `branch-locator` | add source.branch with value `refs/main` | `UNKNOWN_FIELD` | `$.payload.components.linux_kernel.source.branch` | P1 |
| `mutable-ref-locator` | replace source_commit with `refs/main` | `PARSE_SCHEMA_FAILURE` | `$.payload.components.linux_kernel.source.source_commit` | P1 |
| `wrong-board-predicate` | change one Linux compatible string | `CROSS_DOCUMENT_MISMATCH` | `$.payload.identity_match.linux.compatible[0]` | P5 |
| `wrong-chip-predicate` | change chip_id_u32 by one | `CROSS_DOCUMENT_MISMATCH` | `$.payload.identity_match.macos.chip_id_u32` | P5 |
| `stale-topology` | replace selection.topology_digest with the prior generation digest | `CROSS_DOCUMENT_MISMATCH` | `$.payload.selection.topology_digest` | P5 |
| `raw-path-target` | add path to one mutation target reference | `UNKNOWN_FIELD` | `$.payload.mutations[0].target_refs[0].path` | P1 |
| `changed-parent` | replace one topology parent_stable_id | `AMBIGUOUS_IDENTITY` | `$.payload.objects[0].parent_stable_id` | P4 |
| `changed-size` | replace one topology size_bytes | `AMBIGUOUS_IDENTITY` | `$.payload.objects[0].size_bytes` | P4 |
| `changed-uuid` | replace one volume identity UUID | `AMBIGUOUS_IDENTITY` | `$.payload.objects[0].stable_id` | P4 |
| `missing-evidence` | remove one evidence ID required by a passing test | `CROSS_DOCUMENT_MISMATCH` | `$.payload.test_results[0].evidence_ids[0]` | P5 |
| `omitted-required-test` | remove one required test result | `CROSS_DOCUMENT_MISMATCH` | `$.payload.test_results[0]` | P5 |
| `wrong-slot` | change marker slot_id from the trusted slot | `BOOT_CONTEXT_MISMATCH` | `$.payload.slot_id` | P5 |
| `torn-marker` | truncate the marker before the closing JSON byte | `PARSE_SCHEMA_FAILURE` | `$.transport.truncated` | P0 |
| `fallback-outside-rollback` | set fallback.target_slot to a slot absent from rollback | `BOOT_FALLBACK_FAILURE` | `$.payload.fallback.target_slot` | P5 |
| `success-after-failure` | set success to true while one required check is fail | `BOOT_REQUIRED_CHECK_FAILURE` | `$.payload.success` | P5 |
| `wrong-signer-key` | replace the marker signer key_id | `TRUST_FAILURE` | `$.signatures[0].key_id` | P3 |
| `expired-registry` | set registry expires_at before verification time | `REGISTRY_EXPIRY_FAILURE` | `$.payload.expires_at` | P3 |
| `expired-manifest` | set manifest expires_at before verification time | `MANIFEST_EXPIRY_FAILURE` | `$.payload.expires_at` | P3 |
| `expired-qualification` | set qualification expires_at before verification time | `QUALIFICATION_EXPIRY_FAILURE` | `$.payload.expires_at` | P3 |

No fixture combines alternate mutations. Each hostile fixture has an exact expected code, path, and precedence phase.

The 107 rows above are preserved. The following rows extend the catalog for the third
correction round; they are also single-mutation canonical fixtures and have unique IDs:

| Blocker | Fixture | Single mutation | Expected code | Exact path | Phase |
| --- | --- | --- | --- | --- | --- |
| B1 | `owner-actor-self-declared` | replace the actor in the approval with a different valid actor while retaining the proof receipt | `OWNER_PROOF_VERIFICATION_FAILURE` | `$.payload.actor_id` | P3 |
| B1 | `owner-account-self-declared` | replace the account in the approval with a different valid account while retaining the target account record | `OWNER_PROOF_VERIFICATION_FAILURE` | `$.payload.account_id` | P3 |
| B1 | `owner-proof-transplanted` | use a valid proof receipt from a different plan and target identity set | `OWNER_PROOF_VERIFICATION_FAILURE` | `$.payload.plan_digest` | P6 |
| B1 | `target-account-transplanted` | use a valid target account record from a different project | `OWNER_PROOF_VERIFICATION_FAILURE` | `$.payload.project_id` | P6 |
| B2 | `forged-observation-source` | replace the observation evidence bytes without changing observation_digest | `TRUST_BOUNDARY_FAILURE` | `$.source.evidence_digest` | P6 |
| B2 | `forged-clock` | pass a caller wall-clock value without an attestation digest | `TRUST_BOUNDARY_FAILURE` | `$.now` | P6 |
| B2 | `forged-atomic-boot-record` | change a committed boot record counter without changing bytes_digest | `TRUST_BOUNDARY_FAILURE` | `$.attempt_counter` | P6 |
| B2 | `forged-verified-dtb-inputs` | pass an unsealed DTB input record to the producer | `DTB_INPUT_BOUNDARY_FAILURE` | `$.dtb_inputs` | P6 |
| B3 | `domain-transplant-board-registry` | sign board-registry/v1 under the platform-manifest domain | `SIGNATURE_DOMAIN_BOARD_REGISTRY` | `$.domain` | P3 |
| B3 | `context-transplant-platform-manifest` | sign platform-manifest/v1 under the installer-plan context | `SIGNATURE_CONTEXT_PLATFORM_MANIFEST` | `$.context` | P3 |
| B3 | `role-transplant-installer-plan` | sign installer-plan/v1 with the owner-authorization role | `SIGNATURE_ROLE_INSTALLER_PLAN` | `$.signatures[0].signer_role` | P3 |
| B3 | `domain-transplant-qualification-record` | sign qualification-record/v1 under the boot-runtime domain | `SIGNATURE_DOMAIN_QUALIFICATION` | `$.domain` | P3 |
| B3 | `role-transplant-boot-health` | sign boot-health/v1 with the manifest-release role | `SIGNATURE_ROLE_BOOT_HEALTH` | `$.signatures[0].signer_role` | P3 |
| B3 | `context-transplant-owner-approval` | sign owner-approval/v1 under the boot-success-marker context | `SIGNATURE_CONTEXT_OWNER_APPROVAL` | `$.context` | P3 |
| B3 | `role-transplant-boot-success-mark` | sign boot-success-mark/v1 with the dtb-authority role | `SIGNATURE_ROLE_BOOT_MARK` | `$.signatures[0].signer_role` | P3 |
| B3 | `context-transplant-dtb-envelope` | sign dtb-mutation-envelope/v1 under the installer-plan context | `SIGNATURE_CONTEXT_DTB_ENVELOPE` | `$.context` | P3 |
| B4 | `unknown-nested-grammar-type` | set a boot measurement unit to an unlisted value | `PARSE_SCHEMA_FAILURE` | `$.payload.checks[0].measurement.unit` | P1 |
| B4 | `missing-nested-grammar-type` | remove the manifest boot-check profile failure_limit | `PARSE_SCHEMA_FAILURE` | `$.payload.components.boot_stack.boot_check_profile.failure_limit` | P1 |
| B5 | `manifest-top-level-artifact-conflict` | change projected artifact content_digest without changing the component artifact | `MANIFEST_AUTHORITY_CONFLICT` | `$.payload.components.linux_kernel.artifacts[0].content_digest` | P5 |
| B5 | `manifest-rollback-projection-conflict` | change projected rollback artifact_ids without changing component rollback records | `MANIFEST_AUTHORITY_CONFLICT` | `$.payload.rollback.artifact_ids[0]` | P5 |
| B5 | `manifest-compatibility-projection-conflict` | add a relation only to the top-level compatibility projection | `MANIFEST_AUTHORITY_CONFLICT` | `$.payload.compatibility[0]` | P5 |
| B6 | `document-id-reuse` | reuse an accepted document_id for a different payload_digest | `DOCUMENT_ID_REUSE` | `$.payload.document_id` | P3 |
| B6 | `document-id-branch` | add a second child to one document lineage record | `DOCUMENT_ID_FORK` | `$.document_lineage.document_ids[1]` | P5 |
| B7 | `dtb-add-real-before` | use a real current-value digest as the before value for add | `DTB_INPUT_VERIFICATION_FAILURE` | `$.payload.authorized_mutations[0].before_value_digest` | P5 |
| B7 | `dtb-replace-absent-before` | use absent_digest as the before value for replace | `DTB_INPUT_VERIFICATION_FAILURE` | `$.payload.authorized_mutations[0].before_preimage_digest` | P5 |
| B7 | `dtb-remove-real-after` | use a real value digest as the after value for remove | `DTB_INPUT_VERIFICATION_FAILURE` | `$.payload.authorized_mutations[0].after_value_digest` | P5 |
| B7 | `dtb-missing-authorized-mutation` | remove the policy rule for one signed mutation | `UNKNOWN_MUTATION` | `$.payload.authorized_mutations[0].authorization_rule_id` | P5 |
| B7 | `dtb-duplicate-semantic-key` | repeat a mutation property_path with the same operation and sequence | `DUPLICATE_SEMANTIC_KEY` | `$.payload.authorized_mutations[1].property_path` | P1 |
| B7 | `dtb-source-post-recompute` | change post bytes while retaining post_mutation_dtb_digest | `DTB_INPUT_VERIFICATION_FAILURE` | `$.payload.post_mutation_dtb_digest` | P5 |
| B7 | `dtb-wrong-policy-tuple` | replace policy_digest while retaining the manifest policy input | `CROSS_DOCUMENT_MISMATCH` | `$.payload.policy_identity.policy_id` | P5 |
| B8 | `boot-empty-required-checks` | replace the manifest-required check list with an empty list | `BOOT_REQUIRED_CHECK_FAILURE` | `$.payload.checks` | P5 |
| B8 | `boot-extra-unknown-check` | append a check not declared by the manifest profile | `BOOT_REQUIRED_CHECK_FAILURE` | `$.payload.checks[1].check_id` | P5 |
| B8 | `boot-unknown-check-class` | replace a check class with an unlisted class | `BOOT_REQUIRED_CHECK_FAILURE` | `$.payload.checks[0].class` | P5 |
| B8 | `boot-forged-marker-generation` | lower marker_generation below the durable marker generation | `BOOT_COUNTER_FAILURE` | `$.payload.marker_generation` | P4 |
| B8 | `boot-marker-replay-reservation` | reuse marker_replay_id after a committed marker | `EXPIRY_OR_REPLAY_FAILURE` | `$.payload.marker_replay_id` | P6 |
| B9 | `provenance-changing-adapter` | change adapter_id while retaining the physical disk identifier | `AMBIGUOUS_IDENTITY` | `$.payload.objects[0].provenance.adapter_id` | P4 |
| B9 | `provenance-changing-api` | change adapter_api_version while retaining observation_digest | `AMBIGUOUS_IDENTITY` | `$.payload.objects[0].provenance.adapter_api_version` | P4 |
| B9 | `provenance-changing-source-generation` | replace source_generation with an older generation | `BOOT_COUNTER_FAILURE` | `$.payload.source.source_generation` | P4 |
| B10 | `cross-project-approval` | use an approval from another project with equal plan and manifest digests | `PLAN_SCOPE_OR_APPROVAL_FAILURE` | `$.payload.project_id` | P6 |
| B10 | `cross-repository-approval` | use an approval from another repository with equal plan and manifest digests | `PLAN_SCOPE_OR_APPROVAL_FAILURE` | `$.payload.repository_id` | P6 |
| B10 | `cross-slice-approval` | use an approval from another slice with equal plan and manifest digests | `PLAN_SCOPE_OR_APPROVAL_FAILURE` | `$.payload.slice_id` | P6 |
| B10 | `cross-operation-approval` | replace write/v1 with remove/v1 in the approval operation set | `PLAN_SCOPE_OR_APPROVAL_FAILURE` | `$.payload.operations[0].operation` | P6 |
| B11 | `duplicate-failure-code` | assign `TRUST_FAILURE` to a second incompatible path family in the code table | `PARSE_SCHEMA_FAILURE` | `$.failure_codes[1].code` | P1 |
| B11 | `unnamed-hold-code` | add a boot failure decision hold without naming it in the complete HOLD set | `PARSE_SCHEMA_FAILURE` | `$.decision` | P1 |
| B12 | `generated-output-mismatch` | replace generated_output_digest without changing the compiled lock | `BINDING_INTEGRITY_FAILURE` | `$.generated_output_digest` | P5 |
| B12 | `parser-artifact-mismatch` | select a parser artifact not named by the manifest binding | `BINDING_INTEGRITY_FAILURE` | `$.generated_binding_identity.parser_id` | P5 |
| B12 | `boot-binding-selection-mismatch` | select a Rust binding with a boot artifact digest different from the manifest | `BINDING_INTEGRITY_FAILURE` | `$.boot_artifact_digest` | P5 |

The catalog therefore contains 154 hostile or boundary rows: the original 107 rows plus 47
new third-round rows. Fixture IDs and expected `(code, path, phase)` tuples are each unique by
their declared identity tuple; the same attack family may recur only with a distinct fixture
ID and distinct canonical input. The checker must construct every row, plant the single
mutation, and observe the exact code/path/phase. Any unexpected accept, wrong precedence,
duplicate ID, duplicate `(code, path, phase)` assignment, or missing row is a catalog gate
failure.

## 15. Conformance, acceptance gates, and examples

The following table is the normative conformance matrix. It distinguishes design obligations from future implementation evidence.

| Gate | Required observation | Design status in this note |
| --- | --- | --- |
| G1 shape | all eleven schema files and all closed objects validate against Draft 2020-12; exact eight payload types are present | contract defined; implementation absent |
| G2 precedence | P0 through P6 returns the first declared code and exact path | phases and fixtures defined; implementation absent |
| G3 canonicalization | JSON object order does not change JCS bytes; wrong array order rejects; negative zero rejects | rule and fixtures defined; implementation absent |
| G4 digest cycles | plan, core, marker, and reverse qualification cycle cases reject at the named field | formulas and fixtures defined; implementation absent |
| G5 lock graph | input lock is the only schema digest preimage; output lock has no back edge; graph is acyclic | graph and closed grammars defined; implementation absent |
| G6 binding closure | each exact component path has all source, input, lock, artifact, rollback, and relation records | canonical tree defined; implementation absent |
| G7 authority | no API accepts parsed policy, parsed boot context, parsed capabilities, or unverified owner context | sealed types and signatures defined; implementation absent |
| G8 storage | identity preimages are reproducible; parent, extent, generation, replacement, and ambiguity cases fail closed | grammar and fixtures defined; implementation absent |
| G9 boot | lineage IDs and source generations bind core, marker, and Trusted BootContext; 4,096 is accepted and 4,097 rejected | runtime contract defined; implementation absent |
| G10 DTB | producer and consumer bind all exact identities, mutation digests, signer authority, expiry, replay, and source/post digests | eighth payload contract defined; implementation absent |
| G11 negotiation | required and supported sets are exactly equal to eight values; numeric API ordering is used | closed capabilities and fixtures defined; implementation absent |
| G12 privacy | public, private-support, and evidence projections use only closed allowlists and fixed HMAC semantics | projections and fixtures defined; implementation absent |
| G13 reproducibility | Python, Swift, and Rust outputs match concrete output-lock digests and common vectors | future implementation gate; no claim here |
| G14 operational safety | executor revalidates topology before every mutation and uses durable journal/postconditions | future implementation gate; no claim here |
| G15 release honesty | no schema, binding, compile, VM, or booting desktop is called compatibility, qualification, support, release, or DONE evidence | preserved by this note |
| G16 owner seam | independent `Trusted<OwnerProofReceipt>` and `Trusted<TargetAccount>` constructors compare the complete project/scope/policy/topology/identity tuple | design contract defined; implementation absent |
| G17 local trust seam | `Trusted<Observation>`, `VerifiedClock`, `Trusted<AtomicBootRecord>`, and `Trusted<VerifiedDtbInputs>` reject forged, stale, replayed, partial, and recomputation-inconsistent records | design contract defined; implementation absent |
| G18 context matrix | all eight payload rows reject every domain/context/role transplant and enforce exact `ExpectedContext` scope | design contract and fixtures defined; implementation absent |
| G19 manifest authority | component records are canonical and all five top-level projections pass exact set-union/equality checks | design contract and fixtures defined; implementation absent |
| G20 document identity | one ID maps to one digest, correction chains are linear, and reuse/branch/fork rejects | design contract and fixtures defined; implementation absent |
| G21 boot profile | manifest-declared checks, closed measurements, marker clock/replay, counters, lineage, and exact rollback set are recomputed | design contract and fixtures defined; implementation absent |
| G22 DTB seam | source/post bytes, policy tuple, allowlist, operation sentinels, signer authority, expiry, and atomic replay reservation are recomputed | design contract and fixtures defined; implementation absent |
| G23 fixture census | 154 unique fixture IDs and unique expected `(code, path, phase)` tuples cover B01-B12 plus all prior rows | checker procedure defined; implementation absent |
| G24 binding identity | compiled lock, generator/parser/toolchain/API, output path/digest, required manifest bindings, and Rust boot selection are exact | design contract and fixtures defined; implementation absent |

The canonical negotiation example is the exact ordered set:

~~~text
board-registry/v1
platform-manifest/v1
installer-plan/v1
qualification-record/v1
boot-health/v1
owner-approval/v1
boot-success-mark/v1
dtb-mutation-envelope/v1
~~~

The canonical acceptance boundaries are `marker_complete_bytes = 4096`, `marker_complete_bytes = 4097 -> RESOURCE_LIMIT`, `attempt.counter = 0` as unstarted, `attempt.counter = 1` as the first executed attempt, `source_generation = 0` before the first committed topology, `source_generation = 1` for the first committed topology, and `uint64_max = 18,446,744,073,709,551,615` with fail-before-increment. These examples are contract vectors, not observed runtime results.

The implementation cannot enter consumer integration until every accepted and hostile fixture returns its declared code and path with zero unexpected accepts or rejects; independent JCS, signature, digest, lock, cross-document, trust-wrapper, storage, boot, DTB, negotiation, privacy, fuzz, differential-parser, resource, CLI, and clean-checkout gates pass. No schema compilation, recognized Apple chip, generated binding, booting kernel, booting desktop, or green focused test is implementation, release, hardware qualification, support, or F-02 DONE evidence.

The correction-round checker must create throwaway variants under `mktemp` and demonstrate
rejection for self-declared owner/account, forged observation/clock/atomic-boot/DTB inputs,
all eight context-matrix transplants, unknown and missing nested grammar, duplicate and
conflicting manifest projections, document-ID reuse and branch, every add/replace/remove DTB
sentinel and source/post recomputation attack, empty/extra/unknown boot checks, forged marker
generation and counter reset/wrap, provenance-changing stable IDs, cross-project/repository/
slice/operation approval, duplicate codes and unnamed HOLD code, and mismatched generated or
boot binding. It must rerun the prior envelope, JCS, preimage, digest-cycle, lock, semantic
ordering, scope/approval, schema-set, privacy, and 107-row catalog checks. A scratch checker
is evidence of a checker exercising the design only; it is not production implementation or
compatibility evidence.

## 16. Bounded Python, Swift, and Rust handoff

The following handoff is frozen for v1. It is a design contract, not generated implementation. No dependent slice may reopen the boot binding, replace the parser, or introduce a second authenticated format.

| Target | Pinned toolchain | Pinned generator/parser/API | Required artifact and behavior |
| --- | --- | --- | --- |
| Python consumer | CPython 3.12.8, packaging API 1.0.0 | generator `omarchy-schema-gen` 1.0.0, strict-json-python 1.0.0, contract API `OmarchyPlatformContracts-Python/1.0.0` | deterministic typed models, duplicate-key rejection, JCS vectors, no mutable-map admission path |
| Swift consumer | Swift 6.0.3, macOS SDK 15.2, Swift API 1.0.0 | generator `omarchy-schema-gen` 1.0.0, strict-json-swift 1.0.0, contract API `OmarchyPlatformContracts-Swift/1.0.0` | strict unknown-key decoding, typed trust wrappers, canonical bytes and digest helpers |
| Rust boot consumer | rustc 1.84.1 stable, target `aarch64-unknown-none`, no-std profile 1.0.0 | generator `omarchy-schema-gen` 1.0.0, strict-json-rust-no-std 1.0.0, boot API `OmarchyBootHealthBinding/1.0.0` | only bounded core/marker parser, fixed storage, no heap, no arbitrary environment fallback |

The two locks contain concrete source and artifact SHA-256 digests for every schema input,
generator, parser, toolchain input, and generated output when implementation begins. For each
consumer the compiled-lock and output-lock preimages are the exact closed JCS objects defined
in section 3; neither includes a self-digest, current date, absolute path, or discovered
file. A floating package, network fetch at build time, locale-dependent output,
map-iteration order, or compiler nondeterminism is a lock failure. Generators emit only files
listed in `bindings/generated-output.lock`, with stable line endings and stable file order; a
clean rebuild reproduces every output digest byte-for-byte. The generator, parser, toolchain,
API, schema-set, language, binding identity, artifact ID, output path, and output digest form
one immutable tuple. Duplicate tuple members, same schema-set with different generated or
parser artifact, or an output not named by the manifest is `BINDING_INTEGRITY_FAILURE`.

Generated bindings expose parse, canonical bytes, payload digest, verify, and typed conversion only through the private trust seam. They generate limits, schema IDs, enum values, sorted-key checks, error paths, and the schema-set digest. They do not generate trust roots, private keys, privileged operations, or a generic unchecked value constructor. Python, Swift, and Rust use the same accepted, hostile, canonical, digest, signature, trust-wrapper, projection, and no-laundering vectors. CI rejects stale generated output and any consumer-local schema copy. The manifest’s three `required_bindings` entries and their `required_artifacts` digests are the only binding selection authority; negotiation selects exactly one language/API/output tuple and rejects downgrade or substitution.

The Rust boot binding additionally requires the complete-marker 4,096-byte inclusive limit, exact 4,097-byte rejection, maximum depth 8, maximum checks 32, bounded stack and heap accounting recorded in the output lock, constant-time signature comparison, atomic-record validation, no path or environment input, and typed rejection for counter reset, counter wrap, context transplant, marker/core mismatch, and torn records. This is a future implementation gate and is not implementation or qualification evidence in this note.

## 17. CLI and package boundaries

The proposed CLI is diagnostic and CI-only and never escalates privilege:

~~~text
omarchy-platform schema list
omarchy-platform validate --type board-registry/v1 --input FILE
omarchy-platform canonicalize --type platform-manifest/v1 --input FILE --output FILE
omarchy-platform digest --type qualification-record/v1 --input FILE
omarchy-platform verify --input SIGNED_FILE --trust-bundle FILE --at TIME
omarchy-platform admit board --observation FILE --registry SIGNED_FILE --manifest SIGNED_FILE --at TIME
omarchy-platform plan validate --plan SIGNED_FILE --approval SIGNED_FILE --registry SIGNED_FILE --manifest SIGNED_FILE --observation FILE --at TIME
omarchy-platform boot-health evaluate --health SIGNED_FILE --marker SIGNED_FILE --manifest SIGNED_FILE --context FILE --at TIME
omarchy-platform dtb envelope verify --envelope SIGNED_FILE --source FILE --manifest SIGNED_FILE --at TIME
omarchy-platform fixtures run --type TYPE --case CASE
omarchy-platform bindings check --lock bindings/generated-output.lock
~~~

`validate` returns only untrusted parsed/canonical information. `verify` requires an explicit trust bundle and expected context and has no trust-all, key-generation, private-key, network-fetch, or arbitrary privileged-operation option. Admission refuses unsigned, expired, unknown, mismatched, ambiguous, over-bound, or schema-set-incompatible input before an allow decision. All commands are read-only.

The package boundaries are the immutable schema and fixture bundle, schema CLI, generated Python/Swift/Rust contracts, observation and storage adapters, release and qualification tooling, projection and evidence services, and the separately authorized transaction executor. A product shell receives only typed redacted helper results and cannot become a cryptographic verifier or parse signed metadata with ad hoc traversal.

## 18. Resolved decisions and owned residuals

The canonical wire and crypto base is strict JSON, Draft 2020-12, RFC 8785 JCS, and the exact domain-separated Ed25519 envelope. F-03 owns TrustContext roots, role bindings, key custody, thresholds, revocation, rotation, expiry grace, mirror compromise, and offline recovery, but cannot alter F-02 payload vocabulary, envelope fields, roles, domains, limits, or preimages. F-02 owns exact board identity, typed storage identity, exact component paths, one-way plan/approval and manifest/qualification binding, the three auxiliary payloads, boot lineage, schema negotiation, privacy projections, and the named hostile contract.

| Decision | Ruling | Reason and consequence |
| --- | --- | --- |
| D-F02-01 | keep exactly eight authenticated payload types | supporting trusted records close verification seams without widening the wire vocabulary |
| D-F02-02 | use immutable one-ID-to-one-digest history | corrections receive a new document ID and linear trusted lineage; reuse and forks reject |
| D-F02-03 | component records are manifest authority | top-level artifact/package/compatibility/firmware/rollback fields are exact derived projections only |
| D-F02-04 | require independent owner proof and target account seams | caller fields and digest-only external proof cannot establish identity or scope |
| D-F02-05 | require verified local source records | raw observation, clock, atomic boot, topology, and DTB inputs cannot cross an authority boundary |
| D-F02-06 | keep boot core and success marker separate | each digest has an acyclic preimage and marker replay/clock checks remain explicit |
| D-F02-07 | bind DTB mutation to one exact tuple | board, project, source, policy, tool, artifact, firmware, schema, and mutation rule changes reject |
| D-F02-08 | use unique string rejection codes | code meaning, path, phase, and HOLD eligibility cannot collide or be inferred |
| D-F02-09 | lock Python, Swift, and Rust outputs | generator/parser/toolchain/API/output identity and boot binding cannot silently drift |

The following are handoffs, not unanswered design questions and not silent prerequisites.
The design has no open question that can weaken this contract; any future disagreement is a
new coordinator ruling and cannot change the frozen eight-type envelope, preimages, or
fail-closed defaults without a new schema version.

| Residual | Owner | Immutable input | Default ruling | Blocking gate |
| --- | --- | --- | --- | --- |
| Trust root and role lifecycle | F-03 | signed `TrustContext` and `AuthorityRoleBinding` source records | reject absent, stale, revoked, or mismatched authority | G7 and G17 |
| Artifact builder and provenance | F-04 | component source, recipe, toolchain, artifact, firmware, and report digests | reject any floating, missing, or conflicting provenance | G6 and G19 |
| Compatibility and promotion automation | F-05 | signed manifest component tree and qualification bindings | reject any support or promotion result not derived from the canonical manifest | G6 and G15 |
| Transaction journal and executor | I-01/I-03/I-04/I-06 | `Trusted<Observation>`, admitted plan, trusted owner records, and durable journal | hold or reject before every unproven mutation | G7, G8, and G14 |
| Product admission and diagnostics | P-01/P-02/P-04/P-05 | trusted payload and closed projection policy | reject unknown projection fields and preserve redaction | G12 and G15 |
| Boot transport and slot integration | B-03/B-04 | frozen boot core, marker, lineage, `Trusted<AtomicBootRecord>`, and manifest profile | hold on the complete HOLD set; never infer success | G9, G17, and G21 |
| Lab controller and evidence store | Q-01/Q-02 | trusted evidence receipt and expected content digest | reject unauthorized, stale, private, or digest-mismatched evidence | G8 and G12 |
| Concrete board and qualification data | platform qualification owner | signed board registry, observation, qualification, and physical evidence | reject absent physical evidence; no support claim | G1, G6, and G15 |
| Concrete lock and generated output digests | F-02 implementation owner | schema-input lock, output lock, compiled locks, and manifest binding requirements | reject any unknown, stale, duplicate, or nondeterministic artifact | G5, G13, and G24 |
| RFC 8785 JCS implementation | F-02 implementation owner | pinned RFC 8785 vectors and implementation source digest | reject if independent JCS vectors are unavailable or differ | G3 and G13 |
| Schema/toolchain availability | F-02 implementation owner | pinned Draft 2020-12 schemas and toolchain lock entries | reject; unavailable tooling is not a pass | G1, G5, and G13 |
| Hardware and physical qualification | qualification owner | board-specific physical evidence and signed thresholds | reject; simulation or architecture evidence cannot clear the gate | G6 and G15 |

Production code, generated bindings, schema files, fixtures, keys, release manifests, qualification records, support ledgers, storage writers, firmware extractors, package integrations, telemetry, databases, UI, transport, and opaque boot artifacts remain outside this design-only change. Their absence is not implementation evidence and does not authorize a compatibility, support, qualification, release, or DONE claim.

## 19. Design-only handoff

The implementation sequence is to materialize the eleven closed schemas and exact vocabulary; implement strict parsing, canonicalization, and digesting; implement the single trust seam and sealed policy, boot, owner, capability, and authority inputs; generate Python, Swift, and Rust bindings from the input lock; add the named fixtures and independent vectors; implement pure cross-document admission and DTB envelope consumption; expose the read-only CLI; then run consumer, storage, qualification, boot, privacy, and adversarial gates.

The handoff preserves these non-negotiables: exact board identity is not SoC or architecture; a registry is not qualification; a manifest is not artifact proof; a plan is not approval; a core digest is not a marker digest; a stable ID is not a content digest; a parsed value is not a trusted value; a caller-controlled local record is not a Trusted BootContext; a boot marker is not hardware qualification; a generated binding is not a trust root; and no unknown, stale, mismatched, laundered, expired, replayed, or partially verified value may authorize mutation or claim success.
