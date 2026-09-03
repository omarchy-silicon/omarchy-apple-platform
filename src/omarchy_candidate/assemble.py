"""Pure, read-only F-05 candidate assembly."""

from __future__ import annotations

from collections.abc import Mapping

from .errors import CandidateAssemblyError
from .models import ArtifactReader, CandidateAssemblyInput, CandidateAuthority, CandidateManifest, TrustedReceipt, digest_bytes, digest_value, _freeze


def assemble_candidate(
    value: Mapping[str, object],
    *,
    authority: CandidateAuthority | None = None,
    artifacts: ArtifactReader | None = None,
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

    checks = (
        ("platform", assembly.platform, assembly.platform["manifest_digest"]),
        ("intake", assembly.intake, assembly.intake["dataset_digest"]),
        ("qualification", assembly.qualification, assembly.qualification["record_digest"]),
        ("package", assembly.package, assembly.package["index_digest"]),
        ("compliance", assembly.compliance, assembly.compliance["attestation_digest"]),
    )
    receipts: dict[str, TrustedReceipt] = {}
    for kind, record, digest in checks:
        try:
            receipt = authority.verify(kind, record, digest, board_id=assembly.board_id, profile_id=assembly.profile_id, channel=assembly.channel)
        except CandidateAssemblyError:
            raise
        except Exception as error:  # adapters must not leak provider detail
            raise CandidateAssemblyError("AUTHORITY_REJECTED", f"$.{kind}", "authority rejected the exact input") from error
        if not isinstance(receipt, TrustedReceipt):
            raise CandidateAssemblyError("AUTHORITY_UNTRUSTED", f"$.{kind}", "authority did not return a typed trusted receipt")
        if receipt.digest != digest or receipt.board_id != assembly.board_id or receipt.profile_id != assembly.profile_id or receipt.channel != assembly.channel:
            raise CandidateAssemblyError("AUTHORITY_BINDING_MISMATCH", f"$.{kind}", "authority receipt is not bound to the exact candidate")
        receipts[kind] = receipt

    if assembly.compliance["decision"] != "allow":
        raise CandidateAssemblyError("COMPLIANCE_DENIED", "$.compliance.decision", "compliance must explicitly allow")
    if assembly.rollback != tuple(assembly.package["rollback_artifact_digests"]):
        raise CandidateAssemblyError("ROLLBACK_BINDING_MISMATCH", "$.rollback", "candidate rollback set differs from package index")
    package_digests = {item["content_digest"] for item in assembly.package["artifacts"]}
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

    body = assembly.body()
    candidate_digest = digest_value("omarchy-candidate-manifest/v1", body)
    return CandidateManifest(_freeze(body), candidate_digest)
