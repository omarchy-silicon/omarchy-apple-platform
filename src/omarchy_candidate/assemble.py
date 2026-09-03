"""Pure, read-only F-05 candidate assembly."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone

from .errors import CandidateAssemblyError
from omarchy_platform.canonical import canonical_bytes
from omarchy_build import PackageIndex, BuildProvenanceError

from .models import ArtifactReader, CandidateAssemblyInput, CandidateAuthority, CandidateManifest, _AuthorityCapability, _MANIFEST_TOKEN, digest_bytes, digest_value, _freeze


def assemble_candidate(
    value: Mapping[str, object],
    *,
    authority: CandidateAuthority | None = None,
    artifacts: ArtifactReader | None = None,
    verification_time: str | None = None,
) -> CandidateManifest:
    """Revalidate every authority and artifact before producing immutable bytes.

    F-05 intentionally has no local trust table and no boolean trust bypass.
    Production callers must inject F-03/F-06/Q-00/Q-01 adapters and a CAS
    reader. The only positive fixture path is an explicitly synthetic adapter.
    """

    assembly = CandidateAssemblyInput.from_dict(value)
    if authority is None:
        raise CandidateAssemblyError("AUTHORITY_REQUIRED", "$.authority", "F-03/F-06/Q-00/Q-01 authority adapters are required")
    if artifacts is None:
        raise CandidateAssemblyError("ARTIFACT_READER_REQUIRED", "$.artifacts", "content-addressed artifact reader is required")
    metadata_verifier = getattr(artifacts, "verify", None)
    if not callable(metadata_verifier):
        raise CandidateAssemblyError("CAS_VERIFIER_REQUIRED", "$.artifacts", "CAS verifier must rehash artifact metadata")
    if verification_time is None:
        raise CandidateAssemblyError("VERIFICATION_TIME_REQUIRED", "$.verification_time", "explicit UTC verification time is required")
    try:
        checked_time = datetime.fromisoformat(verification_time.removesuffix("Z") + "+00:00")
        if not verification_time.endswith("Z") or checked_time.tzinfo is None:
            raise ValueError
    except ValueError as error:
        raise CandidateAssemblyError("INVALID_VERIFICATION_TIME", "$.verification_time", "UTC verification timestamp required") from error

    checks = (
        ("platform", assembly.platform, assembly.platform["manifest_digest"], assembly.platform["manifest_id"]),
        ("intake", assembly.intake, assembly.intake["dataset_digest"], assembly.intake["record_id"]),
        ("qualification", assembly.qualification, assembly.qualification["record_digest"], assembly.qualification["record_id"]),
        ("package", assembly.package, assembly.package["index_digest"], assembly.package["release_id"]),
        ("compliance", assembly.compliance, assembly.compliance["attestation_digest"], "compliance:" + assembly.compliance["attestation_digest"]),
    )
    state_validator = getattr(authority, "validate_state", None)
    if not callable(state_validator):
        raise CandidateAssemblyError("STATE_VALIDATOR_REQUIRED", "$.authority", "Q-00/Q-01 state validator is required")
    try:
        state_validator(canonical_bytes(assembly.platform), canonical_bytes(assembly.intake), canonical_bytes(assembly.qualification), board_id=assembly.board_id, profile_id=assembly.profile_id, verification_time=verification_time)
    except CandidateAssemblyError:
        raise
    except Exception as error:
        raise CandidateAssemblyError("QUALIFICATION_REJECTED", "$.qualification", "Q-00/Q-01 state validation rejected input") from error
    receipts: dict[str, _AuthorityCapability] = {}
    for kind, record, digest, subject in checks:
        source_bytes = canonical_bytes(record)
        try:
            receipt = authority.verify_canonical(kind, source_bytes, digest=digest, board_id=assembly.board_id, profile_id=assembly.profile_id, channel=assembly.channel, schema_set_digest=assembly.platform["schema_set_digest"], verification_time=verification_time, subject=subject)
        except CandidateAssemblyError:
            raise
        except Exception as error:  # adapters must not leak provider detail
            raise CandidateAssemblyError("AUTHORITY_REJECTED", f"$.{kind}", "authority rejected the exact input") from error
        if not isinstance(receipt, _AuthorityCapability):
            raise CandidateAssemblyError("AUTHORITY_UNTRUSTED", f"$.{kind}", "authority did not return a typed trusted receipt")
        if receipt.digest != digest or receipt.board_id != assembly.board_id or receipt.profile_id != assembly.profile_id or receipt.channel != assembly.channel or receipt.subject != subject or receipt.authority != kind or receipt.schema_set_digest != assembly.platform["schema_set_digest"] or receipt.metadata_digest != digest_bytes(source_bytes):
            raise CandidateAssemblyError("AUTHORITY_BINDING_MISMATCH", f"$.{kind}", "authority receipt is not bound to the exact candidate")
        try:
            expiry = datetime.fromisoformat(receipt.expires_at.removesuffix("Z") + "+00:00")
        except ValueError as error:
            raise CandidateAssemblyError("AUTHORITY_EXPIRED", f"$.{kind}.expires_at", "authority expiry is invalid") from error
        if not receipt.expires_at.endswith("Z") or expiry <= checked_time:
            raise CandidateAssemblyError("AUTHORITY_EXPIRED", f"$.{kind}.expires_at", "authority is expired at verification time")
        receipts[kind] = receipt

    try:
        index = PackageIndex.from_dict(assembly.package["index"])
    except (BuildProvenanceError, KeyError, TypeError, ValueError) as error:
        raise CandidateAssemblyError("PACKAGE_INDEX_INVALID", "$.package.index", "F-04 package index failed closed validation") from error
    if index.release_id != assembly.package["release_id"] or index.index_digest != assembly.package["index_digest"] or index.artifact_set_digest != assembly.package["artifact_set_digest"] or index.channel != assembly.channel or index.platform_manifest_id != assembly.platform["manifest_id"] or index.platform_manifest_digest != assembly.platform["manifest_digest"] or index.schema_set_digest != assembly.platform["schema_set_digest"] or index.rollback_artifact_digests != tuple(assembly.package["rollback_artifact_digests"]):
        raise CandidateAssemblyError("PACKAGE_INDEX_BINDING_MISMATCH", "$.package.index", "package index is not bound to exact platform/channel/rollback tuple")
    indexed = {item.artifact_id: item for item in index.artifacts}
    for item in assembly.package["artifacts"]:
        source = indexed.get(item["artifact_id"])
        if source is None or source.content_digest != item["content_digest"] or source.provenance_digest != item["provenance_digest"] or source.sbom_digest != item["sbom_digest"]:
            raise CandidateAssemblyError("PACKAGE_ARTIFACT_BINDING_MISMATCH", "$.package.artifacts", "artifact metadata differs from package index")
        for kind, digest in (("sbom", source.sbom_digest), ("provenance", source.provenance_digest), *(('build-result', result) for result in source.build_result_digests)):
            try:
                verified = metadata_verifier(digest, kind)
            except Exception as error:
                raise CandidateAssemblyError("CAS_MEMBER_MISSING", f"$.package.artifacts[{item['artifact_id']}].{kind}", "referenced CAS metadata member is absent") from error
            if verified is not True:
                raise CandidateAssemblyError("CAS_DIGEST_MISMATCH", f"$.package.artifacts[{item['artifact_id']}].{kind}", "referenced CAS metadata failed rehash")
    if set(indexed) != {item["artifact_id"] for item in assembly.package["artifacts"]}:
        raise CandidateAssemblyError("ARTIFACT_SET_MISMATCH", "$.package.artifacts", "candidate artifact set differs from package index")

    if assembly.compliance["decision"] != "allow":
        raise CandidateAssemblyError("COMPLIANCE_DENIED", "$.compliance.decision", "compliance must explicitly allow")
    if assembly.rollback != tuple(assembly.package["rollback_artifact_digests"]):
        raise CandidateAssemblyError("ROLLBACK_BINDING_MISMATCH", "$.rollback", "candidate rollback set differs from package index")
    package_digests = {item["content_digest"] for item in assembly.package["artifacts"]}
    if not set(assembly.rollback).issubset(package_digests):
        raise CandidateAssemblyError("ROLLBACK_BINDING_MISMATCH", "$.rollback", "rollback members must be an exact subset of package artifact digests")
    for index, digest in enumerate(assembly.rollback):
        try:
            data = artifacts.read(digest)
        except Exception as error:
            raise CandidateAssemblyError("ARTIFACT_BYTES_MISSING", f"$.rollback[{index}]", "rollback member is absent from CAS") from error
        if not isinstance(data, bytes) or digest_bytes(data) != digest:
            raise CandidateAssemblyError("ARTIFACT_DIGEST_MISMATCH", f"$.rollback[{index}]", "rollback bytes do not match digest")
    for index, artifact in enumerate(assembly.package["artifacts"]):
        digest = artifact["content_digest"]
        try:
            data = artifacts.read(digest)
        except Exception as error:
            raise CandidateAssemblyError("ARTIFACT_BYTES_MISSING", f"$.package.artifacts[{index}]", "artifact member is absent from CAS") from error
        if not isinstance(data, bytes) or digest_bytes(data) != digest:
            raise CandidateAssemblyError("ARTIFACT_DIGEST_MISMATCH", f"$.package.artifacts[{index}].content_digest", "artifact bytes do not match digest")
    if not package_digests:
        raise CandidateAssemblyError("MISSING_ARTIFACT", "$.package.artifacts", "package has no artifact bytes")

    # Receipt replay/expiry enforcement belongs to the authority. We still
    # require distinct replay identities so one authority result cannot be
    # transplanted across the five independent input classes.
    replay_ids = [receipt.replay_id for receipt in receipts.values()]
    if len(set(replay_ids)) != len(replay_ids):
        raise CandidateAssemblyError("AUTHORITY_REPLAY", "$.authority", "authority replay identities must be distinct")

    body = {**assembly.body(), "version": "candidate-manifest/v1"}
    candidate_digest = digest_value("omarchy-candidate-manifest/v1", body)
    return CandidateManifest(_freeze(body), candidate_digest, _token=_MANIFEST_TOKEN)
