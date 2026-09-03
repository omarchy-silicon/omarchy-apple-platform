"""The narrow F-03 verification boundary consumed by F-04."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

from .errors import TrustRejection
from .models import CHANNELS, TrustedTrustContext
from .util import canonical_bytes, digest_bytes, expect_digest, expect_string


@runtime_checkable
class TrustAdapter(Protocol):
    """F-03 supplies this protocol; F-04 never owns keys or trust policy."""

    def verify_and_authorize(
        self,
        metadata_bytes: bytes,
        *,
        schema_set_digest: str,
        signer_role: str,
        channel: str,
        expires_at: str,
        replay_id: str,
    ) -> TrustedTrustContext:
        """Return a closed verified context or raise :class:`TrustRejection`."""


def metadata_digest(metadata_bytes: bytes) -> str:
    return digest_bytes(metadata_bytes)


def require_trusted_context(
    adapter: TrustAdapter | None,
    metadata_bytes: bytes,
    *,
    schema_set_digest: str,
    signer_role: str,
    channel: str,
    expires_at: str | None,
    replay_id: str | None,
) -> TrustedTrustContext:
    """Call F-03 and re-check its closed result at the F-04 seam."""

    if adapter is None or not isinstance(adapter, TrustAdapter):
        raise TrustRejection("TRUST_ADAPTER_UNAVAILABLE", "$", "F-03 trust adapter is unavailable")
    if not isinstance(metadata_bytes, bytes) or not metadata_bytes:
        raise TrustRejection("TRUST_METADATA_INVALID", "$", "canonical metadata bytes required")
    expect_digest(schema_set_digest, "$.schema_set_digest")
    expect_string(signer_role, "$.signer_role")
    if channel not in CHANNELS:
        raise TrustRejection("TRUST_METADATA_INVALID", "$.channel", "unknown channel")
    if not isinstance(expires_at, str) or not expires_at:
        raise TrustRejection("TRUST_METADATA_INVALID", "$.expires_at", "UTC expiry is required")
    if not isinstance(replay_id, str) or not replay_id:
        raise TrustRejection("TRUST_METADATA_INVALID", "$.replay_id", "replay identity is required")
    expect_string(expires_at, "$.expires_at")
    expect_string(replay_id, "$.replay_id")
    try:
        result = adapter.verify_and_authorize(
            metadata_bytes,
            schema_set_digest=schema_set_digest,
            signer_role=signer_role,
            channel=channel,
            expires_at=expires_at,
            replay_id=replay_id,
        )
    except TrustRejection:
        raise
    except Exception as error:
        raise TrustRejection("TRUST_ADAPTER_REJECTED", "$", "F-03 trust adapter rejected metadata") from error
    if not isinstance(result, TrustedTrustContext):
        raise TrustRejection("TRUST_CONTEXT_INVALID", "$", "F-03 returned a non-closed trust result")
    if result.metadata_digest != metadata_digest(metadata_bytes):
        raise TrustRejection("TRUST_CONTEXT_MISMATCH", "$.metadata_digest", "trusted metadata digest mismatch")
    if result.accepted_role != signer_role:
        raise TrustRejection("TRUST_ROLE_REJECTED", "$.accepted_role", "trusted context role differs from requested role")
    if result.schema_set_digest != schema_set_digest or result.channel != channel or result.expires_at != expires_at or result.replay_id != replay_id:
        raise TrustRejection("TRUST_CONTEXT_MISMATCH", "$", "trusted context does not bind requested metadata")
    return result


def stable_authorization(context: TrustedTrustContext) -> bool:
    """Only F-07's closed promotion role may write stable channel records."""

    return context.accepted_role == "promotion/f07"
