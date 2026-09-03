"""Generated-consumer style guard for downstream pre-mutation callers."""

from __future__ import annotations

from typing import Any

from omarchy_platform.canonical import canonical_bytes
from omarchy_platform.strictjson import parse

from .errors import CandidateAssemblyError
from .models import CandidateManifest


def guard_manifest(manifest_bytes: bytes, *, expected_digest: str, board_id: str, profile_id: str, channel: str) -> CandidateManifest:
    """Return only a canonical, exact-identity candidate manifest.

    This guard deliberately accepts no independent artifact/version choices;
    consumers must use the tuple and artifact set carried by this manifest.
    """
    if not isinstance(manifest_bytes, bytes):
        raise CandidateAssemblyError("NONCANONICAL_MANIFEST", "$.manifest", "manifest bytes are required")
    try:
        value: Any = parse(manifest_bytes)
    except (ValueError, TypeError, UnicodeDecodeError) as error:
        raise CandidateAssemblyError("MANIFEST_INVALID", "$.manifest", "manifest bytes are invalid") from error
    if manifest_bytes != canonical_bytes(value):
        raise CandidateAssemblyError("NONCANONICAL_MANIFEST", "$.manifest", "manifest bytes must be canonical")
    manifest = CandidateManifest.from_dict(value)
    if manifest.candidate_digest != expected_digest:
        raise CandidateAssemblyError("CANDIDATE_DIGEST_MISMATCH", "$.candidate_digest", "consumer expected a different candidate")
    body = manifest.body_value
    for field, expected in (("board_id", board_id), ("profile_id", profile_id), ("channel", channel)):
        if body[field] != expected:
            raise CandidateAssemblyError("IDENTITY_MISMATCH", f"$.{field}", "candidate identity differs from consumer target")
    return manifest


__all__ = ["guard_manifest"]
