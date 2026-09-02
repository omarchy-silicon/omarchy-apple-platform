# F-06 Release Compliance Design Note

Status: DESIGN-ONLY — this note defines a future contract and establishes no implementation, canonical schema, validator, legal clearance, redistribution permission, compatibility claim, qualification result, support claim, release readiness, promotion authority, or DONE state.

Slice: F-06

Repository: `omarchy-apple-platform`

Audience: coordinator, F-02 through F-07 owners, installer owners, component maintainers, release-compliance owner, counsel, support, and independent reviewers.

## 1. Purpose and hard boundaries

F-06 evaluates one exact candidate evidence closure and emits signed evidence and a deterministic `ADMIT` or `REJECT` decision. F-06 is evidence-only. It does not build, fetch, mutate, install, qualify hardware, give legal advice, authorize redistribution, publish to a stable channel, copy an artifact to stable storage, or mark any program slice DONE.

The m1n1-omarchy repository is an opaque human-produced boundary. F-06 may consume only an externally supplied signed hash, declared metadata, schema, provenance, and observable qualification evidence covered by an external contract. F-06 never inspects, reads, analyzes, edits, tests, clones, fetches, browses, traverses, characterizes, or delegates work against that boundary. A declaration never authorizes access to its underlying source.

F-06 imports the frozen cross-contract interfaces below. Imported payloads remain owned by their producer. F-06 stores only authenticated `EnvelopeRef` values and independently computed joins; it does not create local shadow identities or transplant a digest, schema set, trust context, decision, candidate, or artifact set into a different scope.

The note is subordinate to the coordinator-owned program at the requested coordinator commit. Design text is not an implementation or evidence that any future gate has passed.

## 2. Authenticated interface imports

### 2.1 Closed F-02 payload set

Exactly these eight payload types are authenticated F-02 inputs. No ninth type, alias, local substitute, or untyped F-02 object is accepted:

| Ordinal | Exact payload type | F-02 role | F-06 use |
| --- | --- | --- | --- |
| 1 | `board-registry/v1` | Board identity and support-registry record | Joins the exact board to the candidate and typed compatibility rows |
| 2 | `platform-manifest/v1` | Immutable release component manifest | Supplies the canonical component closure and release tuple |
| 3 | `installer-plan/v1` | Immutable installer plan | Supplies the pre-consent mutation and acquisition plan |
| 4 | `qualification-record/v1` | Board and capability qualification evidence | Supplies signed Q-00 through Q-08 qualification evidence |
| 5 | `boot-health/v1` | Boot and recovery health evidence | Supplies boot-health and rollback observations |
| 6 | `owner-approval/v1` | Owner-approved disposition payload | Supplies an imported approval only after F-03 trust resolution |
| 7 | `boot-success-mark/v1` | Exact boot-success observation | Joins boot-success evidence to the candidate and board |
| 8 | `dtb-mutation-envelope/v1` | Device-tree mutation evidence | Joins pre/post DTB digests, mutation policy, and rollback evidence |

The set above is closed by `f02_payload_type_set_digest`. A missing member, unknown member, ninth member, spelling variant, or payload with a type outside this set rejects with `F06-F02-TYPE-MISSING` or `F06-F02-TYPE-UNKNOWN` at `/f02_envelope_refs`.

### 2.2 One envelope reference contract

Every authenticated imported payload and every F-06 decision, evidence, report, projection, and event is referenced by the same F-03-owned envelope-reference shape. There is exactly one reference form, not one form per producer and not a loose list of digests.

`EnvelopeRef` has exactly these fields:

| Field | Type and rule |
| --- | --- |
| `payload_type` | Lowercase literal selected from the exact eight-type set in Section 2.1 or the named non-F-02 F-03/F-04/F-05/F-06 record family |
| `payload_version` | Exact major and minor version declared by the signed schema lock |
| `schema_set_digest` | `sha256:` digest of the complete imported schema and vocabulary set; never inferred from payload bytes |
| `document_id` | Stable producer-assigned document identity, unique within `payload_type`, `payload_version`, and `schema_set_digest`; not a content digest |
| `payload_digest` | Separately computed `sha256:` digest of the RFC 8785 JCS canonical payload bytes, excluding the envelope and signature |
| `signed_metadata` | F-03-signed metadata containing issuer key binding, issued time, expiry, sequence/nonce, repository, slice, operation, candidate, artifact-set, and channel scope |
| `signature` | F-03 signature over the canonical payload plus canonical envelope metadata |

`document_id` is stable across an unchanged document being referenced again. `payload_digest` changes when canonical payload bytes change. The evaluator verifies both independently and also verifies that the document identity is bound to the signed metadata. A payload digest is never used as a document identity, and a document identity is never used as a payload digest.

The envelope reference is a binding tuple of `payload_type`, `payload_version`, `schema_set_digest`, `document_id`, `payload_digest`, and signed metadata. Replacing one member while retaining the others is a transplant and rejects with the corresponding binding code. F-06 recomputes `payload_digest`; it never trusts a digest copied into another payload. A local field such as `board_id`, `manifest_id`, `decision_id`, or `artifact_id` cannot replace the authenticated reference.

### 2.3 Trust and authority resolution

Authority resolves only through F-03 `Trusted<TrustContext>` and its closed `AuthorityRoleBinding`. F-06 does not maintain an owner directory, actor-to-role map, local root, email allowlist, or alternate authority registry.

`AuthorityRoleBinding` is closed over `role`, `repository_scope`, `slice_scope`, `operation_scope`, `component_scope`, `candidate_scope`, `channel_scope`, `valid_from`, `valid_until`, `key_id`, `trust_context_digest`, `policy_digest`, `sequence_domain`, and `replay_domain`. Every field is signed and checked. A display name, Git author, email address, unsigned comment, or signature with no matching F-03 binding has no authority.

All decisions and evidence use the following `ScopeBinding`:

| Field | Required exact value or binding |
| --- | --- |
| `project` | `omarchy-silicon` |
| `repository` | `omarchy-apple-platform` |
| `slice` | `F-06` |
| `operation` | One closed operation from Section 6.1 |
| `schema_set_digest` | The exact schema-set digest used to encode the record |
| `candidate_document_id` | The candidate's stable document identity, never merely its payload digest |
| `candidate_payload_digest` | The independently computed candidate payload digest |
| `artifact_set_digest` | Digest of the canonical ordered artifact set |
| `channel` | `edge`, `rc`, or `stable` |
| `policy_digest` | Exact policy lock digest |
| `valid_from` / `valid_until` | Signed validity interval checked against trusted F-03 time |
| `replay_identity` | Signed nonce and sequence in the F-03 replay domain |

Any mismatch in project, repository, slice, operation, schema set, candidate, artifact set, channel, policy, validity, or replay identity rejects. Scope is never narrowed or widened by a consumer.

## 3. Canonical platform-manifest join

F-06 consumes the imported `platform-manifest/v1` object by reference. The following canonical paths are the only paths used to join compliance evidence to the manifest; F-06 cannot add a local component path or shadow field:

| Canonical manifest path | Required content |
| --- | --- |
| `/components/linux/kernel` | Linux kernel source, recipe, artifact, ABI, and signing bindings |
| `/components/linux/device_tree_set` | Board-selected DTB set, pre/post mutation relationships, and DTB digests |
| `/components/firmware/bundle` | Firmware bundle members, immutable digests, source/provenance, and firmware ABI |
| `/components/graphics/mesa_stack` | Mesa stack components, GPU ABI, build provenance, and artifact set |
| `/components/boot/stack` | Opaque boot artifact contract, U-Boot, GRUB, initramfs, boot configuration, and handoff digests |
| `/sources/provenance` | Source snapshots, fork lineage, patch queues, builder inputs, and provenance references |
| `/locks` | Imported schema, policy, toolchain, package, channel, and retention lock digests |
| `/artifacts` | Canonical artifact records and exact content-addressed locations |
| `/rollback` | Rollback target, compatibility proof, retention dependency, and recovery artifact digests |
| `/compatibility/typed` | Board, capability, ABI, firmware, and typed compatibility declarations |

The join requires exact equality between the manifest component key, manifest digest, component path, expected artifact digest set, source/provenance binding, rollback binding, and typed compatibility binding. Chip names, architecture strings, branch names, URLs, package-manager output, and local selectors are diagnostic data only.

The imported F-02 payloads are never reserialized into an F-06 shadow record. Each F-02 reference is present exactly once in the canonical `f02_envelope_refs` map, keyed by its exact payload type. A duplicate key, duplicate payload type, missing type, or type alias rejects before policy evaluation.

## 4. Candidate and typed decision contract

### 4.1 F-06 operations and result boundary

The closed F-06 operation enum is exactly `evaluate`, `verify-evidence`, `render-projection`, `append-correction`, and `append-supersession`. These operations emit evidence, decisions, projections, or immutable lineage records. There is no F-06 operation for build, install, mutate, publish, stable promotion, copy-to-stable, release authorization, or qualification.

The future pure interface is:

`F06.ReleaseCompliance.evaluate.v1(request: ComplianceEvaluationRequest, trust: Trusted<TrustContext>) -> ComplianceEvaluationResult`

The result is valid only for the exact candidate, target channel, policy lock, trust context, artifact set, evidence closure, decision references, and expiry recorded in its `ScopeBinding`. F-06 `ADMIT` is necessary evidence for downstream gates; it is not release authority.

### 4.2 Candidate request

`ComplianceEvaluationRequest` has exactly these top-level fields:

| Field | Type | Rule |
| --- | --- | --- |
| `request_type` | Literal `f06.policy-evaluation/v1` | Required |
| `evaluation_document_id` | Stable `document_id` | Unique evaluation identity |
| `evaluation_time` | RFC 3339 UTC `Z` timestamp | Supplied from trusted context; no evaluator wall-clock read |
| `operation` | Closed operation from Section 4.1 | Scope-bound |
| `target_channel` | `edge`, `rc`, or `stable` | Exact channel requirements apply |
| `scope_binding` | `ScopeBinding` | Required and immutable |
| `f02_envelope_refs` | Map with exactly eight keys from Section 2.1 | Every key has one `EnvelopeRef` |
| `f03_envelope_refs` | Bounded array of F-03 trust and authority references | No local trust substitute |
| `f04_envelope_refs` | Bounded array of F-04 builder, SBOM, provenance, artifact-store, package, index, and reproducibility references | Each scope-bound |
| `f05_candidate_envelope_ref` | One F-05 candidate envelope reference | Exact assembled candidate |
| `inventory_envelope_ref` | One `f06.inventory/v1` envelope reference | Complete closure from Section 5 |
| `decision_bindings` | Typed map from Section 6.2 | No loose decision-reference list |
| `policy_lock_digest` | `Digest` | Exact policy and grammar lock |
| `retention_lock_digest` | `Digest` | Exact retention lock |
| `projection_lock_digest` | `Digest` | Exact projection lock |
| `fixture_manifest_digest` | `Digest` | Closed fixture manifest version |

The request cannot contain an untyped `decision_refs` array, a raw actor, a local owner field, an unqualified URL, a mutable branch, a package-manager resolution, a warning-success field, or a field outside the locked schema.

### 4.3 Result and bounded rejection envelope

`ComplianceEvaluationResult` has exactly `result_type`, `result_document_id`, `decision`, `scope_binding`, `input_envelope_refs`, `notice_bundle_ref`, `source_offer_index_ref`, `findings`, `finding_overflow`, `pass_fail_census`, `attestation_envelope_ref`, `evaluated_at`, `expires_at`, and `payload_digest`.

`decision` is exactly `ADMIT` or `REJECT`. `findings` is an ordered array with a maximum of 4,096 entries. Each `Finding` has exactly `code`, `json_pointer`, `phase`, `subject_key`, `evidence_refs`, and `blocking`. Every finding is blocking. If more than 4,096 findings exist, the evaluator records `finding_overflow.count`, `finding_overflow.digest`, and `F06-INPUT-FINDING-BOUND` at `/findings`; it does not silently truncate, stop early, or turn overflow into success. The envelope itself is bounded to 4,096 findings, 2,048 bytes per finding, and 8 MiB total canonical result size.

`pass_fail_census` has exactly `pass_count`, `fail_count`, `skipped_count`, and `tooling_limitation_count`. `skipped_count` is always zero for an emitted result. A missing runner, missing fixture, unavailable lock, or unavailable required tool increments `fail_count` and produces a finding; it never increments `skipped_count` as a successful outcome. `ADMIT` requires `fail_count=0`, `skipped_count=0`, and every required phase to have an observed pass.

## 5. Exact `f06.inventory/v1` closure graph

### 5.1 Inventory envelope and bounds

The inventory record family is exactly `f06.inventory/v1`. It is an F-06 record referenced by one `EnvelopeRef`, with a `ScopeBinding` and these fields: `inventory_type`, `inventory_document_id`, `scope_binding`, `root_node_ids`, `nodes`, `edges`, `exclusions`, `bounds`, `closure_digest`, and `payload_digest`.

The locked bounds are: 1 to 65,536 nodes; 0 to 262,144 edges; 0 to 16,384 exclusion records; 0 to 256 artifact identities per node; 1 to 256 source references per node; 0 to 256 evidence references per node; 0 to 16,384 bytes per scalar string; 0 to 64 recursion depth; and 0 to 8 MiB canonical inventory bytes. A value at a maximum is valid; maximum plus one rejects with `F06-BOUND-EXCEEDED` at the exact field path. Bounds are part of `bounds_digest` and cannot vary by evaluator.

### 5.2 Node schema and semantic uniqueness

Each `Node` has exactly `node_id`, `semantic_key`, `component_id`, `node_kind`, `lifecycle`, `acquisition_mode`, `artifact_identities`, `source_references`, `provenance_refs`, `recipe_ref`, `represents_node_id`, `manifest_paths`, `required_for`, and `node_evidence_refs`.

`node_kind` is exactly `component`, `source`, `binary`, `firmware`, `package`, `package_index`, `container_image`, `font_theme_artwork`, `installer_component`, `patch_queue`, `opaque_boot_artifact`, `notice`, `source_offer`, or `generated_output`. `lifecycle` is exactly `shipped`, `acquired_only`, `build_only`, or `metadata_only`. `acquisition_mode` is exactly `embedded_in_candidate`, `fetched_from_manifest_source`, `fetched_per_device_from_authoritative_source`, `materialized_by_builder`, or `declared_external_artifact`.

`semantic_key` is the canonical tuple `(component_id, node_kind, lifecycle, acquisition_mode, identity_digest, content_role)`. It is unique across all nodes. Two rows with the same semantic key, even with different node IDs, reject with `F06-INVENTORY-SEMANTIC-DUPLICATE`. A node with no manifest path, root reachability, artifact identity, source reference, or explicit exclusion is not a hidden node; it rejects as incomplete.

Every node that is `shipped` or `acquired_only` has one or more artifacts in the bounded `artifact_identities` array. Every `build_only` node has a recipe and evidence reference. Every `metadata_only` node has a typed `represents_node_id`. An absent artifact array, singular `artifact_identity` member, mixed scalar/array shape, or unbounded artifact collection rejects with `F06-INVENTORY-ARTIFACT-SHAPE` at `/nodes/0/artifact_identities`.

Each `ArtifactIdentity` has exactly `artifact_id`, `artifact_digest`, `artifact_size_bytes`, `media_type`, `content_role`, `location_role`, `candidate_paths`, `artifact_store_ref`, `source_node_ids`, and `artifact_evidence_refs`. `artifact_digest` and `artifact_size_bytes` are immutable and each artifact occurs exactly once in the closure. Multiple artifacts are represented only by the bounded `artifact_identities` array; singular-versus-array ambiguity is forbidden.

### 5.3 Typed edges, exclusions, and closure

Each `Edge` has exactly `edge_id`, `edge_type`, `from_node_id`, `to_node_id`, `ordinal`, and `edge_evidence_refs`. `edge_type` is closed to `depends-on`, `contains`, and `derived-from`. Edge IDs and semantic tuples `(edge_type, from_node_id, to_node_id, ordinal)` are unique. Ordinals start at 1 and are contiguous within an ordered `contains` or `depends-on` adjacency list; `derived-from` has ordinal 0.

The graph is a finite directed acyclic graph. `depends-on` and `derived-from` are dependency edges; `contains` is a closure edge. Self-edges, duplicate edges, unknown node endpoints, dependency cycles, and an edge that creates a second semantic parent where the node kind forbids it reject. Canonical edge order is `from_node_id` bytes, `edge_type` order `contains`, `depends-on`, `derived-from`, then ordinal and `to_node_id` bytes.

`root_node_ids` is the exact set derived from the F-05 candidate component set, installer plan, release artifacts, rollback artifacts, and declared acquisition requirements. A node is in closure if and only if it is reachable from a root by zero or more typed edges and every required dependency is reachable. A node outside reachability rejects with `F06-INVENTORY-NODE-DISCONNECTED`; a reachable manifest, SBOM, artifact-store, installer, package-index, source, output, or acquisition reference with no node rejects with `F06-INVENTORY-NODE-MISSING`.

An `ExclusionRecord` has exactly `exclusion_id`, `reference_kind`, `reference_locator`, `exclusion_reason`, `represented_by_node_id`, `evidence_refs`, `signed_decision_ref`, and `scope_binding`. An exclusion is allowed only for a reference proven not to contribute bytes, metadata, execution, licensing, redistribution, security, branding, rollback, or support output. An excluded reference cannot also be a node, artifact, root, or reachable dependency. Missing a record is not an exclusion.

The closure invariant is: every shipped or acquired input and output is represented by exactly one reachable node and exactly one semantic artifact identity, or by exactly one signed exclusion record. Zero occurrences, two occurrences, disconnected occurrence, or an occurrence in both node and exclusion sets rejects.

## 6. Typed signed decisions

### 6.1 Decision reference shape

Every license, redistribution, export, security, branding/trademark, counsel, and owner disposition contains a typed signed decision reference in its own schema. No top-level list can satisfy a disposition. A reference is not accepted merely because its digest appears somewhere in an evidence array.

`SignedDecisionRef` has exactly `decision_kind`, `decision_envelope_ref`, `role_binding_ref`, `decision_scope`, `component_scope`, `candidate_scope`, `artifact_set_scope`, `channel_scope`, `policy_scope`, `validity`, `replay_identity`, and `join_digest`.

`decision_scope` is closed to `license`, `redistribution`, `export`, `security`, `branding_trademark`, `counsel`, and `owner`. `component_scope` is one or more exact canonical manifest component paths. `candidate_scope` binds both stable `document_id` and payload digest. `artifact_set_scope` binds the ordered artifact-set digest. `channel_scope` is an exact channel or a signed set of channels. `policy_scope` binds the policy digest. `validity` contains signed `valid_from` and `expires_at`; the earliest expiry controls. `replay_identity` contains the F-03 nonce, sequence, and replay domain. `join_digest` covers the complete reference and the disposition field it authorizes.

### 6.2 Closed decision-kind-to-role map

The following is the complete mapping. A role not listed for a decision kind is forbidden, and a decision kind not listed is unknown.

| Decision kind | Required F-03 role binding | Required disposition field |
| --- | --- | --- |
| `license` | `OpenSourceComplianceCounsel` or the separately appointed `LicenseDispositionOwner` | `license_notice.license_resolution` and selected license option |
| `redistribution` | `FirmwareRedistributionOwner` plus `OpenSourceComplianceCounsel` when a license interpretation is required | `redistribution.redistribution_class` and conditions |
| `export` | `ExportSecurityOwner` plus `OpenSourceComplianceCounsel` when legal interpretation is required | `export_security.export_class` and restrictions |
| `security` | `SecurityReleaseOwner` | `export_security.security_flags` and security disposition |
| `branding_trademark` | `TrademarkBrandOwner` | `branding_trademark.disposition` and rendered locations |
| `counsel` | `OpenSourceComplianceCounsel` | Any explicitly counsel-reserved interpretation or source-offer determination |
| `owner` | `ProjectOwner` | Publication, support, channel, exception disposition, or external-impact authorization |

The role names are role bindings, not local identities. Each binding is resolved through F-03 `Trusted<TrustContext>`. A required pair is joined by two distinct signed references; one signature cannot impersonate both roles.

F-06 rejects an unattached, ambiguous, wrong-role, wrong-scope, wrong-component, wrong-candidate, wrong-artifact-set, wrong-channel, wrong-policy, expired, superseded, revoked, replayed, unsigned, or transplanted decision. It also rejects a decision whose `join_digest` does not cover the disposition actually evaluated. Codes are `F06-DECISION-UNATTACHED`, `F06-DECISION-AMBIGUOUS`, `F06-TRUST-ROLE-SCOPE-MISMATCH`, `F06-TRUST-DECISION-EXPIRED`, `F06-TRUST-DECISION-REPLAYED`, `F06-TRUST-DECISION-STALE`, `F06-TRUST-DECISION-UNSIGNED`, and `F06-DECISION-TRANSPLANT`.

### 6.3 Variant-complete license and source obligations

`LicenseNoticeBinding` has exactly `choice_kind`, `license_options`, `selected_license_option_ids`, `exceptions`, `notices`, `attributions`, `modification_disclosures`, `corresponding_source`, `source_offers`, `decision_ref`, `evidence_refs`, and `binding_digest`.

`choice_kind` is exactly `single`, `one-of`, or `all-of`. Each `LicenseOption` has exactly `option_id`, `expression_kind`, `expression`, `license_text_refs`, `exception_ids`, `notice_ids`, `modification_disclosure_ids`, `source_obligation`, and `option_digest`. `expression_kind` is `spdx` or `declared_non_spdx`; `NOASSERTION`, a prose guess, an empty expression, or an undigested URL is invalid. `one-of` requires exactly one selected option; `all-of` requires every option; `single` requires exactly one option and one selection. An option with missing text, exception, notice, modification disclosure, or source obligation rejects.

Each `ExceptionRecord` has `exception_id`, `text_digest`, `location`, `scope`, `valid_from`, `expires_at`, `signature_ref`, and `evidence_refs`. Each `NoticeRecord` has `notice_id`, `notice_digest`, `location`, `notice_kind`, `scope`, `modification_status`, `valid_from`, `expires_at`, and `evidence_refs`. Each `ModificationDisclosure` has `disclosure_id`, `text_digest`, `changed_scope`, `location`, `signature_ref`, and `evidence_refs`. All locations are immutable references, not mutable URLs alone.

`corresponding_source` is exactly one of `not-required`, `source-available`, `source-offer-required`, `source-offer-satisfied`, `source-missing`, or `unknown-unresolved`. When it is `not-required`, `source_offers` has cardinality zero. When it is `source-available`, there is exactly one immutable source reference and zero offers. When it is `source-offer-required` or `source-offer-satisfied`, `source_offers` has cardinality one through eight and exactly one `selected_offer_id`; every alternative offer is complete and signed. `source-missing` and `unknown-unresolved` reject.

Each `SourceOffer` has exactly `offer_id`, `source_snapshot_digest`, `source_size_bytes`, `locations`, `offer_text_digest`, `availability_evidence_refs`, `signature_ref`, `valid_from`, `expires_at`, `scope`, and `offer_digest`. Each location has an immutable location digest, public retrieval method, checked time, and evidence reference. An offer without a source digest, size, offer text, signature, validity, cardinality-consistent selection, or current availability rejects with `F06-SOURCE-OFFER-INCOMPLETE`, `F06-SOURCE-OFFER-UNSIGNED`, or `F06-SOURCE-OFFER-UNAVAILABLE`.

`RedistributionDisposition` has exactly `redistribution_class`, `conditions`, `decision_ref`, `channel_scope`, and `binding_digest`. The class is exactly `permitted`, `per-device-direct-authoritative-fetch-only`, `prohibited`, or `unknown-unresolved`. `ExportSecurityDisposition` has exactly `export_class`, `security_flags`, `restrictions`, `decision_ref`, and `binding_digest`. `BrandingTrademarkDisposition` has exactly `use_kind`, `disposition`, `rendered_locations`, `attribution_refs`, `decision_ref`, and `binding_digest`. Every disposition requires its matching typed signed decision reference, even for `not-applicable` or an absence of restrictions.

`CounselDisposition` has exactly `interpretation_kind`, `interpretation_digest`, `affected_component_paths`, `source_offer_ids`, `decision_ref`, and `binding_digest`. `OwnerDisposition` has exactly `disposition_kind`, `external_impact`, `affected_component_paths`, `affected_artifact_set_digest`, `channel_scope`, `decision_ref`, and `binding_digest`. `SecurityDisposition` has exactly `security_kind`, `security_flags`, `mitigation_evidence_refs`, `decision_ref`, and `binding_digest`. These three records are required when their decision kinds occur; each `decision_ref` is a `SignedDecisionRef` with the exact role, scope, validity, and replay join from Sections 2.3 and 6.1.

## 7. Deterministic parsing, structure, policy, and handshake rules

### 7.1 Frozen primitive grammars and canonical order

The grammar lock freezes these forms:

| Type | Exact grammar and bound |
| --- | --- |
| `Digest` | `sha256:[0-9a-f]{64}`, exactly 71 bytes |
| `DocumentId` | `doc-[0-9a-hj-km-np-tv-z]{26}`, lowercase Crockford base32 without `i`, `l`, `o`, or `u` |
| `ComponentId` | `cmp-[a-z0-9]+(?:-[a-z0-9]+){0,7}`, 8 to 64 bytes |
| `NodeId` | `node-[0-9a-hj-km-np-tv-z]{26}` |
| `ArtifactId` | `art-[0-9a-hj-km-np-tv-z]{26}` |
| `DecisionId` | `dec-[0-9a-hj-km-np-tv-z]{26}` |
| `EventId` | `evt-[0-9a-hj-km-np-tv-z]{26}` |
| `UtcTimestamp` | RFC 3339 UTC with `Z`, four-digit year, seconds, and no leap-second spelling |
| `HttpsLocation` | `https` URI with no credentials, fragment, mutable query, or IP-literal authority |
| `GitLocation` | `git+https` URI with no credentials or fragment; immutable commit and digest are separate required fields |
| `BundleLocation` | `bundle:/` plus a normalized relative path, no leading slash and no `..` segment |
| `JsonPointer` | RFC 6901 pointer; `/` is root; `~` occurs only in `~0` or `~1`; array indexes are decimal without leading zero |

JSON is UTF-8 without BOM and is canonicalized with RFC 8785 JCS. Object keys use JCS order. Arrays are ordered by their locked semantic keys: F-02 references by the eight-type ordinal; component paths by manifest path bytes; nodes by `node_id`; artifacts by `artifact_id`; edges by the order in Section 5.3; decision bindings by decision kind then component path; findings by the tuple in Section 7.3; fixtures by `fixture_id`; handoffs by `handoff_id`. Locale, insertion order, filesystem order, hash-map order, and evaluator version never select an order.

All strings reject control characters, invalid Unicode, NUL, unpaired surrogates, and non-canonical escaping. Numeric values are JSON numbers, not numeric strings, and are finite unsigned integers where a bound says so. Strings have a maximum of 16,384 UTF-8 bytes; arrays 65,536 items; maps 65,536 members; nested condition depth 16; nested object depth 64; and canonical record bytes 8 MiB unless a lower record bound applies. Duplicate JSON object keys always reject before semantic processing.

### 7.2 Path, condition, duplicate-scope, and capability grammar

Conditions have exactly this recursive grammar: `equals(path, scalar)`, `in(path, scalar-array)`, `not-in(path, scalar-array)`, `exists(path, boolean)`, `digest-equals(path, Digest)`, `all(condition-array)`, `any(condition-array)`, and `not(condition)`. `all` and `any` require 1 to 256 children; `in` and `not-in` require 1 to 256 unique scalar values; `not` has one child. A condition object has exactly `kind`, `path`, and the kind-specific value fields. Unknown condition kinds, unknown fields, malformed paths, duplicate condition keys, duplicate scalar values, empty `all`/`any`, depth overflow, and a condition referencing an unbound scope reject with `F06-CONDITION-MALFORMED`, `F06-PATH-MALFORMED`, `F06-SEMANTIC-DUPLICATE`, or `F06-BOUND-EXCEEDED`.

Duplicate scope is checked at every join: duplicate JSON key, duplicate F-02 payload type, duplicate manifest path, duplicate component key, duplicate semantic node key, duplicate artifact digest plus content role, duplicate edge tuple, duplicate decision kind plus component path, duplicate condition semantic key, duplicate fixture ID, duplicate handoff ID, or duplicate replay identity rejects. A same-named object in separate scopes is allowed only when its complete `ScopeBinding` differs and the schema explicitly allows that scope; a digest cannot make an otherwise duplicate semantic key unique.

The handshake has exact fields `protocol`, `major`, `minor`, `schema_set_digest`, `capabilities`, and `conditions_grammar`. `capabilities` is a sorted unique array from the locked set `jcs-rfc8785`, `typed-envelope-ref`, `inventory-closure-v1`, `signed-decision-join-v1`, `event-lineage-v1`, `projection-redaction-v1`, `retention-tombstone-v1`, and `f07-copy-terminal-v1`. Exact outcomes are `COMPATIBLE`, `INCOMPATIBLE-MAJOR`, `INCOMPATIBLE-MINOR`, `INCOMPATIBLE-SCHEMA-SET`, `INCOMPATIBLE-CAPABILITY`, and `INCOMPATIBLE-CONDITION-GRAMMAR`. An unknown capability, version, condition grammar, or duplicate capability rejects; no consumer silently ignores an unsupported admission-affecting field.

Minor negotiation is compatible only when the same major is present, the requested minor is no greater than the locked supported minor, the schema-set digest is exact, all required capabilities are present, and the condition grammar digest matches. Higher major, unsupported minor, missing required capability, extra unknown capability, schema transplant, or grammar mismatch has the exact incompatible outcome and emits `F06-HANDSHAKE-INCOMPATIBLE` at the offending field.

### 7.3 Total deterministic error-selection algorithm

The evaluator uses one total algorithm for every input. It never has a stop-first mode, an optional collect mode, a warning-success mode, or evaluator-dependent precedence. It parses every bounded field it can parse, records every independently observable finding, marks dependent phases blocked, and emits one result.

The fixed phases are: `P0 bytes-and-bounds`, `P1 lexical-and-canonical`, `P2 schema-and-types`, `P3 duplicate-and-semantic-uniqueness`, `P4 trust-and-authority`, `P5 scope-and-envelope-binding`, `P6 inventory-reachability`, `P7 artifact-and-provenance`, `P8 license-and-source`, `P9 decision-and-policy`, `P10 channel-and-output`, and `P11 result-canonicalization`. The phase order is immutable. A failed earlier phase does not permit a later policy success; a later phase emits findings for fields that are structurally available and emits no fabricated finding for unavailable data.

The stable selection key is `(phase_ordinal, json_pointer_utf8_bytes, subject_key_utf8_bytes, rejection_code_utf8_bytes)`. Findings are sorted by that key, duplicate findings with the same key are coalesced with evidence references sorted by digest, and the result is rejected if coalescing would lose distinct evidence. A missing field emits `F06-INPUT-MISSING`; an unknown field emits `F06-INPUT-UNKNOWN-FIELD`; a duplicate emits `F06-INPUT-DUPLICATE`; malformed syntax or type emits `F06-INPUT-MALFORMED`; out-of-range data emits `F06-BOUND-EXCEEDED`; a structurally inconsistent join emits `F06-STRUCTURE-INCONSISTENT`; a policy-invalid value emits `F06-POLICY-INVALID`. These codes are stable and all carry the exact JSON Pointer.

Every pointer is resolved in the canonical request unless its first segment is an authenticated imported payload or projection named by the fixture. In that case the pointer is resolved in that exact payload document after the corresponding `EnvelopeRef` is verified; a pointer is never shortened to a display path or wildcard.

The parser creates a bounded parse-rejection envelope with `parse_result`, `phase_results`, `findings`, `finding_overflow`, `canonical_input_digest`, and `tooling_limitations`. `parse_result` is exactly `VALID` or `INVALID`. Any missing parser, schema lock, validator, fixture, or report is an observed failure, never a successful empty result. A result is signed only after canonicalization and digest computation; signature verification cannot alter findings or order.

The base rejection vocabulary has one path rule per class:

| Code | Exact path rule |
| --- | --- |
| `F06-INPUT-DUPLICATE` | Exact duplicated JSON member, semantic key, or replay identity path |
| `F06-INPUT-MISSING` | Exact required member or referenced object path |
| `F06-INPUT-MALFORMED` | Exact byte, type, identifier, timestamp, URI, or encoding path |
| `F06-BOUND-EXCEEDED` | Exact scalar, array, map, depth, finding, or byte-count path |
| `F06-INPUT-UNKNOWN-FIELD` | Exact unknown object-member path |
| `F06-STRUCTURE-INCONSISTENT` | Exact join, graph, cardinality, or state-transition path |
| `F06-POLICY-INVALID` | Exact policy, disposition, channel, or required-evidence path |

Specialized codes in Sections 6, 8, 10, 12, 13, and 15 refine these classes but never replace the exact pointer rule. A validator must report the specialized code and the same canonical path for the mutated field.

The following specialized codes from the preceding F-06 contract remain valid refinements, with their paths resolved through the corrected typed bindings rather than a loose decision list:

| Preserved code | Exact path rule |
| --- | --- |
| `F06-INPUT-VERSION-UNSUPPORTED` | `/request_type`, `/f02_envelope_refs/platform-manifest~1v1/payload_version`, or the exact unsupported version field |
| `F06-INPUT-NONCANONICAL` | `/` |
| `F06-INPUT-COLLECTION-BOUND` | Exact collection path when a lock-bound collection is exceeded or truncated |
| `F06-TRUST-ENVELOPE-INVALID` | Exact `EnvelopeRef` or signed metadata path |
| `F06-TRUST-ROLE-UNRESOLVED` | Exact `role_binding_ref` in the typed decision binding |
| `F06-TRUST-ROLE-SCOPE-MISMATCH` | Exact decision disposition path or `role_binding_ref` path |
| `F06-TRUST-DECISION-UNSIGNED` | Exact typed `decision_envelope_ref` or `signature` path |
| `F06-TRUST-DECISION-EXPIRED` | Exact typed decision `validity/expires_at` path |
| `F06-TRUST-DECISION-REPLAYED` | Exact typed decision `replay_identity` path |
| `F06-TRUST-DECISION-STALE` | Exact supersession, revocation, or stale-scope path |
| `F06-BINDING-MANIFEST-MISMATCH` | `/f05_candidate_envelope_ref` or the exact manifest binding path |
| `F06-BINDING-MANIFEST-INVENTORY-MISMATCH` | Exact manifest binding or inventory node path |
| `F06-CLOSURE-COMPONENT-MISSING` | Exact missing component or closure reference path |
| `F06-CLOSURE-UNREFERENCED-COMPONENT` | Exact unreferenced inventory node path |
| `F06-CLOSURE-OPAQUE-DECLARATION-MISSING` | Exact opaque declaration reference path |
| `F06-IDENTITY-IMMUTABLE-REF-MISSING` | Exact immutable source or artifact reference path |
| `F06-IDENTITY-DIGEST-MISMATCH` | Exact recomputed digest field |
| `F06-PROVENANCE-FORK-GAP` | Exact fork-lineage field |
| `F06-PROVENANCE-PATCH-GAP` | Exact patch-queue entry |
| `F06-PROVENANCE-RECIPE-MISSING` | Exact recipe binding path |
| `F06-PROVENANCE-SBOM-INCOMPLETE` | Exact SBOM/provenance binding path |
| `F06-LICENSE-MISSING` | Exact license option or expression path |
| `F06-LICENSE-AMBIGUOUS` | Exact license choice or expression path |
| `F06-LICENSE-TEXT-MISSING` | Exact license-text reference path |
| `F06-NOTICE-MISSING` | Exact notice or attribution reference path |
| `F06-NOTICE-ALTERED` | Exact notice text digest path |
| `F06-NOTICE-EXPIRED` | Exact notice validity or location-check path |
| `F06-MODIFICATION-NOTICE-MISSING` | Exact modification disclosure path |
| `F06-SOURCE-OFFER-INCOMPLETE` | Exact source-offer field with missing digest, size, location, or evidence |
| `F06-SOURCE-OFFER-UNAVAILABLE` | Exact source-offer location or availability-evidence path |
| `F06-REDISTRIBUTION-DIRECT-ONLY-BUNDLED` | Exact direct-fetch acquisition or bundle-membership path |
| `F06-REDISTRIBUTION-PROHIBITED` | Exact redistribution-class path |
| `F06-STATUS-UNKNOWN` | Exact unknown or unresolved status path |
| `F06-POLICY-RESULT-MISSING` | `/f05_candidate_envelope_ref` or exact absent result binding |
| `F06-BRANDING-UNRESOLVED` | Exact branding/trademark disposition path |
| `F06-CHANNEL-REBUILD-FORBIDDEN` | Exact changed artifact digest or copy-terminal input path |
| `F06-SHADOW-FIELD-BYPASS` | Exact reserved alias or consumer-only field path |
| `F06-OPAQUE-METADATA-TRANSPLANT` | Exact opaque declaration or interface-contract path |
| `F06-SUPERSESSION-CURRENT-INVALID` | Exact current event-lineage path |
| `F06-RETENTION-PROJECTION-INVALID` | Exact retention or projection lock/path |

## 8. Acquisition, verified cache, consent, and mutation boundary

### 8.1 Closed acquisition-authority set

The acquisition authority enum is closed to exactly these seven authorities:

| Authority | Permitted input family | Required external contract |
| --- | --- | --- |
| `apple-authoritative` | Apple/vendor firmware and board-specific device inputs | Immutable endpoint identity, selector digest, expected blob digest and size, signed provenance, and availability evidence |
| `vendor-authoritative` | Vendor firmware, firmware ABI companions, and vendor metadata | Immutable vendor release identity, digest, size, signature, provenance, and redistribution decision |
| `recovery-stub-authoritative` | RecoveryOS, 1TR, recovery, and installer stub inputs | Immutable recovery identity, digest, size, signature, scope, and behavior evidence |
| `omarchy-release-authoritative` | Omarchy images, release manifests, boot assets, and public compliance bundles | Signed release document, immutable artifact digest, size, provenance, channel, and expiry |
| `package-index-authoritative` | Package indexes, repository metadata, and index signatures | Immutable index digest, repository identity, snapshot time, signature, and package closure |
| `package-payload-authoritative` | Package payloads and package signatures | Immutable package coordinate, payload digest, size, signature, index digest, and license evidence |
| `opaque-human-declaration-authoritative` | Human-produced opaque artifacts and their declarations | Signed declaration, declared digest and size, interface-contract digest, provenance, and observable behavior evidence |

An authority outside this set, a mutable mirror, a branch, a tag, a credentialed location, a resolver fallback, a local path, or a human assertion is rejected. Apple/vendor and opaque human-produced inputs remain bounded by their declared external contracts; F-06 never expands those contracts.

### 8.2 Pre-consent verified-cache handoff

The installer plan must execute this closed sequence before user consent or any destructive mutation: resolve the exact F-02 `installer-plan/v1` reference; enumerate every direct and transitive acquisition; fetch through the allowlisted authority; verify signature, immutable source, digest, size, provenance, and scope; write a content-addressed cache object; create a signed cache receipt; recompute the complete inventory closure; and show the exact plan and closure to the user. Direct-device fetch is inside this same handoff, not a later installer exception.

`VerifiedCacheReceipt` has exactly `receipt_document_id`, `scope_binding`, `authority`, `source_identity`, `artifact_digest`, `artifact_size_bytes`, `provenance_digest`, `verification_time`, `cache_object_digest`, `cache_location`, `closure_parent_ids`, `signature_ref`, and `receipt_digest`. A direct-device input is valid only when its receipt is present, its expected digest and size match the manifest, its source selector is bound, and its node is reachable in `f06.inventory/v1` before consent.

Consent is a signed acknowledgment of the exact displayed plan, candidate document ID, artifact-set digest, inventory closure digest, cache receipt set, rollback boundary, target channel, and expiry. Missing receipt, missing closure node, digest/size mismatch, unverified provenance, changed plan after consent, or incomplete offline bundle rejects before mutation.

### 8.3 Network-denied mutation

The mutation phase consumes only the verified cache closure and signed consent. Its network policy is exactly `deny-all`; DNS, HTTP, Git, package-manager resolution, mirror selection, credential lookup, and resolver fallback are forbidden. The mutation process fails closed if a required byte is absent from the cache or if a network-capable operation is attempted. A successful mutation cannot be reported when the network-denial proof is missing.

The offline bundle is complete only when every `shipped`, `acquired_only`, and required `build_only` input reachable from the installer root has a verified cache receipt or an explicit direct-device receipt allowed by the channel contract. A direct-fetch input absent from the cache closure rejects with `F06-CACHE-CLOSURE-MISSING`; a network-dependent mutation rejects with `F06-MUTATION-NETWORK-ALLOWED`.

## 9. License, redistribution, export, security, and branding policy

F-06 records evidence and joins signed decisions. It never concludes legal clearance, trademark permission, export clearance, security approval, or redistribution permission by itself. Uncertain, incomplete, contradictory, expired, unsigned, or missing evidence is a rejection.

The hard policy predicate is:

`valid_envelopes AND exact_f02_set AND exact_manifest_join AND complete_inventory AND immutable_provenance AND complete_sbom AND variant_complete_license_notice AND source_obligations_satisfied AND typed_signed_decisions AND current_trust_bindings AND no_prohibited_input AND channel_requirements_satisfied`

The predicate is false for an empty component set, empty evidence set, absent decision, unknown status, ambiguous license choice, incomplete source offer, missing direct-fetch receipt, digest mismatch, or unresolved exception. `WARN`, `PENDING`, `PASS_WITH_WARNINGS`, `BEST_EFFORT`, `ASSUMED`, and `MANUAL_EXCEPTION` are not decision values.

Each decision includes exact scope, component, candidate document ID and digest, artifact-set digest, channel, policy digest, validity interval, nonce/sequence, and F-03 authority binding. License choice, redistribution class, export/security flags, branding location, counsel interpretation, and owner disposition are joined independently. One decision cannot be reused across a component, candidate, channel, policy, or artifact set.

## 10. Closed supersession and correction event graph

### 10.1 Event schema and binding

The future event record family is exactly `f06.event/v1`. Each event has exactly `event_document_id`, `event_type`, `state`, `generation`, `predecessor_event_id`, `corrects_record_id`, `supersedes_record_id`, `lineage_digest`, `scope_binding`, `replay_identity`, `reason_code`, `created_at`, `valid_until`, `terminal_outcome`, `evidence_refs`, and `signature_ref`.

`event_type` is exactly `create`, `validate`, `accept`, `correct`, `supersede`, `revoke`, `reject`, or `close`. `state` is exactly `proposed`, `validated`, `accepted`, `corrected`, `superseded`, `revoked`, `rejected`, or `terminal`. `terminal_outcome` is required only for `rejected` or `terminal` and is exactly `REJECT` or `ADMIT`; it never means stable publication.

Every approval, result, evidence record, projection, and event has the complete `ScopeBinding` from Section 2.3: project, repository, slice, operation, schema-set digest, candidate document ID and payload digest, artifact-set digest, channel, policy digest, validity, and replay identity. Cross-slice, cross-repository, cross-operation, cross-candidate, cross-artifact, cross-channel, and cross-schema transplantation rejects.

### 10.2 States, transitions, generation, and lineage

The only transitions are `proposed -> validated`, `validated -> accepted`, `validated -> rejected`, `accepted -> corrected`, `accepted -> superseded`, `accepted -> revoked`, `corrected -> accepted`, `superseded -> terminal`, `revoked -> terminal`, and `rejected -> terminal`. No other edge is valid. `terminal` has no outgoing edge.

`generation` starts at 0 for `create` and increments exactly one from its predecessor for `correct`, `supersede`, or `revoke`. A correction must reference the exact corrected record and preserve its scope while changing its document ID and payload digest. A supersession must reference the exact prior record and bind the replacement to the same scope. A generation decrease, skipped generation, self-reference, repeated predecessor, cycle, or lineage digest mismatch rejects with `F06-EVENT-GENERATION-ROLLBACK`, `F06-EVENT-CYCLE`, or `F06-EVENT-LINEAGE-MISMATCH`.

The graph is bounded to 65,536 events, 64 lineage depth, and 262,144 lineage edges. Each event has one predecessor except the generation-zero root. Event IDs, replay identities, and predecessor tuples are unique. On restart, the evaluator reloads the signed event closure, replays events in `(generation, event_id)` order, verifies every signature and lineage digest, and resumes only from the last valid non-terminal state. Replaying the same event is idempotent only when its complete bytes and replay identity are identical; a same ID with changed bytes or a reused nonce rejects with `F06-EVENT-REPLAY`. A missing predecessor, terminal record with a child, or invalid state transition emits `F06-EVENT-TRANSITION-INVALID` and ends in `REJECT`.

Correction and supersession never delete or rewrite prior records. A new result must recompute all dependent joins, emit a new result digest, and carry a correction-chain receipt. F-06 terminal `ADMIT` is an evidence decision only; F-07 remains the sole stable-channel promotion terminal.

## 11. F-07-only stable promotion boundary

F-06 has no promotion operation, stable-copy authority, release-authority role, stable ledger writer, or path that bypasses F-07. F-06 may emit an `ADMIT` result and evidence bundle to its signed handoff. It cannot promote, copy to stable, authorize publication, rebuild, substitute, reclassify, or mutate any candidate.

F-07 is the sole stable-channel promotion terminal. F-07 may perform exact-copy promotion only after it verifies the already-approved digests and recomputes, against the final F-05 candidate closure: F-02 manifest and board joins; F-03 trust and authority; F-04 build and provenance; installer closure and network-denial evidence; rollback compatibility; license, redistribution, export, security, branding, counsel, and owner decisions; qualification Q-00 through Q-08; B-04; and public-ledger closure. F-07 copies bytes by digest and does not rebuild them.

F-07 rejects any rebuild, byte substitution, digest substitution, reclassification, channel widening, stale evidence, altered notice/source-offer bundle, rollback incompatibility, or path that reaches stable storage without the F-07 terminal. F-06 records this as a failed handoff when the required F-07 evidence is absent; it never treats an F-06 result as F-07 authority.

## 12. Private, reviewer, support, and public projections

### 12.1 Source evidence and projection allowlists

The private source evidence record is canonical and scope-bound. It may contain the authenticated envelopes, complete inventory graph, raw evidence references, signed decisions, review identities, exact filesystem and device observations, cache receipts, command output, and correction chain. It is accessible only to the ACL roles `coordinator`, `release-compliance-owner`, `counsel`, `security-reviewer`, `auditor`, and the named evidence custodian.

The four projections have exact field allowlists. A projection containing a field outside its allowlist rejects.

| Projection | Exact allowed fields |
| --- | --- |
| `private/v1` | `projection_type`, `projection_document_id`, `source_evidence_digest`, `scope_binding`, `raw_envelope_refs`, `inventory_digest`, `artifact_digest_set`, `decision_kinds`, `decision_digests`, `reviewer_pseudonyms`, `source_locations`, `filesystem_observations`, `device_observations`, `cache_receipt_digests`, `command_vector_digest`, `correction_chain_digest`, `retention_state`, `acl`, `audit_receipt_ref`, `projection_digest` |
| `reviewer/v1` | `projection_type`, `projection_document_id`, `source_evidence_digest`, `scope_binding`, `input_digest_set`, `inventory_digest`, `artifact_digest_set`, `finding_codes`, `finding_paths`, `decision_kinds`, `decision_digests`, `reviewer_pseudonyms`, `tool_versions`, `pass_fail_census`, `correction_chain_digest`, `audit_receipt_ref`, `projection_digest` |
| `support/v1` | `projection_type`, `projection_document_id`, `source_evidence_digest`, `scope_binding`, `candidate_document_id`, `candidate_payload_digest`, `board_public_id`, `channel`, `decision`, `finding_codes`, `public_artifact_digests`, `rollback_digest`, `support_pseudonyms`, `observed_at`, `expires_at`, `correction_chain_digest`, `audit_receipt_ref`, `projection_digest` |
| `public/v1` | `projection_type`, `projection_document_id`, `source_evidence_digest`, `scope_binding`, `candidate_document_id`, `candidate_payload_digest`, `channel`, `decision`, `public_artifact_digests`, `notice_bundle_digest`, `source_offer_index_digest`, `qualification_summary_digest`, `rollback_digest`, `public_pseudonyms`, `published_at`, `expires_at`, `correction_chain_digest`, `audit_receipt_ref`, `projection_digest` |

The reviewer projection may reveal finding paths and tool versions but never raw identities or secret-bearing locations. Support may reveal only a public board identifier and keyed pseudonyms. Public may reveal only public artifact, notice, source-offer, qualification-summary, rollback, decision, and lineage digests. Private fields are not copied into support or public projections by omission defaults; the projection generator constructs a fresh allowlisted object.

### 12.2 Pseudonymization, redaction, ACL, and proof

Every pseudonym matches `hmac-sha256:key-[a-z0-9-]{1,32}:v[0-9]+:[0-9a-f]{64}` and is computed over the domain-separated tuple `(project, repository, slice, candidate_document_id, subject_kind, subject_value)`. The HMAC key ID and version are signed in the projection lock and never derived from a user, device, path, or secret. Key rotation creates a new projection and digest; it never rewrites an old projection.

The forbidden-field set is closed and checked recursively: `filesystem_path`, `home_path`, `username`, `hostname`, `device_serial`, `device_uuid`, `mac_address`, `ip_address`, `secret`, `password`, `access_token`, `private_key`, `credential`, `private_url`, `query_secret`, `raw_reviewer_identity`, and `customer_data`. Forbidden keys, values, path-shaped strings, credentials in URIs, and secrets in canonical bytes, logs, notices, source-offer indexes, or projections reject with `F06-OUTPUT-PRIVATE-FIELD-LEAK`.

Each projection binds `source_evidence_digest`, `scope_binding`, `projection_policy_digest`, and `projection_digest`. The generator emits an audit receipt with `actor_role_binding_ref`, `input_digest`, `output_digest`, `field_allowlist_digest`, `redaction_rule_digest`, `acl_decision`, and `created_at`. The proof job expands every source field, applies the forbidden-field scanner, compares output keys to the exact allowlist, verifies pseudonym key/version binding, recomputes the projection digest, and runs a noninterference check: changing any forbidden private field changes neither support nor public bytes. Any leak, missing redaction proof, wrong ACL, or digest mismatch blocks publication.

## 13. Immutable retention and deletion

The retention lock contains immutable values in days. A record's effective deletion time is computed from the maximum of the applicable evidence-class retention, legal hold, supersession-chain dependency, rollback dependency, active-channel dependency, and audit dependency. No record or artifact may be deleted while any dependency remains reachable in the signed inventory or event graph.

| Evidence class | Minimum retention | Deletion form |
| --- | --- | --- |
| Canonical input envelope and F-02/F-03/F-04/F-05 references | 2,555 days | Signed tombstone after all dependencies clear |
| F-06 result, rejection findings, and pass/fail census | 2,555 days | Signed tombstone after all dependencies clear |
| Inventory and closure graph | 2,555 days | Signed tombstone after no candidate, rollback, or audit reaches it |
| License, notice, source-offer, export, security, branding, counsel, and owner decisions | 2,555 days | Signed tombstone after decision chain and active-channel dependencies clear |
| Installer cache receipts and mutation evidence | 730 days | Signed tombstone after rollback and support dependencies clear |
| Private and reviewer projections | 2,555 days | Signed tombstone after ACL audit and correction dependencies clear |
| Support projection | 2,555 days | Signed tombstone after active support channel and correction dependencies clear |
| Public projection, notice bundle, and source-offer index | 3,650 days | Public ledger tombstone; public correction history remains addressable |
| Audit receipts, command output, redaction proof, and promotion-copy proof | 2,555 days | Signed tombstone after audit closure and legal hold clear |
| Correction and supersession event records | 3,650 days | Never remove while any descendant, ledger entry, or audit receipt is reachable |

A legal hold is a signed `retention-hold/v1` record bound to the exact project, repository, slice, operation, schema set, candidate, artifact set, evidence class, and record IDs. It contains `hold_id`, `issued_by_role_binding_ref`, `reason_digest`, `starts_at`, `expires_at`, `extension_of`, `nonce`, and `signature_ref`. Only `ProjectOwner` and `OpenSourceComplianceCounsel` together may extend a hold; each extension is a new signed record, has an expiry no later than 365 days after issuance, and references the prior hold. An expired hold does not erase the hold history.

Precedence is total and ordered: `legal_hold` > `supersession_or_correction_chain` > `rollback_dependency` > `active_channel` > `audit_dependency` > `retention_expiry` > `deletion_eligibility`. The first true blocker controls. Deletion is eligible only when every higher-precedence blocker is false, retention expiry has passed, the record is unreachable from all roots, and the custodian has a signed deletion authorization. Deletion emits a tombstone containing the deleted record digest, reason, eligibility proof, prior chain digest, and deletion time. A tombstone is itself retained for 3,650 days and cannot be used to hide an earlier record.

## 14. Implementation, locks, reports, and CI contract

This section names future deliverables. None is implemented by this design-only change.

### 14.1 Exact deliverables

The implementation must create exactly these F-06 contract artifacts before any gate is claimed: `schemas/f06-records/v1.json`, `schemas/f06.inventory/v1.json`, `schemas/f06.event/v1.json`, `schemas/f06-projection/v1.json`, `schemas/f06-retention/v1.json`, `validators/f06_validate.py`, `validators/f06_projection.py`, `validators/f06_retention.py`, `reports/f06-report/v1.json`, `locks/f06-records.lock.json`, `locks/f06-policy.lock.json`, `locks/f06-grammar.lock.json`, `locks/f06-conformance.lock.json`, `locks/f06-retention.lock.json`, `locks/f06-projections.lock.json`, `locks/f06-tools.lock.json`, `locks/f06-imports.lock.json`, `fixtures/f06/manifest.json`, `fixtures/f06/baseline/`, `fixtures/f06/hostile/`, and `.github/workflows/f06-clean-checkout.yml`.

The lock files must pin `schema_set_digest`, every imported F-02 through F-05 version and digest, RFC 8785 JCS implementation `jcs==0.2.1`, Python `3.12.4`, `jsonschema==4.23.0`, `referencing==0.35.1`, `cryptography==43.0.1`, `pytest==8.3.3`, `git==2.45.2`, and `ripgrep==14.1.1`. The lock-derived tool set is closed; an unavailable, replaced, or unpinned tool is a failed gate.

### 14.2 Valid lock-derived command arrays

The following are valid JSON arrays of argv arrays. They contain no shell pseudo-commands, glob interpolation, ellipses, unspecified tools, or fail-open fallback. The command vector itself is recorded and digested in the report.

```json
[
  ["git", "status", "--porcelain=v1", "--untracked-files=all"],
  ["git", "diff", "--check", "--exit-code"],
  ["python3.12", "-m", "f06_locks.verify", "--lock", "locks/f06-records.lock.json", "--lock", "locks/f06-policy.lock.json", "--lock", "locks/f06-grammar.lock.json", "--lock", "locks/f06-conformance.lock.json", "--lock", "locks/f06-retention.lock.json", "--lock", "locks/f06-projections.lock.json", "--lock", "locks/f06-tools.lock.json", "--lock", "locks/f06-imports.lock.json"],
  ["python3.12", "-m", "f06_records.validate", "--schema", "schemas/f06-records/v1.json", "--imports", "locks/f06-imports.lock.json"],
  ["python3.12", "-m", "f06_inventory.validate", "--schema", "schemas/f06.inventory/v1.json", "--manifest", "fixtures/f06/manifest.json"],
  ["python3.12", "-m", "f06_events.validate", "--schema", "schemas/f06.event/v1.json", "--manifest", "fixtures/f06/manifest.json"],
  ["python3.12", "-m", "f06_policy.conformance", "--policy-lock", "locks/f06-policy.lock.json", "--fixture-manifest", "fixtures/f06/manifest.json"],
  ["python3.12", "-m", "f06_projection.verify", "--schema", "schemas/f06-projection/v1.json", "--lock", "locks/f06-projections.lock.json"],
  ["python3.12", "-m", "f06_retention.verify", "--schema", "schemas/f06-retention/v1.json", "--lock", "locks/f06-retention.lock.json"],
  ["python3.12", "-m", "f06_reports.validate", "--schema", "reports/f06-report/v1.json", "--fixture-manifest", "fixtures/f06/manifest.json"],
  ["rg", "--line-number", "--hidden", "--glob", "!.git/**", "(\\x3c{7}|\\x3d{7}|\\x3e{7})", "."],
  ["rg", "--line-number", "--hidden", "--glob", "!.git/**", "\\t", "."],
  ["git", "ls-files", "--error-unmatch", "schemas/f06-records/v1.json", "schemas/f06.inventory/v1.json", "schemas/f06.event/v1.json", "fixtures/f06/manifest.json", "reports/f06-report/v1.json"]
]
```

The `rg` commands are assertions: exit code 1 means no match and is a pass; exit code 0 means a forbidden match and is a fail; any other exit code is a tooling failure and is a fail. The lock verifier must reject any missing command, module, lock, schema, fixture, report, or imported digest before validators run. The CI runner must run from a clean checkout and preserve raw stdout, stderr, exit codes, command-vector digest, and the signed report.

### 14.3 Phase semantics and expected artifacts

| Phase | Required command family | Required result | Required artifact |
| --- | --- | --- | --- |
| `P0` lock admission | `f06_locks.verify` | `PASS` or fail-closed `FAIL` | Lock verification report and tool-version record |
| `P1` canonical parsing | `f06_records.validate` | `PASS` or `FAIL` with code/path census | Canonical bytes and parse-rejection envelope |
| `P2` inventory closure | `f06_inventory.validate` | `PASS` or `FAIL` with node/edge census | `f06.inventory/v1` closure report |
| `P3` event lineage | `f06_events.validate` | `PASS` or `FAIL` with transition census | `f06.event/v1` lineage report |
| `P4` policy conformance | `f06_policy.conformance` | Exact fixture result for every closed fixture | Fixture result matrix and result digests |
| `P5` projections | `f06_projection.verify` | `PASS` or `FAIL` with leak census | Four projection reports and redaction proof |
| `P6` retention | `f06_retention.verify` | `PASS` or `FAIL` with blocker census | Retention eligibility and tombstone proof |
| `P7` report schema | `f06_reports.validate` | `PASS` or `FAIL` | Signed machine report |
| `P8` clean checkout | Git and scans | `PASS` only on zero dirty paths and zero forbidden matches | Clean-checkout receipt |

Each phase is required. A missing runner, missing report, missing fixture, absent expected code/path, command encoding error, tool-version mismatch, or omitted phase is `FAIL`; no phase is silently skipped.

### 14.4 Report schema and retained artifacts

`f06-report/v1` has exactly `report_type`, `report_document_id`, `scope_binding`, `commit_sha`, `clean_checkout`, `lock_digests`, `tool_versions`, `command_vector_digest`, `phase_results`, `fixture_manifest_digest`, `decision`, `rejection_findings`, `pass_count`, `fail_count`, `skipped_count`, `tooling_limitation_count`, `artifact_refs`, `reviewer_binding_ref`, `started_at`, `finished_at`, `expires_at`, `correction_chain_digest`, `retention_state`, and `report_digest`.

Every report must contain a mandatory PASS/FAIL census for every phase and fixture. `pass_count`, `fail_count`, and `skipped_count` are exact counts, with `skipped_count=0` for a complete run. A missing or malformed report rejects with `F06-REPORT-SCHEMA-MISSING` at `/report` or `F06-REPORT-CENSUS-INCOMPLETE` at `/pass_fail_census`.

The closed retained-artifact set is canonical input envelopes, lock files, generated schemas, canonical inventory, F-04 evidence references, F-03 decision envelopes, evaluator result, rejection findings, NOTICE bundle, attribution bundle, source-offer index, four projections, fixture manifest, every fixture input and output, command output, redaction proof, retention proof, F-07 exact-copy proof when consumed, reviewer report, and correction/supersession events. Retention follows Section 13; no artifact may be dropped because it is large, private, failed, superseded, or inconvenient.

## 15. Closed hostile and positive fixture manifest

The fixture manifest is closed to exactly the IDs in the tables below. Every fixture contains a valid baseline candidate plus one named mutation, an exact expected decision, one exact rejection code, and one exact RFC 6901 JSON Pointer. A fixture harness must match decision, code, pointer, phase, and canonical result digest. A non-zero command alone is not a passing fixture.

### 15.1 Hostile fixtures

| Fixture ID | Mutation | Expected decision | Expected code | Expected JSON Pointer |
| --- | --- | --- | --- | --- |
| `f02-missing-type` | Remove one member from the authenticated F-02 set | `REJECT` | `F06-F02-TYPE-MISSING` | `/f02_envelope_refs` |
| `f02-unknown-ninth-type` | Add a ninth authenticated F-02 payload type | `REJECT` | `F06-F02-TYPE-UNKNOWN` | `/f02_envelope_refs/ninth-type/v1` |
| `envelope-schema-set-transplant` | Replace the schema-set digest while retaining signed payload bytes | `REJECT` | `F06-ENVELOPE-SCHEMA-SET-MISMATCH` | `/f02_envelope_refs/platform-manifest/v1/schema_set_digest` |
| `envelope-document-id-transplant` | Reuse a document ID from a different payload | `REJECT` | `F06-ENVELOPE-DOCUMENT-ID-MISMATCH` | `/f02_envelope_refs/platform-manifest/v1/document_id` |
| `envelope-payload-digest-transplant` | Copy a payload digest from another document | `REJECT` | `F06-ENVELOPE-PAYLOAD-DIGEST-MISMATCH` | `/f02_envelope_refs/platform-manifest/v1/payload_digest` |
| `decision-loose-reference` | Put a decision digest in an unattached collection | `REJECT` | `F06-DECISION-UNATTACHED` | `/decision_bindings` |
| `decision-wrong-role` | Use a source-review role for a redistribution disposition | `REJECT` | `F06-TRUST-ROLE-SCOPE-MISMATCH` | `/components/firmware/redistribution/decision_ref` |
| `inventory-disconnected-node` | Add a node not reachable from any root | `REJECT` | `F06-INVENTORY-NODE-DISCONNECTED` | `/nodes/node-disconnected` |
| `inventory-duplicate-node` | Add two nodes with the same semantic key | `REJECT` | `F06-INVENTORY-SEMANTIC-DUPLICATE` | `/nodes/node-duplicate/semantic_key` |
| `inventory-singular-artifact` | Replace the bounded artifact array with a singular artifact object | `REJECT` | `F06-INVENTORY-ARTIFACT-SHAPE` | `/nodes/node-artifact/artifact_identities` |
| `duplicate-scope-key` | Duplicate a decision/component semantic scope | `REJECT` | `F06-SEMANTIC-DUPLICATE` | `/decision_bindings/redistribution/components/0` |
| `path-malformed` | Use a path with an invalid escape and leading-zero array index | `REJECT` | `F06-PATH-MALFORMED` | `/policy/conditions/0/path` |
| `condition-malformed` | Use an unknown condition kind and empty `all` | `REJECT` | `F06-CONDITION-MALFORMED` | `/policy/conditions/0/kind` |
| `bound-exact-plus-one` | Set a collection to its locked maximum plus one | `REJECT` | `F06-BOUND-EXCEEDED` | `/nodes` |
| `handshake-version-mismatch` | Offer a higher unsupported minor version | `REJECT` | `F06-HANDSHAKE-INCOMPATIBLE` | `/handshake/minor` |
| `handshake-capability-mismatch` | Omit a required capability and add an unknown one | `REJECT` | `F06-HANDSHAKE-INCOMPATIBLE` | `/handshake/capabilities/0` |
| `event-supersession-cycle` | Make a correction lineage point back to its descendant | `REJECT` | `F06-EVENT-CYCLE` | `/events/evt-cycle/predecessor_event_id` |
| `event-generation-rollback` | Set a correction generation below its predecessor | `REJECT` | `F06-EVENT-GENERATION-ROLLBACK` | `/events/evt-rollback/generation` |
| `event-replay` | Reuse an F-03 nonce with changed event bytes | `REJECT` | `F06-EVENT-REPLAY` | `/events/evt-replay/replay_identity` |
| `license-alternative-ambiguous` | Select zero or two options for a `one-of` license | `REJECT` | `F06-LICENSE-CHOICE-AMBIGUOUS` | `/components/linux/license_notice/selected_license_option_ids` |
| `source-offer-incomplete` | Remove source digest, size, and availability evidence | `REJECT` | `F06-SOURCE-OFFER-INCOMPLETE` | `/components/linux/license_notice/source_offers/0` |
| `source-offer-unsigned` | Remove the source-offer signature reference | `REJECT` | `F06-SOURCE-OFFER-UNSIGNED` | `/components/linux/license_notice/source_offers/0/signature_ref` |
| `direct-fetch-cache-missing` | Omit the verified-cache receipt for a direct-device input | `REJECT` | `F06-CACHE-CLOSURE-MISSING` | `/f02_envelope_refs/installer-plan/v1/cache_receipts/0` |
| `mutation-network-allowed` | Change mutation network policy from deny-all | `REJECT` | `F06-MUTATION-NETWORK-ALLOWED` | `/f02_envelope_refs/installer-plan/v1/mutation/network_policy` |
| `f06-local-promotion` | Add an F-06 stable-copy operation and stable authority | `REJECT` | `F06-F07-PROMOTION-BYPASS` | `/operation` |
| `public-private-field-leak` | Include a private filesystem path in the public projection | `REJECT` | `F06-OUTPUT-PRIVATE-FIELD-LEAK` | `/public/filesystem_path` |
| `pseudonym-key-mismatch` | Change the pseudonym key version without changing projection scope | `REJECT` | `F06-OUTPUT-PSEUDONYM-INVALID` | `/public/public_pseudonyms/0` |
| `projection-source-digest-mismatch` | Change source evidence without recomputing projection digest | `REJECT` | `F06-OUTPUT-PROJECTION-DIGEST-MISMATCH` | `/public/source_evidence_digest` |
| `deletion-under-legal-hold` | Delete a record while a signed hold is active | `REJECT` | `F06-RETENTION-HOLD-BLOCKS-DELETION` | `/retention/eligibility` |
| `deletion-under-rollback` | Delete an artifact reachable from rollback closure | `REJECT` | `F06-RETENTION-ROLLBACK-BLOCKS-DELETION` | `/retention/rollback_dependency` |
| `deletion-under-reachability` | Delete an event with a reachable descendant | `REJECT` | `F06-RETENTION-REACHABILITY-BLOCKS-DELETION` | `/retention/reachable_descendants` |
| `command-array-invalid` | Encode a glob and conditional as invalid JSON-like shell text | `REJECT` | `F06-COMMAND-ENCODING-INVALID` | `/command_vector/0` |
| `fixture-manifest-missing` | Remove the closed fixture manifest | `REJECT` | `F06-FIXTURE-MANIFEST-MISSING` | `/fixture_manifest_digest` |
| `report-schema-missing` | Remove the required report schema from the locked deliverable set | `REJECT` | `F06-REPORT-SCHEMA-MISSING` | `/report` |
| `reviewer-identity-overlap` | Assign the record author as independent reviewer and approver | `REJECT` | `F06-IDENTITY-INTERSECTION` | `/roles/independent_reviewer` |
| `handoff-omitted` | Remove the F-06 to qualification handoff row | `REJECT` | `F06-HANDOFF-MISSING` | `/handoffs/f06-qualification` |

### 15.2 Positive fixtures

The closed positive set is exactly `valid-source-complete`, `valid-license-one-of`, `valid-source-offer`, `valid-direct-device-cache`, `valid-opaque-declaration`, `valid-correction-chain`, `valid-f07-copy-input`, and `valid-boundary-at-maximum`. Positive fixtures may produce `ADMIT` only as an F-06 evidence decision for their exact scope; none proves stable publication, compatibility, qualification, legal clearance, support, or DONE.

## 16. Identity separation and handoff matrix

### 16.1 Disjoint roles

The role-intersection matrix is closed. The identities for `record_author`, `evidence_producer`, `evaluator`, `candidate_assembler`, `independent_reviewer`, `approver`, `projection_publisher`, and `retention_custodian` must be distinct where the matrix says `forbidden`. A role binding is an F-03 authority binding, not an email comparison.

| Role pair | Intersection |
| --- | --- |
| `record_author` / `evaluator` | Forbidden |
| `record_author` / `independent_reviewer` | Forbidden |
| `evidence_producer` / `independent_reviewer` | Forbidden |
| `candidate_assembler` / `independent_reviewer` | Forbidden |
| `candidate_assembler` / `approver` | Forbidden |
| `evaluator` / `approver` | Forbidden |
| `projection_publisher` / `independent_reviewer` | Forbidden |
| `retention_custodian` / `independent_reviewer` | Forbidden |
| `ProjectOwner` / `OpenSourceComplianceCounsel` | Forbidden for a two-party decision |
| `TrademarkBrandOwner` / `record_author` | Forbidden for the branding decision |

An overlap, missing role binding, role reuse across a forbidden pair, or self-approval rejects with `F06-IDENTITY-INTERSECTION` at the exact role path. The coordinator may review a design, but cannot convert an overlapping implementation run into independent evidence.

### 16.2 Authoritative producer-consumer handoff matrix

Every handoff row has an immutable input, producer, consumer, gate, rejection code and JSON path, freshness/scope binding, and residual owner. The matrix is closed to the rows below; an omitted row is a failed design handoff.

| Handoff ID | Immutable input | Producer -> consumer | Gate | Rejection code/path | Freshness and scope binding | Residual owner |
| --- | --- | --- | --- | --- | --- | --- |
| `f02-to-f06` | Eight `EnvelopeRef` values and payload-set digest | F-02 -> F-06 | Exact eight-type import and signature verification | `F06-F02-TYPE-UNKNOWN` `/f02_envelope_refs` | Current schema-set digest, candidate, artifact set, channel | F-02 owner |
| `f03-to-f06` | `Trusted<TrustContext>` and `AuthorityRoleBinding` references | F-03 -> F-06 | Signature, role, scope, validity, replay verification | `F06-TRUST-ROLE-SCOPE-MISMATCH` `/f03_envelope_refs` | F-03 trusted time; exact project/repository/slice/operation | F-03 owner |
| `f04-to-f06` | Builder, SBOM, provenance, artifact-store, package, index, reproducibility envelopes | F-04 -> F-06 | Complete source/artifact/dependency closure | `F06-PROVENANCE-SBOM-INCOMPLETE` `/f04_envelope_refs` | Exact candidate, artifact set, recipe, toolchain, policy | F-04 owner |
| `f05-to-f06` | Assembled candidate envelope and final manifest digest | F-05 -> F-06 | Candidate and manifest join | `F06-BINDING-MANIFEST-MISMATCH` `/f05_candidate_envelope_ref` | Current candidate document ID and payload digest | F-05 owner |
| `f06-to-f07` | Signed F-06 result, evidence digests, notice/source-offer bundles | F-06 -> F-07 | F-07 recomputes all closure and exact-copy inputs | `F06-F07-PROMOTION-BYPASS` `/f07_handoff` | Fresh for exact candidate, channel, policy, rollback, qualification | F-07 owner |
| `i01-to-f06` | Signed launch and immutable installer release metadata | I-01 -> F-06 | Signed release metadata and board scope | `F06-INPUT-MISSING` `/installer/i01` | Launch metadata expiry and candidate scope | Installer owner |
| `i02-to-f06` | Read-only board, firmware, APFS, Recovery, and power inventory | I-02 -> F-06 | Stable identifiers and no inferred board | `F06-STRUCTURE-INCONSISTENT` `/installer/i02/inventory` | Observation time and board candidate scope | Installer owner |
| `i03-to-f06` | Board-registry resolution and typed compatibility result | I-03 -> F-06 | Exact registry component join | `F06-BINDING-MANIFEST-INVENTORY-MISMATCH` `/installer/i03/board_ref` | Current board registry digest and candidate | Installer owner |
| `i04-to-f06` | Human-readable and machine-readable plan | I-04 -> F-06 | Plan covers every partition, byte, rollback, and recovery change | `F06-CLOSURE-COMPONENT-MISSING` `/installer/i04/plan` | Plan digest, board, candidate, channel | Installer owner |
| `i05-to-f06` | Verified cache receipts and offline closure | I-05 -> F-06 | Every required input verified before consent | `F06-CACHE-CLOSURE-MISSING` `/installer/i05/cache_receipts` | Receipt time, authority, digest, size, candidate | Installer owner |
| `i06-to-f06` | Signed consent for exact plan and closure | I-06 -> F-06 | Consent binds plan, closure, rollback, and expiry | `F06-DECISION-TRANSPLANT` `/installer/i06/consent` | Consent validity and exact scope | Installer owner |
| `i07-to-f06` | Ephemeral credential channel and credential-state evidence | I-07 -> F-06 | No credential in canonical bytes or logs | `F06-OUTPUT-PRIVATE-FIELD-LEAK` `/installer/i07/credentials` | Operation-bound, single-use, expiry-bound | Installer owner |
| `i08-to-f06` | Network-denial and mutation transcript | I-08 -> F-06 | Mutation resolver cannot access network or fallback | `F06-MUTATION-NETWORK-ALLOWED` `/installer/i08/network_policy` | Mutation operation and cache closure binding | Installer owner |
| `i09-to-f06` | Boot handoff, clean-path, recovery, and rollback result | I-09 -> F-06 | Exact F-07/F-05 and qualification joins are present | `F06-BINDING-MANIFEST-INVENTORY-MISMATCH` `/installer/i09/result` | Candidate, board, rollback, channel, operation | Installer owner |
| `ledger-public-to-f06` | Public notice, attribution, source-offer, and ledger digests | Public evidence ledger -> F-06 | Projection and public closure digest equality | `F06-OUTPUT-PROJECTION-DIGEST-MISMATCH` `/public_ledger` | Publication time, channel, candidate, correction chain | PublicSourceOfferCustodian |
| `ledger-support-to-f06` | Support projection, redaction proof, and audit receipt | Support evidence ledger -> F-06 | Support allowlist and noninterference proof | `F06-OUTPUT-PRIVATE-FIELD-LEAK` `/support_ledger` | Active support channel, source digest, ACL | Support owner |
| `rollback-to-f06` | Rollback target, compatibility proof, and retained artifacts | Rollback owner -> F-06 | Rollback closure and reachability | `F06-RETENTION-ROLLBACK-BLOCKS-DELETION` `/rollback` | Current candidate, artifact set, channel, retention | Rollback owner |
| `q00-to-f06` | Canonical board intake/admission evidence | Q-00 -> F-06 | Digest-addressed registry admission | `F06-BINDING-MANIFEST-MISMATCH` `/qualification/q00` | Board, registry, candidate, evidence expiry | Q-00 owner |
| `q01-to-f06` | Installation safety qualification | Q-01 -> F-06 | Required installation and APFS observations | `F06-POLICY-INVALID` `/qualification/q01` | Board, installer plan, candidate, run time | Q-01 owner |
| `q02-to-f06` | Boot-picker, Recovery, and DFU qualification | Q-02 -> F-06 | Required Apple boot and recovery observations | `F06-POLICY-INVALID` `/qualification/q02` | Board, boot tuple, candidate, run time | Q-02 owner |
| `q03-to-f06` | Core platform and boot-tuple qualification | Q-03 -> F-06 | Kernel, DTB, firmware ABI, Mesa, and boot stack tuple | `F06-POLICY-INVALID` `/qualification/q03` | Exact typed compatibility and artifact set | Q-03 owner |
| `q04-to-f06` | Power, thermal, and suspend qualification | Q-04 -> F-06 | Quantitative threshold evidence and repeat count | `F06-POLICY-INVALID` `/qualification/q04` | Board, kernel/firmware tuple, threshold lock | Q-04 owner |
| `q05-to-f06` | Display and graphics qualification | Q-05 -> F-06 | All applicable display/GPU rows and evidence | `F06-POLICY-INVALID` `/qualification/q05` | Board capabilities, Mesa digest, channel | Q-05 owner |
| `q06-to-f06` | I/O, network, and peripheral qualification | Q-06 -> F-06 | Applicable I/O, Wi-Fi, Bluetooth, and hotplug rows | `F06-POLICY-INVALID` `/qualification/q06` | Board, firmware, package, and run freshness | Q-06 owner |
| `q07-to-f06` | Audio, camera, input, and media qualification | Q-07 -> F-06 | Applicable audio/input/media rows and safety checks | `F06-POLICY-INVALID` `/qualification/q07` | Board, firmware, kernel, Mesa, channel | Q-07 owner |
| `q08-to-f06` | Security, update, rollback, and removal qualification | Q-08 -> F-06 | Security boundary, update, rollback, and clean-removal rows | `F06-POLICY-INVALID` `/qualification/q08` | Candidate lineage, rollback closure, retention | Q-08 owner |
| `b04-to-f06` | B-04 artifact, build, or boundary evidence | B-04 -> F-06 | Exact artifact/provenance/security boundary join | `F06-PROVENANCE-RECIPE-MISSING` `/b04` | Artifact set, source/provenance, operation | B-04 owner |
| `p04-to-f06` | P-04 policy and trust evidence | P-04 -> F-06 | Policy lock and trust context equality | `F06-ENVELOPE-SCHEMA-SET-MISMATCH` `/p04` | Policy digest, schema set, candidate, channel | P-04 owner |
| `p06-to-f06` | P-06 integration and delivery evidence | P-06 -> F-06 | Integration evidence does not replace F-07 terminal | `F06-F07-PROMOTION-BYPASS` `/p06` | Exact operation, candidate, channel | P-06 owner |
| `p07-to-f06` | P-07 release ledger and terminal evidence | P-07 -> F-06 | Public-ledger closure and F-07 handoff evidence | `F06-HANDOFF-MISSING` `/p07` | Candidate, channel, rollback, qualification | P-07 owner |
| `owner-to-f06` | Signed owner disposition envelope | ProjectOwner -> F-06 | Typed owner decision and F-03 role binding | `F06-TRUST-ROLE-SCOPE-MISMATCH` `/decision_bindings/owner` | Exact external impact, channel, policy, expiry | ProjectOwner |
| `counsel-to-f06` | Signed counsel license/source-offer interpretation | OpenSourceComplianceCounsel -> F-06 | Typed counsel decision and source evidence join | `F06-DECISION-UNATTACHED` `/decision_bindings/counsel` | Exact component, candidate, artifact set, expiry | OpenSourceComplianceCounsel |

## 17. Future gates and explicit design-time fail census

The future gate IDs are `G-F06-01` through `G-F06-10` and have no pass claim in this design-only slice.

| Gate | Required observed output | Current design-time result |
| --- | --- | --- |
| `G-F06-01` | Schema, JCS bytes, grammar, bounds, and imported-type report | `FAIL: NOT IMPLEMENTED` |
| `G-F06-02` | F-03 trust, authority, expiry, scope, and replay report | `FAIL: NOT IMPLEMENTED` |
| `G-F06-03` | Exact inventory node, artifact, edge, exclusion, and reachability report | `FAIL: NOT IMPLEMENTED` |
| `G-F06-04` | F-04 provenance, SBOM, recipe, source, and artifact digest report | `FAIL: NOT IMPLEMENTED` |
| `G-F06-05` | License, alternatives, exceptions, notices, modification, source-offer report | `FAIL: NOT IMPLEMENTED` |
| `G-F06-06` | Typed decision, role, scope, validity, direct-fetch, export, security, and branding report | `FAIL: NOT IMPLEMENTED` |
| `G-F06-07` | Private/reviewer/support/public projection and noninterference report | `FAIL: NOT IMPLEMENTED` |
| `G-F06-08` | Closed hostile and positive fixture code/path census | `FAIL: NOT IMPLEMENTED` |
| `G-F06-09` | F-05 consumer guard and F-07 exact-copy terminal evidence | `FAIL: NOT IMPLEMENTED` |
| `G-F06-10` | Clean-checkout CI, pinned tools, disjoint identities, retention, and independent review | `FAIL: NOT IMPLEMENTED` |

The design-time fail census is explicit: canonical schemas are not implemented; validators are not implemented; the F-03 resolver is not integrated; F-04 adapters are not implemented; the F-05 consumer guard is not implemented; installer cache and network-denial enforcement is not implemented; license, source-offer, redistribution, export, security, and branding decisions are not cleared; projection and redaction enforcement is not implemented; retention and tombstone enforcement is not implemented; hostile and positive fixtures are not implemented; CI and independent review are not implemented; no legal clearance is claimed; no hardware compatibility or qualification is claimed; no support or release readiness is claimed; F-06 is not DONE.

### 17.1 Blocker closure map

This map is the cross-reference index for all thirteen reviewed blockers and names the contract that closes each one.

| Blocker | Closing contract sections |
| --- | --- |
| `B1` | Sections 2 and 3: exact eight-type F-02 map, one `EnvelopeRef`, separate schema/document/payload identities, and canonical manifest paths |
| `B2` | Section 6: typed signed decisions, closed decision-kind-to-role map, F-03 resolution, exact scope, freshness, and replay joins |
| `B3` | Section 5: exact `f06.inventory/v1` nodes, artifact arrays, typed edges, exclusions, reachability, and exactly-once closure |
| `B4` | Section 7.3: total phased parser, stable code/path vocabulary, bounded rejection envelope, and deterministic selection key |
| `B5` | Sections 7.1 and 7.2: frozen grammars, bounds, ordering, duplicate scopes, conditions, and handshake outcomes |
| `B6` | Section 10: closed bounded event DAG, states, transitions, generation, lineage, replay, restart, and terminal rules |
| `B7` | Section 6.3: variant-complete licenses, choices, exceptions, notices, modifications, source offers, and signed joins |
| `B8` | Section 8: seven-authority allowlist, pre-consent verified cache, direct-device receipt, closure, and network-denied mutation |
| `B9` | Section 11: F-06 evidence-only boundary and F-07 sole exact-copy stable terminal |
| `B10` | Section 12: four field-allowlisted projections, pseudonym key/version binding, ACLs, redaction, audit, and proof |
| `B11` | Section 13: immutable day values, holds, correction receipts, precedence, eligibility, and tombstones |
| `B12` | Section 14: exact deliverables, pinned tools, valid argv arrays, phase artifacts, closed fixtures, reports, and fail-closed CI |
| `B13` | Section 16: disjoint identities and the authoritative producer-consumer handoff matrix |

## 18. Residual owners and coordinator ruling

The following residuals remain named and blocking: coordinator approval of the imported locks and exact F-06 schemas; F-02 through F-05 agreement on generated bindings and version ranges; F-03 implementation of `Trusted<TrustContext>`, `AuthorityRoleBinding`, and replay protection; appointment of disjoint role identities; counsel decisions for licenses, source offers, export, and redistribution; firmware/vendor and opaque-artifact declarations; trademark and branding decisions; installer pre-consent cache and network-denial implementation; Q-00 through Q-08 evidence; B-04 and P-04/P-06/P-07 handoffs; F-05 candidate guard; F-07 exact-copy terminal; projection ACL/redaction proof; retention lock and legal-hold process; closed fixture implementation; clean-checkout CI; and independent review.

Each residual blocks the affected gate and cannot be waived by prose, a local assertion, a warning, a branch, a mutable URL, a copied digest, an unsigned checkpoint, or an F-06 result. Human and counsel checkpoints remain human decisions. The opaque artifact boundary remains external and is not a future F-06 source-inspection task.

Requested coordinator ruling: accept, reject, or amend this design-only contract. If accepted, implementation may begin only after the imported locks, generated bindings, residual role bindings, closed fixtures, and handoff owners exist. F-06 must remain evidence-only, fail closed, and subordinate to F-05 and the F-07 stable-channel terminal.

This note does not claim implementation, legal clearance, redistribution permission, compatibility, qualification, support, release readiness, promotion authority, or DONE.
