"""Canonical, domain-separated metadata for release mutations."""

from __future__ import annotations

from typing import Any

from .util import canonical_bytes, digest_value


def _operation_bytes(version: str, fields: dict[str, Any]) -> bytes:
    return canonical_bytes({"version": version, **fields})


def rollback_identity(index_digest: str, rollback_artifact_digests: tuple[str, ...]) -> str:
    """Identify the exact retained artifact set used by a mutation."""

    return digest_value(
        "omarchy-rollback-identity/v1",
        {"index_digest": index_digest, "rollback_artifact_digests": list(rollback_artifact_digests)},
    )


def promotion_operation_bytes(
    *,
    source_channel: str,
    target_channel: str,
    release_id: str,
    source_record_digest: str,
    source_index_digest: str,
    artifact_set_digest: str,
    rollback_artifact_digests: tuple[str, ...],
) -> bytes:
    return _operation_bytes(
        "promotion-operation/v1",
        {
            "source_channel": source_channel,
            "target_channel": target_channel,
            "release_id": release_id,
            "source_record_digest": source_record_digest,
            "source_index_digest": source_index_digest,
            "artifact_set_digest": artifact_set_digest,
            "rollback_artifact_digests": list(rollback_artifact_digests),
            "rollback_identity": rollback_identity(source_index_digest, rollback_artifact_digests),
        },
    )


def rollback_operation_bytes(
    *,
    channel: str,
    failed_release_id: str,
    restore_release_id: str,
    failed_record_digest: str,
    restore_record_digest: str,
    failed_index_digest: str,
    restore_index_digest: str,
    restore_artifact_set_digest: str,
    rollback_artifact_digests: tuple[str, ...],
) -> bytes:
    return _operation_bytes(
        "rollback-operation/v1",
        {
            "channel": channel,
            "failed_release_id": failed_release_id,
            "restore_release_id": restore_release_id,
            "failed_record_digest": failed_record_digest,
            "restore_record_digest": restore_record_digest,
            "failed_index_digest": failed_index_digest,
            "restore_index_digest": restore_index_digest,
            "restore_artifact_set_digest": restore_artifact_set_digest,
            "rollback_artifact_digests": list(rollback_artifact_digests),
            "rollback_identity": rollback_identity(restore_index_digest, rollback_artifact_digests),
        },
    )
