# F-06 Release Compliance Design Note

Status: DESIGN-ONLY — coordinator ruling required; no implementation, canonical schema, policy engine, test suite, workflow, release artifact, legal clearance, compatibility claim, or DONE state is established by this note.

Slice: F-06

Repository: `omarchy-apple-platform`

Audience: coordinator, F-02/F-03/F-04/F-05 owners, installer owner, component maintainers, release-compliance owner, counsel, and independent reviewers.

## 1. Purpose and hard boundaries

F-06 defines the future release-compliance contract that determines whether a candidate may be assembled and promoted. It covers the evidence closure, policy inputs, human decision checkpoints, public compliance projections, and fail-closed gates for every shipped or acquired input. It does not implement those controls in this slice.

The note consumes the canonical interfaces named by the program. It does not redefine `board-registry/v1`, `platform-manifest/v1`, `installer-plan/v1`, `qualification-record/v1`, `boot-health/v1`, the F-03 signed-envelope and trust contracts, or the F-04 builder, SBOM, provenance, artifact-store, package-index, and promotion contracts. A future implementation must import generated bindings and validators for those interfaces. Repeating a field in an F-06 reference is a binding or digest reference, not a second authority for the imported object.

The m1n1-omarchy repository is an opaque human-produced artifact boundary. F-06 must not inspect, read, analyze, edit, test, clone, fetch, browse, characterize, or delegate work against that repository or its source. The only acceptable F-06 inputs for that boundary are human-produced signed declarations, declared metadata, signed hashes, schemas, provenance, and externally observable artifact behavior evidence. A declaration cannot authorize access to the underlying source.

The source checkout used to read the canonical program had a pre-existing modification to `PROGRAM.md`; this lane does not copy, alter, or adjudicate that modification. This note is based on the requested `origin/main` worktree and remains subordinate to the coordinator-owned program and ruling.

## 2. Design-only decision model

The future F-06 implementation will publish one typed result for one exact candidate input. The result is an admission decision, not a legal opinion and not a hardware or compatibility qualification result.

The only policy result decisions are `ADMIT` and `REJECT`. There is no `WARN`, `PASS_WITH_WARNINGS`, `PENDING`, or implicit success value. An absent result is a rejection at F-05. A `REJECT` result must contain a deterministic fail census. An `ADMIT` result is valid only for the exact candidate, target channel, policy lock, trust context, artifact digests, notice bundle, source-offer index, and expiry named by the result.

F-06 admission is necessary but not sufficient for release. F-05 must additionally prove manifest, tuple, ABI, board, trust, build, installer, qualification, rollback, and channel gates. F-06 must never turn an absent or failing F-05 gate into a compliance success.

For this design, `release-compliance/v1` is a proposed F-06 record family name pending coordinator approval. It is not a checked-in schema or a permission to add one in this slice.

## 3. Canonical interface imports

The following are hard input contracts. F-06 stores their identifiers and digests and resolves them through the owning implementation; it does not copy their payload field lists or create local substitutes.

| Owned interface | F-06 consumes | F-06 must not do |
| --- | --- | --- |
| F-02 `board-registry/v1` and canonical digest/canonicalization rules | The selected board record digest, platform identity binding, and exact manifest-to-board relationship | Infer a board from a chip family, invent a second board map, or accept an unvalidated local selector |
| F-02 `platform-manifest/v1` | The exact component keys, source commits, recipe digests, artifact digests, package versions, inter-component constraints, signing identities, channel, and rollback compatibility | Select versions independently, replace a manifest field with a handwritten shadow field, or treat a branch, tag, URL, or package-manager resolution as authority |
| F-03 signed envelopes and trust context | Envelope verification, key role, threshold, delegation, expiry, freeze, rollback, revocation, and `AuthorityRoleBinding` resolution | Verify with a local trust root, accept an unsigned decision, treat an actor name as authority, or launder an untrusted declaration through F-06 |
| F-04 builder/SBOM/provenance/artifact contracts | Builder identity, source closure, recipe and toolchain digests, SBOM and provenance evidence, artifact-store identity, package/index signatures, and reproducibility results | Reconstruct provenance from logs, accept a partial SBOM, compute a new artifact during promotion, or replace an F-04 record with a compliance assertion |
| F-05 candidate assembly | Candidate digest, required-gate census, generated consumer bindings, tuple/ABI validation, and final immutable manifest output | Admit a candidate that F-05 did not assemble or let a downstream consumer bypass the assembled manifest |

Every imported object is referenced by its canonical digest and signed envelope reference. The signed payload is canonicalized before its digest is computed. A result digest excludes its own signature and result-digest field, preventing a self-referential digest from becoming evidence. Signature verification covers the canonical payload and envelope metadata according to F-03.

## 4. Closed component compliance inventory

### 4.1 Inventory scope

The future inventory is the complete closure of the candidate platform manifest, installer manifest, package and image indexes, builder inputs, runtime dependencies, embedded resources, acquisition requirements, and public compliance bundle. It includes shipped items and items acquired only during build, install, first boot, update, recovery, or support generation. Discovery is complete only when every manifest reference, SBOM node, package index entry, image layer, installer payload, patch queue entry, font/theme/artwork file, and opaque boot artifact reference resolves to one inventory component.

The inventory is closed over both direct and transitive inputs. A component may not be omitted because it is generated, downloaded during installation, embedded in another file, copied from an upstream project, selected by an index, needed only for recovery, or not installed on every board. If an input is intentionally excluded, the inventory must contain an explicit signed exclusion record with the exclusion basis and evidence; an absent row is not an exclusion.

### 4.2 Closed component classes

`component_class` is a closed enum with exactly these values:

| Value | Required coverage |
| --- | --- |
| `binary` | Executables, shared libraries, kernel modules, helper programs, and generated machine-code payloads shipped or acquired |
| `source` | Source snapshots, vendored source, generated source inputs, documentation source used to build a shipped item, and source archives |
| `firmware_blob` | Device firmware, audio/DSP firmware, wireless/NVRAM/regulatory data, GPU/media firmware, boot firmware inputs, and other non-source blobs |
| `package` | Package payloads, package metadata, package signatures, package scripts, and package-level dependencies |
| `package_index` | Repository databases, package indexes, repository metadata, mirror metadata, and index signatures |
| `container_image` | Builder, test, installer, recovery, and runtime container or image manifests, layers, and configuration |
| `font_theme_artwork` | Fonts, icon fonts, themes, wallpapers, artwork, logos, UI assets, and generated visual resources |
| `installer_component` | macOS application bundles, helper tools, scripts, recovery components, APFS/boot handoff resources, and installer-local data |
| `downstream_patch_queue` | Ordered patches, rebases, carried fixes, generated patch series, and upstream disposition evidence for a fork |
| `opaque_boot_artifact` | A human-produced boot artifact accepted only through the external opaque-boundary declaration and behavior contract |

The class is not a license or redistribution decision. A single upstream project may produce multiple inventory rows when its source, binary, firmware, package, image, patch queue, and artwork have different identities or obligations. A `firmware_blob` row does not imply that its source is available. An `opaque_boot_artifact` row does not imply anything about the source that produced it.

### 4.3 Inventory lifecycle and acquisition mode

`lifecycle` is a closed enum with exactly `shipped`, `acquired_only`, `build_only`, and `metadata_only`. `acquisition_mode` is a closed enum with exactly `embedded_in_candidate`, `fetched_from_manifest_source`, `fetched_per_device_from_authoritative_source`, `materialized_by_builder`, and `declared_external_artifact`.

The following combinations are mandatory:

| Condition | Required combination |
| --- | --- |
| Bytes are shipped inside a release, installer, package, image, or offline bundle | `lifecycle=shipped` and `acquisition_mode=embedded_in_candidate` |
| Bytes are consumed by build or test but are not shipped | `lifecycle=build_only` or `acquired_only`, with the actual acquisition mode |
| A source, notice, index, or declaration is carried without the underlying runtime bytes | `lifecycle=metadata_only` and a typed reference to the represented component |
| A device-specific vendor input is fetched from an authoritative endpoint | `acquisition_mode=fetched_per_device_from_authoritative_source`, exact expected digest, endpoint evidence, and no bundled bytes |
| A human-produced artifact is supplied at the platform boundary | `component_class=opaque_boot_artifact`, `acquisition_mode=declared_external_artifact`, and a valid opaque declaration |

An item marked `fetched_per_device_from_authoritative_source` cannot be present in the candidate byte bundle or an offline bundle. If it is bundled, evaluation rejects the candidate as a direct-fetch-only redistribution violation. An offline installation claim requires the exact permitted bytes and all required compliance evidence to be present in the signed offline bundle.

### 4.4 Completeness invariant

The inventory completeness predicate is:

`inventory_complete = manifest_closure_complete AND sbom_closure_complete AND artifact_store_closure_complete AND installer_acquisition_closure_complete AND opaque_declaration_closure_complete AND no_unresolved_reference`.

F-06 evaluates this predicate against the exact candidate and does not accept a maintainer assertion, a count copied from a report, or an inventory generated from only the top-level manifest. Any closure mismatch is a hard rejection.

## 5. Typed F-06 record contract

This section is a design-level field contract for a future generated record family. It is not a production schema. Field names and types below are exact for the F-06 proposal, while imported F-02/F-03/F-04 fields remain owned by those slices.

### 5.1 Primitive types and identifier grammar

All identifiers are lowercase ASCII and are compared byte-for-byte after canonicalization. The proposed grammar is:

| Type | Grammar and meaning |
| --- | --- |
| `ComponentId` | `cmp-[a-z0-9]+(?:-[a-z0-9]+){0,7}`, maximum 64 bytes |
| `RecordId` | `rec-[0-9a-hj-km-np-tv-z]{26}`, a lowercase Crockford base32 payload excluding `i`, `l`, `o`, and `u` |
| `ArtifactId` | `art-[0-9a-hj-km-np-tv-z]{26}` |
| `EvidenceId` | `evd-[0-9a-hj-km-np-tv-z]{26}` |
| `DecisionId` | `dec-[0-9a-hj-km-np-tv-z]{26}` |
| `BundleId` | `bnd-[0-9a-hj-km-np-tv-z]{26}` |
| `OriginId` | `org-[0-9a-hj-km-np-tv-z]{26}` |
| `PatchQueueId` | `pq-[0-9a-hj-km-np-tv-z]{26}` |
| `PatchId` | `pat-[0-9a-hj-km-np-tv-z]{26}` |
| `TextId` | `txt-[0-9a-hj-km-np-tv-z]{26}` |
| `OfferId` | `off-[0-9a-hj-km-np-tv-z]{26}` |
| `Digest` | `sha256:[0-9a-f]{64}`; no uppercase, alternate algorithm, or unqualified hexadecimal value |
| `GitCommitDigest` | `git-sha1:[0-9a-f]{40}` or `git-sha256:[0-9a-f]{64}` |
| `ByteCount` | Unsigned decimal integer encoded as a JSON number with value between 0 and 9223372036854775807 |
| `UtcTimestamp` | RFC 3339 UTC time with `Z`, seconds present, and no leap-second spelling |
| `HttpsLocation` | `https` URI with no username, password, fragment, or mutable query parameter; credentials are forbidden |
| `GitLocation` | `git+https` URI with no username, password, or fragment; the immutable commit and content digest are required separately |
| `BundleLocation` | `bundle:/` followed by a normalized relative path containing no `..` segment or leading slash |
| `MediaType` | Lowercase IANA media type with no parameters that change interpretation; parameters are stored separately and canonically |

The future schema must reject control characters, invalid Unicode, duplicate object keys, unrecognized enum values, numeric strings where a number is required, and numbers where a string identifier is required. Canonical JSON uses UTF-8 without a BOM, RFC 8785 JSON Canonicalization Scheme, lowercase enum literals, and normalized object-key ordering. Arrays are ordered by the rules in Section 13; they are never sorted by an implementation-specific locale.

An imported envelope reference is an F-03 `EnvelopeRef`, not a locally defined object. A binding reference is a typed tuple of that envelope reference, the imported payload digest, the applicable component or candidate key, and the expected subject digest set; it never copies or shadows the imported payload. `origin_id` uses `OriginId`, `patch_queue_id` uses `PatchQueueId`, `patch_id` uses `PatchId`, and `text_id` uses `TextId`. Every `*_digest` field uses `Digest` unless an imported F-02, F-03, or F-04 type explicitly names another digest algorithm.

### 5.2 Envelope-level fields

The F-06 record family has these fields. The signature and trust fields are references to F-03, not a local envelope design.

| Field | Type | Presence and meaning |
| --- | --- | --- |
| `record_type` | Literal `f06.component_compliance.v1` | Required; selects this record family |
| `record_id` | `RecordId` | Required; immutable record identity |
| `component_id` | `ComponentId` | Required; joins the record to the canonical platform manifest component key |
| `component_class` | Closed enum from Section 4.2 | Required |
| `lifecycle` | Closed enum from Section 4.3 | Required |
| `acquisition_mode` | Closed enum from Section 4.3 | Required |
| `manifest_binding` | Binding reference | Required; includes the imported `platform_manifest/v1` envelope reference, manifest digest, component key, and expected artifact digest set |
| `origin` | Tagged `OriginDescriptor` | Required; identifies where the input came from and how the origin was evidenced |
| `immutable_reference` | Tagged `ImmutableReference` | Required for source, binary, package, image, installer, firmware, patch, and opaque artifacts; exact immutable identity is required even when no source is redistributable |
| `fork_lineage` | Tagged `ForkLineage` | Required for a fork or carried downstream input; `not_applicable` is allowed only for a non-fork origin variant |
| `patch_provenance` | Tagged `PatchProvenance` | Required for `downstream_patch_queue` and any component whose shipped result includes downstream changes; otherwise `not_applicable` |
| `recipe_binding` | `RecipeBinding` | Required for built or materialized output; references the F-04 recipe, builder, toolchain, input closure, and acquisition recipe digests |
| `artifact_identity` | `ArtifactIdentity` | Required when bytes exist; records artifact identity, media type, size, location role, and digest |
| `sbom_provenance` | `SbomProvenanceBinding` | Required for every shipped or acquired component and must resolve to complete F-04 evidence |
| `license_notice` | `LicenseNoticeBinding` | Required for every component, including an explicit `not_applicable` variant only when signed evidence establishes why no license or notice text applies |
| `redistribution` | `RedistributionDecision` | Required for every shipped or acquired component |
| `export_security` | `ExportSecurityDisposition` | Required; a `not_applicable` variant is still explicit and evidence-bound |
| `branding_trademark` | `BrandingTrademarkDisposition` | Required for every visible name, logo, font, artwork, package label, and installer surface; `not_applicable` is explicit for other inputs |
| `review` | `ReviewBinding` | Required; resolves the reviewing authority and human decision references through F-03 |
| `timestamps` | `RecordTimestamps` | Required; all times are UTC and immutable |
| `supersession` | `SupersessionBinding` | Required; identifies current, superseded, revoked, or corrected state without rewriting history |

No field named `owner`, `owner_name`, `license_ok`, `notice_ok`, `source_ok`, `redistributable`, `warning`, `exception`, `approved_by`, or equivalent handwritten alias is valid. Human authority is represented only by F-03-resolved role bindings and signed decision references.

### 5.3 Origin and immutable source identity

`OriginDescriptor` is a tagged union with exactly `upstream_project`, `omarchy_project`, `forked_project`, `vendor_artifact`, `device_authoritative_source`, and `human_produced_opaque`. Each variant carries `origin_id`, `display_name`, `authority_location`, `publisher_identity`, `retrieval_evidence_refs`, and `origin_metadata_digest`. `display_name` is informational and never an authority.

`ImmutableReference` is a tagged union with exactly these variants:

| Variant | Required fields |
| --- | --- |
| `vcs_source` | `vcs_kind`, `repository_location`, `immutable_commit`, `tree_digest`, `source_snapshot_digest`, and `ref_name_observed` |
| `release_archive` | `authority_location`, `release_identifier`, `archive_digest`, `archive_size_bytes`, and `retrieval_timestamp` |
| `package_coordinate` | `repository_id`, `package_name`, `package_version`, `package_architecture`, `package_digest`, and `index_digest` |
| `container_or_image` | `registry_location`, `image_reference_observed`, `manifest_digest`, `layer_digests`, and `configuration_digest` |
| `device_authoritative_blob` | `authority_location`, `device_fetch_protocol`, `device_selector_digest`, `expected_blob_digest`, and `expected_blob_size_bytes` |
| `opaque_declared_artifact` | `declaration_envelope_ref`, `declared_artifact_digest`, `declared_artifact_size_bytes`, and `interface_contract_digest` |

`ref_name_observed` is retained as historical observation only. It cannot satisfy immutability without the commit and source snapshot digest. A URL, tag, branch, package name, image tag, filename, or display label alone never satisfies this contract.

Source identity is separate from artifact identity. A source snapshot digest proves the bytes of the source snapshot; a built artifact digest proves the output bytes; a recipe digest proves the declared construction or acquisition procedure. One digest may not be substituted for another.

### 5.4 Fork lineage and patch provenance

`ForkLineage` has exactly two variants: `not_applicable` and `fork`. The `fork` variant requires `upstream_origin_id`, `upstream_repository_location`, `upstream_base_commit`, `upstream_base_tree_digest`, `fork_repository_location`, `fork_tip_commit`, `fork_tip_tree_digest`, `ordered_patch_queue_id`, `ordered_patch_queue_digest`, `upstream_disposition`, and `lineage_evidence_refs`.

`upstream_disposition` is a closed enum with exactly `carried_not_submitted`, `submitted_pending`, `accepted_upstream`, `rejected_upstream`, and `not_submitted_reason_recorded`. It describes the recorded disposition, not a claim that upstream accepted Omarchy's release. `not_submitted_reason_recorded` requires a signed reason evidence record and a named maintainer checkpoint.

`PatchProvenance` requires `patch_queue_id`, `patch_queue_digest`, `base_commit`, `result_commit`, `patches`, and `queue_evidence_refs`. Each `patches` entry requires `patch_id`, `patch_digest`, `ordinal`, `subject`, `author_identity_ref`, `authored_at`, `applied_at`, `base_tree_digest`, `result_tree_digest`, `origin_evidence_refs`, and `upstream_disposition`. Ordinals start at 1 and are contiguous. Patches are compared in ordinal order; a reordered or duplicated patch is a different queue and cannot reuse the previous decision.

For an Omarchy, Asahi-derived, U-Boot, Linux, or Mesa fork, missing base commit, missing ordered queue digest, absent author or origin evidence, or an unresolved upstream disposition rejects the component. A project may carry a patch while upstream work is pending, but F-06 cannot infer permission or source obligations from that status.

### 5.5 Build and acquisition recipe binding

`RecipeBinding` is a reference to the F-04 recipe contract and requires `recipe_kind`, `recipe_digest`, `builder_definition_digest`, `toolchain_digest`, `input_closure_digest`, `command_vector_digest`, `environment_lock_digest`, `network_policy_digest`, `acquisition_authority_digest`, and `recipe_evidence_refs`. `recipe_kind` is exactly `build`, `package_acquisition`, `device_fetch`, `container_materialization`, or `opaque_artifact_ingest`.

For a built artifact, F-04 must provide source closure, builder identity, toolchain identity, and reproducibility evidence. For an acquired artifact, the record must identify the exact authority, request selector, expected digest, retrieval procedure, and whether bytes may be redistributed. For an opaque artifact, the acquisition recipe is the ingest and verification contract only; it must not contain source inspection steps.

F-06 does not accept a shell transcript, mutable network URL, package-manager result, local filename, or human assertion as a recipe digest. The command vector and environment lock are F-04-owned evidence references, not free-form fields that F-06 interprets.

### 5.6 Artifact, SBOM, and provenance evidence

`ArtifactIdentity` requires `artifact_id`, `artifact_digest`, `artifact_size_bytes`, `media_type`, `content_role`, `candidate_paths`, `artifact_store_ref`, `source_component_ids`, and `artifact_evidence_refs`. `content_role` is exactly `runtime`, `installer`, `boot`, `firmware`, `package`, `package_index`, `image`, `font`, `theme`, `artwork`, `notice`, `source_offer`, or `debug_evidence`. A component can have multiple artifacts, but each artifact has exactly one byte digest and size.

`SbomProvenanceBinding` requires `sbom_digest`, `sbom_format`, `provenance_digest`, `provenance_format`, `subject_artifact_digests`, `dependency_closure_digest`, `completeness`, `generator_identity_ref`, and `evidence_refs`. `sbom_format` is exactly `spdx_json`, `cyclonedx_json`, or `f04_canonical`; `provenance_format` is exactly `in_toto_statement`, `slsa_provenance`, or `f04_canonical`. `completeness` is exactly `complete`, `incomplete`, `ambiguous`, or `unknown_unresolved`. Only `complete` can satisfy an RC or stable candidate, and the subject and dependency closure digests must match the inventory.

SBOM and provenance evidence is evidence of declared construction and dependency closure. It is not a license decision and cannot supply missing license, notice, source-offer, or redistribution facts.

### 5.7 License, texts, notices, attribution, and source obligations

`LicenseNoticeBinding` requires `license_resolution`, `license_expression`, `license_text_refs`, `required_notice_refs`, `attribution_refs`, `modification_notice_refs`, `corresponding_source`, `evidence_refs`, and `text_digest_set`.

`license_resolution` is exactly `resolved_spdx`, `resolved_non_spdx`, `ambiguous`, `missing`, `expired`, or `unknown_unresolved`. `license_expression` is a tagged union with exactly `spdx` and `declared_non_spdx` variants. `resolved_spdx` requires a parsed SPDX expression; `resolved_non_spdx` requires the declared expression, signed evidence, and a bounded human or counsel checkpoint. `NOASSERTION`, an empty expression, a prose sentence, a URL without a text digest, or a guessed SPDX identifier is not a resolved expression. `license_text_refs` are immutable references containing `text_id`, `text_digest`, `location`, `language`, `retrieved_at`, and `evidence_refs`.

Each required notice entry contains `notice_id`, `text_digest`, `location`, `required_by_evidence_refs`, `scope_component_ids`, `notice_kind`, and `modification_status`. `notice_kind` is exactly `copyright`, `license`, `third_party_notice`, `attribution`, `modification`, or `source_offer`. `modification_status` is exactly `not_modified`, `modified_notice_present`, `modified_notice_missing`, or `unknown_unresolved`.

`corresponding_source` is a tagged union with exactly `not_required`, `source_available`, `source_offer_required`, `source_offer_satisfied`, `source_missing`, and `unknown_unresolved`. The non-`not_required` variants require `source_snapshot_digest` or `offer_id`, `locations`, `availability_evidence_refs`, and `location_checked_at`. A source offer location must identify the exact source snapshot or offer record and the public location where it can be obtained. A source URL without an immutable source digest, an expired location check, or a missing offer text is not sufficient.

F-06 records the cited license and notice evidence and the resulting decision; it does not declare that a license permits a specific redistribution. Where the evidence is uncertain, contradictory, non-standard, expired, or incomplete, the result is unresolved and a named human checkpoint is required.

### 5.8 Redistribution, export/security, and branding dispositions

`RedistributionDecision` requires `redistribution_class`, `conditions`, `decision_id`, `decision_digest`, `decision_basis_evidence_refs`, `scope_digest`, `channel_scope`, `decided_at`, `expires_at`, and `authority_binding_ref`. `redistribution_class` is a closed enum with exactly `permitted_redistribution`, `per_device_direct_authoritative_fetch_only`, `prohibited`, and `unknown_unresolved`. A decision is current only when all of those fields are present and verified through F-03.

`conditions` is a canonical ordered set of machine-checkable conditions. It may be empty only for `permitted_redistribution` when the decision evidence says no additional condition applies. A condition that F-06 cannot evaluate is an unresolved decision, not a warning. `per_device_direct_authoritative_fetch_only` is allowed in a candidate only as a non-bundled acquisition requirement with a device-fetch contract and explicit channel disclosure. It is never permitted as embedded release bytes.

`ExportSecurityDisposition` is a tagged union with `not_applicable` and `applicable`. `applicable` requires `export_class` exactly `none_declared`, `cryptographic_functionality`, `security_sensitive_function`, or `restricted_by_evidence`, `security_flags` as an ordered set of `cryptography_present`, `boot_authority`, `credential_boundary`, `firmware_authority`, and `safety_sensitive`, `evidence_refs`, and `human_checkpoint_ref` when the evidence is restricted or uncertain. `not_applicable` requires evidence explaining why the component has none of those properties. These fields record evidence and routing, not an export-control conclusion.

`BrandingTrademarkDisposition` is a tagged union with `not_applicable` and `applicable`. `applicable` requires `use_kind` exactly `project_name`, `upstream_name`, `vendor_mark`, `logo`, `font_or_artwork`, or `installer_label`, `disposition` exactly `cleared_for_use`, `attribution_only`, `restricted_use`, or `unknown_unresolved`, `mark_evidence_refs`, `rendered_locations`, and `human_checkpoint_ref`. `unknown_unresolved` blocks any candidate carrying the marked surface. This record does not grant trademark permission; uncertain vendor or upstream use goes to `TrademarkBrandOwner` and, where legal interpretation is needed, `OpenSourceComplianceCounsel`.

### 5.9 Review authority, timestamps, and supersession

`ReviewBinding` requires `reviewer_role`, `authority_role_binding_ref`, `review_decision_ref`, `review_scope_digest`, `reviewed_at`, `review_expires_at`, and `review_evidence_refs`. The referenced role binding must be resolved by F-03 in a `Trusted<TrustContext>` whose scope includes F-06, the component, the requested channel, and the exact candidate digest. A display name, email address, Git author, or signed comment without a matching F-03 binding is not reviewer authority.

`RecordTimestamps` requires `observed_at`, `created_at`, `decided_at`, `expires_at`, and `source_location_checked_at` when a source, notice, or offer location is present. Times are checked against the trusted evaluation time, not the worker's local clock. A future decision time, expired evidence, or clock ambiguity is a rejection.

`SupersessionBinding` requires `state` exactly `current`, `superseded`, `revoked`, or `corrected`, `supersedes_record_ids`, `superseded_by_record_id`, `reason_code`, `event_digest`, and `event_at`. `current` has an empty `superseded_by_record_id`; every other state has a valid replacement or revocation event. Supersession chains are append-only and bounded. A correction never edits the old record, reuses its record ID, or silently preserves its candidate admission.

## 6. Closed statuses and fail-closed semantics

The following vocabularies are closed. Unknown, absent, malformed, ambiguous, expired, mismatched, or out-of-scope values are failures, not additional status values.

| Domain | Allowed values | Admission rule |
| --- | --- | --- |
| Policy result | `ADMIT`, `REJECT` | Only `ADMIT` can be consumed as an F-05 compliance gate |
| Redistribution | `permitted_redistribution`, `per_device_direct_authoritative_fetch_only`, `prohibited`, `unknown_unresolved` | `prohibited` and `unknown_unresolved` always reject; direct-fetch-only rejects if bundled and otherwise requires its acquisition contract |
| License resolution | `resolved_spdx`, `resolved_non_spdx`, `ambiguous`, `missing`, `expired`, `unknown_unresolved` | Only `resolved_spdx` or a separately signed, in-scope `resolved_non_spdx` decision can proceed; all other values reject |
| Notice status | `complete`, `missing`, `altered`, `expired`, `unknown_unresolved` | Only `complete` with digest equality can proceed |
| Corresponding source | `not_required`, `source_available`, `source_offer_required`, `source_offer_satisfied`, `source_missing`, `unknown_unresolved` | Required source or offer must be satisfied and location-checked; missing or unresolved rejects |
| SBOM/provenance | `complete`, `incomplete`, `ambiguous`, `unknown_unresolved` | Only `complete` with exact subject and closure digests can proceed |
| Decision freshness | `current`, `expired`, `superseded`, `revoked`, `replayed`, `not_found` | Only `current` with trusted time and scope can proceed |
| Branding | `not_applicable`, `cleared_for_use`, `attribution_only`, `restricted_use`, `unknown_unresolved` | Restricted use must be absent or separately satisfied; unresolved blocks the affected surface |
| Evaluation | `structurally_valid`, `structurally_invalid` | Structural invalidity prevents policy evaluation and produces `REJECT` with a structural code |

The words `warning`, `best effort`, `assumed`, `legacy`, `temporary`, and `manual exception` have no admission semantics. A future UI or report may explain a rejected or informational observation, but it must not label an unresolved condition successful.

The parser checks the reserved handwritten-alias set before the generic unknown-field rule. A field such as `warning`, `redistributable`, `license_ok`, or `approved_by` therefore emits `F06-SHADOW-FIELD-BYPASS` at its exact JSON Pointer; any other unrecognized field emits `F06-INPUT-UNKNOWN-FIELD`. Neither path can be consumed as evidence.

The minimum hard predicate for `ADMIT` is:

`valid_envelopes AND current_trusted_bindings AND complete_inventory AND exact_manifest_join AND exact_artifact_digests AND complete_sbom_provenance AND resolved_license_notice_source_evidence AND valid_redistribution_decisions AND valid_owner_checkpoints AND no_prohibited_or_unknown_component AND channel_requirements_satisfied`.

An empty component set, empty evidence set, absent policy result, partial parse, omitted optional-looking field, or unrecognized field cannot satisfy any term in that predicate.

## 7. Human and counsel decision checkpoints

Human or counsel input is accepted only as a bounded signed owner approval whose signature and authority are resolved by F-03 through `Trusted<TrustContext>` and `AuthorityRoleBinding`. F-06 stores a reference to the signed decision and validates its scope, expiry, nonce or sequence, supersession state, and decision digest. F-06 does not define or create `owners.v1`, an owner directory, or a local actor-to-role mapping.

The proposed role names below are named checkpoints, not authority records. F-03 must resolve the currently appointed human to the role binding before a decision can be used.

| Checkpoint role | Required decision boundary | Blocking effect when absent or uncertain |
| --- | --- | --- |
| `ProjectOwner` | Stable publication, release-channel authorization, support-facing disposition, and irreversible external impact | No RC or stable promotion |
| `ReleaseComplianceOwner` | Completeness review, policy-rule activation, correction acceptance, and compliance attestation | No F-06 `ADMIT` result |
| `OpenSourceComplianceCounsel` | Ambiguous license expression, source-offer interpretation, corresponding-source location, or uncertain redistribution | Affected component remains `unknown_unresolved` |
| `FirmwareRedistributionOwner` | Exact vendor, Apple, audio, wireless, GPU, media, and device firmware acquisition or redistribution class | No bundled firmware and no affected candidate admission until resolved |
| `TrademarkBrandOwner` | Omarchy, Asahi-derived, U-Boot, Linux, Mesa, Apple, vendor, logo, font, and artwork use disposition | Affected visible surface is withheld or candidate rejects |
| `OpaqueBootArtifactHumanOwner` | Human-signed identity, provenance declaration, interface attestation, behavior evidence, and redistribution decision for the opaque boot artifact | No boot artifact admission; no source inspection is attempted |
| `PublicSourceOfferCustodian` | Public corresponding-source and source-offer hosting, availability check, correction, and retention | Candidate rejects when a required offer cannot be verified |
| `IndependentComplianceReviewer` | Read-only review and hostile fixture result independent of the record author and candidate assembler | No final compliance attestation |
| `F05CandidateAssemblyOwner` | Consumption of the exact F-06 result and fail-closed candidate assembly | Candidate is not emitted or promoted |

An approval must bind `candidate_digest`, `platform_manifest_digest`, `inventory_digest`, `component_id` or the explicitly bounded component set, `artifact_digest_set`, `redistribution_class`, `source_offer_index_digest`, `notice_bundle_digest`, `target_channel`, `policy_lock_digest`, `trust_context_digest`, `issued_at`, `expires_at`, and a unique F-03 replay-protection value. Reusing a decision for a different digest, channel, component, policy lock, or evidence set is a scope mismatch or stale decision, never a convenience.

## 8. Deterministic policy-evaluation API

This is a future interface design, not an implementation. The evaluator is a pure function over canonical bytes and a trusted evaluation context. Network access, mutable repository state, local environment variables, wall-clock reads outside the supplied trusted time, and package-manager resolution are not evaluator inputs.

Proposed operation:

`F06.ReleaseCompliance.evaluate.v1(request: ComplianceEvaluationRequest, trust: Trusted<TrustContext>) -> ComplianceEvaluationResult`

`ComplianceEvaluationRequest` has exactly these top-level fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `api_version` | Literal `f06.policy-evaluation/v1` | Protocol version |
| `evaluation_id` | `RecordId` | One immutable evaluation attempt |
| `evaluation_time` | `UtcTimestamp` | Trusted time supplied by the caller and checked against F-03 metadata |
| `target_channel` | `edge`, `rc`, or `stable` | Channel-specific requirements |
| `platform_manifest_envelope_ref` | F-03 envelope reference | Exact imported `platform-manifest/v1` payload |
| `board_registry_envelope_ref` | F-03 envelope reference | Exact imported board binding |
| `candidate_binding` | Candidate digest binding | F-05 candidate identity, component-set digest, and assembled manifest digest |
| `inventory_envelope_ref` | F-03 envelope reference | Complete F-06 inventory record collection |
| `f04_evidence_envelope_refs` | Ordered digest references | Builder, artifact, SBOM, provenance, index, and reproducibility evidence |
| `owner_decision_envelope_refs` | Ordered digest references | Bounded human or counsel decisions; no raw actor fields |
| `policy_lock_digest` | `Digest` | Exact rule and vocabulary lock used for evaluation |
| `retention_policy_digest` | `Digest` | Exact approved retention and projection lock |
| `public_projection_policy_digest` | `Digest` | Exact approved public/private projection lock |
| `requested_result_expiry` | `UtcTimestamp` | Maximum requested result lifetime, bounded by trust and policy limits |

The evaluator returns exactly these top-level fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `result_type` | Literal `f06.policy-result.v1` | Result family |
| `result_id` | `RecordId` | Immutable result identity |
| `decision` | `ADMIT` or `REJECT` | Sole admission decision |
| `candidate_binding` | Echoed canonical digest binding | Proves which candidate was evaluated |
| `input_digests` | Ordered digest set | Manifest, board, inventory, F-04 evidence, policy, retention, projection, and decisions |
| `rejection_findings` | Ordered `RejectionFinding` set | Empty only when `decision=ADMIT`; every entry has stable code, JSON Pointer, component identity where applicable, and evidence refs |
| `notice_bundle_binding` | Bundle digest binding | Required for `ADMIT` and exact public bundle output |
| `source_offer_index_binding` | Index digest binding | Required when any source offer or corresponding-source obligation exists |
| `attestation_binding` | F-03 envelope reference | Signed result and authority binding |
| `evaluated_at` | `UtcTimestamp` | Trusted evaluation time |
| `expires_at` | `UtcTimestamp` | Result expiry, never later than the earliest required decision or evidence expiry |
| `result_digest` | `Digest` | Digest of the canonical result payload excluding signature and this field |

`RejectionFinding` has exactly `code`, `json_pointer`, `component_id`, `evidence_refs`, and `phase`. `phase` is exactly `parse`, `trust`, `binding`, `closure`, `identity`, `provenance`, `license_notice`, `decision`, `channel`, or `output`. There is no warning-finding member. Non-blocking observations belong in immutable audit evidence and cannot change `decision=REJECT` to `ADMIT`.

### 8.1 Ordered validation algorithm

The future evaluator performs these phases in order. Structural and trust failures may stop dependent phases; otherwise it collects all independently observable findings so the result has a complete deterministic fail census.

1. Parse the exact canonical request and imported envelopes. Reject duplicate keys, reserved handwritten aliases, unknown fields, unsupported major versions, malformed identifiers, non-canonical bytes, unrecognized enum values, missing required fields, and collection bounds violations. Reserved aliases use `F06-SHADOW-FIELD-BYPASS`; other unknown fields use `F06-INPUT-UNKNOWN-FIELD`.
2. Resolve F-03 trust for every envelope and `Trusted<TrustContext>`. Verify signature, key role, threshold, delegation, expiry, freeze, rollback, revocation, sequence or nonce, and role binding before reading a decision as authority.
3. Resolve the F-02 manifest and board registry bindings. Require exact declared versions, accepted evolution rules, matching manifest and board digests, and a candidate target supported by the manifest's own immutable data. Do not infer from names or architecture.
4. Join F-05 candidate components to the manifest component keys and the F-06 inventory keys. Require one and only one current compliance record per shipped or acquired component and no unreferenced record that can affect the candidate.
5. Resolve every artifact, source, package, index, image layer, installer resource, font/theme/artwork item, patch queue, and opaque artifact reference. Recompute content digests from the referenced bytes where bytes are available and compare them to every manifest, artifact-store, SBOM, and inventory digest.
6. Validate immutable source identity, fork lineage, patch order, recipe binding, builder and acquisition evidence, and F-04 source closure. Reject missing, altered, ambiguous, or transitive provenance.
7. Validate SBOM and provenance completeness, subject identity, dependency closure, source-to-artifact mapping, and reproducibility evidence required by the component class and target channel.
8. Validate license expressions, license texts, notices, attributions, modification notices, corresponding-source obligations, source-offer locations, and evidence freshness. No text is replaced by a URL, an SPDX guess, or a maintainer statement.
9. Resolve redistribution, export/security, and branding dispositions. Verify each current owner or counsel decision against its F-03 authority role binding, exact scope, expiry, supersession, and replay protection. Reject direct-fetch-only bytes that appear in a bundle, prohibited bytes, and unresolved status.
10. Generate the canonical NOTICE bundle and public source-offer index from the validated inventory and evidence. Recompute their digests and ensure the result references the exact generated bytes.
11. Apply channel rules. `edge` may be used for controlled engineering evaluation but still rejects prohibited, unknown, missing, mismatched, expired, and absent required evidence. `rc` requires all F-06 records and all F-05 candidate gates. `stable` additionally requires current owner publication authorization, current public projections, rollback retention, and no unresolved residual declared blocking by the coordinator.
12. Emit `ADMIT` only if the hard predicate holds. Otherwise emit `REJECT` with findings sorted by phase order, JSON Pointer UTF-8 bytes, component ID bytes, and rejection code bytes. The result is signed by the F-03-resolved authority after the digest is fixed.

The evaluator never repairs inputs, downloads missing evidence, reclassifies an item, truncates a collection, consults an untrusted fallback, or turns a failed check into a warning. Repair means a new immutable record and a new evaluation.

## 9. Stable rejection codes and JSON paths

The codes below are the proposed stable public vocabulary for F-06. Code spelling and path semantics require coordinator ruling before implementation. Paths are RFC 6901 JSON Pointers into the canonical request or the keyed inventory record. A component path uses the actual component key; it is not a wildcard and there is no alternate path alias.

| Code | Required path form | Meaning |
| --- | --- | --- |
| `F06-INPUT-VERSION-UNSUPPORTED` | `/api_version` or `/candidate_binding/manifest_version` | An imported or F-06 major version is not supported |
| `F06-INPUT-UNKNOWN-FIELD` | Exact unknown object member | Strict parsing found a field outside the locked contract |
| `F06-INPUT-NONCANONICAL` | `/` | Bytes do not match canonical encoding |
| `F06-INPUT-COLLECTION-BOUND` | Exact collection path | A collection exceeds its declared bound or is truncated |
| `F06-TRUST-ENVELOPE-INVALID` | Exact envelope reference path | Signature, canonical payload, or envelope metadata fails |
| `F06-TRUST-ROLE-UNRESOLVED` | `/owner_decision_envelope_refs/0` or exact decision path | F-03 cannot resolve the required authority role binding |
| `F06-TRUST-ROLE-SCOPE-MISMATCH` | Exact `/components/cmp-key/review` path | Authority does not cover component, candidate, channel, or action |
| `F06-TRUST-DECISION-UNSIGNED` | Exact owner decision path | Human or counsel decision lacks a valid F-03 signature |
| `F06-TRUST-DECISION-EXPIRED` | Exact owner decision path | Decision expiry precedes trusted evaluation time |
| `F06-TRUST-DECISION-REPLAYED` | Exact owner decision path | F-03 nonce or sequence was already consumed or replayed |
| `F06-TRUST-DECISION-STALE` | Exact owner decision path | Decision is superseded, revoked, or bound to stale evidence |
| `F06-BINDING-MANIFEST-MISMATCH` | `/candidate_binding` | Candidate and signed platform manifest do not match |
| `F06-BINDING-MANIFEST-INVENTORY-MISMATCH` | `/inventory_envelope_ref` or `/components/cmp-key/manifest_binding` | Inventory component or expected digest differs from the manifest |
| `F06-CLOSURE-COMPONENT-MISSING` | `/components/cmp-key` | A manifest, SBOM, installer, or acquisition reference has no component record |
| `F06-CLOSURE-UNREFERENCED-COMPONENT` | `/components/cmp-key` | A record affects the candidate but is absent from the signed candidate closure |
| `F06-CLOSURE-OPAQUE-DECLARATION-MISSING` | `/components/cmp-opaque-boot/immutable_reference` | Opaque artifact has no acceptable human declaration |
| `F06-IDENTITY-IMMUTABLE-REF-MISSING` | `/components/cmp-key/immutable_reference` | Source or artifact identity is not immutable |
| `F06-IDENTITY-DIGEST-MISMATCH` | Exact digest field | Recomputed or cross-record digest differs |
| `F06-PROVENANCE-FORK-GAP` | `/components/cmp-key/fork_lineage` | Fork base, tip, queue, or upstream disposition is incomplete |
| `F06-PROVENANCE-PATCH-GAP` | `/components/cmp-key/patch_provenance/patches/0` | Patch identity, order, authorship, or origin evidence is incomplete |
| `F06-PROVENANCE-RECIPE-MISSING` | `/components/cmp-key/recipe_binding` | Build or acquisition recipe binding is absent |
| `F06-PROVENANCE-SBOM-INCOMPLETE` | `/components/cmp-key/sbom_provenance` | SBOM or provenance is incomplete, ambiguous, or not subject-bound |
| `F06-LICENSE-MISSING` | `/components/cmp-key/license_notice/license_expression` | No license evidence or expression is present |
| `F06-LICENSE-AMBIGUOUS` | `/components/cmp-key/license_notice/license_expression` | Evidence supports more than one unresolved interpretation |
| `F06-LICENSE-TEXT-MISSING` | `/components/cmp-key/license_notice/license_text_refs` | Required license text is absent or has no immutable location |
| `F06-NOTICE-MISSING` | `/components/cmp-key/license_notice/required_notice_refs` | Required notice or attribution is absent |
| `F06-NOTICE-ALTERED` | Exact notice text digest | Notice bytes differ from cited evidence |
| `F06-NOTICE-EXPIRED` | `/components/cmp-key/license_notice/required_notice_refs/0` | Required notice evidence or its location check is outside the policy freshness bound |
| `F06-MODIFICATION-NOTICE-MISSING` | `/components/cmp-key/license_notice/modification_notice_refs` | A required modification notice is absent |
| `F06-SOURCE-OFFER-INCOMPLETE` | `/components/cmp-key/license_notice/corresponding_source` | Required source or offer lacks exact source digest, location, or availability evidence |
| `F06-SOURCE-OFFER-UNAVAILABLE` | Exact offer location path | Required public source location failed the locked availability check |
| `F06-REDISTRIBUTION-DIRECT-ONLY-BUNDLED` | `/components/cmp-key/acquisition_mode` | Direct-authoritative-fetch-only bytes were bundled |
| `F06-REDISTRIBUTION-PROHIBITED` | `/components/cmp-key/redistribution/redistribution_class` | Prohibited component is in the candidate closure |
| `F06-STATUS-UNKNOWN` | Exact unresolved status field | Unknown or unresolved status was submitted as an admission input |
| `F06-POLICY-RESULT-MISSING` | `/f06_policy_result` | F-05 has no current signed F-06 result |
| `F06-BRANDING-UNRESOLVED` | `/components/cmp-key/branding_trademark` | Visible branding or trademark disposition is unresolved |
| `F06-CHANNEL-REBUILD-FORBIDDEN` | `/candidate_binding/artifact_digests` | Promotion changed bytes or rebuilt rather than copying an approved digest |
| `F06-SHADOW-FIELD-BYPASS` | Exact shadow field path | An alias, warning field, handwritten status, or consumer-specific field bypasses canonical data |
| `F06-OPAQUE-METADATA-TRANSPLANT` | `/components/cmp-opaque-boot/immutable_reference` | Opaque metadata is bound to a different artifact, declaration, interface, or candidate |
| `F06-SUPERSESSION-CURRENT-INVALID` | `/components/cmp-key/supersession` | Current record is superseded, revoked, corrected, or missing its event chain |
| `F06-RETENTION-PROJECTION-INVALID` | `/retention_policy_digest` or projection path | Retention or public/private projection does not match the approved lock |

The exact JSON path in a finding always points to the first invalid canonical field for the phase. If multiple fields independently fail, findings retain the phase and stable sorting rules rather than relying on map iteration order.

## 10. Consolidated evidence and public compliance outputs

### 10.1 Deterministic NOTICE bundle

The future generator creates a content-addressed bundle from the admitted inventory and imported evidence. It is generated, never hand-edited. Its canonical entries are ordered by `component_id`, then `notice_kind`, then `text_digest`, then `location` bytes. The bundle contains exactly:

1. `NOTICE`, a deterministic human-readable aggregation of required copyright, license, third-party, attribution, and modification notices.
2. `LICENSES/index.json`, mapping each text digest to component IDs, evidence references, and bundle locations.
3. `ATTRIBUTION`, a deterministic attribution projection for components whose evidence requires attribution.
4. `SOURCE-OFFERS/index.json`, the public source-offer and corresponding-source index described below.
5. `COMPLIANCE-REPORT.json`, the approved public projection containing candidate and component digests, status, evidence links, and residual disclosure.
6. `BUNDLE-MANIFEST.json`, the ordered member list, member digests, generator version, policy lock digest, and bundle generation time.

The bundle generator must preserve cited text bytes exactly, including copyright notices and license punctuation. It may add headings and provenance references in generated sections but may not rewrite, merge, or summarize a cited legal text as if that summary were authoritative.

### 10.2 Public source-offer index

Each `OfferId` entry contains `offer_id`, `component_id`, `source_snapshot_digest`, `offer_kind` exactly `corresponding_source` or `source_offer`, `public_location`, `location_checked_at`, `availability_evidence_digest`, `retention_class`, and `correction_chain_head`. A required offer has one current entry with an immutable source snapshot digest and a reachable public location under the approved projection policy. A URL that redirects to a moving branch, requires credentials, lacks the source digest, or fails the availability check is not a satisfied offer.

The index is public evidence of where the source or offer can be obtained. It is not a legal conclusion that the obligation applies or has been discharged; that conclusion remains in the cited evidence and bounded human checkpoint. The public custodian must be able to correct a location by appending a new signed index record without mutating the old record.

### 10.3 Immutable evidence retention

The future implementation uses content-addressed immutable evidence records with append-only correction and revocation events. Proposed bounded retention classes, pending coordinator ruling, are:

| Retention class | Minimum retention | Maximum default |
| --- | --- | --- |
| `candidate_evidence` | Seven years after final channel withdrawal | Fifteen years after final channel withdrawal |
| `support_lifetime_evidence` | Board support lifetime plus seven years | Twenty years after final supported release withdrawal |
| `public_source_offer` | Through the signed source-offer obligation period and seven years after final distribution | Twenty years after final distribution unless a current obligation requires longer |
| `incident_and_revocation` | Ten years after incident closure | Twenty-five years after incident closure |
| `rollback_release` | Full board support lifetime plus seven years | Twenty years after final supported release withdrawal |

The longer signed owner or counsel retention requirement wins; no record is deleted while an obligation, incident, audit hold, correction chain, or rollback dependency remains open. A retention extension is a new signed decision and does not rewrite the old retention record. The exact values are a coordinator decision and are a blocking residual until approved.

### 10.4 Corrections and supersession

An altered license text, notice, source location, digest, decision, or artifact creates a new record with a new record ID and a `supersedes_record_ids` link. The old bytes, old digest, old result, and reason remain retained and addressable. A correction immediately invalidates any candidate result whose input digest set includes the corrected record; the next evaluation must reject until a new result is signed.

Revocation blocks new promotion and triggers a channel impact report. It does not silently delete or alter already-published evidence. A public projection includes the current state, correction-chain head, superseded digest, and concise reason code without exposing private identities or secrets. A private evidence record retains the signed decision, authority binding, evidence references, and operator audit data under restricted access.

### 10.5 Channel promotion

Promotion is a copy of already-approved immutable digests. The promotion operation receives the source channel, destination channel, candidate manifest digest, artifact digest set, F-06 result digest, NOTICE bundle digest, source-offer index digest, and F-03 promotion authorization. It copies those exact objects into the destination namespace and records a promotion event.

Promotion must not rebuild, repackage, re-sign as a different artifact, resolve a new source, refresh an index in place, change a redistribution class, or silently reclassify a direct-fetch-only, prohibited, or unknown component. Any byte, policy, evidence, channel scope, or public projection change creates a new candidate and runs the full evaluation again. `F06-CHANNEL-REBUILD-FORBIDDEN` is the result when promotion observes a changed digest.

## 11. Fork, upstream, vendor, and Apple-input policy

These are evidence and process requirements, not legal conclusions. Exact license, notice, source-offer, export, and trademark decisions are made at the named human checkpoints and are recorded with citations and immutable evidence.

| Input family | F-06 design treatment | Required human checkpoint |
| --- | --- | --- |
| Omarchy-owned source and downstream changes | Record the Omarchy origin, immutable source snapshot, fork lineage when applicable, ordered patch queue, authorship/origin evidence, build recipe, and upstream disposition. Internal ownership does not erase third-party obligations. | `ReleaseComplianceOwner` and `OpenSourceComplianceCounsel` for uncertain obligations |
| Asahi-derived installer pieces | Identify the exact upstream project and source snapshot, copied files or patches, license and notice texts, modification notices, corresponding-source obligations, and any Omarchy changes. Do not rely on a repository name or an upstream release label. | `OpenSourceComplianceCounsel`; `TrademarkBrandOwner` for visible Asahi marks |
| U-Boot | Treat the upstream commit, Omarchy fork tip, ordered patch queue, board configuration, generated image, and U-Boot license/notice evidence as separate linked records. A compatible boot result is not provenance. | U-Boot maintainer plus `ReleaseComplianceOwner`; counsel for uncertainty |
| Linux | Treat upstream kernel source, device trees, backports, generated configuration, patch queue, firmware interfaces, source offer, SBOM, and package artifacts as distinct records. Kernel build success is not compliance closure. | Kernel maintainer plus `OpenSourceComplianceCounsel` |
| Mesa | Record the authoritative freedesktop.org source snapshot, mirror evidence, Omarchy AGX patch queue, build configuration, conformance artifacts, and license/notice closure separately. A mirror relationship is evidence, not a license decision. | Mesa maintainer plus `ReleaseComplianceOwner` |
| Firmware and audio components | Separate open-source drivers and tooling from proprietary firmware, DSP images, calibration data, wireless data, and Apple or vendor blobs. Each blob gets its own immutable identity, acquisition mode, redistribution class, notice/source evidence, and safety/security flags. | `FirmwareRedistributionOwner`; `OpenSourceComplianceCounsel` when uncertain |
| Apple-provided inputs | Default to `per_device_direct_authoritative_fetch_only` unless an exact artifact-level signed decision establishes permitted redistribution. Fetch from the authoritative Apple endpoint per device, verify expected digest and selector, do not mirror or bundle by assumption, and do not treat Apple availability as permission. | `FirmwareRedistributionOwner`, `ProjectOwner`, and `OpenSourceComplianceCounsel` |
| Opaque human-produced boot artifact | Consume only the signed human declaration, artifact digest, schema, provenance, redistribution decision, interface attestation, and external behavior evidence. F-06 does not inspect the source or infer lineage beyond the declaration. | `OpaqueBootArtifactHumanOwner`, `ReleaseComplianceOwner`, and `IndependentComplianceReviewer` |

Open-source fork, carry, and upstream duties remain distinct from vendor-artifact acquisition. An upstream commit does not authorize a bundled vendor blob. A per-device fetch does not satisfy source or notice obligations for an open-source component. An opaque artifact declaration does not make a human-produced repository an agent-operable input.

## 12. Handoff contracts

### 12.1 F-03 trust roles

F-03 supplies the trusted envelope verifier and resolves `AuthorityRoleBinding` within `Trusted<TrustContext>`. F-06 requires, by reference, the trust-root bundle digest, key ID, role, delegation chain, threshold result, sequence or nonce, issued and expiry times, revocation and freeze state, and scope digest. F-06 returns its result in an F-03-signed envelope and never creates a parallel trust root, key directory, owner directory, signature policy, or replay ledger.

F-03 must reject an envelope before F-06 uses any payload field as evidence. An unsigned or expired owner decision is not downgraded to an observation. A valid signature from a role outside F-06 scope is still a role failure.

### 12.2 F-04 builder, SBOM, provenance, and artifact records

F-04 supplies exact recipe, builder, toolchain, source-closure, SBOM, provenance, artifact-store, package-index, reproducibility, and signature evidence. Each evidence item arrives as a signed digest reference bound to the platform manifest component key and subject artifact digest. F-06 checks presence, binding, completeness, and freshness; it does not regenerate or reinterpret F-04 evidence.

F-04 must expose a complete dependency closure for every shipped or acquired artifact, including image layers, package scripts, installer resources, generated fonts/themes/artwork, firmware payloads, and opaque boot artifacts as declared external subjects. Missing evidence is a hard F-06 input failure.

### 12.3 F-05 candidate assembly

F-05 passes the exact candidate manifest digest, component-set digest, board binding, target channel, artifact digest set, inventory envelope reference, and F-06 policy result reference to the candidate assembler. F-05 accepts only a current signed `ADMIT` result whose input digests exactly equal the candidate inputs. F-05 must reject absent results, stale results, result scope mismatches, unknown or prohibited statuses, direct-fetch-only bytes bundled into the candidate, and any candidate containing a field not represented by the canonical manifest or generated F-06 binding.

The F-05 output must include the F-06 result digest, NOTICE bundle digest, source-offer index digest, complete failure census, and immutable candidate manifest. F-05 cannot replace a missing compliance record with a handwritten exception field.

### 12.4 Installer prefetch and offline behavior

Before any APFS, boot, Recovery, LocalPolicy, or other privileged mutation, the installer must prefetch and verify every candidate item whose acquisition mode is `embedded_in_candidate` or `fetched_from_manifest_source`, including its compliance evidence and the exact opaque artifact envelope. The prefetch cache is content-addressed and user-cache-only before consent. A corrupt, absent, unsigned, expired, or digest-mismatched item blocks the mutation boundary.

For `fetched_per_device_from_authoritative_source`, the installer receives an exact device selector digest, endpoint authority, expected digest, size, and F-06 decision reference. It fetches on the device through the owner-authorized path, verifies before use, records the result, and does not substitute a mirror or bundled copy. An offline bundle may claim completeness only if it contains every required byte and evidence item; a direct-fetch-only requirement makes the offline claim false and blocks an offline-only mode.

The installer must not use a compliance report as mutation authority. It consumes the signed platform manifest and installer-plan contracts, verifies the F-06 result, and maintains its own transaction and device-identity guards.

### 12.5 Release channels and rollback

`edge`, `rc`, and `stable` are distinct immutable namespaces. F-06 results are channel-bound. An edge result cannot be copied to RC without a new channel-scoped promotion authorization and verification that the exact input digests still satisfy RC rules. Promotion copies bytes and evidence; it never rebuilds.

Every rollback target retains its F-06 result, inventory, SBOM/provenance evidence, NOTICE bundle, source-offer index, owner decisions, and correction chain for the full board support lifetime plus the approved retention period. A revoked or superseded rollback target remains identifiable and cannot be silently selected as current.

### 12.6 Public support and evidence ledger

F-06 supplies the public projection digest, candidate and component digests, redistribution class, source and notice locations, correction-chain head, expiry, and residual disclosure to the support ledger. The ledger must not convert `ADMIT` into a statement of legal clearance, physical qualification, or all-board compatibility. It must link to F-05 and qualification evidence and show when a component is direct-fetch-only or a public source offer is required.

## 13. Bounded collections, uniqueness, ordering, and evolution

### 13.1 Proposed bounds

The future record family rejects oversized input instead of truncating it. Proposed bounds, pending coordinator ruling, are:

| Collection | Maximum count per candidate or record |
| --- | ---: |
| Candidate components | 4096 |
| Artifacts per component | 128 |
| Source references per component | 64 |
| Patch entries per queue | 8192 |
| Evidence references per component | 256 |
| License text references per component | 32 |
| Required notice references per component | 128 |
| Source offers per component | 32 |
| Conditions per redistribution decision | 64 |
| Owner decision references per evaluation | 64 |
| Supersession links per record | 64 |
| Rejection findings per result | 4096 |
| Public projection residuals per candidate | 256 |

The bytes of an individual text, evidence record, source-offer index, public projection, or bundle member are also bounded by the approved `f06-conformance.lock.json` and must be rejected when the lock is exceeded. A future implementation must not use a larger local bound than the signed policy lock.

### 13.2 Semantic uniqueness

`component_id`, `record_id`, `artifact_id`, `evidence_id`, `decision_id`, `bundle_id`, and `offer_id` are unique within their signed collection. One `artifact_digest` may be referenced by multiple paths but must resolve to one immutable byte object. One `source_snapshot_digest` may support multiple artifacts only when every binding is explicit. A component may have one current compliance record for a candidate; superseded records are retained outside the current join.

The following tuples must be unique: `(component_id, artifact_digest, content_role)`, `(component_id, notice_kind, text_digest, location)`, `(component_id, source_snapshot_digest, offer_kind)`, `(patch_queue_id, ordinal)`, `(decision_id, scope_digest)`, and `(record_id, event_digest)`. Duplicates reject even when the duplicated payloads are byte-identical.

### 13.3 Canonical ordering

Object keys are ordered by RFC 8785. Component collections sort by `component_id`; artifacts by `artifact_id`; source and evidence references by digest then location; notices by `notice_kind`, `text_digest`, then location; patches by ordinal; decisions by `decision_id`; supersession links by event time then event digest; and rejection findings by phase order, JSON Pointer bytes, component ID bytes, then code bytes. The resulting canonical bytes are the only bytes that may be signed or hashed.

### 13.4 Projections and access control

The public projection contains candidate, component, source, artifact, notice, license-text, source-offer, redistribution-class, correction, expiry, and evidence-link fields needed for reproducibility and support. It omits personal names, private authority metadata, operator accounts, hostnames, serials, raw device identifiers, private endpoints, tokens, credentials, signing material, unreleased incident details, and raw logs.

The restricted evidence projection contains full signed decision references, authority bindings, source and build evidence, audit events, incident material, and redaction proofs. The secret store contains only private keys and credentials and is never represented in a compliance record or public bundle. Access is role-based: public read for published projections; authenticated read for candidate evidence; release-compliance and independent-review read for restricted evidence; F-03 key custodians only for signing material. Writers cannot approve their own record, and candidate assemblers cannot alter evidence.

### 13.5 Identifier and secret rules

Identifiers are opaque, non-secret, and must not contain serial numbers, MAC addresses, filesystem UUIDs, usernames, hostnames, home paths, access tokens, passwords, private URLs, or customer data. Source and artifact identifiers use digests and project-scoped component keys. Secrets never enter canonical bytes, logs, notices, source-offer indexes, public projections, or approval payloads. A secret scan failure is a hard CI failure even when the secret appears only in evidence.

### 13.6 Evolution and negotiation

F-06 accepts only `release-compliance/v1` and `f06.policy-evaluation/v1` major versions approved by the signed policy lock. A minor version may add fields only when the lock declares them optional, the canonical parser rejects unknown required fields, and the producer and consumer negotiate the same minor capability set. No consumer may silently ignore a field that can affect admission. A higher major version, unknown enum, removed required field, or unsupported minor capability rejects with `F06-INPUT-VERSION-UNSUPPORTED`.

Imported F-02, F-03, F-04, and F-05 major versions must match the version ranges recorded in the policy lock. Generated bindings and conformance vectors are regenerated from those canonical locks. Version negotiation is recorded in the result input digest set so a result cannot be transplanted across a rule or binding evolution.

## 14. Conformance and hostile-fixture matrix

The future fixture set is deterministic, committed under the F-06 implementation tree, and executed against the exact lock named in Section 15. Each fixture contains a valid baseline candidate plus one controlled mutation. The expected result is `REJECT`, with the exact code and JSON Pointer below. Fixture names are stable identifiers, not prose descriptions.

| Fixture name | Mutation | Expected code | Expected JSON Pointer |
| --- | --- | --- | --- |
| `license-missing-cmp-asahi-installer` | Remove the license expression and all license-text evidence for the Asahi-derived installer component | `F06-LICENSE-MISSING` | `/components/cmp-asahi-installer/license_notice/license_expression` |
| `license-ambiguous-cmp-linux` | Add contradictory unresolved license evidence for the Linux component | `F06-LICENSE-AMBIGUOUS` | `/components/cmp-linux/license_notice/license_expression` |
| `notice-absent-cmp-omarchy` | Remove a required third-party notice from the Omarchy component | `F06-NOTICE-MISSING` | `/components/cmp-omarchy/license_notice/required_notice_refs` |
| `notice-altered-cmp-mesa` | Change the notice bytes without changing the recorded digest | `F06-NOTICE-ALTERED` | `/components/cmp-mesa/license_notice/required_notice_refs/0/text_digest` |
| `source-offer-incomplete-cmp-linux` | Keep the offer name but remove its immutable source digest and availability evidence | `F06-SOURCE-OFFER-INCOMPLETE` | `/components/cmp-linux/license_notice/corresponding_source` |
| `source-offer-unavailable-cmp-uboot` | Point a required source offer at a credentialed or moving location | `F06-SOURCE-OFFER-UNAVAILABLE` | `/components/cmp-uboot/license_notice/corresponding_source/locations/0` |
| `wrong-artifact-digest-cmp-mesa` | Alter Mesa bytes while retaining the manifest and inventory digest | `F06-IDENTITY-DIGEST-MISMATCH` | `/components/cmp-mesa/artifact_identity/artifact_digest` |
| `fork-provenance-gap-cmp-linux` | Remove the downstream patch queue digest and upstream base commit | `F06-PROVENANCE-FORK-GAP` | `/components/cmp-linux/fork_lineage` |
| `patch-provenance-gap-cmp-uboot` | Skip patch ordinal 2 and remove author evidence for ordinal 3 | `F06-PROVENANCE-PATCH-GAP` | `/components/cmp-uboot/patch_provenance/patches/1` |
| `owner-decision-unsigned-cmp-firmware` | Remove the F-03 signature envelope from a firmware redistribution decision | `F06-TRUST-DECISION-UNSIGNED` | `/components/cmp-apple-firmware/review/review_decision_ref` |
| `owner-decision-expired-cmp-firmware` | Set the firmware decision expiry before trusted evaluation time | `F06-TRUST-DECISION-EXPIRED` | `/components/cmp-apple-firmware/review/review_decision_ref` |
| `owner-decision-replayed-cmp-firmware` | Reuse an already-consumed F-03 nonce for a new candidate | `F06-TRUST-DECISION-REPLAYED` | `/components/cmp-apple-firmware/review/review_decision_ref` |
| `role-scope-mismatch-cmp-artwork` | Use a source-only role binding for a trademark clearance decision | `F06-TRUST-ROLE-SCOPE-MISMATCH` | `/components/cmp-artwork/branding_trademark` |
| `direct-fetch-only-artifact-bundled-cmp-apple-firmware` | Add a direct-authoritative-fetch-only Apple firmware blob to the offline bundle | `F06-REDISTRIBUTION-DIRECT-ONLY-BUNDLED` | `/components/cmp-apple-firmware/acquisition_mode` |
| `prohibited-artifact-admitted-cmp-vendor-blob` | Change the vendor blob class to prohibited while retaining candidate membership | `F06-REDISTRIBUTION-PROHIBITED` | `/components/cmp-vendor-blob/redistribution/redistribution_class` |
| `unknown-status-laundered-to-warning-cmp-audio` | Add a warning field beside an unknown redistribution status and request ADMIT | `F06-SHADOW-FIELD-BYPASS` | `/components/cmp-audio/warning` |
| `stale-decision-transplant-cmp-linux` | Copy a valid Linux decision from an older candidate digest into the current candidate | `F06-TRUST-DECISION-STALE` | `/components/cmp-linux/review/review_decision_ref` |
| `incomplete-sbom-cmp-installer` | Remove one transitive installer dependency from the SBOM closure | `F06-PROVENANCE-SBOM-INCOMPLETE` | `/components/cmp-installer/sbom_provenance` |
| `manifest-inventory-mismatch-cmp-kernel` | Change the manifest artifact digest without changing the inventory record | `F06-BINDING-MANIFEST-INVENTORY-MISMATCH` | `/components/cmp-kernel/manifest_binding` |
| `shadow-field-bypass-cmp-mesa` | Add `redistributable=true` while the canonical decision is unresolved | `F06-SHADOW-FIELD-BYPASS` | `/components/cmp-mesa/redistributable` |
| `opaque-artifact-metadata-transplant-cmp-m1n1-boot` | Reuse an opaque declaration for a different artifact digest and interface contract | `F06-OPAQUE-METADATA-TRANSPLANT` | `/components/cmp-m1n1-boot/immutable_reference` |
| `opaque-artifact-source-inspection-cmp-m1n1-boot` | Add a source-inspection assertion or source path to the opaque declaration | `F06-INPUT-UNKNOWN-FIELD` | `/components/cmp-m1n1-boot/immutable_reference/source_path` |
| `missing-policy-result-candidate` | Omit the signed F-06 result from the F-05 candidate binding | `F06-POLICY-RESULT-MISSING` | `/f06_policy_result` |
| `expired-notice-cmp-font` | Retain a notice location check older than the policy freshness bound | `F06-NOTICE-EXPIRED` | `/components/cmp-font/license_notice/required_notice_refs/0` |
| `replayed-superseded-record-cmp-theme` | Select a superseded current record without its replacement | `F06-SUPERSESSION-CURRENT-INVALID` | `/components/cmp-theme/supersession` |

Positive fixtures must include at least `valid-open-source-fork`, `valid-permitted-package`, `valid-device-fetch-only-firmware`, `valid-opaque-human-artifact`, `valid-source-offer`, and `valid-correction-chain`. The device-fetch-only positive fixture must prove that no bytes for that component appear in the candidate or offline bundle. The opaque positive fixture must use only an external declaration and behavior evidence; it must not contain or reference source content.

The conformance suite must also mutate every bounded collection, every identifier grammar rule, every version negotiation branch, every projection redaction rule, every supersession state, and every F-03 trust condition. A fixture is not passing merely because a command exits non-zero; the harness must match `decision`, exact code set, exact path set, and canonical result digest.

## 15. Future implementation deliverables and CI gates

This section is the exact future delivery contract. None of the named files, commands, schemas, or tools is created by this design-only slice.

### 15.1 Required implementation deliverables

1. A coordinator-approved `release-compliance/v1` canonical record package and lock verifier generated from the locked F-02/F-03/F-04 bindings, with strict parsing, canonicalization, identifier validation, version negotiation, and collection bounds.
2. A deterministic F-06 evaluator implementing `F06.ReleaseCompliance.evaluate.v1`, with the rejection vocabulary in Section 9 and no warning-success path.
3. A signed decision resolver that calls F-03 `Trusted<TrustContext>` and `AuthorityRoleBinding` APIs and has no `owners.v1` or local owner map.
4. F-04 adapters for builder, acquisition, SBOM, provenance, artifact-store, package-index, source-closure, and reproducibility records.
5. A complete inventory closure builder covering all Section 4 classes, including generated resources, device-fetch-only inputs, and the opaque artifact declaration boundary.
6. A deterministic NOTICE and attribution bundle generator plus public source-offer index generator.
7. An append-only evidence store, correction and supersession event model, retention enforcement, public/private projections, redaction checks, and access-control audit.
8. An F-05 candidate-assembly adapter and consumer guard that requires a current F-06 `ADMIT` result bound to exact candidate digests.
9. Installer prefetch and offline-bundle validators that enforce the direct-authoritative-fetch-only rule before the destructive boundary.
10. Hostile and positive fixtures named in Section 14, with exact expected code and pointer assertions.
11. A generated report schema and report renderer containing result digest, fail census, input digests, bundle digests, source-offer digest, authority binding, timestamps, expiry, and residuals.
12. A clean-checkout CI workflow with separated author, evaluator, candidate assembler, and independent reviewer identities. The workflow must preserve raw evidence and publish only signed projections.

### 15.2 Named locks and exact verification command arrays

The future implementation must commit these named locks before it can claim a passing gate: `locks/f06-records.lock.json`, `locks/f06-policy.lock.json`, `locks/f06-conformance.lock.json`, `locks/f06-retention.lock.json`, `locks/f06-projections.lock.json`, and the imported F-02/F-03/F-04/F-05 lock digests recorded in `locks/f06-imports.lock.json`.

The proposed clean-checkout verification command arrays are:

```text
[
  "test -z \"$(git status --porcelain=v1)\"",
  "git diff --check --exit-code",
  "python3 -m f06_locks.verify --records locks/f06-records.lock.json --policy locks/f06-policy.lock.json --conformance locks/f06-conformance.lock.json --retention locks/f06-retention.lock.json --projections locks/f06-projections.lock.json --imports locks/f06-imports.lock.json",
  "python3 -m f06_records.validate --lock locks/f06-records.lock.json --imports locks/f06-imports.lock.json",
  "python3 -m f06_policy.validate --lock locks/f06-policy.lock.json --imports locks/f06-imports.lock.json",
  "python3 -m f06_policy.conformance --lock locks/f06-conformance.lock.json --fixtures fixtures/f06/",
  "python3 -m f06_bundles.verify --lock locks/f06-projections.lock.json --retention-lock locks/f06-retention.lock.json",
  "python3 -m f06_candidate.verify --imports locks/f06-imports.lock.json --policy-lock locks/f06-policy.lock.json",
  "if rg -n --hidden --glob '!\.git/**' '^(<<<<<<<|=======|>>>>>>>)' .; then exit 1; fi",
  "if rg -n --hidden --glob '!\.git/**' '\t' .; then exit 1; fi",
  "git ls-files -z | xargs -0 -n1 shasum -a 256"
]
```

The command array is a design contract, not a claim that these future modules exist. The lock files define the exact imported versions, fixture set, bounds, projection rules, and retention values. The lock verifier runs before any validator and fails if a named lock or imported digest is absent or altered. A command that is unavailable, skipped, replaced by a local fallback, or run against a dirty checkout is a tooling failure, not a pass.

The future CI gates are:

| Gate | Required evidence | Failure result |
| --- | --- | --- |
| G-F06-01 schema and canonical bytes | Lock digest, parser report, canonicalization vectors, generated binding digest | Blocks all later gates |
| G-F06-02 trust and authority | F-03 verification report, threshold/expiry/replay fixtures, role-scope report | Blocks policy evaluation |
| G-F06-03 inventory closure | Candidate-to-manifest-to-SBOM-to-artifact closure report | Blocks candidate assembly |
| G-F06-04 provenance and SBOM | F-04 evidence report, digest recomputation, source/fork/patch closure | Blocks candidate assembly |
| G-F06-05 license and notice | License parser report, cited text digest report, notice/modification/source-offer report | Blocks candidate assembly |
| G-F06-06 redistribution and human decisions | Decision-scope, freshness, direct-fetch, prohibited, branding, and export/security report | Blocks candidate assembly |
| G-F06-07 bundle and public projection | NOTICE, attribution, source-offer, private evidence, redaction, and digest report | Blocks publication |
| G-F06-08 hostile conformance | Fixture result matrix with exact codes and paths | Any unexpected pass or code blocks |
| G-F06-09 F-05 integration | Candidate result binding, no-shadow-field scan, promotion copy proof | Blocks RC and stable |
| G-F06-10 clean-checkout and reviewer separation | Clean status, exact command-array output, independent reviewer evidence, artifact retention receipt | No release-compliance attestation |

### 15.3 Required report and retained artifacts

Every future run emits a signed machine report with `report_type`, `report_version`, `run_id`, `commit_sha`, `clean_checkout`, `lock_digests`, `input_digests`, `command_vector_digest`, `decision`, `rejection_findings`, `pass_count`, `fail_count`, `skipped_count`, `tooling_limitations`, `artifact_refs`, `reviewer_binding_ref`, `started_at`, `finished_at`, `expires_at`, and `result_digest`. `skipped_count` is never folded into `pass_count`.

Required retained artifacts are the canonical input envelopes, lock files, inventory, F-04 evidence references, F-03 decision envelopes, evaluator report, fail census, NOTICE bundle, attribution bundle, source-offer index, public/private projections, fixture outputs, command output, redaction proof, promotion-copy proof, reviewer report, and correction-chain events. Retention follows the signed retention lock and the limits in Section 10.3.

The author of a component record cannot be the sole evaluator, the F-05 assembler cannot be the independent compliance reviewer, and the reviewer cannot mutate the candidate or evidence after review. A reviewer may report `REJECT` or `PASS` for the tested gate, but only the coordinator can rule on the design slice and only the program process can mark a slice DONE.

### 15.4 Explicit F-06 fail census

At design time, the F-06 census is:

| Failure class | Current state in this slice | Blocking effect |
| --- | --- | --- |
| Canonical F-06 records and validators | NOT IMPLEMENTED | No F-06 gate exists |
| F-03 trust resolver integration | NOT IMPLEMENTED | No human decision is authoritative to F-06 |
| F-04 inventory/SBOM/provenance adapters | NOT IMPLEMENTED | Evidence closure cannot be computed |
| F-05 candidate guard | NOT IMPLEMENTED | Candidate assembly cannot consume F-06 safely |
| License, notice, attribution, and source-offer generator | NOT IMPLEMENTED | No compliance bundle exists |
| Redistribution, firmware, Apple-input, and branding decisions | NOT IMPLEMENTED | No component is cleared for redistribution |
| Opaque artifact declaration verifier | NOT IMPLEMENTED | No opaque boot artifact can enter a candidate |
| Correction, supersession, retention, and projections | NOT IMPLEMENTED | No immutable public/private evidence lifecycle exists |
| Positive and hostile conformance fixtures | NOT IMPLEMENTED | No fail-closed behavior is demonstrated |
| Clean-checkout CI and independent review | NOT IMPLEMENTED | No release attestation exists |
| Legal or trademark clearance | NOT CLAIMED | Human/counsel checkpoints remain required |
| Hardware compatibility or qualification | NOT CLAIMED | F-06 cannot establish board support |
| F-06 slice completion | NOT DONE | Coordinator ruling and later implementation remain required |

This census is the truthful result of a design note. It is not a release report and cannot be used to promote an artifact.

## 16. Residuals and coordinator ruling requests

Each residual has an owner checkpoint and a blocking effect. None is silently deferred.

| Residual | Owner checkpoint | Blocking effect |
| --- | --- | --- |
| Approve the F-06 record family name, exact field contract, bounds, enum values, and JSON Pointer vocabulary | `ProjectOwner` and `ReleaseComplianceOwner` | No canonical record implementation or generated binding |
| Resolve imported F-02/F-03/F-04/F-05 version ranges and canonical field names without competing authorities | F-02, F-03, F-04, and F-05 owners with `ReleaseComplianceOwner` | No evaluator can safely parse or join inputs |
| Approve the F-03 API surface for `Trusted<TrustContext>`, `AuthorityRoleBinding`, replay protection, and result signing | F-03 owner and `ProjectOwner` | No human or counsel decision can authorize a candidate |
| Appoint the human identities bound to the named checkpoints | `ProjectOwner` | Every uncertain legal, vendor, branding, and opaque-artifact decision blocks |
| Decide exact license and source-offer interpretation for each acquired component | `OpenSourceComplianceCounsel` | Affected component remains `unknown_unresolved` |
| Decide redistribution class for every Apple, vendor, audio, wireless, GPU, media, and other firmware input | `FirmwareRedistributionOwner` with counsel | Affected bytes cannot be bundled or admitted |
| Decide Omarchy, Asahi, U-Boot, Linux, Mesa, Apple, vendor, logo, font, and artwork trademark dispositions | `TrademarkBrandOwner` | Affected visible surface cannot be published |
| Obtain the opaque human artifact declaration, signed digest binding, interface attestation, and external behavior evidence | `OpaqueBootArtifactHumanOwner` | No opaque boot artifact can enter any candidate; no source inspection is permitted |
| Approve public source-offer hosts, availability procedure, correction path, and retention | `PublicSourceOfferCustodian` and counsel | Required offer obligations cannot be marked satisfied |
| Approve retention durations and legal-hold extension process | `ProjectOwner` and counsel | Evidence lifecycle lock cannot be finalized |
| Approve public/private projection fields and redaction policy | `ReleaseComplianceOwner` and `ProjectOwner` | No public compliance bundle or support-ledger update |
| Implement and independently review the hostile fixtures and exact rejection census | `IndependentComplianceReviewer` | No F-06 attestation or F-05 admission |
| Prove installer behavior for prefetch, device-authoritative fetch, and offline completeness | Installer owner and `F05CandidateAssemblyOwner` | No clean-installer RC or stable promotion |
| Define coordinator treatment of an F-06 `ADMIT` when physical qualification, trust, or rollback evidence is stale | Coordinator | F-06 cannot override other release gates |

The coordinator must rule on these residuals before implementation begins. This note deliberately does not resolve legal, trademark, vendor redistribution, m1n1 source, physical qualification, or release-authority questions.

## 17. Coordinator handoff

Requested ruling: accept, reject, or amend this design-only F-06 contract. If accepted, implementation may begin only after F-02/F-03/F-04/F-05 imported locks and the residual owner bindings are available. The next implementation slice must preserve the opaque m1n1 boundary, add the named artifacts and hostile fixtures, and report actual command output with an explicit fail census.

This document does not claim implementation, legal clearance, redistribution permission, compatibility, qualification, release readiness, or DONE.
