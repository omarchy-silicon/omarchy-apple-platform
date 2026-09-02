# F-06 Release Compliance Design Note

Status: DESIGN MODEL ONLY — this correction defines a future contract and establishes no implementation, canonical F-06 schema, generated binding, validator, fixture result, CI result, legal clearance, redistribution permission, compatibility claim, qualification result, support claim, release readiness, promotion authority, merge, or DONE state.

Slice: F-06

Repository: `omarchy-apple-platform`

Exact program authority: the coordinator-owned `PROGRAM.md` at the supplied remote-main authority. The structural integrity of that program is distinct from implementation, qualification, and release evidence.

This is the sole F-06 design file in this correction round. It is subordinate to the coordinator ruling and to future ratified contracts. F-02 remains rejected and provisional at comparison tip `c315c7e79928d0041deb582bed79a61074361b21`; F-03 and all dependent foundations remain unratified. F-06 therefore has no current trusted input and its future admission result is HOLD until the exact external contracts exist.

## 1. Purpose and hard boundaries

F-06 evaluates one exact release-compliance evidence closure for one candidate, scope, operation, and channel. It can eventually emit a signed evidence result of `ADMIT`, `HOLD`, or `REJECT`, but F-06 is evidence-only. `ADMIT` means only that the F-06 evidence predicate was satisfied for its exact scope; it is not legal clearance, physical qualification, support, release, stable publication, or DONE.

F-06 never builds, fetches, installs, mutates a device, selects a board, selects a component, authorizes an owner, gives legal advice, grants redistribution permission, writes a stable channel, copies bytes to stable storage, or changes any producer-owned payload. F-06 has no local promotion operation and no alternate stable writer.

An external human-produced boot input may cross this design only as an opaque signed hash, size, schema, provenance, license/notice declaration, interface declaration, and independently observable evidence. F-06 does not inspect, read, list, traverse, fetch, clone, analyze, characterize, edit, test, or delegate work against the producing boundary. A hash or metadata declaration is not access to its source and is not evidence that the source was examined.

Design prose is a model for future implementation. A model, branch, document, green static check, opened channel, saved DNS form, signed declaration, or coordinator intent is not executable enforcement. Unknown, missing, stale, unsigned, unratified, locally copied, mismatched, replayed, downgraded, incomplete, or ambiguous input fails closed.

The 13 original blocker classes are explicitly closed by this note:

| Blocker | Contract section | Primary future gate/result |
| --- | --- | --- |
| 1 cross-contract import seam | 2 | F-02/F-03 trusted binding HOLD and exact eight-type join |
| 2 signed decisions and role/scope | 3 | exact signed decision join or F-03 authority HOLD |
| 3 inventory closure | 4 | closed node/artifact/edge/exclusion graph and closure digest |
| 4 deterministic error composition | 5 | parse envelope, source-preserving mapping, earliest finding |
| 5 grammar/bounds/negotiation | 6 | immutable grammar lock and exact capability handshake |
| 6 event lineage/supersession | 7 | bounded acyclic current-record selection |
| 7 license/source/counsel/branding | 8 | variant-complete disposition closure |
| 8 pre-consent content closure | 9 | signed cache/source closure and deny-after-consent evidence |
| 9 F-07 promotion authority | 10 | typed handoff and F-07-only exact-copy terminal |
| 10 projection/redaction/privacy | 11 | future F-02 public authority plus private redaction proof |
| 11 retention/deletion | 12 | frozen lock, eligibility, tombstone, and recovery result |
| 12 executable acceptance | 13-14 | pinned runner, report, and hostile/positive manifest |
| 13 identity/handoff closure | 15 | disjoint identities and complete handoff matrix |

## 2. Cross-contract import seam

### 2.1 Future F-02 type imports

F-06 consumes exactly these eight future ratified F-02 `Trusted<T>` values. The names below are the provisional comparison vocabulary from the rejected F-02 blob and are not a local F-06 authority. F-06 may consume a value only after a future ratified F-02 generated binding and the future ratified F-03 trust seam have returned the matching nominal `Trusted<T>` value.

| Ordinal | Exact future F-02 payload type | F-02-owned meaning | F-06 consumption |
| --- | --- | --- | --- |
| 1 | `board-registry/v1` | Exact board and SoC identity, firmware schema, capabilities, lifecycle, and qualification profile | Bind the candidate board and every applicable capability; SoC-only identity never admits a board |
| 2 | `platform-manifest/v1` | Exact component tree, source/config/patch/toolchain/report/artifact locks, typed compatibility, channel, boot policy, and rollback | Supply the sole component, artifact, package, firmware-schema, compatibility, and rollback authority |
| 3 | `installer-plan/v1` | Read-only inventory, stable target identities, proposed mutations, selected board/manifest, policy, and approval requirements | Bind installer and pre-consent closure evidence without modifying the closed plan payload |
| 4 | `qualification-record/v1` | Board-specific physical evidence, manifest binding, checks, failures, residuals, operators, lab, and evidence references | Verify the exact applicable qualification closure; parsing is not qualification |
| 5 | `boot-health/v1` | Signed boot-health core, slot, attempt, required checks, lineage, and fallback state | Consume only as a trusted boot result joined to the candidate and rollback set |
| 6 | `owner-approval/v1` | Exact plan/scope/target/operation authorization result and proof references | Consume only as a trusted owner decision; it cannot become a compliance or release decision |
| 7 | `boot-success-mark/v1` | Separate marker bound to the boot-health core, slot, lineage, source generation, counter, and checks | Consume only as a trusted marker joined to boot health; it is not qualification |
| 8 | `dtb-mutation-envelope/v1` | Exact DTB source/post bytes, policy, tool, artifact, firmware, schema, authorized mutation, signer, expiry, and replay bindings | Verify the external DTB result without recreating a DTB authority |

The exact eight-value set is closed to the table above. A missing or unknown F-02 type is a structural `REJECT`; absence of the ratified generated binding, absence of the ratified F-02 schema lock, absence of the ratified F-03 `Trusted<TrustContext>`, a stale binding, a locally copied field model, a generated-output digest mismatch, or any mismatch between the imported value and its lock is a deterministic `HOLD`. No F-06-local substitute schema, role table, trust root, owner directory, or copied F-02 field list can satisfy that hold.

### 2.2 Opaque reference versus authenticated envelope

`EnvelopeRef` is only a reference to a verified producer-owned value. It is not an envelope, does not carry a signature, and does not redefine any F-02 signature, component, artifact, schema, stable identity, or document authority. Its closed shape is:

```text
EnvelopeRef = {
  ref_schema: "f06-envelope-ref/v1",
  payload_type: one exact future F-02 type from Section 2.1,
  payload_version: "v1",
  schema_set_digest: Digest,
  document_id: DocumentId,
  payload_digest: Digest
}
```

The F-02 producer owns the authenticated envelope and all signatures. F-06 stores one `EnvelopeRef` per type, verifies the exact producer envelope through the ratified `Trusted<T>` seam, and stores no signed metadata inside `EnvelopeRef`. F-06 never resolves a reference by fetching a URL, selecting a branch, matching an artifact name, or trusting a copied signature.

`document_id`, `payload_digest`, and artifact/source content digests are disjoint identities. `document_id` is the immutable producer document identity and is never a digest. `payload_digest` is `sha256(JCS(P))` over the complete canonical producer payload. An artifact `content_digest` is the digest of the exact artifact bytes; a source/evidence `content_digest` is the digest of those exact bytes; neither is a document ID or a payload digest. Any field named `document_id`, `payload_digest`, or `content_digest` is compared in its own namespace and preimage. A digest copied between namespaces is `F06-IDENTITY-NAMESPACE-MISMATCH` and never a successful join.

### 2.3 Schema-set, lock, and generated-binding identity

F-06 does not define or own the F-02 schema set. It consumes a receipt proving that the future ratified F-02 lock was verified:

```text
F02SchemaSetReceipt = {
  receipt_schema: "f06-f02-schema-set-receipt/v1",
  schema_set_id: "platform-schema-set/v1",
  schema_set_digest: Digest,
  schema_input_lock_digest: Digest,
  schema_input_lock_preimage_digest: Digest,
  source_binding_digest: Digest,
  trust_binding_digest: Digest,
  receipt_digest: Digest
}
```

The receipt is an opaque reference to the future F-02 trusted lock; it is not a schema lock, schema authority, or F-06-local substitute. The future F-02 preimage remains exactly `schema_set_digest = sha256(ASCII("omarchy-schema-set/v1") || 0x00 || JCS(SchemaInputLock))`, where `schemas/schema-input.lock` is the sole preimage and contains the exact eleven F-02 schema-input IDs, source/reference digests, canonicalization implementation, limits, and generator/parser/toolchain inputs. `bindings/generated-output.lock` is a later output lock, binds back to `schema_set_digest`, and is never inserted into the schema-input-lock preimage.

The receipt itself is only evidence of that external verification: `receipt_digest = sha256(ASCII("omarchy-f06-f02-schema-set-receipt/v1") || 0x00 || JCS(F02SchemaSetReceipt without receipt_digest))`. The receipt is accepted only when its lock digests, preimage digest, source-binding digest, trust-binding digest, and schema-set digest are recomputed from the future ratified F-02 lock; a receipt cannot manufacture or replace that lock.

F-06 consumes only the following receipt for each future generated binding; it does not generate, copy, or reinterpret the binding:

```text
F02GeneratedBindingReceipt = {
  receipt_schema: "f06-f02-generated-binding-receipt/v1",
  schema_set_digest: Digest,
  language: "python" | "swift" | "rust-boot",
  binding_id: LowerAsciiToken,
  binding_version: Version,
  binding_source_digest: Digest,
  parser_id: LowerAsciiToken,
  parser_version: Version,
  parser_source_digest: Digest,
  api_id: LowerAsciiToken,
  api_version: ApiVersion,
  api_source_digest: Digest,
  generated_artifact_id: ArtifactId,
  generated_output_path: RelativeBindingPath,
  generated_output_digest: Digest,
  compiled_lock_digest: Digest,
  receipt_digest: Digest
}
```

The receipt is valid only when `schema_set_digest`, binding identity, parser identity, API identity, generated artifact/path/output digest, and compiled-lock digest exactly match the future ratified F-02 `generated-output.lock`, compiled lock, and manifest-required binding. Its preimage is `receipt_digest = sha256(ASCII("omarchy-f06-f02-generated-binding-receipt/v1") || 0x00 || JCS(F02GeneratedBindingReceipt without receipt_digest))`. A missing, rejected, stale, locally copied, duplicate, or mismatched receipt is `HOLD`, not a nearby-version fallback. The only usable value is the future ratified generated `Trusted<T>` binding; an untrusted JSON object, a cast, a public unchecked constructor, a consumer-local schema copy, or a different generated artifact never becomes trusted.

### 2.4 Exact F-02 component paths

The only manifest component paths are the exact future F-02 paths below. The old aliases `kernel`, `device_tree`, `firmware`, `mesa`, `boot`, `linux`, `linux/kernel`, `components/linux/kernel`, and equivalent paths are unknown and reject. F-06 does not create a competing component tree.

| Component ID | Exact F-02 component path | Sole owned records |
| --- | --- | --- |
| `linux-kernel` | `$.payload.components.linux_kernel` | `source`, `provenance`, locks, artifacts, packages, rollback, and relations at this path |
| `dtb-set` | `$.payload.components.dtb_set` | Device-tree source, policy, DT schema, artifacts, rollback, and relations at this path |
| `firmware-bundle` | `$.payload.components.firmware_bundle` | Firmware source, schema, artifacts, rollback, and relations at this path |
| `mesa-stack` | `$.payload.components.mesa_stack` | Mesa source, provenance, artifacts, packages, rollback, and relations at this path |
| `boot-stack` | `$.payload.components.boot_stack` | Opaque boot input declaration, boot artifacts, profile, rollback, and relations at this path |

The exact F-02 component paths, their `component_id` values, and their component-owned artifact/package/compatibility/firmware/rollback projections are compared byte-for-byte. Top-level manifest projections are usable only after F-02 recomputes them from those component paths; F-06 cannot select a top-level projection as a winner.

## 3. Signed decisions and role/scope closure

### 3.1 Exact future F-03 authority seam

All authority is resolved only through a future ratified F-03 `Trusted<TrustContext>` and its exact `AuthorityRoleBinding`. F-06 has no local authority table. The binding shape and role vocabulary are the exact F-02 seam that F-03 must ratify and implement:

```text
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
```

`Trusted<TrustContext>` is valid only when its exact context schema, authority-binding list, key-set digest, revocation epoch, issued/expiry window, signatures, threshold, replay reservation, rotation/revocation state, and offline recovery evidence are current. The F-02-v1 role enum is closed. F-06 may not invent names such as counsel, brand owner, release writer, or retention custodian as authority roles. A future F-03 ratified role/policy must explicitly bind a human checkpoint to an allowed binding; if no current F-03 binding can represent a required checkpoint, F-06 returns `HOLD` with `F06-F03-ROLE-UNAVAILABLE`. A role string, key ID, actor ID, account ID, email, Git author, or signed comment alone has no authority.

### 3.2 Decision kinds and exact signed joins

The decision-kind set is closed to `license`, `redistribution`, `export`, `security`, `branding_trademark`, `counsel`, and `owner`. A decision kind is not a role and cannot grant itself authority. Each disposition is resolved through an exact future F-03 binding and an independently signed decision record:

```text
SignedDecisionRef = {
  ref_schema: "f06-signed-decision-ref/v1",
  decision_id: DecisionId,
  decision_kind: "license" | "redistribution" | "export" | "security" | "branding_trademark" | "counsel" | "owner",
  decision_payload_digest: Digest,
  role_binding_digest: Digest,
  signer_actor_id: ActorId,
  signer_account_id: AccountId,
  authorization_method: "human-signature/v1" | "counsel-signed-review/v1" | "owner-approval/v1" | "service-attestation/v1",
  authorization_result: "allow" | "deny" | "hold" | "correct",
  proof_digest: Digest,
  policy_id: PolicyId,
  policy_digest: Digest,
  schema_set_digest: Digest,
  project_id: ProjectId,
  repository_id: RepositoryId,
  slice_id: SliceId,
  operation: F06Operation,
  board_id: BoardId,
  manifest_id: DocumentId,
  manifest_digest: Digest,
  candidate_document_id: DocumentId,
  candidate_payload_digest: Digest,
  artifact_set_digest: Digest,
  component_paths: ExactList<RelativeManifestPath, path>,
  artifact_scope_digest: Digest,
  license_scope_digest: Digest,
  source_scope_digest: Digest,
  brand_scope_digest: Digest,
  channel: "edge" | "rc" | "stable",
  issued_at: Timestamp,
  expires_at: Timestamp,
  replay_id: UUID,
  sequence: uint64,
  rejection_code: FailureCode | null,
  rejection_path: JsonPointer | null,
  rejection_phase: F06Phase | null,
  authority_role: "board-admission" | "manifest-release" | "installer-planner" | "owner-authorization" | "ci-conformance" | "qualification-lab" | "boot-runtime" | "dtb-authority" | "evidence-reader",
  checkpoint_id: CheckpointId,
  join_digest: Digest
}
```

The `join_digest` preimage is exactly `sha256(ASCII("omarchy-f06-decision-join/v1") || 0x00 || JCS(SignedDecisionRef without join_digest))`. It binds signer/account, exact role binding and resolved role, checkpoint, method, result, proof, clock, freshness/expiry, replay identity, policy/schema/document identities, project, repository, slice, operation, board, manifest, candidate, channel, component path, artifact set, artifact/license/source/brand scope, and any exact rejection code/path/phase. The decision payload itself has a separate `decision_payload_digest` preimage; an ID, proof digest, or join digest cannot stand in for payload bytes. `CheckpointId` is exactly `open-source-compliance-counsel`, `firmware-redistribution-owner`, `export-security-owner`, `security-release-owner`, `trademark-brand-owner`, or `project-owner`.

The decision matrix is closed. Every row requires a future F-03 trusted binding and the named human checkpoint where applicable; the human checkpoint is not legal clearance and prose is not owner approval.

| Decision kind | Required disposition record | Required join | Missing/stale/expired authority | Explicit deny or contradiction |
| --- | --- | --- | --- | --- |
| `license` | Variant-complete license, notice, modification, and source-obligation record | F-03 binding plus exact artifact/license/source scope | `HOLD` `F06-F03-AUTHORITY-HOLD` at `/decision_bindings/license/role_binding_digest` | `REJECT` `F06-LICENSE-DENIED` at `/decisions/license/authorization_result` |
| `redistribution` | Per-artifact redistribution class and conditions | F-03 binding plus artifact, channel, and source scope | `HOLD` `F06-F03-AUTHORITY-HOLD` at `/decision_bindings/redistribution/role_binding_digest` | `REJECT` `F06-REDISTRIBUTION-PROHIBITED` at `/decisions/redistribution/class` |
| `export` | Export class, restrictions, and security flags | F-03 binding plus artifact and destination scope | `HOLD` `F06-F03-AUTHORITY-HOLD` at `/decision_bindings/export/role_binding_digest` | `REJECT` `F06-EXPORT-RESTRICTED` at `/decisions/export/class` |
| `security` | Security disposition and mitigation evidence | F-03 binding plus candidate and artifact scope | `HOLD` `F06-F03-AUTHORITY-HOLD` at `/decision_bindings/security/role_binding_digest` | `REJECT` `F06-SECURITY-UNRESOLVED` at `/decisions/security/result` |
| `branding_trademark` | Rendered locations, attribution, and trademark disposition | F-03 binding plus brand scope and exact rendered locations | `HOLD` `F06-F03-ROLE-UNAVAILABLE` at `/decisions/branding_trademark/role_binding_digest` | `REJECT` `F06-BRANDING-UNRESOLVED` at `/decisions/branding_trademark/disposition` |
| `counsel` | Counsel interpretation or source-offer determination | F-03 binding plus exact legal scope and proof | `HOLD` `F06-F03-ROLE-UNAVAILABLE` at `/decisions/counsel/role_binding_digest` | `REJECT` `F06-COUNSEL-CONTRADICTION` at `/decisions/counsel/interpretation_digest` |
| `owner` | Publication, support, channel, exception, or external-impact disposition | F-03 binding plus exact scope and owner proof | `HOLD` `F06-F03-ROLE-UNAVAILABLE` at `/decisions/owner/role_binding_digest` | `REJECT` `F06-OWNER-DENIED` at `/decisions/owner/authorization_result` |

The required `authority_role` is copied from the exact resolved `AuthorityRoleBinding`; it is never inferred from `decision_kind` or `checkpoint_id`. For `owner`, the binding role must be `owner-authorization`. For every other row, the future F-03 service policy must explicitly authorize that disposition and checkpoint for the exact scope while retaining one of the closed roles above; no F-02 role is presumed to confer legal, export, security, or branding authority. Until that exact binding and policy capability are ratified and verified, the row is `HOLD` `F06-F03-ROLE-UNAVAILABLE`. A binding with a role or service policy that does not explicitly authorize the row is `REJECT` `F06-TRUST-ROLE-SCOPE-MISMATCH`.

The evaluator requires the current decision result and exact rejection code/path/phase to agree with the decision record. `allow`, `deny`, `hold`, and `correct` are not interchangeable. A missing decision, unattached digest, wrong role, wrong scope, wrong operation, changed signer/account, changed artifact/license/source/brand scope, invalid method/result/proof, stale clock, expiry, replay, correction, or contradictory decision has no default winner and cannot be laundered into `ADMIT`.

## 4. Canonical inventory closure: `f06.inventory/v1`

### 4.1 Closed bytes, bounds, and digest preimages

`f06.inventory/v1` is a future F-06 record family referenced outside the closed F-02 installer-plan payload. Its canonical UTF-8 JSON body has exactly `inventory_schema`, `inventory_document_id`, `scope`, `root_node_ids`, `nodes`, `artifacts`, `source_references`, `evidence_references`, `edges`, `exclusions`, `bounds`, and `closure_digest`. Its separately computed payload digest is `sha256(JCS(inventory_body))`; `closure_digest` is a different digest.

The immutable inventory bounds are: 65,536 nodes maximum; 65,536 artifacts maximum; 65,536 source references maximum; 65,536 evidence references maximum; 262,144 edges maximum; 16,384 exclusions maximum; 256 artifact references per node maximum; 256 source references per node maximum; 256 evidence references per node maximum; 16,384 UTF-8 bytes per scalar string maximum; 64 graph depth maximum; and 8,388,608 canonical inventory bytes maximum. Minimum node count is 1 and maximum root count is 65,536. Boundary values are inclusive; maximum plus one is `F06-BOUND-EXCEEDED`. These limits are contract constants, not implementation-selected values.

The record preimages are closed and exclude their derived digest field:

```text
node_digest = sha256(ASCII("omarchy-f06-inventory-node/v1") || 0x00 || JCS(Node without node_digest))
artifact_record_digest = sha256(ASCII("omarchy-f06-inventory-artifact/v1") || 0x00 || JCS(Artifact without artifact_record_digest))
edge_digest = sha256(ASCII("omarchy-f06-inventory-edge/v1") || 0x00 || JCS(Edge without edge_digest))
exclusion_digest = sha256(ASCII("omarchy-f06-inventory-exclusion/v1") || 0x00 || JCS(Exclusion without exclusion_digest))
closure_digest = sha256(ASCII("omarchy-f06.inventory/v1") || 0x00 || JCS({inventory_schema, inventory_document_id, scope, root_node_ids, nodes, artifacts, source_references, evidence_references, edges, exclusions, bounds}))
```

No preimage contains a self-digest, mutable locator, discovery order, current wall-clock value, secret, raw evidence bytes, or output-lock digest. A declared digest is recomputed from the named bytes and compared before any graph or policy decision.

### 4.2 Closed Node, Artifact, Edge, and Exclusion records

```text
Node = {
  node_id: NodeId,
  semantic_key: {component_id: ComponentId, node_kind: NodeKind, content_role: ContentRole, lifecycle: Lifecycle, identity_digest: Digest, scope_digest: Digest},
  component_id: ComponentId,
  node_kind: "component" | "source" | "source-snapshot" | "build-input" | "binary" | "firmware" | "package" | "package-index" | "image" | "container-image" | "generated-output" | "schema-lock" | "toolchain" | "patch-queue" | "notice" | "source-offer" | "license-text" | "qualification-evidence" | "installer-input" | "rollback-input" | "opaque-external-input",
  content_role: "source" | "source-snapshot" | "build-input" | "build-output" | "runtime" | "firmware" | "package-index" | "package" | "image" | "boot" | "notice" | "source-offer" | "license-text" | "branding" | "rollback" | "evidence" | "generated-binding" | "schema-lock" | "toolchain" | "opaque-external",
  lifecycle: "shipped" | "acquired-only" | "build-only" | "metadata-only",
  acquisition_mode: "embedded-in-candidate" | "fetched-from-authoritative-source" | "fetched-per-device" | "materialized-by-builder" | "declared-external",
  identity_digest: Digest,
  artifact_ids: SortedList<ArtifactId, artifact_id>,
  source_reference_ids: SortedList<SourceReferenceId, source_reference_id>,
  evidence_reference_ids: SortedList<EvidenceId, evidence_id>,
  recipe_reference_id: LowerAsciiToken | null,
  represents_node_id: NodeId | null,
  manifest_paths: SortedList<RelativeManifestPath, path>,
  required_for: ExactList<RootRole, root_role>,
  node_digest: Digest
}
Artifact = {
  artifact_id: ArtifactId,
  content_digest: Digest,
  content_size_bytes: uint64,
  media_type: LowerAsciiToken,
  content_role: ContentRole,
  location_role: "cache-object" | "candidate-object" | "source-object" | "evidence-object" | "public-ledger-object",
  scope: F06Scope,
  owner_node_ids: SortedList<NodeId, node_id>,
  source_reference_ids: SortedList<SourceReferenceId, source_reference_id>,
  evidence_reference_ids: SortedList<EvidenceId, evidence_id>,
  artifact_record_digest: Digest
}
Edge = {
  edge_id: EdgeId,
  edge_type: "contains" | "depends-on" | "derived-from",
  from_node_id: NodeId,
  to_node_id: NodeId,
  ordinal: uint32,
  edge_digest: Digest
}
Exclusion = {
  exclusion_id: ExclusionId,
  reference_kind: "source" | "artifact" | "metadata" | "execution-input" | "license" | "brand" | "rollback" | "support",
  reference_identity_digest: Digest,
  reference_locator_digest: Digest,
  exclusion_reason: "not-contributing" | "not-redistributed" | "out-of-scope",
  represented_by_node_id: NodeId | null,
  evidence_reference_ids: SortedList<EvidenceId, evidence_id>,
  signed_decision_ref: SignedDecisionRef,
  scope: F06Scope,
  exclusion_digest: Digest
}
```

The referenced records are also closed; their arrays are part of the inventory body and are not implicit maps:

```text
SourceReference = {
  source_reference_id: SourceReferenceId,
  source_kind: "direct-device" | "apple" | "recovery-stub" | "image" | "package-index" | "package" | "omarchy" | "opaque-external",
  source_identity_digest: Digest,
  content_digest: Digest,
  content_size_bytes: uint64,
  selector_digest: Digest,
  scope_digest: Digest,
  receipt_digest: Digest
}
EvidenceReference = {
  evidence_id: EvidenceId,
  content_digest: Digest,
  content_size_bytes: uint64,
  privacy_class: "public" | "restricted" | "private" | "secret",
  scope_digest: Digest,
  receipt_digest: Digest
}
```

The inventory vocabulary is closed: `NodeKind` is exactly the node-kind union shown above, `ContentRole` is exactly the content-role union shown above, and `Lifecycle = shipped | acquired-only | build-only | metadata-only`. These aliases are nominal and are not replaceable by arbitrary lower-case strings.

`NodeId`, `EdgeId`, `ExclusionId`, `SourceReferenceId`, and `EvidenceId` use the exact lowercase prefixed-token grammar `node:`, `edge:`, `exclusion:`, `source:`, and `evidence:` followed by `LowerAsciiToken`. `ArtifactId`, `ComponentId`, `ProjectId`, `RepositoryId`, `SliceId`, `PolicyId`, and `DocumentId` retain the exact future F-02 grammar and are never replaced by F-06 labels. `RelativeManifestPath` and every stored location are normalized relative ASCII paths with no leading slash, empty segment, backslash, NUL, control character, `..`, URL delimiter, shell expansion, or absolute-path prefix.

Every shipped or acquired-only node has at least one artifact; every build-only node has a recipe reference and evidence; every metadata-only node has exactly one `represents_node_id`; no node may use both an artifact and a contradictory exclusion. An artifact has exactly one canonical artifact record but may have one-to-many owner nodes. Multiple owner nodes are valid only when their complete `(component_id, content_role, content_digest, content_size_bytes, source scope, candidate scope, and artifact identity)` tuple is byte-identical. A second owner with a contradictory component, role, bytes, size, source, or scope is `F06-INVENTORY-AMBIGUOUS-OWNER`; one artifact is never cloned into separate identities to avoid that check.

### 4.3 Ordering, roots, closure, and hostile graph behavior

Canonical order is closed: `root_node_ids` by NodeId; `nodes` by NodeId; `artifacts` by ArtifactId; `edges` by `(from_node_id, edge_type order contains, depends-on, derived-from, ordinal, to_node_id)`; `exclusions` by ExclusionId; owner/source/evidence arrays by their typed IDs; and all `semantic_key` members by their declared tuple. Arrays are not sorted by the evaluator. Wrong order, missing member, duplicate key, extra member, duplicate semantic tuple, or second map representation fails at the first exact pointer.

`RootRole` is exactly `candidate`, `installer-plan`, `source-closure`, `legal-compliance`, `rollback`, `qualification`, `projection`, and `public-ledger`. The root set is derived, in that order, from the exact F-05 candidate components, the F-02 installer plan, every pre-consent source input, every required decision root, every rollback input, every applicable qualification record, every private/public projection input, and the publication ledger handoff. A root must be present, reachable, and have the matching `required_for` value. F-06 cannot add an unrequested root to excuse a missing root.

Closure is calculated as follows: start with the exact sorted root set; follow all `contains`, `depends-on`, and `derived-from` edges; require every endpoint to exist; reject self-edges, repeated semantic edges, invalid ordinals, and any cycle; require every mandatory dependency of every reachable node to be reachable; require every F-02/F-03/F-04/F-05/installer/decision/rollback/qualification/projection/public-ledger reference, source reference, and evidence reference to resolve to exactly one reachable node or exactly one signed exclusion; require every artifact owner to be reachable and every node/artifact/source/evidence scope digest to equal the inventory scope or its explicitly bound sub-scope; and reject every unreferenced node, artifact, source, evidence, edge, or exclusion. The graph is closed and acyclic. An orphan, missing endpoint, extra root, disconnected node, excluded reachable input, node-plus-exclusion contradiction, duplicate artifact, ambiguous owner, scope mismatch, or cycle is never ignored, pruned, merged, or treated as metadata.

## 5. Total deterministic error composition

### 5.1 F-06 phases and parse-rejection envelope

The closed F-06 phases are:

| Phase | Name | Inputs allowed | First failure result |
| --- | --- | --- | --- |
| `F06-P0` | transport and bytes | Raw bounded UTF-8 bytes only | Structural parse-rejection envelope; no typed value |
| `F06-P1` | grammar, shape, and bounds | Parsed local request fields | `REJECT` with exact field pointer |
| `F06-P2` | canonicalization and local preimages | Closed parsed values | `REJECT` with canonical/preimage pointer |
| `F06-P3` | F-02/F-03 trust and generated-binding seam | Only future ratified trusted seams | `HOLD` for absent/unratified trust foundation; otherwise mapped producer rejection |
| `F06-P4` | identity and scope | Verified references and exact scope records | `REJECT` or `HOLD` for missing trust |
| `F06-P5` | inventory graph and source closure | Trusted records and bounded graph | `REJECT` for contradiction; `HOLD` for unavailable required source |
| `F06-P6` | provenance, artifact, and content closure | Reachable source/artifact records | `REJECT` for mismatch or prohibited content |
| `F06-P7` | signed decisions and policy | Trusted decision joins and human checkpoints | `HOLD` for missing authority/decision; `REJECT` for deny/contradiction |
| `F06-P8` | event, projection, retention, and report dependencies | Verified evidence graph | `REJECT` or `HOLD` according to the closed code table |
| `F06-P9` | F-07 handoff | Typed F-07 request/result references only | `REJECT` for local promotion or copy violation |
| `F06-P10` | output canonicalization and attestation | Complete result body | `REJECT`; no unsigned partial result |

The structural parse-rejection envelope is closed and is the only result emitted when bytes cannot reach a typed request:

```text
ParseRejection = {
  error_schema: "f06-parse-rejection/v1",
  input_content_digest: Digest,
  parser_binding_digest: Digest | null,
  phase: "F06-P0" | "F06-P1" | "F06-P2",
  code: "F06-INPUT-MALFORMED" | "F06-INPUT-UNKNOWN-FIELD" | "F06-INPUT-DUPLICATE" | "F06-INPUT-MISSING" | "F06-BOUND-EXCEEDED" | "F06-INPUT-NONCANONICAL" | "F06-INPUT-VERSION-UNSUPPORTED",
  path: JsonPointer,
  decision: "REJECT",
  message_id: LowerAsciiToken,
  report_digest: Digest | null
}
```

`ParseRejection` contains no raw bytes, input value, secret, signature, path value, or partial trusted object. A missing parser binding is `F06-TOOLING-BLOCK` and never a parse pass. A parser must reject invalid UTF-8, BOM, control characters, duplicate JSON names, duplicate semantic keys, non-finite numbers, negative zero, invalid escaping, malformed identifiers, invalid timestamps, unknown fields, absent fields, wrong types, out-of-range values, and over-bound bytes before trust or cross-document processing.

### 5.2 F-02 phase/code/path mapping without laundering

F-02 has its own exact phases `P0` through `P6`, code strings, JsonPath grammar, and decision meanings. F-06 never replaces them with a generic success, warning, or local code. When a future ratified F-02 verifier rejects an imported value, the F-06 finding carries all four fields: `source_contract = "F-02"`, the exact upstream `source_phase` (`P0` through `P6`), the exact upstream `source_code`, and the exact upstream `source_json_path`. The F-06 finding also carries a local JSON Pointer to the import reference and the exact upstream decision. The mapped local code is an injective namespaced rendering formed by `F06-F02-SOURCE-` followed by the exact source code; no two source codes map to one local code, the mapped namespace is disjoint from `F06_CODES`, and `ACCEPT` is never converted to F-06 `ADMIT`.

The path mapping is lossless: the original F-02 JsonPath is preserved verbatim; where its grammar permits a direct conversion, `$` maps to `/`, `$.name` maps to `/name`, and `$[n]` maps to `/n`; the local pointer always retains the import root, for example `/f02_imports/platform-manifest~1v1`. An unrepresentable or ambiguous conversion is `F06-F02-PATH-UNREPRESENTABLE` with the import pointer and the unchanged source JsonPath, never a shortened or wildcard path.

The comparison-only upstream code vocabulary is exactly:

```text
{ACCEPT, PARSE_SCHEMA_FAILURE, UNKNOWN_FIELD, DUPLICATE_SEMANTIC_KEY, CANONICALIZATION_FAILURE, SIGNATURE_CONTEXT_MISMATCH, SIGNATURE_DOMAIN_BOARD_REGISTRY, SIGNATURE_CONTEXT_PLATFORM_MANIFEST, SIGNATURE_ROLE_INSTALLER_PLAN, SIGNATURE_DOMAIN_QUALIFICATION, SIGNATURE_ROLE_BOOT_HEALTH, SIGNATURE_CONTEXT_OWNER_APPROVAL, SIGNATURE_ROLE_BOOT_MARK, SIGNATURE_CONTEXT_DTB_ENVELOPE, TRUST_FAILURE, TRUST_BOUNDARY_FAILURE, EXPIRY_OR_REPLAY_FAILURE, OWNER_EXPIRY_FAILURE, DTB_EXPIRY_FAILURE, REGISTRY_EXPIRY_FAILURE, MANIFEST_EXPIRY_FAILURE, QUALIFICATION_EXPIRY_FAILURE, CROSS_DOCUMENT_MISMATCH, IDENTITY_INCOMPLETE, AMBIGUOUS_IDENTITY, PLAN_SCOPE_OR_APPROVAL_FAILURE, PLAN_DIGEST_CYCLE, UNKNOWN_MUTATION, MANIFEST_AUTHORITY_CONFLICT, OWNER_PROOF_VERIFICATION_FAILURE, CAPABILITY_BOUNDARY_FAILURE, DTB_INPUT_BOUNDARY_FAILURE, DOCUMENT_ID_REUSE, DOCUMENT_ID_FORK, DTB_INPUT_VERIFICATION_FAILURE, BOOT_MARKER_AUTH_FAILURE, BOOT_CONTEXT_MISMATCH, BOOT_COUNTER_FAILURE, BOOT_REQUIRED_CHECK_FAILURE, BOOT_FALLBACK_FAILURE, BOOT_DIGEST_CYCLE, BOOT_MARKER_DIGEST_CYCLE, BINDING_INTEGRITY_FAILURE, RESOURCE_LIMIT, CLI_USAGE_OR_INTERNAL_FAILURE}
```

`F02Phase` is exactly `P0 | P1 | P2 | P3 | P4 | P5 | P6`, and `F02SourceCode` is exactly the 45 values in the comparison-only set above. The source fields in a mapped finding use these closed types, not free-form labels.

The mapped decision is also preserved in `source_decision`; `F06-F02-SOURCE-<source_code>` has exactly the upstream decision and never a locally chosen result. `TRUST_BOUNDARY_FAILURE` may produce `HOLD` only where the future F-02 contract says hold; all other mapped upstream failure results remain `REJECT`. Missing, stale, rejected, locally copied, or mismatched F-02 generated bindings are not upstream payload failures: they are the local `F06-F02-BINDING-HOLD` and `HOLD` at the binding receipt. `F06-F02-SOURCE-ACCEPT` is forbidden because an upstream accept is not an F-06 admission.

### 5.3 Closed F-06 error registry and earliest-failure invariant

The local F-06 failure code vocabulary is closed to the following values. Every code has one phase family and one decision class; every concrete finding adds one exact JSON Pointer from its fixture or input. A code outside this set, a duplicate code definition, a code with two decision classes, an unnamed HOLD code, or a code with two incompatible path families is a contract/CI failure.

```text
F06_CODES = {
  F06-INPUT-MALFORMED, F06-INPUT-UNKNOWN-FIELD, F06-INPUT-DUPLICATE, F06-INPUT-MISSING, F06-BOUND-EXCEEDED, F06-INPUT-NONCANONICAL, F06-INPUT-VERSION-UNSUPPORTED,
  F06-F02-TYPE-MISSING, F06-F02-TYPE-UNKNOWN, F06-F02-BINDING-HOLD, F06-F02-PATH-UNREPRESENTABLE, F06-F02-TRUST-REJECTED,
  F06-F03-AUTHORITY-HOLD, F06-F03-ROLE-UNAVAILABLE, F06-F03-TRUST-REJECTED, F06-TRUST-ROLE-SCOPE-MISMATCH, F06-TRUST-DECISION-EXPIRED, F06-TRUST-DECISION-REPLAYED, F06-TRUST-DECISION-STALE,
  F06-IDENTITY-NAMESPACE-MISMATCH, F06-SCOPE-MISMATCH, F06-SCOPE-DUPLICATE, F06-DECISION-UNATTACHED, F06-DECISION-AMBIGUOUS, F06-DECISION-METHOD-INVALID, F06-DECISION-RESULT-INVALID, F06-DECISION-PROOF-MISSING, F06-DECISION-REJECTION-UNBOUND, F06-DECISION-TRANSPLANT,
  F06-INVENTORY-ROOT-MISSING, F06-INVENTORY-NODE-MISSING, F06-INVENTORY-NODE-DISCONNECTED, F06-INVENTORY-NODE-ORPHAN, F06-INVENTORY-SEMANTIC-DUPLICATE, F06-INVENTORY-ARTIFACT-SHAPE, F06-INVENTORY-ARTIFACT-DUPLICATE, F06-INVENTORY-AMBIGUOUS-OWNER, F06-INVENTORY-EXCLUSION-CONTRADICTION, F06-INVENTORY-EDGE-DUPLICATE, F06-INVENTORY-CYCLE,
  F06-IDENTITY-DIGEST-MISMATCH, F06-PROVENANCE-MISSING, F06-PROVENANCE-CONFLICT, F06-SOURCE-CLOSURE-HOLD, F06-SOURCE-CLOSURE-INCOMPLETE, F06-SOURCE-CONTENT-MISMATCH, F06-LICENSE-MISSING, F06-LICENSE-DENIED, F06-LICENSE-CHOICE-AMBIGUOUS, F06-NOTICE-MISSING, F06-SOURCE-OFFER-INCOMPLETE, F06-SOURCE-OFFER-UNSIGNED, F06-SOURCE-OFFER-UNAVAILABLE, F06-REDISTRIBUTION-PROHIBITED, F06-EXPORT-RESTRICTED, F06-SECURITY-UNRESOLVED, F06-COUNSEL-CONTRADICTION, F06-BRANDING-UNRESOLVED, F06-OWNER-DENIED,
  F06-HANDSHAKE-VERSION, F06-HANDSHAKE-SCHEMA, F06-HANDSHAKE-CAPABILITY, F06-HANDSHAKE-GRAMMAR, F06-HANDSHAKE-DOWNGRADE, F06-CANONICAL-ORDER,
  F06-EVENT-CYCLE, F06-EVENT-FORK, F06-EVENT-CURRENT-AMBIGUOUS, F06-EVENT-STALE, F06-EVENT-PREDECESSOR-MISSING, F06-EVENT-TRANSITION-INVALID, F06-EVENT-GENERATION-ROLLBACK, F06-EVENT-SEQUENCE-FAILURE, F06-EVENT-REPLAY, F06-EVENT-SCOPE-TRANSPLANT, F06-EVENT-RESTART-INCOMPLETE, F06-EVENT-TRUNCATED, F06-EVENT-TERMINAL-CHILD,
  F06-F07-PROMOTION-BYPASS, F06-F07-HANDOFF-MISSING, F06-F07-COPY-PREIMAGE-MISMATCH, F06-F07-PREREQUISITE-MISSING, F06-F07-STALE-HEALTH, F06-F07-ROLLBACK-MISMATCH, F06-F07-DOWNGRADE, F06-F07-DUPLICATE-WRITER, F06-F07-INTERRUPTED-COPY,
  F06-PROJECTION-POLICY-MISSING, F06-PROJECTION-POLICY-MISMATCH, F06-OUTPUT-PRIVATE-FIELD-LEAK, F06-OUTPUT-SECRET-CONTENT, F06-OUTPUT-PSEUDONYM-INVALID, F06-OUTPUT-PROJECTION-DIGEST-MISMATCH, F06-PUBLIC-AUTHORITY-REDEFINED, F06-PROJECTION-ACL-INVALID, F06-PROJECTION-NONINTERFERENCE,
  F06-RETENTION-LOCK-MISSING, F06-RETENTION-POLICY-MUTABLE, F06-RETENTION-HOLD-BLOCKS-DELETION, F06-RETENTION-EXTENSION-BLOCKS-DELETION, F06-RETENTION-CORRECTION-BLOCKS-DELETION, F06-RETENTION-ROLLBACK-BLOCKS-DELETION, F06-RETENTION-REACHABILITY-BLOCKS-DELETION, F06-RETENTION-NOT-ELIGIBLE, F06-RETENTION-AUTHORITY-HOLD, F06-RETENTION-TOMBSTONE-MISMATCH, F06-RETENTION-PARTIAL,
  F06-COMMAND-ENCODING-INVALID, F06-REPORT-SCHEMA-MISSING, F06-REPORT-CENSUS-INCOMPLETE, F06-FIXTURE-MANIFEST-MISSING, F06-FIXTURE-NOT-IMPLEMENTED, F06-TOOLING-BLOCK, F06-CLEAN-CHECKOUT-FAILURE, F06-TRACKED-ARTIFACT-MISSING, F06-CONFLICT-MARKER, F06-SECRET-SCAN, F06-ABSOLUTE-PATH, F06-PLACEHOLDER, F06-IDENTITY-INTERSECTION
}
```

`FailureCode` is the disjoint union of one exact member of `F06_CODES` or one exact `F06-F02-SOURCE-<source_code>` value. The local registry assigns every `F06_CODES` member exactly one phase and decision: `F06-P0`/`F06-P1` parse and grammar codes are `REJECT`; `F06-P2` canonical and preimage codes are `REJECT`; `F06-P3` trust, binding, decision-freshness, and authority-availability codes are `HOLD` only where the closed rows above or the fixture manifest say `HOLD`, otherwise `REJECT`; `F06-P4` identity and scope codes are `REJECT`; `F06-P5` inventory, source, and F-07 prerequisite contradictions are `REJECT`, with only unavailable required source evidence `HOLD`; `F06-P6` provenance and artifact contradictions are `REJECT`, with only absent required provenance `HOLD`; `F06-P7` decision denial/contradiction is `REJECT` and missing authority is `HOLD`; `F06-P8` event, projection, and retention codes use the exact `HOLD`/`REJECT` values in the fixture manifest; `F06-P9` promotion and handoff codes are `REJECT`; and `F06-P10` report, clean-checkout, tracked-artifact, secret, conflict, path, placeholder, fixture, and tooling codes are `REJECT` except `F06-TOOLING-BLOCK`, which is a non-pass `TOOLING_BLOCK` result. A code outside this disjoint registry, a duplicate code rule, or an unassigned path family is a contract failure.

The closed result envelope is:

```text
ComplianceEvaluationResult = {
  result_schema: "f06-compliance-result/v1",
  result_document_id: DocumentId,
  scope: F06Scope,
  decision: "ADMIT" | "HOLD" | "REJECT",
  input_envelope_refs: SortedList<EnvelopeRef, payload_type>,
  inventory_ref: F06RecordRef,
  decision_refs: SortedList<SignedDecisionRef, decision_kind>,
  findings: ExactList<Finding, finding_key>,
  finding_overflow: {count: uint64, digest: Digest} | null,
  pass_fail_census: {pass: uint64, fail: uint64, not_executable: uint64, tooling_block: uint64},
  evaluated_at: Timestamp,
  expires_at: Timestamp,
  result_payload_digest: Digest,
  attestation_ref: F06RecordRef | null
}
Finding = {
  code: FailureCode,
  path: JsonPointer,
  phase: F06Phase,
  subject_key: LowerAsciiToken,
  source_contract: "F-02" | "F-03" | "F-04" | "F-05" | "F-06" | "installer" | "F-07" | "ledger" | "owner" | "legal" | "qualification" | "support" | "release",
  source_phase: F02Phase | null,
  source_code: F02SourceCode | null,
  source_json_path: JsonPath | null,
  source_decision: "allow" | "hold" | "reject" | null,
  evidence_refs: SortedList<EvidenceId, evidence_id>,
  blocking: true
}
```

`result_payload_digest = sha256(ASCII("omarchy-f06-compliance-result/v1") || 0x00 || JCS(ComplianceEvaluationResult without result_payload_digest))`; it is not self-authenticating. `findings` has a maximum of 4,096 entries; overflow is a finding, never truncation. The canonical result maximum is 8,388,608 bytes. `not_executable` and `tooling_block` are not passes. `ADMIT` requires `fail = 0`, `not_executable = 0`, `tooling_block = 0`, no HOLD foundation, all required phases observed, all hostile fixtures observed with their exact expected outcomes, and every required signed join current.

The total evaluator first parses and bounds the entire request, canonicalizes every available closed object, verifies imported F-02/F-03 bindings, verifies local identity and scope, checks inventory and source closure, checks provenance, checks decisions and policy, checks event/projection/retention dependencies, verifies the F-07 handoff, and canonicalizes the result. It records every independently observable finding but chooses the primary finding by the stable key `(phase_ordinal, path UTF-8 bytes, subject_key UTF-8 bytes, code UTF-8 bytes, source_phase, source_path)`. The output finding order and result digest are therefore invariant under permutation of unordered request maps, handoff arrays, and reference input order. A semantically ordered array is itself validated for its declared order; a permutation that changes a required order is a different invalid input, not evaluator-order dependence. No stop-first, warning-success, first-map-member, last-map-member, deduplicate-and-continue, or input-order winner exists.

## 6. Closed grammar, bounds, ordering, and negotiation

### 6.1 F-06 grammar lock

The future `f06-grammar-lock/v1` is immutable and has `major = 1`, `supported_minor = 0`, `max_request_bytes = 8388608`, `max_result_bytes = 8388608`, `max_string_bytes = 16384`, `max_array_items = 65536`, `max_map_members = 65536`, `max_depth = 64`, `max_condition_depth = 16`, `max_findings = 4096`, `max_events = 65536`, `max_lineage_depth = 64`, `max_command_argv_items = 64`, `max_command_argument_bytes = 4096`, and `max_path_bytes = 512`. All bounds are inclusive and are part of `grammar_lock_digest`; the implementation may not choose a different limit.

The lock is closed to exactly `{lock_schema, major, supported_minor, max_request_bytes, max_result_bytes, max_string_bytes, max_array_items, max_map_members, max_depth, max_condition_depth, max_findings, max_events, max_lineage_depth, max_command_argv_items, max_command_argument_bytes, max_path_bytes}`. Its preimage is `grammar_lock_digest = sha256(ASCII("omarchy-f06-grammar-lock/v1") || 0x00 || JCS(F06GrammarLock without grammar_lock_digest))`; it contains no current date, discovered file, output digest, absolute path, or self-reference.

The F-06 policy expression is closed to the following records and no other condition kind:

```text
F06Policy = {
  policy_schema: "f06-policy/v1",
  policy_id: PolicyId,
  policy_version: Version,
  root_condition: PolicyCondition,
  policy_digest: Digest
}
PolicyCondition = {
  kind: "all",
  conditions: ExactList<PolicyCondition, condition_key>
} | {
  kind: "any",
  conditions: ExactList<PolicyCondition, condition_key>
} | {
  kind: "not",
  condition: PolicyCondition
} | {
  kind: "equals-digest",
  path: JsonPointer,
  expected_digest: Digest
} | {
  kind: "in-digest-set",
  path: JsonPointer,
  allowed_digests: SortedList<Digest, digest>
} | {
  kind: "present",
  path: JsonPointer,
  expected: boolean
}
```

Each union branch has exactly the fields shown, `all` and `any` have at least one child, `in-digest-set` has at least one digest, child arrays are sorted by canonical child bytes, and the total recursive depth is at most `max_condition_depth = 16` with no more than `max_array_items` condition nodes. `condition_key` is the derived `sha256(ASCII("omarchy-f06-policy-condition/v1") || 0x00 || JCS(PolicyCondition))` used only for array ordering and duplicate detection. A condition reads only the named closed-field JSON Pointer and compares a digest or presence bit; it cannot carry raw values, arbitrary expressions, code, URLs, maps, a field selector outside the request/result records, or a default allow. `policy_digest = sha256(ASCII("omarchy-f06-policy/v1") || 0x00 || JCS(F06Policy without policy_digest))`; true evaluates to `allow`, false to `reject`, and unavailable required input to `hold`. Unknown kind, empty logical array, duplicate child key, excessive depth/count, malformed path, or extra field is `F06-INPUT-MALFORMED` at the earliest exact condition pointer.

F-06 uses the exact future F-02 grammar for `Digest`, `DocumentId`, `ProjectId`, `RepositoryId`, `SliceId`, `ArtifactId`, `ComponentId`, `PolicyId`, `ActorId`, `AccountId`, `Timestamp`, `Version`, `ApiVersion`, `UUID`, `JsonPath`, `JsonPointer`, `Channel`, `SourceReferenceId`, and `EvidenceId`; imported F-02 `Operation` values retain the exact F-02 enum. F-06-specific identifiers use lowercase ASCII prefixed tokens and never use free-form names. URLs are immutable HTTPS locations with no credentials, query, fragment, IP-literal authority, or mutable selector. Paths are normalized relative paths; absolute paths, `~`, `$VAR`, command substitutions, globs, `..`, backslashes, and placeholders are rejected.

The remaining F-06 vocabulary is closed: `F06Phase = F06-P0 | F06-P1 | F06-P2 | F06-P3 | F06-P4 | F06-P5 | F06-P6 | F06-P7 | F06-P8 | F06-P9 | F06-P10`; `F06Operation = evaluate/v1 | admit/v1 | publish/v1 | retain/v1 | delete/v1`; `Channel = edge | rc | stable`; `DecisionId = decision:` plus `LowerAsciiToken`; `CheckpointId` is the six values in Section 3; `NodeId = node:` plus `LowerAsciiToken`; `EdgeId = edge:` plus `LowerAsciiToken`; `ExclusionId = exclusion:` plus `LowerAsciiToken`; `SourceReferenceId = source:` plus `LowerAsciiToken`; `EvidenceId = evidence:` plus `LowerAsciiToken`; and `RelativePath`/`RelativeManifestPath` are non-empty ASCII slash-separated paths of at most 512 bytes with no leading slash, empty segment, `..`, backslash, NUL, control character, URL delimiter, shell expansion, or placeholder. `F06RecordType` is exactly `f03-trust-context/v1`, `f04-build-provenance/v1`, `f05-candidate/v1`, `f06.inventory/v1`, `f06-compliance-result/v1`, `f06-cache-receipt/v1`, `f06-preconsent-source-closure/v1`, `f06-network-policy/v1`, `f06-rollback/v1`, `f06-legal-bundle/v1`, `f06-qualification-bundle/v1`, `f06-support-projection/v1`, `f06-public-ledger/v1`, `f06-projection-consent/v1`, `f06-projection-proof/v1`, `f06-privacy-acl/v1`, `f06-audit-receipt/v1`, `f06-retention/v1`, `f06-correction-chain/v1`, `f06-dependency-proof/v1`, `f06-deletion-result/v1`, `f06-tombstone/v1`, or `f07-copy-receipt/v1`. Stable copying is solely an F-07 operation and is never an F-06 operation value.

Typed references to non-F-02 records use exactly this closed shape and never use `EnvelopeRef`:

```text
F06RecordRef = {
  ref_schema: "f06-record-ref/v1",
  record_type: F06RecordType,
  document_id: DocumentId,
  payload_digest: Digest,
  content_digest: Digest | null,
  record_digest: Digest,
  scope_digest: Digest
}
F03SignatureRef = {
  ref_schema: "f03-signature-ref/v1",
  authority_role: "board-admission" | "manifest-release" | "installer-planner" | "owner-authorization" | "ci-conformance" | "qualification-lab" | "boot-runtime" | "dtb-authority" | "evidence-reader",
  role_binding_digest: Digest,
  signer_actor_id: ActorId,
  signer_account_id: AccountId,
  signature_digest: Digest,
  signature_preimage_digest: Digest
}
```

`record_digest = sha256(ASCII("omarchy-f06-record-ref/v1") || 0x00 || JCS(F06RecordRef without record_digest))`. `signature_digest` and `signature_preimage_digest` remain F-03-owned signature identities; F-06 compares the exact F-03 binding and never substitutes a local signature or role proof.

Every JSON object is closed, every array declares a fixed semantic key and order, every string rejects control characters, NUL, invalid Unicode, unpaired surrogates, and non-canonical escaping, and every number is finite and within its field bound. No field accepts a stringified number, null-for-missing coercion, unknown enum default, open map, arbitrary condition, or locally chosen limit. Duplicate JSON names are rejected before JCS.

### 6.2 Scope, uniqueness, and lock immutability

`F06Scope` is closed to `scope_schema = "f06-scope/v1"`, `project_id`, `repository_id`, `slice_id`, `operation`, `schema_set_digest`, `candidate_document_id`, `candidate_payload_digest`, `artifact_set_digest`, `policy_id`, `policy_digest`, `channel`, `board_id`, `board_registry_digest`, `manifest_id`, `manifest_digest`, `target_account_id`, `target_account_binding`, `valid_from`, `expires_at`, `replay_id`, and `scope_digest`. `scope_digest = sha256(ASCII("omarchy-f06-scope/v1") || 0x00 || JCS(F06Scope without scope_digest))`. The declared field order is the canonical order; F-06 `operation` is the exact `F06Operation` enum, while imported F-02 operation values retain their F-02 type, and the complete tuple is compared, never reconstructed from selected digests.

`target_account_id` and `target_account_binding` are null together exactly when no owner authorization or target mutation is in scope; both are required for every `decision_kind = owner` join and every installer/target mutation handoff. One null without the other, an account mismatch, or a binding that is not the exact account proof is `F06-SCOPE-MISMATCH`.

The exact scope tuple is unique across all decisions, events, projections, retention records, reports, and handoffs. Duplicate JSON keys, duplicate F-02 type, duplicate component path, duplicate artifact/content-role pair, duplicate node/edge/exclusion semantic key, duplicate decision kind plus component path, duplicate replay tuple, duplicate event sequence, duplicate fixture ID, duplicate handoff ID, and duplicate output path are rejected. A digest cannot make an otherwise duplicate semantic key unique.

Lock rules are immutable and one-way: schema/input locks precede generated/output locks; grammar and policy locks precede reports; fixture manifests precede fixture results; retention and projection locks are referenced by results but never rewritten by them. A lock self-digest is excluded from its own preimage. A lock containing an output back-edge, current date, absolute path, discovered file, locale, unpinned tool, mutable URL, placeholder, or downgrade alias is rejected.

### 6.3 Capability handshake and negotiation

The handshake has exactly `protocol`, `major`, `minor`, `schema_set_digest`, `grammar_digest`, and `capabilities`. `protocol` is `f06-compliance/v1`; `major = 1`; `minor = 0`; and the exact required capability set is:

```text
{f02-trusted-generated-binding-v1, f03-trusted-context-v1, deterministic-error-v1, inventory-closure-v1, signed-decision-join-v1, preconsent-source-closure-v1, event-lineage-v1, projection-redaction-v1, retention-tombstone-v1, f07-copy-terminal-v1, identity-handoff-matrix-v1}
```

Capabilities are sorted unique lowercase tokens. Compatibility succeeds only when major equals 1, requested minor is no greater than supported minor 0, `schema_set_digest` is exact, `grammar_digest` is exact, and the offered set equals the required set. Missing, extra, unknown, duplicate, stale, or reordered capabilities fail with `F06-HANDSHAKE-CAPABILITY`; higher major, unsupported minor, or downgrade fails with `F06-HANDSHAKE-VERSION` or `F06-HANDSHAKE-DOWNGRADE`; schema mismatch fails with `F06-HANDSHAKE-SCHEMA`; grammar mismatch fails with `F06-HANDSHAKE-GRAMMAR`. No unknown capability is ignored and no lower minor is silently selected.

## 7. Event lineage, supersession, and restart recovery

### 7.1 Closed event graph

The future `f06.event/v1` record has exactly `event_schema`, `event_id`, `event_document_id`, `event_type`, `state`, `scope`, `generation`, `sequence`, `predecessor_event_id`, `supersedes_record_id`, `corrects_record_id`, `lineage_id`, `event_payload_digest`, `replay_identity`, `created_at`, `valid_until`, `reason_code`, `terminal_outcome`, `commit_state`, `lineage_digest`, and `event_digest`.

`event_type` is exactly `create`, `evaluate`, `admit`, `reject`, `correct`, `supersede`, `revoke`, or `close`. `state` is exactly `proposed`, `evaluated`, `admitted`, `rejected`, `corrected`, `superseded`, `revoked`, or `closed`. `terminal_outcome` is null except on `close`, where it is exactly `ADMIT`, `HOLD`, or `REJECT`. `commit_state` is `prepared` or `committed`; a prepared event is never current evidence.

The event field relation is closed: `create` requires `state = proposed`, no predecessor, no correction/supersession target, and `terminal_outcome = null`; `evaluate` requires `state = evaluated`; `admit` requires `state = admitted`; `reject` requires `state = rejected`; `correct` requires `state = corrected` and exactly one `corrects_record_id`; `supersede` requires `state = superseded` and exactly one `supersedes_record_id`; `revoke` requires `state = revoked` and exactly one referenced record; and `close` requires `state = closed` and one non-null `terminal_outcome`. Every non-root event has one `predecessor_event_id`; only `correct`, `supersede`, and `revoke` may carry their corresponding target, and no event may carry an unrelated target or a second relation.

The graph is bounded to 65,536 events, 262,144 edges, 64 lineage depth, and `uint64` sequence/generation values with fail-before-wrap. A root `create` has generation 0, sequence 1, and no predecessor. Every later event has exactly one predecessor and generation exactly predecessor generation plus one. A correction or supersession has exactly one referenced record and a new document ID/payload digest; it cannot reuse the old ID or digest as a new correction. A revoke cannot create an admit. `closed`, `superseded`, and `revoked` records are terminal record states; no event may mutate them in place. A correction chain is a new immutable record linked by `corrects_record_id` and a signed correction receipt, not a rewrite of the old record.

The only valid event transitions are `create -> evaluate`, `evaluate -> admit`, `evaluate -> reject`, `admit -> close`, `reject -> close`, `admit -> correct`, `reject -> correct`, `admit -> supersede`, `reject -> supersede`, `admit -> revoke`, `reject -> revoke`, `correct -> evaluate`, `supersede -> close`, `revoke -> close`, and `close` to no later event in that record lineage. A correction/supersession relation is separately checked for one parent and one child; it cannot create a second current record.

### 7.2 Current record, lineage preimages, clocks, and replay

`event_digest = sha256(ASCII("omarchy-f06-event/v1") || 0x00 || JCS(Event without event_digest))`. `lineage_digest = sha256(ASCII("omarchy-f06-lineage/v1") || 0x00 || JCS({lineage_id, scope_digest, ordered event IDs, ordered event digests, generations, sequences}))`. `replay_key = sha256(ASCII("omarchy-f06-replay/v1") || 0x00 || JCS({project_id, repository_id, slice_id, operation, schema_set_digest, candidate_document_id, channel, event_id, replay_id, sequence}))`.

The current-record algorithm constructs the exact scope group, verifies every predecessor and correction/supersession receipt, rejects cycles, forks, missing predecessors, skipped generations, duplicate sequences, duplicate replay keys, terminal children, and two records with equal maximal generation, and selects the one unique maximal committed record with no valid superseding/correcting child. No first, last, timestamp, array order, or digest-only selection is allowed. A committed record whose `valid_until` is before the verified clock and which has no valid current successor is exactly `REJECT` `F06-EVENT-STALE` at `/events/current_record_ids/0/valid_until`; two valid maximal records are exactly `REJECT` `F06-EVENT-CURRENT-AMBIGUOUS` at `/events/current_record_ids`. These meanings are frozen locally and are not conditional on a future code table.

Every event `created_at` must be no later than the verified clock and `valid_until`, and every validity interval is no longer than 30 days (2,592,000 seconds). Clock, sequence, generation, replay nonce, and event bytes are verified by the future F-03 seam. A restarted evaluator reads only atomically committed records, reserves replay identity before accepting an event, and recomputes the complete lineage digest. A torn, truncated, interrupted, prepared-only, or storage-generation-mismatched record produces `HOLD` `F06-EVENT-RESTART-INCOMPLETE` or `F06-EVENT-TRUNCATED`; it never retries by guessing, reuses a sequence, or chooses a neighboring event. Same bytes plus same replay identity is idempotent; same ID, nonce, or sequence with changed bytes is `REJECT` `F06-EVENT-REPLAY`.

The complete anti-transplant scope is `(project_id, repository_id, slice_id, operation, schema_set_digest, candidate_document_id, candidate_payload_digest, artifact_set_digest, policy_digest, board_id, manifest_id, channel)`. Any cross-scope replay, equal-digest transplant, branch, fork, stale/current ambiguity, truncation, counter reset, counter wrap, or interrupted restart fails closed.

## 8. License, source, counsel, and branding closure

### 8.1 Variant-complete records and authoritative roots

F-06 requires a complete license/source decision closure for every reachable artifact variant, including kernel, DTB, firmware, Mesa, boot, package, image, installer, font, theme, artwork, generated output, source snapshot, notice, source-offer, license-text, and opaque external input. A component-level prose note cannot cover an artifact-level obligation.

The authoritative root for source and artifact identity is the future F-04 signed source/provenance/artifact record joined to the exact F-02 component path and artifact `content_digest`. The authoritative root for legal, redistribution, export, security, owner, counsel, and branding dispositions is the future F-03 trusted signed decision join in Section 3. A URL, repository name, SPDX string, filename, package coordinate, or human assertion is not a root.

```text
LicenseNoticeBinding = {
  binding_schema: "f06-license-notice/v1",
  artifact_id: ArtifactId,
  artifact_content_digest: Digest,
  choice_kind: "single" | "one-of" | "all-of",
  license_options: SortedList<LicenseOption, option_id>,
  selected_option_ids: ExactList<LicenseOptionId, option_id>,
  exception_ids: SortedList<ExceptionId, exception_id>,
  notice_ids: SortedList<NoticeId, notice_id>,
  modification_disclosure_ids: SortedList<DisclosureId, disclosure_id>,
  source_obligation: "not-required" | "source-available" | "source-offer-required" | "source-offer-satisfied" | "source-missing" | "unknown-unresolved",
  source_reference_ids: ExactList<SourceReferenceId, source_reference_id>,
  source_offer_ids: SortedList<SourceOfferId, offer_id>,
  selected_source_offer_id: SourceOfferId | null,
  decision_ref: SignedDecisionRef,
  evidence_ids: SortedList<EvidenceId, evidence_id>,
  binding_digest: Digest
}
LicenseOption = {
  option_id: LicenseOptionId,
  expression_kind: "spdx" | "declared-non-spdx",
  expression_digest: Digest,
  license_text_digest: Digest,
  exception_ids: SortedList<ExceptionId, exception_id>,
  notice_ids: SortedList<NoticeId, notice_id>,
  modification_disclosure_ids: SortedList<DisclosureId, disclosure_id>,
  source_obligation: SourceObligation,
  option_digest: Digest
}
SourceOffer = {
  offer_id: SourceOfferId,
  source_snapshot_digest: Digest,
  source_size_bytes: uint64,
  location_digests: SortedList<Digest, digest>,
  offer_text_digest: Digest,
  availability_evidence_ids: ExactList<EvidenceId, evidence_id>,
  signature_ref: F03SignatureRef,
  valid_from: Timestamp,
  expires_at: Timestamp,
  scope: F06Scope,
  offer_digest: Digest
}
```

`LicenseOptionId`, `ExceptionId`, `NoticeId`, `DisclosureId`, `SourceOfferId`, and `RelativeManifestPath` are lowercase ASCII prefixed tokens with the exact prefixes `license-option:`, `exception:`, `notice:`, `disclosure:`, `offer:`, and a relative manifest path respectively. `SourceObligation` is exactly the six values in `source_obligation`. `choice_kind = single` requires exactly one option and one selection; `one-of` requires at least two complete options and exactly one selection; `all-of` requires every option and every selected obligation. `not-required` requires zero source references, zero offers, and null selected offer; `source-available` requires exactly one source reference, zero offers, and null selected offer; `source-offer-required` and `source-offer-satisfied` require zero direct source references, 1 through 8 complete signed offers, and exactly one selected offer, with only the latter permitted to admit. `source-missing` and `unknown-unresolved` cannot admit. Empty, `NOASSERTION`, guessed, undigested, contradictory, or missing license text, exception, notice, modification disclosure, or source obligation is not complete. A license/source preimage uses domain-separated JCS bytes and excludes its derived digest: `license_binding_digest = sha256(ASCII("omarchy-f06-license-binding/v1") || 0x00 || JCS(LicenseNoticeBinding without binding_digest))`; each option, notice, disclosure, and offer has an explicit no-self-digest preimage under its own fixed domain.

Source-offer cardinality is exact as above. Every alternative offer remains complete and signed even when not selected. `source_offer_digest = sha256(ASCII("omarchy-f06-source-offer/v1") || 0x00 || JCS(SourceOffer without offer_digest))`; an offer binds source bytes, size, immutable location digests, offer text, availability evidence, signature, validity, artifact scope, and candidate scope. No source offer is invented from a public URL.

### 8.2 Decision combinations and human checkpoints

The only combinations that can reach F-06 `ADMIT` are: every artifact has a complete license choice; every required notice and modification disclosure exists; each source obligation is `not-required`, `source-available`, or `source-offer-satisfied`; redistribution is explicitly permitted for the exact channel or is explicitly `per-device-direct-authoritative-fetch-only` with no bundled bytes; export/security is explicitly allowed and all restrictions are satisfied; branding is explicitly allowed for each rendered location; counsel joins every counsel-reserved interpretation; and owner decisions explicitly cover publication/support/external impact. A direct-fetch-only artifact is never simultaneously marked as a bundled artifact. `unknown`, `prohibited`, `source-missing`, `deny`, contradiction, expired decision, missing source, missing notice, and absent human checkpoint cannot become `ADMIT`.

The human checkpoints are `open-source-compliance-counsel`, `firmware-redistribution-owner`, `export-security-owner`, `security-release-owner`, `trademark-brand-owner`, and `project-owner`. These are accountable checkpoint labels, not authority. Each must resolve to the future F-03 `Trusted<TrustContext>` and exact `AuthorityRoleBinding`; without that binding the result is `HOLD`. A prose approval, unchecked box, merged pull request, or author identity is not an owner decision.

Correction and expiry rules are deterministic: a correction creates a new decision ID, new payload digest, new join digest, one predecessor, and one correction receipt; it never rewrites the old decision. The earliest expiry across payload, role binding, policy, source offer, evidence, and channel controls the join. A signed denial or contradiction is `REJECT`; a missing, unratified, stale, or unavailable authority is `HOLD`; no result is silently renewed.

## 9. Pre-consent content and source closure

### 9.1 Allowlisted inputs and exact source closure

F-06 consumes a future installer handoff proving that every required byte and metadata input was acquired and verified before final consent. The allowlisted authority set is exactly `direct-device-authoritative`, `apple-authoritative`, `vendor-authoritative`, `recovery-stub-authoritative`, `omarchy-release-authoritative`, `package-index-authoritative`, `package-payload-authoritative`, and `opaque-human-declaration-authoritative`.

The closure includes the direct-device fetch and every Apple firmware input, RecoveryOS/1TR/recovery-stub input, image, boot input, package-index/repository metadata input, package payload, installer input, source snapshot, notice/source-offer input, and opaque external input named by the exact candidate and installer plan. Each input is either an allowlisted content-addressed object with one verified receipt or one signed exclusion that proves it contributes no bytes, metadata, execution, licensing, security, branding, rollback, qualification, support, or publication output. A missing or unlisted input is not an offline exception.

```text
VerifiedCacheReceipt = {
  receipt_schema: "f06-cache-receipt/v1",
  receipt_document_id: DocumentId,
  scope: F06Scope,
  authority_kind: "direct-device-authoritative" | "apple-authoritative" | "vendor-authoritative" | "recovery-stub-authoritative" | "omarchy-release-authoritative" | "package-index-authoritative" | "package-payload-authoritative" | "opaque-human-declaration-authoritative",
  source_identity_digest: Digest,
  selector_digest: Digest,
  content_digest: Digest,
  content_size_bytes: uint64,
  provenance_digest: Digest,
  verified_at: Timestamp,
  expires_at: Timestamp,
  cache_object_digest: Digest,
  cache_object_ref: RelativePath,
  parent_receipt_ids: SortedList<DocumentId, document_id>,
  signature_ref: F03SignatureRef,
  receipt_digest: Digest
}
PreConsentSourceClosure = {
  closure_schema: "f06-preconsent-source-closure/v1",
  closure_document_id: DocumentId,
  installer_plan_ref: EnvelopeRef,
  receipt_refs: SortedList<F06RecordRef, document_id>,
  inventory_ref: F06RecordRef,
  consent_ref: EnvelopeRef,
  network_policy_ref: F06RecordRef,
  closure_digest: Digest
}
```

`receipt_digest = sha256(ASCII("omarchy-f06-cache-receipt/v1") || 0x00 || JCS(VerifiedCacheReceipt without receipt_digest))`; `closure_digest = sha256(ASCII("omarchy-f06-preconsent-source-closure/v1") || 0x00 || JCS(PreConsentSourceClosure without closure_digest))`. A cache object is addressed by its content digest and exact size; a receipt cannot be transplanted between project, repository, slice, operation, candidate, board, manifest, artifact set, channel, or schema set.

### 9.2 Closed installer payload boundary and network policy

The F-02 `installer-plan/v1` payload remains closed exactly as defined by future ratified F-02. F-06 does not add `cache_receipts`, `network_policy`, mutation transcripts, or source-closure fields to that payload. `PreConsentSourceClosure` and `NetworkPolicyEvidence` are separate typed F-06/installer handoff records referenced outside the installer-plan body.

The installer must complete the exact sequence: resolve the trusted installer-plan reference; enumerate every direct and transitive input; fetch only through the eight allowlisted authorities; verify signature, selector, provenance, scope, digest, size, and freshness; create a content-addressed cache object and receipt; verify the inventory closure; present the exact plan, closure, rollback boundary, and consent scope; obtain final consent; and only then cross the destructive boundary. F-06 only verifies the resulting handoff and never performs this sequence.

```text
NetworkPolicyEvidence = {
  policy_schema: "f06-network-policy/v1",
  policy_id: PolicyId,
  policy_digest: Digest,
  mode: "deny-after-final-consent/v1",
  allowed_endpoint_set_digest: Digest,
  denied_endpoint_set_digest: Digest,
  denied_operation_set_digest: Digest,
  observed_attempts_digest: Digest,
  evidence_digest: Digest,
  scope: F06Scope,
  valid_from: Timestamp,
  expires_at: Timestamp,
  evidence_ref: F06RecordRef
}
```

`NetworkPolicyEvidence` is complete only when its `allowed_endpoint_set_digest` covers the pre-consent allowlist, its denied endpoint and operation sets cover every post-consent resolver, and its evidence digest is recomputed from the observed deny result and exact consent/scope tuple. After final consent, network acquisition is denied: DNS, HTTP, Git, package resolution, mirror selection, credential lookup, and resolver fallback cannot run. Missing, mutable, incomplete, stale, unapproved, cross-target, digest-mismatched, direct-device-unreceipted, or network-dependent input is `HOLD` `F06-SOURCE-CLOSURE-HOLD` before mutation. A network attempt after consent is `REJECT` `F06-SOURCE-CLOSURE-INCOMPLETE` at `/source_closure/network_policy/mode`; it cannot become a warning-success.

## 10. F-07 sole promotion authority

F-06 has no stable-copy operation, stable storage path, promotion key, release-writer role, or API branch that can write stable. Its only release handoff is a typed request reference to F-07.

```text
F07PromotionRequest = {
  request_schema: "f07-promotion-request/v1",
  request_document_id: DocumentId,
  project_id: ProjectId,
  repository_id: RepositoryId,
  slice_id: SliceId,
  candidate_document_id: DocumentId,
  candidate_payload_digest: Digest,
  candidate_content_digest: Digest,
  candidate_channel: "edge" | "rc",
  target_channel: "stable",
  schema_set_digest: Digest,
  required_slice_closure_digest: Digest,
  f02_manifest_ref: EnvelopeRef,
  f03_trust_ref: F06RecordRef,
  f04_build_provenance_ref: F06RecordRef,
  f05_candidate_ref: F06RecordRef,
  f06_result_ref: F06RecordRef,
  installer_closure_ref: F06RecordRef,
  rollback_ref: F06RecordRef,
  legal_bundle_ref: F06RecordRef,
  qualification_bundle_ref: F06RecordRef,
  support_projection_ref: F06RecordRef,
  public_ledger_ref: F06RecordRef,
  source_closure_ref: F06RecordRef,
  product_integration_ref: F06RecordRef,
  writer_binding_refs: SortedList<F07WriterBindingRef, writer_id>,
  copy_destination_ref: RelativePath,
  request_scope: F06Scope,
  copy_preimage_digest: Digest,
  request_digest: Digest
}
F07PromotionResult = {
  result_schema: "f07-promotion-result/v1",
  result_document_id: DocumentId,
  request_document_id: DocumentId,
  decision: "PROMOTE" | "REJECT",
  candidate_payload_digest: Digest,
  candidate_content_digest: Digest,
  copied_content_digest: Digest | null,
  target_channel: "stable",
  stable_object_ref: RelativePath | null,
  required_slice_closure_digest: Digest,
  copy_preimage_digest: Digest,
  copy_receipt_ref: F07RecordRef | null,
  rejection_code: FailureCode | null,
  rejection_path: JsonPointer | null,
  result_digest: Digest
}
F07WriterBindingRef = {
  writer_id: LowerAsciiToken,
  role_binding_digest: Digest,
  actor_id: ActorId,
  account_id: AccountId,
  scope_digest: Digest,
  valid_from: Timestamp,
  expires_at: Timestamp
}
F07RecordRef = {
  ref_schema: "f07-record-ref/v1",
  record_type: "f07-copy-receipt/v1",
  document_id: DocumentId,
  payload_digest: Digest,
  content_digest: Digest,
  record_digest: Digest,
  scope_digest: Digest
}
```

`candidate_content_digest = sha256(ASCII("omarchy-f07-candidate-content/v1") || 0x00 || exact candidate bytes)`; `copy_preimage_digest = sha256(ASCII("omarchy-f07-copy-preimage/v1") || 0x00 || JCS({candidate_document_id, candidate_payload_digest, candidate_content_digest, candidate_channel, target_channel, schema_set_digest, required_slice_closure_digest, f02_manifest_ref, f03_trust_ref, f04_build_provenance_ref, f05_candidate_ref, f06_result_ref, installer_closure_ref, rollback_ref, legal_bundle_ref, qualification_bundle_ref, support_projection_ref, public_ledger_ref, source_closure_ref, product_integration_ref, writer_binding_refs, copy_destination_ref, request_scope}))`; `request_digest = sha256(ASCII("omarchy-f07-promotion-request/v1") || 0x00 || JCS(F07PromotionRequest without request_digest))`. F-07 recomputes these preimages, every referenced digest, the complete required-slice closure, all applicable board/profile qualification, legal/source/notice, support/public projection, rollback, installer, product-integration, and health evidence before any exact-copy operation.

`result_digest = sha256(ASCII("omarchy-f07-promotion-result/v1") || 0x00 || JCS(F07PromotionResult without result_digest))`; `F07RecordRef.record_digest` covers its complete closed reference without `record_digest`. Exactly one writer binding may be present, it must be the future F-07 stable writer for the exact request scope, and a duplicate or different writer identity is `F06-F07-DUPLICATE-WRITER`.

Only F-07 may copy the already-built candidate bytes by exact digest. F-07 must reject rebuild, byte substitution, digest substitution, downgrade, channel widening, missing prerequisite, stale health, rollback-lineage mismatch, interrupted copy, partial copy without recovery, duplicate writer, or any alternate stable writer. F-06 records an absent or invalid F-07 handoff as `HOLD`/`REJECT` evidence and never treats its own `ADMIT` as promotion.

## 11. Projection, redaction, and privacy

### 11.1 Consume public/v1; do not redefine it

F-06 consumes the future ratified F-02 `Trusted<PublicProjection>` and `Trusted<ProjectionPolicy>`. It does not define a competing `public/v1` schema, add fields to the F-02 public payload, or accept a consumer-local public map. The exact F-02 public/v1 allowlist is `schema`, `schema_set_digest`, `document_id`, `issued_at`, `expires_at`, `board_id`, `manifest_id`, `manifest_digest`, `channel`, `release_version`, `lifecycle`, `capability_id`, `support_requirement`, `content_digest`, `outcome`, `failure_code`, `projection_version`, and `projection_digest`; `issuer` is transformed only as allowed by the future F-02 projection contract. Any public field outside that allowlist is `F06-PUBLIC-AUTHORITY-REDEFINED`.

F-06 defines only private evidence and handoff wrappers. The private record is constructed from a trusted source before persistence and has exactly `private_schema`, `private_document_id`, `source_record_digest`, `scope`, `trusted_input_refs`, `inventory_digest`, `artifact_set_digest`, `decision_refs`, `review_binding_refs`, `cache_receipt_refs`, `command_vector_digest`, `projection_policy_digest`, `retention_ref`, `acl_binding_refs`, `redaction_rule_digest`, `audit_receipt_ref`, and `private_record_digest`. It contains references and digests, not raw secrets, credentials, raw source bytes, raw device identifiers, or raw command output.

The wrapper and access decision are closed:

```text
ProjectionConsent = {
  consent_schema: "f06-projection-consent/v1",
  consent_document_id: DocumentId,
  scope: F06Scope,
  projection_version: "public/v1" | "private-support/v1" | "evidence-authorized/v1",
  purpose: "qualification-review" | "incident-review" | "release-audit" | "support-diagnostic" | "retention-audit",
  endpoint_allowlist_digest: Digest,
  retention_class: "short" | "standard" | "long" | "legal-hold",
  decision: "allow" | "deny",
  issued_at: Timestamp,
  expires_at: Timestamp,
  role_binding_digest: Digest,
  consent_digest: Digest
}
PrivateEvidenceRecord = {
  private_schema: "f06-private-evidence/v1",
  private_document_id: DocumentId,
  source_record_digest: Digest,
  scope: F06Scope,
  trusted_input_refs: SortedList<F06RecordRef, document_id>,
  inventory_digest: Digest,
  artifact_set_digest: Digest,
  decision_refs: SortedList<SignedDecisionRef, decision_kind>,
  review_binding_refs: SortedList<F06RecordRef, document_id>,
  cache_receipt_refs: SortedList<F06RecordRef, document_id>,
  command_vector_digest: Digest,
  projection_policy_digest: Digest,
  retention_ref: F06RecordRef,
  acl_binding_refs: SortedList<F06RecordRef, document_id>,
  redaction_rule_digest: Digest,
  audit_receipt_ref: F06RecordRef,
  private_record_digest: Digest
}
ProjectionProof = {
  proof_schema: "f06-projection-proof/v1",
  private_record_digest: Digest,
  output_digest: Digest,
  field_allowlist_digest: Digest,
  redaction_rule_digest: Digest,
  acl_decision_digest: Digest,
  projection_policy_digest: Digest,
  clock_digest: Digest,
  audit_receipt_digest: Digest,
  proof_digest: Digest
}
```

`consent_digest = sha256(ASCII("omarchy-f06-projection-consent/v1") || 0x00 || JCS(ProjectionConsent without consent_digest))`; `private_record_digest = sha256(ASCII("omarchy-f06-private-evidence/v1") || 0x00 || JCS(PrivateEvidenceRecord without private_record_digest))`; and `proof_digest = sha256(ASCII("omarchy-f06-projection-proof/v1") || 0x00 || JCS(ProjectionProof without proof_digest))`. The exact `PRIVATE_FIELD_ALLOWLIST` is the 17 private-record fields above; the public allowlist remains solely future F-02 `public/v1`. `ProjectionConsent` must be current, scope-equal, purpose-limited, ACL-bound, endpoint-bound, and explicit before any output is persisted. Missing consent is `HOLD`, not local default allow.

### 11.2 Allowlist, redaction order, pseudonyms, and proof

The private evidence allowlist is closed to the fields above. The public projection is the future F-02 public/v1 object. A reviewer projection may contain only exact finding codes/paths, tool versions, census, trusted input digests, correction digest, and pseudonymized reviewer references. A support wrapper may contain only the future public/v1 projection, support-safe finding codes, public artifact digests, rollback digest, support pseudonyms, expiry, and audit receipt. A projection containing a secret field, unclassified field, raw evidence, raw path, raw device token, or authority-bearing private field rejects.

Redaction occurs before persistence: recursively classify each source field, reject any secret path/content, construct a fresh output from the closed allowlist, recompute the output digest, and only then persist. There is no persist-then-redact mode. Forbidden field/content classes are `password`, `passphrase`, `credential`, `token`, `private_key`, `signature_bytes`, `bearer`, `raw_serial`, `raw_uuid`, `filesystem_path`, `home_path`, `hostname`, `MAC`, `IP`, `SSID`, `BSSID`, `raw_partition_map`, `raw_command_output`, `raw_source_bytes`, and `customer_data`; any occurrence in a key, value, URI, log, evidence payload, or projection is `F06-OUTPUT-SECRET-CONTENT` or `F06-OUTPUT-PRIVATE-FIELD-LEAK`.

Pseudonyms use the exact future F-02 preimage `HMAC_input = ASCII("omarchy-public-pseudonym/v1") || 0x00 || UTF8(field_path) || 0x00 || UTF8(normalized_private_value)` and `token = "pseudonym:v1:" || decimal(hmac_key_version) || ":" || base64url(HMAC-SHA256(K[hmac_key_domain, hmac_key_version], HMAC_input))`. The key is supplied only by the future ratified projection authority, never enters a payload, and is bound to `ProjectionPolicy` and `projection_policy_digest`. A bare hash, changed domain, changed field path, changed normalization, unknown key version, or key supplied by F-06 is invalid.

Every private/reviewer/support handoff includes `projection_policy_digest`; the exact future F-02 public/v1 object is not modified to add it. The projection proof contains `source_record_digest`, `output_digest`, `field_allowlist_digest`, `redaction_rule_digest`, `acl_decision_digest`, `projection_policy_digest`, `clock_digest`, and `audit_receipt_digest`. The noninterference test changes every forbidden private field one at a time and requires the public/support bytes to remain identical while the private source digest and audit proof change. The proof also verifies output derives from the exact private record, not from a parallel summary. Missing policy, wrong ACL, wrong key, leakage, digest mismatch, or noninterference failure blocks publication.

ACL access is granted only by exact future F-03 binding references and purpose-limited evidence authorization. The closed access purposes are `qualification-review`, `incident-review`, `release-audit`, `support-diagnostic`, and `retention-audit`; the closed retention classes are `short`, `standard`, `long`, and `legal-hold`. Local-default handling is fail-closed: absent ACL, absent consent, absent endpoint allowlist, absent retention class, or absent policy produces HOLD and persists no sensitive output. Network endpoints for projection/evidence access are an explicit allowlisted digest set bound by `ProjectionConsent.endpoint_allowlist_digest`; F-06 never discovers an endpoint.

## 12. Immutable retention and deletion

### 12.1 Frozen retention lock and states

The future `f06-retention-lock/v1` freezes these values: `short_days = 730`, `standard_days = 2555`, `long_days = 3650`, `tombstone_days = 3650`, `signed_extension_max_days = 365`, `clock_skew_seconds = 0`, and `max_dependency_depth = 64`. Its closed lock preimage is `retention_lock_digest = sha256(ASCII("omarchy-f06-retention-lock/v1") || 0x00 || JCS({lock_schema, short_days, standard_days, long_days, tombstone_days, signed_extension_max_days, clock_skew_seconds, max_dependency_depth}))`; it has no implementation-selected field, current date, or self-digest. Legal hold has no expiry while active. These are contract values, not implementation-selected policy; a missing concrete lock is `F06-RETENTION-LOCK-MISSING`/`HOLD`.

The only retention states are `retained`, `blocked`, `eligible`, `authorized`, `deleting`, `partial`, and `tombstoned`. The only transitions are `retained -> blocked|eligible`, `blocked -> retained|eligible`, `eligible -> authorized`, `authorized -> deleting`, `deleting -> tombstoned|partial`, and `partial -> deleting|blocked`. `tombstoned` is terminal. A tombstone is not deletion authority and never hides the historical record digest.

`RetentionRecord` has exactly `retention_schema`, `record_id`, `record_content_digest`, `scope`, `retention_lock_digest`, `retention_class`, `retained_until`, `state`, `legal_hold_refs`, `extension_refs`, `correction_chain_digest`, `rollback_dependency_digest`, `active_channel_dependency_digest`, `audit_dependency_digest`, `dependency_proof_digest`, `delete_authorization_ref`, `tombstone_ref`, `result_evidence_ref`, and `retention_digest`. `retention_digest = sha256(ASCII("omarchy-f06-retention/v1") || 0x00 || JCS(RetentionRecord without retention_digest))`.

### 12.2 Precedence, eligibility, authorization, and tombstones

The closed `RetentionExtension`, `CorrectionChainReceipt`, `DependencyProof`, and `DeletionResult` records are:

```text
RetentionExtension = {extension_document_id: DocumentId, record_id: DocumentId, record_content_digest: Digest, scope_digest: Digest, extension_days: uint16, reason_digest: Digest, role_binding_digest: Digest, issued_at: Timestamp, expires_at: Timestamp, extension_digest: Digest}
CorrectionChainReceipt = {receipt_document_id: DocumentId, record_id: DocumentId, predecessor_record_id: DocumentId | null, correction_record_id: DocumentId, predecessor_digest: Digest | null, correction_digest: Digest, scope_digest: Digest, receipt_digest: Digest}
DependencyProof = {proof_document_id: DocumentId, record_id: DocumentId, record_content_digest: Digest, scope_digest: Digest, reachable_dependency_ids: SortedList<DocumentId, document_id>, unresolved_dependency_ids: SortedList<DocumentId, document_id>, dependency_depth: uint16, no_delete: boolean, checked_at: Timestamp, proof_digest: Digest}
DeletionResult = {result_document_id: DocumentId, record_id: DocumentId, record_content_digest: Digest, scope_digest: Digest, state: "tombstoned" | "partial" | "blocked", deleted_object_digest_set: Digest, remaining_object_digest_set: Digest, recovery_cursor: LowerAsciiToken | null, result_decision: "ALLOW" | "HOLD" | "REJECT", result_code: "F06-RETENTION-NOT-ELIGIBLE" | "F06-RETENTION-AUTHORITY-HOLD" | "F06-RETENTION-PARTIAL" | null, evidence_digest: Digest, result_digest: Digest}
```

The corresponding preimages exclude the named derived digest: `extension_digest` uses `omarchy-f06-retention-extension/v1`, `receipt_digest` uses `omarchy-f06-correction-chain/v1`, `proof_digest` uses `omarchy-f06-dependency-proof/v1`, and `result_digest` uses `omarchy-f06-deletion-result/v1`. The total precedence is `active legal hold > active signed extension > open correction/supersession chain > reachable rollback dependency > active channel/public ledger dependency > reachable audit/support dependency > retained_until > delete authorization`. The eligibility algorithm evaluates those predicates in that order, requires `retention_lock_digest` to equal the frozen lock, requires no unresolved dependency and `dependency_depth <= 64`, verifies every correction-chain receipt, and requires a signed delete authorization bound to the exact future F-03 retention authority, record ID, content digest, scope, policy, clock, and replay identity. A legal hold, extension, dependency, or retention interval rejects deletion with its exact code; an absent authority or incomplete dependency proof is HOLD; no record is deleted merely because its nominal date passed.

The delete authorization is closed to `authorization_document_id`, `record_id`, `record_content_digest`, `scope_digest`, `policy_digest`, `dependency_proof_digest`, `requested_at`, `expires_at`, `role_binding_digest`, `replay_id`, and `authorization_digest`; `authorization_digest = sha256(ASCII("omarchy-f06-delete-authorization/v1") || 0x00 || JCS(delete_authorization without authorization_digest))`. It must resolve through a future F-03 binding whose service policy explicitly authorizes retention deletion; F-06 never invents a retention-custodian role, so absent representable authority is `HOLD`. The tombstone is closed to `tombstone_schema = "f06-tombstone/v1"`, `tombstone_document_id`, `record_id`, `record_content_digest`, `prior_retention_digest`, `eligibility_proof_digest`, `delete_authorization_digest`, `scope_digest`, `deleted_at`, `state = "tombstoned"`, and `tombstone_digest`; `tombstone_digest = sha256(ASCII("omarchy-f06-tombstone/v1") || 0x00 || JCS(tombstone without tombstone_digest))`.

Deletion is idempotent: an exact existing tombstone returns the same tombstone receipt and performs no second delete; a differing tombstone is a mismatch. A partial delete atomically records `partial`, the exact deleted/remaining object digest sets, the failure evidence, result code, and recovery cursor; restart rereads that record and resumes only the remaining exact IDs. It never guesses, broadens scope, deletes by path, or treats a partial delete as complete. Legal-hold release, signed extension, correction closure, dependency clearance, delete authorization, tombstone, and result evidence are retained under the same lock.

## 13. Executable acceptance contract

### 13.1 Future tracked deliverables

The following paths are the exact future F-06 deliverable set. None exists in this design-only checkout, and every item is `NOT IMPLEMENTED` until its file, lock, generator/validator behavior, fixture corpus, and clean-checkout evidence are independently observed:

```text
schemas/f06/v1/request.schema.json
schemas/f06/v1/inventory.schema.json
schemas/f06/v1/decision.schema.json
schemas/f06/v1/source-closure.schema.json
schemas/f06/v1/event.schema.json
schemas/f06/v1/projection.schema.json
schemas/f06/v1/retention.schema.json
schemas/f06/v1/f07-handoff.schema.json
schemas/f06/v1/parse-rejection.schema.json
schemas/f06/v1/report.schema.json
schemas/f06/v1/grammar.lock.json
schemas/f06/v1/policy.lock.json
schemas/f06/v1/fixture-manifest.json
bindings/f06/v1/python/generated.py
bindings/f06/v1/swift/Generated.swift
bindings/f06/v1/rust-boot/generated.rs
src/__init__.py
src/f06/__init__.py
src/f06/validator.py
src/f06/inventory.py
src/f06/decisions.py
src/f06/events.py
src/f06/projection.py
src/f06/retention.py
src/f06/f07_handoff.py
src/f06/report.py
reports/f06/v1/report.json
tests/f06/fixtures/positive.jsonl
tests/f06/fixtures/hostile.jsonl
tests/f06/fixtures/manifest.json
.github/workflows/f06-clean-checkout.yml
```

The future implementation must not add a second schema family, local F-02 field list, local F-03 role table, alternate public/v1 schema, stable-copy command, or an additional fixture directory not named by the manifest. These paths are a deliverable contract, not evidence that they exist.

### 13.2 Pinned tool, runtime, container, and command contract

The future lock must pin exact versions and content digests: CPython `3.12.8`; Swift `6.0.3` with macOS SDK `15.2`; Rust `1.84.1` stable for target `aarch64-unknown-none`; Git `2.45.2`; ripgrep `14.1.1`; JSON Schema Draft `2020-12`; RFC 8785 implementation identity `omarchy-jcs/v1` and its concrete F-02 lock version/digest; and container `f06-validator/v1` with a concrete `sha256:` image digest supplied by the implementation lock. An unavailable exact version or missing digest is `TOOLING_BLOCK`, never PASS. The future lock also pins every module source digest, generated output digest, schema-set digest, fixture-manifest digest, and command-vector digest.

The command vector is a valid JSON value containing only argv arrays. It contains no shell conditionals, shell pipelines, JSON-like pseudo-arrays, escaped globs, ellipses, environment fallback, or unbounded discovery:

```json
[
  ["git", "status", "--porcelain=v1", "--untracked-files=all"],
  ["git", "diff", "--check", "--exit-code", "--", "docs/design/release-compliance.md"],
  ["git", "diff", "--quiet", "--exit-code", "--"],
  ["git", "ls-files", "--others", "--exclude-standard"],
  ["python3.12", "-m", "src.f06.validator", "--request", "tests/f06/fixtures/manifest.json", "--report", "reports/f06/v1/report.json"],
  ["python3.12", "-m", "src.f06.inventory", "--schema", "schemas/f06/v1/inventory.schema.json", "--fixtures", "tests/f06/fixtures/manifest.json"],
  ["python3.12", "-m", "src.f06.decisions", "--schema", "schemas/f06/v1/decision.schema.json", "--fixtures", "tests/f06/fixtures/manifest.json"],
  ["python3.12", "-m", "src.f06.events", "--schema", "schemas/f06/v1/event.schema.json", "--fixtures", "tests/f06/fixtures/manifest.json"],
  ["python3.12", "-m", "src.f06.projection", "--schema", "schemas/f06/v1/projection.schema.json", "--policy-lock", "schemas/f06/v1/policy.lock.json"],
  ["python3.12", "-m", "src.f06.retention", "--schema", "schemas/f06/v1/retention.schema.json", "--policy-lock", "schemas/f06/v1/policy.lock.json"],
  ["python3.12", "-m", "src.f06.f07_handoff", "--schema", "schemas/f06/v1/f07-handoff.schema.json", "--fixtures", "tests/f06/fixtures/manifest.json"],
  ["python3.12", "-m", "src.f06.report", "--schema", "schemas/f06/v1/report.schema.json", "--report", "reports/f06/v1/report.json"],
  ["rg", "--line-number", "--hidden", "--glob", "!.git/**", "<<<<<<<", "schemas", "src", "tests", "reports", ".github"],
  ["rg", "--line-number", "--hidden", "--glob", "!.git/**", "private_key|password|bearer", "schemas", "src", "tests", "reports", ".github"],
  ["rg", "--pcre2", "--line-number", "--hidden", "--glob", "!.git/**", "(^|[^A-Za-z0-9_])/(?!/)|file://|\\.\\./|(^|[^A-Za-z0-9_])~", "schemas", "src", "tests", "reports", ".github"],
  ["rg", "--line-number", "--hidden", "--glob", "!.git/**", "UNRESOLVED_MARKER|PLACEHOLDER_DIGEST|PLACEHOLDER_PATH", "schemas", "src", "tests", "reports", ".github"],
  ["git", "ls-files", "--error-unmatch", "schemas/f06/v1/request.schema.json", "schemas/f06/v1/inventory.schema.json", "schemas/f06/v1/decision.schema.json", "schemas/f06/v1/source-closure.schema.json", "schemas/f06/v1/event.schema.json", "schemas/f06/v1/projection.schema.json", "schemas/f06/v1/retention.schema.json", "schemas/f06/v1/f07-handoff.schema.json", "schemas/f06/v1/parse-rejection.schema.json", "schemas/f06/v1/report.schema.json", "schemas/f06/v1/grammar.lock.json", "schemas/f06/v1/policy.lock.json", "schemas/f06/v1/fixture-manifest.json", "src/__init__.py", "src/f06/__init__.py", "src/f06/validator.py", "src/f06/inventory.py", "src/f06/decisions.py", "src/f06/events.py", "src/f06/projection.py", "src/f06/retention.py", "src/f06/f07_handoff.py", "src/f06/report.py", "reports/f06/v1/report.json", "tests/f06/fixtures/positive.jsonl", "tests/f06/fixtures/hostile.jsonl", "tests/f06/fixtures/manifest.json"]
]
```

For the `rg` assertions, exit code 1 means no match and is a pass; exit code 0 means a forbidden match and is a fail; any other exit code is `TOOLING_BLOCK`. The final `git status` must be empty, `git diff --check` must be zero, every named deliverable must be tracked, no untracked generated output may exist, and the command vector itself must be hashed into the report. A command that discovers files through an unbound glob is invalid; the manifest must enumerate each file.

The command vector contains exactly 17 argv arrays: four repository-state checks, eight future module invocations, four forbidden-content scans, and one tracked-deliverable enumeration.

### 13.3 Runner phases, reports, and clean-checkout semantics

The future runner executes every phase in order and never skips a missing phase:

| Phase | Required artifact | Exact result semantics |
| --- | --- | --- |
| `F06-P0` | Parse-rejection schema and transport report | `PASS` only for all transport vectors; malformed input returns the declared structural envelope |
| `F06-P1` | Grammar/schema/bounds report | Exact code/path for every shape, bound, identifier, path, duplicate, and ordering vector |
| `F06-P2` | JCS/preimage report | Exact canonical bytes and every domain-separated digest vector |
| `F06-P3` | F-02/F-03 trust and generated-binding report | `HOLD` when foundations are absent; no local substitute or partial trusted value |
| `F06-P4` | Identity/scope/replay report | Exact namespace, scope, freshness, and anti-transplant outcomes |
| `F06-P5` | Inventory/source closure report | Exact graph, artifact, exclusion, cache, and network-denial outcomes |
| `F06-P6` | Provenance/license/source decision report | Exact per-artifact and variant-complete closure |
| `F06-P7` | Decision/role/policy report | Exact signer/account/method/result/proof/expiry/replay/scope outcomes |
| `F06-P8` | Event/projection/retention report | Exact lineage, redaction, ACL, retention, tombstone, and recovery outcomes |
| `F06-P9` | F-07 handoff report | Exact typed request/result and no-local-promotion proof |
| `F06-P10` | Signed report and clean-checkout receipt | Exact census, command digest, tracked-artifact, secret, conflict, absolute-path, and placeholder outcomes |

`f06-report/v1` has exactly `report_schema`, `report_document_id`, `commit_sha`, `clean_checkout`, `scope`, `schema_set_digest`, `grammar_lock_digest`, `policy_lock_digest`, `fixture_manifest_digest`, `tool_versions`, `container_digest`, `command_vector_digest`, `phase_results`, `fixture_results`, `pass_count`, `fail_count`, `not_executable_count`, `tooling_block_count`, `primary_finding`, `artifact_refs`, `reviewer_binding_ref`, `started_at`, `finished_at`, `expires_at`, `correction_chain_digest`, `retention_ref`, and `report_digest`. `report_digest` excludes itself from its preimage. Every phase and every fixture has one result; a missing result is `F06-REPORT-CENSUS-INCOMPLETE`.

The current design-time runner result is `NOT EXECUTABLE`: none of the future schemas, bindings, validators, fixture files, reports, locks, CI workflow, F-03 resolver, F-04 adapters, F-05 guard, installer cache enforcement, F-07 terminal, legal decisions, physical evidence, or release evidence exists in this design checkout. A missing runtime artifact is never a PASS.

## 14. Hostile and positive fixture manifest

The fixture manifest is closed to the hostile IDs below and the positive IDs below. Each fixture has one canonical baseline, exactly one mutation, one expected decision, one exact code, one exact pointer, one exact F-06 phase, and one expected result evidence record. Every row is currently `NOT IMPLEMENTED`; a prose model is not a runnable fixture. The runner must construct every row, plant only its mutation, and compare code, path, phase, decision, and result digest. No fixture may combine mutations.

### 14.1 Hostile fixtures

| Fixture ID | Single mutation | Expected decision | Expected code | Exact JSON Pointer | Phase | Current |
| --- | --- | --- | --- | --- | --- | --- |
| `f02-missing-type` | Remove one member from the eight-type import set | `REJECT` | `F06-F02-TYPE-MISSING` | `/f02_imports` | `F06-P1` | `NOT IMPLEMENTED` |
| `f02-unknown-ninth-type` | Add a ninth authenticated payload type | `REJECT` | `F06-F02-TYPE-UNKNOWN` | `/f02_imports/ninth-type~1v1` | `F06-P1` | `NOT IMPLEMENTED` |
| `f02-binding-absent-hold` | Remove the ratified generated Trusted binding receipt | `HOLD` | `F06-F02-BINDING-HOLD` | `/f02_bindings/platform-manifest~1v1` | `F06-P3` | `NOT IMPLEMENTED` |
| `f02-binding-stale-generated` | Use an expired generated-output lock receipt | `HOLD` | `F06-F02-BINDING-HOLD` | `/f02_bindings/platform-manifest~1v1/compiled_lock_digest` | `F06-P3` | `NOT IMPLEMENTED` |
| `f02-binding-locally-copied` | Supply a consumer-local field model without a trusted receipt | `HOLD` | `F06-F02-BINDING-HOLD` | `/f02_bindings/platform-manifest~1v1/source_binding_digest` | `F06-P3` | `NOT IMPLEMENTED` |
| `f02-generated-digest-mismatch` | Change generated output digest while retaining the compiled lock | `HOLD` | `F06-F02-BINDING-HOLD` | `/f02_bindings/platform-manifest~1v1/generated_output_digest` | `F06-P3` | `NOT IMPLEMENTED` |
| `envelope-schema-set-transplant` | Replace schema-set digest while retaining producer bytes | `REJECT` | `F06-IDENTITY-NAMESPACE-MISMATCH` | `/f02_imports/platform-manifest~1v1/schema_set_digest` | `F06-P4` | `NOT IMPLEMENTED` |
| `envelope-document-id-transplant` | Reuse a document ID from a different payload | `REJECT` | `F06-IDENTITY-NAMESPACE-MISMATCH` | `/f02_imports/platform-manifest~1v1/document_id` | `F06-P4` | `NOT IMPLEMENTED` |
| `envelope-payload-digest-transplant` | Copy a payload digest from another document | `REJECT` | `F06-IDENTITY-DIGEST-MISMATCH` | `/f02_imports/platform-manifest~1v1/payload_digest` | `F06-P2` | `NOT IMPLEMENTED` |
| `envelope-signed-field-redefined` | Add signature or signed_metadata fields to EnvelopeRef | `REJECT` | `F06-INPUT-UNKNOWN-FIELD` | `/f02_imports/platform-manifest~1v1/signed_metadata` | `F06-P1` | `NOT IMPLEMENTED` |
| `document-vs-payload-digest-collapse` | Set document_id equal to payload_digest | `REJECT` | `F06-IDENTITY-NAMESPACE-MISMATCH` | `/f02_imports/platform-manifest~1v1/document_id` | `F06-P2` | `NOT IMPLEMENTED` |
| `f02-component-path-alias` | Rename `components.linux_kernel` to `components.kernel` | `REJECT` | `F06-INPUT-UNKNOWN-FIELD` | `/f02_imports/platform-manifest~1v1/payload/components/kernel` | `F06-P1` | `NOT IMPLEMENTED` |
| `decision-loose-reference` | Put a decision digest in an unattached collection | `REJECT` | `F06-DECISION-UNATTACHED` | `/decision_bindings/unattached` | `F06-P7` | `NOT IMPLEMENTED` |
| `decision-wrong-role` | Use a binding whose role is not authorized for the disposition | `REJECT` | `F06-TRUST-ROLE-SCOPE-MISMATCH` | `/decision_bindings/redistribution/role_binding_digest` | `F06-P7` | `NOT IMPLEMENTED` |
| `role-scope-project-transplant` | Change project while retaining signer and decision bytes | `REJECT` | `F06-SCOPE-MISMATCH` | `/decision_bindings/license/project_id` | `F06-P4` | `NOT IMPLEMENTED` |
| `role-scope-operation-transplant` | Change operation from evaluate to publish | `REJECT` | `F06-SCOPE-MISMATCH` | `/decision_bindings/owner/operation` | `F06-P4` | `NOT IMPLEMENTED` |
| `decision-method-result-proof-missing` | Remove method, result, or proof digest | `REJECT` | `F06-DECISION-PROOF-MISSING` | `/decision_bindings/counsel/proof_digest` | `F06-P7` | `NOT IMPLEMENTED` |
| `decision-expiry-replay` | Reuse an expired decision replay identity | `REJECT` | `F06-TRUST-DECISION-REPLAYED` | `/decision_bindings/license/replay_id` | `F06-P7` | `NOT IMPLEMENTED` |
| `decision-rejection-code-path-unbound` | Emit a deny decision without its exact rejection code/path/phase | `REJECT` | `F06-DECISION-REJECTION-UNBOUND` | `/decision_bindings/security/rejection_code` | `F06-P7` | `NOT IMPLEMENTED` |
| `inventory-disconnected-node` | Add a node not reachable from any root | `REJECT` | `F06-INVENTORY-NODE-DISCONNECTED` | `/inventory/nodes/node:disconnected` | `F06-P5` | `NOT IMPLEMENTED` |
| `inventory-duplicate-node` | Add two nodes with one semantic key | `REJECT` | `F06-INVENTORY-SEMANTIC-DUPLICATE` | `/inventory/nodes/node:duplicate/semantic_key` | `F06-P1` | `NOT IMPLEMENTED` |
| `inventory-singular-artifact` | Replace artifact ID array with a singular object | `REJECT` | `F06-INVENTORY-ARTIFACT-SHAPE` | `/inventory/nodes/node:artifact/artifact_ids` | `F06-P1` | `NOT IMPLEMENTED` |
| `inventory-missing-root` | Remove the source-closure root | `REJECT` | `F06-INVENTORY-ROOT-MISSING` | `/inventory/root_node_ids` | `F06-P5` | `NOT IMPLEMENTED` |
| `inventory-cycle` | Add a dependency edge from a node to an ancestor | `REJECT` | `F06-INVENTORY-CYCLE` | `/inventory/edges/edge:cycle` | `F06-P5` | `NOT IMPLEMENTED` |
| `inventory-orphan-artifact` | Add an artifact with no reachable owner node | `REJECT` | `F06-INVENTORY-NODE-ORPHAN` | `/inventory/artifacts/artifact:orphan/owner_node_ids` | `F06-P5` | `NOT IMPLEMENTED` |
| `inventory-exclusion-contradiction` | Exclude a source that is reachable and required | `REJECT` | `F06-INVENTORY-EXCLUSION-CONTRADICTION` | `/inventory/exclusions/exclusion:reachable` | `F06-P5` | `NOT IMPLEMENTED` |
| `inventory-ambiguous-artifact-owner` | Give one artifact owners with different content roles | `REJECT` | `F06-INVENTORY-AMBIGUOUS-OWNER` | `/inventory/artifacts/artifact:shared/owner_node_ids` | `F06-P5` | `NOT IMPLEMENTED` |
| `inventory-duplicate-edge` | Repeat one edge semantic tuple | `REJECT` | `F06-INVENTORY-EDGE-DUPLICATE` | `/inventory/edges/edge:duplicate` | `F06-P1` | `NOT IMPLEMENTED` |
| `duplicate-scope-key` | Duplicate a decision/component semantic scope | `REJECT` | `F06-SCOPE-DUPLICATE` | `/decision_bindings/redistribution/component_paths/1` | `F06-P1` | `NOT IMPLEMENTED` |
| `path-malformed` | Use absolute, parent, wildcard, and leading-zero index syntax | `REJECT` | `F06-INPUT-MALFORMED` | `/scope/component_paths/0` | `F06-P1` | `NOT IMPLEMENTED` |
| `condition-malformed` | Use an unknown condition kind | `REJECT` | `F06-INPUT-MALFORMED` | `/policy/root_condition/kind` | `F06-P1` | `NOT IMPLEMENTED` |
| `bound-exact-plus-one` | Set nodes to 65,537 | `REJECT` | `F06-BOUND-EXCEEDED` | `/inventory/nodes` | `F06-P1` | `NOT IMPLEMENTED` |
| `unknown-identifier-normalization` | Use uppercase or Unicode lookalike in an identifier | `REJECT` | `F06-INPUT-MALFORMED` | `/scope/candidate_document_id` | `F06-P1` | `NOT IMPLEMENTED` |
| `f02-error-code-laundering` | Map an F-02 `TRUST_FAILURE` rejection to generic warning-success | `REJECT` | `F06-F02-SOURCE-TRUST_FAILURE` | `/f02_findings/0/source_code` | `F06-P3` | `NOT IMPLEMENTED` |
| `simultaneous-failure-order` | Plant malformed, missing, duplicate, and scope failures together | `REJECT` | `F06-INPUT-MALFORMED` | `/request` | `F06-P0` | `NOT IMPLEMENTED` |
| `input-order-instability` | Permute unordered handoff maps and compare primary result | `REJECT` | `F06-CANONICAL-ORDER` | `/handoffs` | `F06-P2` | `NOT IMPLEMENTED` |
| `handshake-version-mismatch` | Offer minor 1 when supported minor is 0 | `REJECT` | `F06-HANDSHAKE-VERSION` | `/handshake/minor` | `F06-P1` | `NOT IMPLEMENTED` |
| `handshake-capability-mismatch` | Omit one required capability and add an unknown one | `REJECT` | `F06-HANDSHAKE-CAPABILITY` | `/handshake/capabilities/0` | `F06-P1` | `NOT IMPLEMENTED` |
| `handshake-schema-mismatch` | Replace schema-set digest | `REJECT` | `F06-HANDSHAKE-SCHEMA` | `/handshake/schema_set_digest` | `F06-P4` | `NOT IMPLEMENTED` |
| `handshake-downgrade` | Select an older grammar or binding lock | `REJECT` | `F06-HANDSHAKE-DOWNGRADE` | `/handshake/minor` | `F06-P1` | `NOT IMPLEMENTED` |
| `event-supersession-cycle` | Make a correction predecessor point to its descendant | `REJECT` | `F06-EVENT-CYCLE` | `/events/event:cycle/predecessor_event_id` | `F06-P8` | `NOT IMPLEMENTED` |
| `event-generation-rollback` | Lower generation below predecessor | `REJECT` | `F06-EVENT-GENERATION-ROLLBACK` | `/events/event:rollback/generation` | `F06-P8` | `NOT IMPLEMENTED` |
| `event-replay` | Reuse nonce with changed event bytes | `REJECT` | `F06-EVENT-REPLAY` | `/events/event:replay/replay_identity` | `F06-P8` | `NOT IMPLEMENTED` |
| `event-current-ambiguity` | Create two maximal current records in one scope | `REJECT` | `F06-EVENT-CURRENT-AMBIGUOUS` | `/events/current_record_ids` | `F06-P8` | `NOT IMPLEMENTED` |
| `event-cross-scope-replay` | Replay event across repository and candidate scope | `REJECT` | `F06-EVENT-SCOPE-TRANSPLANT` | `/events/event:transplant/scope` | `F06-P8` | `NOT IMPLEMENTED` |
| `event-restart-truncation` | Truncate a committed record after its commit marker | `HOLD` | `F06-EVENT-TRUNCATED` | `/events/event:torn/commit_state` | `F06-P8` | `NOT IMPLEMENTED` |
| `event-interrupted-restart` | Leave a prepared event without its atomic commit | `HOLD` | `F06-EVENT-RESTART-INCOMPLETE` | `/events/event:prepared/commit_state` | `F06-P8` | `NOT IMPLEMENTED` |
| `event-sequence-wrap` | Increment maximum uint64 sequence | `HOLD` | `F06-EVENT-SEQUENCE-FAILURE` | `/events/event:max/sequence` | `F06-P8` | `NOT IMPLEMENTED` |
| `license-alternative-ambiguous` | Select zero or two options for `one-of` | `REJECT` | `F06-LICENSE-CHOICE-AMBIGUOUS` | `/license_bindings/artifact:one/selected_option_ids` | `F06-P7` | `NOT IMPLEMENTED` |
| `license-authoritative-root-missing` | Remove the F-04 source/provenance root | `HOLD` | `F06-PROVENANCE-MISSING` | `/inventory/root_node_ids/source-closure` | `F06-P6` | `NOT IMPLEMENTED` |
| `source-content-preimage-mismatch` | Change source bytes while retaining content digest | `REJECT` | `F06-SOURCE-CONTENT-MISMATCH` | `/license_bindings/artifact:one/source_offer_ids/0` | `F06-P6` | `NOT IMPLEMENTED` |
| `source-offer-incomplete` | Remove source digest, size, or availability evidence | `REJECT` | `F06-SOURCE-OFFER-INCOMPLETE` | `/license_bindings/artifact:one/source_offer_ids/0` | `F06-P7` | `NOT IMPLEMENTED` |
| `source-offer-unsigned` | Remove source-offer signature reference | `REJECT` | `F06-SOURCE-OFFER-UNSIGNED` | `/source_offers/offer:one/signature_ref` | `F06-P7` | `NOT IMPLEMENTED` |
| `source-offer-unavailable` | Expire all source-offer locations | `REJECT` | `F06-SOURCE-OFFER-UNAVAILABLE` | `/source_offers/offer:one/availability_evidence_ids` | `F06-P7` | `NOT IMPLEMENTED` |
| `counsel-join-mismatch` | Change counsel interpretation digest without its signed join | `REJECT` | `F06-COUNSEL-CONTRADICTION` | `/decision_bindings/counsel/join_digest` | `F06-P7` | `NOT IMPLEMENTED` |
| `branding-join-mismatch` | Add an unapproved rendered trademark location | `REJECT` | `F06-BRANDING-UNRESOLVED` | `/decisions/branding_trademark/rendered_locations/0` | `F06-P7` | `NOT IMPLEMENTED` |
| `owner-checkpoint-self-approval` | Use the record author as owner approver | `REJECT` | `F06-IDENTITY-INTERSECTION` | `/roles/owner` | `F06-P8` | `NOT IMPLEMENTED` |
| `direct-fetch-cache-missing` | Omit receipt for a direct-device input | `HOLD` | `F06-SOURCE-CLOSURE-HOLD` | `/source_closure/receipt_refs/0` | `F06-P5` | `NOT IMPLEMENTED` |
| `recovery-stub-cross-target` | Use a Recovery-stub receipt for another board | `HOLD` | `F06-SOURCE-CLOSURE-HOLD` | `/source_closure/receipt_refs/0/scope/board_id` | `F06-P5` | `NOT IMPLEMENTED` |
| `package-index-missing` | Omit signed package-index metadata | `HOLD` | `F06-SOURCE-CLOSURE-HOLD` | `/source_closure/receipt_refs/package-index` | `F06-P5` | `NOT IMPLEMENTED` |
| `source-closure-incomplete` | Omit an image, package, or opaque external input | `HOLD` | `F06-SOURCE-CLOSURE-INCOMPLETE` | `/inventory/root_node_ids/source-closure` | `F06-P5` | `NOT IMPLEMENTED` |
| `mutation-network-allowed` | Change network mode from deny-after-final-consent | `REJECT` | `F06-SOURCE-CLOSURE-INCOMPLETE` | `/source_closure/network_policy/mode` | `F06-P5` | `NOT IMPLEMENTED` |
| `installer-plan-payload-field-added` | Add cache receipt field to closed installer plan | `REJECT` | `F06-INPUT-UNKNOWN-FIELD` | `/f02_imports/installer-plan~1v1/payload/cache_receipts` | `F06-P1` | `NOT IMPLEMENTED` |
| `f06-local-promotion` | Add an F-06 stable-copy operation | `REJECT` | `F06-F07-PROMOTION-BYPASS` | `/operation` | `F06-P9` | `NOT IMPLEMENTED` |
| `f07-handoff-missing` | Remove one typed F-07 prerequisite reference | `REJECT` | `F06-F07-HANDOFF-MISSING` | `/f07_handoff/f04_build_provenance_ref` | `F06-P9` | `NOT IMPLEMENTED` |
| `f07-copy-preimage-mismatch` | Change rollback or legal digest without recomputing copy preimage | `REJECT` | `F06-F07-COPY-PREIMAGE-MISMATCH` | `/f07_handoff/copy_preimage_digest` | `F06-P9` | `NOT IMPLEMENTED` |
| `f07-duplicate-writer` | Present two stable writer identities | `REJECT` | `F06-F07-DUPLICATE-WRITER` | `/f07_handoff/writer_binding_refs/1` | `F06-P9` | `NOT IMPLEMENTED` |
| `f07-interrupted-copy` | Report stable copy after a partial write | `REJECT` | `F06-F07-INTERRUPTED-COPY` | `/f07_handoff/copy_receipt_ref` | `F06-P9` | `NOT IMPLEMENTED` |
| `f07-rollback-lineage-mismatch` | Use rollback evidence from another candidate lineage | `REJECT` | `F06-F07-ROLLBACK-MISMATCH` | `/f07_handoff/rollback_ref` | `F06-P9` | `NOT IMPLEMENTED` |
| `f07-downgrade` | Request stable target below candidate policy minimum | `REJECT` | `F06-F07-DOWNGRADE` | `/f07_handoff/target_channel` | `F06-P9` | `NOT IMPLEMENTED` |
| `public-private-field-leak` | Include a private filesystem path in public output | `REJECT` | `F06-OUTPUT-PRIVATE-FIELD-LEAK` | `/public/filesystem_path` | `F06-P8` | `NOT IMPLEMENTED` |
| `projection-unredacted-before-persist` | Persist raw evidence before redaction | `REJECT` | `F06-OUTPUT-PRIVATE-FIELD-LEAK` | `/private_persist_order` | `F06-P8` | `NOT IMPLEMENTED` |
| `projection-secret-path` | Include a credential path in a projection | `REJECT` | `F06-OUTPUT-SECRET-CONTENT` | `/support/credential_path` | `F06-P8` | `NOT IMPLEMENTED` |
| `projection-policy-digest-omitted` | Remove policy digest from private wrapper proof | `REJECT` | `F06-PROJECTION-POLICY-MISMATCH` | `/private/projection_policy_digest` | `F06-P8` | `NOT IMPLEMENTED` |
| `pseudonym-key-mismatch` | Use a bare hash or wrong HMAC key domain | `REJECT` | `F06-OUTPUT-PSEUDONYM-INVALID` | `/support/support_pseudonyms/0` | `F06-P8` | `NOT IMPLEMENTED` |
| `projection-source-digest-mismatch` | Change private source digest without output recomputation | `REJECT` | `F06-OUTPUT-PROJECTION-DIGEST-MISMATCH` | `/private/source_record_digest` | `F06-P8` | `NOT IMPLEMENTED` |
| `projection-public-authority-redefined` | Add a F-06 public field outside future F-02 public/v1 | `REJECT` | `F06-PUBLIC-AUTHORITY-REDEFINED` | `/public/extra_field` | `F06-P8` | `NOT IMPLEMENTED` |
| `projection-acl-missing` | Remove exact evidence-reader ACL binding | `HOLD` | `F06-PROJECTION-ACL-INVALID` | `/private/acl_binding_refs` | `F06-P8` | `NOT IMPLEMENTED` |
| `deletion-under-legal-hold` | Delete while signed legal hold is active | `REJECT` | `F06-RETENTION-HOLD-BLOCKS-DELETION` | `/retention/legal_hold_refs` | `F06-P8` | `NOT IMPLEMENTED` |
| `deletion-under-extension` | Delete while signed extension is active | `REJECT` | `F06-RETENTION-EXTENSION-BLOCKS-DELETION` | `/retention/extension_refs` | `F06-P8` | `NOT IMPLEMENTED` |
| `deletion-under-correction` | Delete a record with an open correction chain | `REJECT` | `F06-RETENTION-CORRECTION-BLOCKS-DELETION` | `/retention/correction_chain_digest` | `F06-P8` | `NOT IMPLEMENTED` |
| `deletion-under-rollback` | Delete an artifact reachable from rollback | `REJECT` | `F06-RETENTION-ROLLBACK-BLOCKS-DELETION` | `/retention/rollback_dependency_digest` | `F06-P8` | `NOT IMPLEMENTED` |
| `deletion-under-reachability` | Delete an event with a reachable descendant | `REJECT` | `F06-RETENTION-REACHABILITY-BLOCKS-DELETION` | `/retention/dependency_proof_digest` | `F06-P8` | `NOT IMPLEMENTED` |
| `retention-policy-mutable` | Change locked standard retention days | `HOLD` | `F06-RETENTION-POLICY-MUTABLE` | `/retention_lock/standard_days` | `F06-P8` | `NOT IMPLEMENTED` |
| `retention-tombstone-mismatch` | Change tombstone prior digest | `REJECT` | `F06-RETENTION-TOMBSTONE-MISMATCH` | `/tombstone/prior_retention_digest` | `F06-P8` | `NOT IMPLEMENTED` |
| `retention-partial-delete` | Mark only one of two objects deleted as complete | `HOLD` | `F06-RETENTION-PARTIAL` | `/retention/state` | `F06-P8` | `NOT IMPLEMENTED` |
| `command-array-invalid` | Encode a glob and conditional as pseudo-shell text | `REJECT` | `F06-COMMAND-ENCODING-INVALID` | `/command_vector/0` | `F06-P1` | `NOT IMPLEMENTED` |
| `absolute-path-in-command` | Add an absolute host path to argv | `REJECT` | `F06-ABSOLUTE-PATH` | `/command_vector/1/3` | `F06-P1` | `NOT IMPLEMENTED` |
| `placeholder-in-lock` | Leave a digest placeholder or unresolved marker in a lock | `REJECT` | `F06-PLACEHOLDER` | `/locks/f06/placeholder` | `F06-P1` | `NOT IMPLEMENTED` |
| `fixture-manifest-missing` | Remove the closed fixture manifest | `REJECT` | `F06-FIXTURE-MANIFEST-MISSING` | `/fixture_manifest_digest` | `F06-P1` | `NOT IMPLEMENTED` |
| `report-schema-missing` | Remove the required report schema | `REJECT` | `F06-REPORT-SCHEMA-MISSING` | `/report` | `F06-P10` | `NOT IMPLEMENTED` |
| `untracked-schema-artifact` | Generate a schema not named and tracked by the lock | `REJECT` | `F06-TRACKED-ARTIFACT-MISSING` | `/artifact_refs/extra` | `F06-P10` | `NOT IMPLEMENTED` |
| `missing-clean-checkout` | Run with an untracked or modified file | `REJECT` | `F06-CLEAN-CHECKOUT-FAILURE` | `/clean_checkout` | `F06-P10` | `NOT IMPLEMENTED` |
| `conflict-marker` | Add a merge conflict marker to a tracked artifact | `REJECT` | `F06-CONFLICT-MARKER` | `/artifact_refs/0/content` | `F06-P10` | `NOT IMPLEMENTED` |
| `secret-scan` | Put a token or password in a report field | `REJECT` | `F06-SECRET-SCAN` | `/report/artifact_refs/0` | `F06-P10` | `NOT IMPLEMENTED` |
| `author-evaluator-overlap` | Assign record author and evaluator to one identity | `REJECT` | `F06-IDENTITY-INTERSECTION` | `/roles/evaluator` | `F06-P8` | `NOT IMPLEMENTED` |
| `evaluator-approver-overlap` | Assign evaluator and approver to one identity | `REJECT` | `F06-IDENTITY-INTERSECTION` | `/roles/approver` | `F06-P8` | `NOT IMPLEMENTED` |
| `retention-custodian-reviewer-overlap` | Assign retention custodian and reviewer to one identity | `REJECT` | `F06-IDENTITY-INTERSECTION` | `/roles/retention_custodian` | `F06-P8` | `NOT IMPLEMENTED` |
| `reviewer-identity-overlap` | Assign record author as independent reviewer and approver | `REJECT` | `F06-IDENTITY-INTERSECTION` | `/roles/independent_reviewer` | `F06-P8` | `NOT IMPLEMENTED` |
| `source-producer-evaluator-overlap` | Assign the source producer as the evaluator of its own evidence | `REJECT` | `F06-IDENTITY-INTERSECTION` | `/roles/evaluator` | `F06-P8` | `NOT IMPLEMENTED` |
| `multi-role-binding` | Assign one identity to two forbidden F-06 roles | `REJECT` | `F06-IDENTITY-INTERSECTION` | `/roles/identity` | `F06-P8` | `NOT IMPLEMENTED` |
| `role-replay-across-scope` | Reuse one role replay identity for another candidate scope | `REJECT` | `F06-DECISION-TRANSPLANT` | `/decision_bindings/owner/replay_id` | `F06-P7` | `NOT IMPLEMENTED` |
| `handoff-omitted` | Remove the F-06-to-F-07 handoff row | `REJECT` | `F06-F07-HANDOFF-MISSING` | `/handoffs/f06-to-f07` | `F06-P9` | `NOT IMPLEMENTED` |
| `qualification-scope-stale` | Use qualification evidence for an older manifest digest | `REJECT` | `F06-SCOPE-MISMATCH` | `/handoffs/q00-to-f06/exact_scope/manifest_digest` | `F06-P4` | `NOT IMPLEMENTED` |
| `support-public-projection-mismatch` | Change support projection without public source digest | `REJECT` | `F06-OUTPUT-PROJECTION-DIGEST-MISMATCH` | `/handoffs/support-to-f06/content_digest` | `F06-P8` | `NOT IMPLEMENTED` |
| `public-ledger-source-offer-mismatch` | Publish a source-offer index for another candidate | `REJECT` | `F06-SCOPE-MISMATCH` | `/handoffs/ledger-to-f06/candidate_payload_digest` | `F06-P4` | `NOT IMPLEMENTED` |

### 14.2 Positive fixtures

The positive fixture IDs are exactly `valid-source-complete`, `valid-license-one-of`, `valid-source-offer`, `valid-direct-device-cache`, `valid-opaque-declaration`, `valid-correction-chain`, `valid-f07-copy-input`, and `valid-boundary-at-maximum`. Each is currently `NOT IMPLEMENTED`; a future positive observation may produce only an exact-scope F-06 evidence result and never legal clearance, physical qualification, stable promotion, support, or DONE.

| Fixture ID | Baseline closure | Expected decision | Expected code | Exact JSON Pointer | Phase | Current |
| --- | --- | --- | --- | --- | --- | --- |
| `valid-source-complete` | Complete variant-level source, license, notice, and artifact closure | `ADMIT` | `null` | `null` | `F06-P10` | `NOT IMPLEMENTED` |
| `valid-license-one-of` | Complete one-of license choice with every alternative present and signed | `ADMIT` | `null` | `null` | `F06-P10` | `NOT IMPLEMENTED` |
| `valid-source-offer` | Complete signed source-offer closure with one selected offer | `ADMIT` | `null` | `null` | `F06-P10` | `NOT IMPLEMENTED` |
| `valid-direct-device-cache` | Complete direct-device receipt, cache, consent, and network-denial closure | `ADMIT` | `null` | `null` | `F06-P10` | `NOT IMPLEMENTED` |
| `valid-opaque-declaration` | Complete opaque external declaration with signed hash/metadata only | `ADMIT` | `null` | `null` | `F06-P10` | `NOT IMPLEMENTED` |
| `valid-correction-chain` | Complete immutable correction chain with one current record | `ADMIT` | `null` | `null` | `F06-P10` | `NOT IMPLEMENTED` |
| `valid-f07-copy-input` | Complete F-07 request inputs with exactly one writer binding | `ADMIT` | `null` | `null` | `F06-P10` | `NOT IMPLEMENTED` |
| `valid-boundary-at-maximum` | Valid inclusive maximum bounds without overflow | `ADMIT` | `null` | `null` | `F06-P10` | `NOT IMPLEMENTED` |

## 15. Identity separation and authoritative handoff matrix

### 15.1 Disjoint identities

The following identity classes are separate authority-bearing identities. A role binding is verified by F-03, not by string comparison. Every forbidden intersection is a hostile fixture obligation; a multi-role identity or replayed proof is not an optimization.

| Identity class | Responsibility | Forbidden intersection |
| --- | --- | --- |
| `record_author` | Creates the F-06 record body | evaluator, independent reviewer, approver, projection publisher, retention custodian, release writer |
| `source_producer` | Produces source/cache/evidence bytes | independent reviewer, evaluator for that evidence, approver |
| `evaluator` | Runs F-06 policy evaluation | record author, candidate assembler, independent reviewer, approver, retention custodian |
| `candidate_assembler` | Produces F-05 candidate | evaluator, independent reviewer, approver, release writer |
| `independent_reviewer` | Replays hostile/positive gates and reports review | record author, source producer, evaluator, candidate assembler, approver, projection publisher, retention custodian, release writer |
| `approver` | Signs the exact owner/legal/decision checkpoint | record author, evaluator, candidate assembler, independent reviewer, release writer; two-party counsel and owner decisions require distinct identities |
| `projection_publisher` | Produces projection wrapper and audit receipt | evaluator, independent reviewer, retention custodian, release writer |
| `retention_custodian` | Authorizes retention/deletion and tombstones | evaluator, independent reviewer, projection publisher, release writer |
| `release_writer` | F-07 stable-copy writer only | every F-06 role, candidate assembler, evaluator, independent reviewer, approver, projection publisher, retention custodian |
| `counsel_checkpoint` | Human legal interpretation | project owner for a two-party decision, record author, evaluator |
| `brand_checkpoint` | Human brand/trademark decision | record author, evaluator, projection publisher |
| `project_owner_checkpoint` | Human owner/external-impact decision | counsel checkpoint for a two-party decision, record author, evaluator, release writer |

The forbidden fixture set includes author/evaluator, evaluator/approver, author/reviewer, candidate/reviewer, projection/reviewer, retention/reviewer, release-writer/evaluator, counsel/owner, and identity-replayed decision cases. No role may reuse a replay identity across a different scope or decision.

### 15.2 Required handoff fields

Every handoff row below is authoritative only when it contains producer, consumer, artifact/document ID, content/payload digest and exact preimage, schema/binding lock, freshness/expiry, exact project/repository/slice/operation/candidate/board/artifact/channel scope, gate, rejection code/path/phase/result, residual owner, due-before gate, and acceptance artifact. The matrix is closed; an omitted F-07 handoff is `F06-F07-HANDOFF-MISSING`, and no generic or duplicate handoff code is admitted.

The exact scope requirement is the complete `F06Scope` tuple, including project, repository, slice, F-06 operation, schema set, candidate document and payload/content digests, artifact set, policy, channel, board, board-registry digest, manifest ID/digest, target account/binding, validity interval, and replay identity. A table cell that names only the join-specific subset is an abbreviation of that complete tuple, never permission to omit a member.

| Handoff ID | Producer | Consumer | Artifact/document ID | Content/payload digest and exact preimage | Schema/binding lock | Freshness/expiry | Exact scope | Gate | Rejection code / JSON Pointer / phase / result | Residual owner | Due-before gate | Acceptance artifact |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `f02-to-f06` | Future ratified F-02 | F-06 | Eight `EnvelopeRef` document IDs | Each `payload_digest = sha256(JCS(P))`; source envelope signature preimage remains F-02-owned | Future F-02 `schema-input.lock`, `generated-output.lock`, and Trusted binding receipt | Trusted expiry and replay; exact current schema set | Project, repository, F-06 slice, operation, candidate, board, manifest, artifact set, channel | Eight-type import and binding seam | `F06-F02-BINDING-HOLD` / `/f02_bindings` / `F06-P3` / `HOLD`; type omission is `F06-F02-TYPE-MISSING` / `/f02_imports` / `F06-P1` / `REJECT` | F-02 implementation owner | G-F06-01 | Future F-02 trusted import report and eight-type vector report |
| `f03-to-f06` | Future ratified F-03 | F-06 | `Trusted<TrustContext>` and `AuthorityRoleBinding` records | Binding digest covers the complete closed binding except `binding_digest`; context digest is F-03-owned | Future F-03 trust-root/role/replay lock | Verified clock, issued/expiry, revocation epoch, replay reservation | Exact project/repository/slice/operation/candidate/policy and role scope | Trust and decision authority | `F06-F03-AUTHORITY-HOLD` / `/f03_trust_ref` / `F06-P3` / `HOLD` | F-03 owner | G-F06-02 | Future trust verification, expiry, revocation, and replay report |
| `f04-to-f06` | Future F-04 | F-06 | Source, provenance, SBOM, builder, package/index, and artifact records | Each content digest covers exact bytes; each provenance digest covers its closed source/build/toolchain preimage | Future F-04 builder and artifact locks plus F-02 manifest binding | Artifact/source/evidence expiry and candidate scope | Exact component paths, artifact IDs, source IDs, candidate, channel, policy | Source and artifact closure | `F06-PROVENANCE-MISSING` / `/f04_refs` / `F06-P6` / `HOLD` | F-04 owner | G-F06-04 | Future provenance/SBOM/artifact closure report |
| `f05-to-f06` | Future F-05 | F-06 | Candidate document ID and payload/content digest | Candidate payload digest and candidate byte/content digest have separate exact JCS/byte preimages | Future F-05 candidate/consumer lock and F-02 binding | Candidate validity, manifest expiry, current required-slice closure | Exact project/repository/slice, board set, manifest, artifacts, channel | Candidate join | `F06-SCOPE-MISMATCH` / `/f05_candidate_ref` / `F06-P4` / `REJECT` | F-05 owner | G-F06-04 | Future candidate assembly and consumer-guard report |
| `installer-to-f06` | Future installer | F-06 | Installer plan ref, source-closure ref, consent ref, network-policy ref | Plan payload digest is F-02-owned; cache/closure/content digests use their named domain-separated preimages | Future F-02 installer binding plus installer closure lock | Before-consent verification and consent expiry; no mutation after stale | Exact board, topology, targets, plan, candidate, artifacts, operation, channel | Pre-consent complete closure and network deny evidence | `F06-SOURCE-CLOSURE-HOLD` / `/source_closure` / `F06-P5` / `HOLD` | Installer owner | G-F06-05 | Future pre-consent cache receipt, closure, consent, and network-denial report |
| `f06-to-f07` | F-06 | Future F-07 | F-06 result, evidence bundle, and typed `F07PromotionRequest` | F-07 copy preimage binds every referenced digest and exact request scope | Future F-07 handoff and promotion lock | Result, qualification, health, legal, support, ledger, rollback, and source expiry | Exact candidate, candidate channel, stable target, board/profile set, schema/policy | F-07 recomputation and exact-copy terminal | `F06-F07-HANDOFF-MISSING` / `/f07_handoff` / `F06-P9` / `REJECT` | F-07 owner | G-F06-09 | Future F-07 request/result, copy receipt, and no-alternate-writer report |
| `f07-to-stable-consumer` | Future F-07 | Stable release consumer | Stable object ref and copy receipt | Exact candidate content digest copied without rebuild; result digest covers receipt | Future F-07 promotion lock | Stable write lease, copy transaction, health and rollback expiry | Stable channel, candidate, public ledger, support, qualification, legal, rollback | Only F-07 may write stable | `F06-F07-PROMOTION-BYPASS` / `/stable_write` / `F06-P9` / `REJECT` | F-07 owner | PROGRAM F-07 gate | Future atomic copy receipt and stable re-read digest |
| `owner-to-f06` | Project owner checkpoint | F-06 | Owner decision document ID and payload digest | Decision payload and join digests use separate named preimages | Future F-03 exact role binding and owner-proof seam | Current trusted clock, expiry, replay | Exact external impact, candidate, channel, policy, artifact/brand scope | Owner decision join | `F06-F03-ROLE-UNAVAILABLE` / `/decision_bindings/owner` / `F06-P7` / `HOLD` | Project owner | G-F06-07 | Future signed owner decision and proof receipt |
| `legal-to-f06` | Counsel checkpoint | F-06 | License/source/counsel decision IDs and source-offer index | License/offer/decision joins use their exact domain-separated preimages | Future F-03 binding plus F-04 source/provenance lock | Offer availability, decision expiry, correction chain | Exact artifact/license/source/counsel scope and channel | Legal/source closure | `F06-COUNSEL-CONTRADICTION` / `/decision_bindings/counsel` / `F06-P7` / `REJECT` | Counsel owner | G-F06-07 | Future variant-complete notice/source-offer/counsel report |
| `qualification-to-f06` | Q-00 through Q-08 | F-06 | Qualification record IDs and evidence IDs | Evidence `content_digest` covers exact bytes; qualification payload digest remains F-02-owned | Future F-02 qualification binding and F-03 qualification-lab binding | Board/manifest/profile/fixture/evidence freshness and expiry | Every applicable board/profile, manifest, artifact set, operation, channel | Qualification closure | `F06-SCOPE-MISMATCH` / `/qualification` / `F06-P4` / `REJECT` | Qualification owner | PROGRAM Q gates | Future physical evidence and qualification closure report |
| `rollback-to-f06` | Rollback owner | F-06 | Rollback record and retained artifact IDs | Rollback digest covers exact ordered manifest/artifact/slot set | F-02 manifest rollback projection and retention lock | Current candidate lineage and retention lifetime | Exact candidate, previous stable, board, artifact set, channel | Rollback reachability | `F06-F07-ROLLBACK-MISMATCH` / `/rollback` / `F06-P9` / `REJECT` | Rollback owner | G-F06-09 | Future rollback compatibility and retention proof |
| `support-to-f06` | Support projection owner | F-06 | Support projection document ID, source digest, and audit receipt | Projection digest covers exact allowlisted output; policy digest is in wrapper proof | Future ratified public/projection lock and F-03 ACL binding | Support expiry and correction chain | Exact public board, candidate, channel, source, and support scope | Support-safe projection | `F06-OUTPUT-PROJECTION-DIGEST-MISMATCH` / `/support` / `F06-P8` / `REJECT` | Support owner | G-F06-08 | Future support projection and redaction/noninterference report |
| `ledger-to-f06` | Public ledger/publication owner | F-06 | Public/v1 projection, notice bundle, source-offer index, ledger record | Public projection digest is future F-02-owned; wrapper binds source private digest and policy proof | Future F-02 public/v1 and F-03 publication binding | Publication expiry and correction chain | Exact candidate, channel, artifact/source/qualification digests | Public derivation and source closure | `F06-PUBLIC-AUTHORITY-REDEFINED` / `/public` / `F06-P8` / `REJECT` | Public ledger owner | G-F06-08 | Future public projection derivation and ledger receipt |
| `release-consumer-to-f06` | Release consumer | F-06 | Consumer capability, release request, and observed result | Consumer output/content digest and source/payload digest remain separate | Future generated binding/output lock and F-05 consumer lock | API/schema-set expiry and current channel | Exact language/API, schema set, candidate, channel, artifact set | Consumer binding and no warning-success | `F06-F02-BINDING-HOLD` / `/release_consumer/binding` / `F06-P3` / `HOLD` | Release consumer owner | G-F06-10 | Future consumer conformance and warning-success rejection report |
| `retention-to-f06` | Retention custodian | F-06 | Retention record, dependency proof, authorization, tombstone | Retention/tombstone digests use the closed preimages in Section 12 | Future retention lock and F-03 retention authority binding | Legal hold, extension, retention, correction, audit, rollback expiry | Exact record/content/scope/dependency IDs | Eligibility and idempotent deletion | `F06-RETENTION-AUTHORITY-HOLD` / `/retention/delete_authorization_ref` / `F06-P8` / `HOLD` | Retention custodian | G-F06-08 | Future eligibility, partial-recovery, and tombstone report |

## 16. Current state, acceptance census, and residuals

### 16.1 Recomputed design census

The correction contains 106 hostile fixture declarations and 8 positive fixture declarations, one 11-capability handshake set, one closed F-02 upstream code set of 45 values, one closed local F-06 code set of 120 values plus the disjoint 45-value mapped F-02 source namespace, 10 future schema files, 31 exact future tracked deliverable paths, and 15 authoritative handoff rows. These are design declarations, not runtime observations. The hostile fixture rows are all `NOT IMPLEMENTED`; no positive fixture has a runtime result.

The design model itself has no executable PASS. The current evidence census is:

| Evidence class | Current result | Exact reason |
| --- | --- | --- |
| F-02 generated trusted bindings and schema lock | `HOLD / NOT EXECUTABLE` | F-02 remains rejected/provisional and no ratified binding is observed |
| F-03 TrustContext and AuthorityRoleBinding | `HOLD / NOT EXECUTABLE` | F-03 trust root, role resolver, replay, and expiry implementation are absent |
| F-04 source/provenance/artifact closure | `HOLD / NOT EXECUTABLE` | F-04 remains an unratified dependent foundation; no implementation or signed build/source closure is observed in the allowed scope |
| F-05 candidate guard | `HOLD / NOT EXECUTABLE` | F-05 remains an unratified dependent foundation; no candidate assembler or cross-repository guard is observed |
| Installer pre-consent closure/network denial | `HOLD / NOT EXECUTABLE` | The installer foundation remains unratified; no cache receipt validator or network-denial enforcement is observed |
| F-06 schemas, validator, bindings, fixtures, reports, and CI | `HOLD / NOT EXECUTABLE` | F-06 has no trusted foundation and all future artifacts named in Section 13 are absent from this design-only slice |
| Legal/counsel/owner/branding decisions | `HOLD / NOT EXECUTABLE` | No current trusted human decision joins are observed; prose is not clearance |
| Physical qualification and support | `NOT EXECUTABLE` | No independent physical qualification or support evidence is observed here |
| F-07 promotion terminal | `HOLD / NOT EXECUTABLE` | F-07 remains dependent on unratified foundations; its request/result, recomputation, exact-copy terminal, and writer guard are absent |
| Stable publication/release readiness/DONE | `REJECT` | F-06 cannot self-mark completion or promote, and all prerequisites remain open |

### 16.2 Residual ownership and gate closure

The residuals are blocking and have no prose waiver: future F-02 ratification or owner exception; future F-03 trust roots/role binding/replay; F-04 source and artifact closure; F-05 candidate guard; installer cache/consent/network enforcement; Q-00 through Q-08 physical and evidence closure; legal/counsel/source-offer/redistribution/export/security/branding/owner decisions; projection ACL/redaction/noninterference; retention lock/holds/tombstones; generated bindings and exact tool/container locks; every hostile and positive fixture; clean-checkout CI; independent adversarial review; and F-07 sole promotion terminal.

Every residual has an explicit HOLD/REJECT path in the code registry or handoff matrix. Missing tooling, missing files, unavailable exact versions, absent signed evidence, or unavailable physical hardware is `NOT IMPLEMENTED` or `TOOLING_BLOCK`, never PASS. No residual owner may treat a branch, design note, signed hash, static check, or opened PR as the required acceptance artifact.

This note does not claim implementation, legal clearance, redistribution permission, compatibility, qualification, support, release readiness, promotion authority, merge, or DONE.
