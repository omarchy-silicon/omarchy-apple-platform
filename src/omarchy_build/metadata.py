"""Package-index assembly and F-03 trust verification helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from omarchy_platform.strictjson import parse
from omarchy_platform.errors import ParseError

from .comparison import compare_results
from .errors import BuildProvenanceError
from .models import HIGH_TRUST_CLASSES, BuildResult, PackageArtifact, PackageIndex, Provenance, Sbom
from .trust import TrustAdapter, require_trusted_context
from .util import canonical_bytes, digest_bytes, expect_digest, expect_string, sorted_unique


def make_package_index(
    *,
    release_id: str,
    channel: str,
    platform_manifest_id: str,
    platform_manifest_digest: str,
    schema_set_digest: str,
    artifact_id: str,
    artifact_class: str,
    left: BuildResult,
    right: BuildResult,
    provenance: Provenance,
    sbom: Sbom,
    rollback_artifact_digests: tuple[str, ...],
) -> PackageIndex:
    """Create an index only after two independent fixture results match."""

    if artifact_class not in HIGH_TRUST_CLASSES:
        raise BuildProvenanceError("UNKNOWN_ARTIFACT_CLASS", "$.artifact_class", "artifact class is outside F-04 launch vocabulary")
    compare_results(left, right)
    if provenance.provenance_digest not in {left.provenance_digest, right.provenance_digest}:
        raise BuildProvenanceError("PROVENANCE_BINDING_MISMATCH", "$.provenance_digest", "provenance is not from either build")
    if sbom.sbom_digest not in {left.sbom_digest, right.sbom_digest}:
        raise BuildProvenanceError("SBOM_ARTIFACT_SET_MISMATCH", "$.sbom_digest", "SBOM is not from either build")
    if left.artifact_set_digest != sbom.artifact_set_digest:
        raise BuildProvenanceError("SBOM_ARTIFACT_SET_MISMATCH", "$.artifact_set_digest", "SBOM is not bound to build output")
    if len(left.outputs) != 1:
        raise BuildProvenanceError("ARTIFACT_PROJECTION_INVALID", "$.outputs", "fixture package index expects one output")
    output = left.outputs[0]
    artifact = PackageArtifact(artifact_id, artifact_class, output.content_digest, tuple(sorted((left.result_digest, right.result_digest))), provenance.provenance_digest, sbom.sbom_digest)
    return PackageIndex.create(
        release_id=release_id,
        channel=channel,
        platform_manifest_id=platform_manifest_id,
        platform_manifest_digest=platform_manifest_digest,
        schema_set_digest_value=schema_set_digest,
        artifacts=(artifact,),
        rollback_artifact_digests=tuple(sorted(rollback_artifact_digests)),
    )


def verify_index_bytes(
    metadata_bytes: bytes,
    *,
    adapter: TrustAdapter | None,
    signer_role: str,
    channel: str,
    expires_at: str,
    replay_id: str,
) -> PackageIndex:
    """Parse closed index bytes and require F-03 authorization."""

    if not isinstance(metadata_bytes, bytes):
        raise BuildProvenanceError("NONCANONICAL_METADATA", "$.metadata", "metadata bytes must be canonical JSON")
    try:
        value = parse(metadata_bytes)
    except (ParseError, ValueError, TypeError, UnicodeDecodeError) as error:
        raise BuildProvenanceError("INDEX_INVALID", "$.metadata", "package index is invalid") from error
    if metadata_bytes != canonical_bytes(value):
        raise BuildProvenanceError("NONCANONICAL_METADATA", "$.metadata", "metadata bytes must be canonical JSON")
    try:
        index = PackageIndex.from_dict(value)
    except BuildProvenanceError:
        raise
    except (ValueError, TypeError, UnicodeDecodeError) as error:
        raise BuildProvenanceError("INDEX_INVALID", "$.metadata", "package index is invalid") from error
    if index.channel != channel:
        raise BuildProvenanceError("CHANNEL_BINDING_MISMATCH", "$.channel", "index channel differs from requested channel")
    require_trusted_context(adapter, metadata_bytes, schema_set_digest=index.schema_set_digest, signer_role=signer_role, channel=channel, expires_at=expires_at, replay_id=replay_id)
    return index
