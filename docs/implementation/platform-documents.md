# F-02 platform documents implementation ruling

Status: implementation increment only. This note records the coordinator ruling before production edits; it is not a support, qualification, release, trust, or DONE claim.

The implementation materializes the eight authenticated payloads as closed Draft 2020-12 schemas, immutable untrusted Python value objects, and a pure unsigned structural-conformance seam. The common envelope remains the transport boundary and F-03 retains signatures, key authority, expiry policy, replay protection, trust decisions, and external byte verification. `conformance validate` therefore reports `structural_only: true, release_eligible: false, trusted: false` after all named inputs are present exactly once and all cross-document bindings pass.

The boundary is deliberately composite: Draft 2020-12 schemas are the raw shape authority (including recursive closure, bounds, enums, and whole-value array uniqueness), while Python is the mandatory semantic authority for semantic-key uniqueness/order, canonical digest recomputation, and cross-document admission. A plain Draft validator is not an admission API because JSON Schema cannot express general lexicographic ordering or uniqueness by one object member. Neither layer verifies artifact or evidence bytes; those remain untrusted until a later byte-verification input is supplied.

The provisional design vocabulary is used as shape input, with these conservative rulings where implementation scope and the design note could conflict:

- Exact eight payload types and the existing common envelope are retained. No supporting verification record becomes a ninth authenticated payload.
- Cross-document identity is represented by canonical digest strings and exact IDs. A digest is recomputed from the parsed payload; it is never accepted as a trust proof or signature.
- Manifest projections are authoritative only when they exactly equal the component/artifact projection in the same document. The implementation uses a compact closed component/artifact record sufficient to exercise this invariant; unsupported release and provenance claims remain absent.
- Qualification admission requires exactly one manifest target and exactly one binding in this bundle version, with the qualification record naming that same board and manifest, outcome `pass`, every declared required check passing, and non-empty physical evidence. Multi-board release qualification requires a later bundle version capable of carrying one record per target. No fixture or validator claims that evidence is real hardware evidence.
- Installer plans contain a single selection, a closed artifact set, and declarative mutations. Plan validation is read-only and does not authorize execution.
- Boot health and success-marker fields are acyclic: the marker binds the boot core digest, while the core never embeds the marker digest. DTB envelopes bind source, pre-mutation, and post-mutation identities without performing a mutation.
- Unknown fields, duplicate semantic IDs, unsorted collections, incomplete evidence, failed required checks, and any mismatch return one deterministic structured error and no admission result.
- RFC 8785 safe-integer bounds from the foundation remain in force. Signatures and trust are explicitly F-03 residuals.

Nothing in this increment establishes Apple Silicon compatibility, physical qualification, installer execution, boot success, release readiness, or support.
