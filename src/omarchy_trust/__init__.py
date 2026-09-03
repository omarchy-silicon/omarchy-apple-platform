"""F-03 Ed25519 trust-root verification boundary."""

from .core import key_id, verify_artifact_bytes, verify_document, verify_root_bundle
from .errors import TrustFailure
from .models import ReplayProposal, ReplaySnapshot, TrustAnchors, TrustedTrustContext

__all__ = [
    "ReplayProposal",
    "ReplaySnapshot",
    "TrustAnchors",
    "TrustFailure",
    "TrustedTrustContext",
    "key_id",
    "verify_artifact_bytes",
    "verify_document",
    "verify_root_bundle",
]
