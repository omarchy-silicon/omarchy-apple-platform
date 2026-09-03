"""Closed F-03 policy constants and limits."""

from __future__ import annotations

from types import MappingProxyType

TRUST_FORMAT = "omarchy-trust-root/v1"
TRUST_PREIMAGE_DOMAIN = "omarchy-trust-root-preimage/v1"
AUTH_PREIMAGE_DOMAIN = "omarchy-auth-preimage/v1"
MAX_METADATA_BYTES = 1_048_576
MAX_ARTIFACT_BYTES = 8 * 1024 * 1024 * 1024
MAX_CLOCK_SKEW_SECONDS = 300
MAX_SIGNATURES = 16
MAX_KEYS = 64
MAX_DELEGATIONS = 128
MAX_REVOCATIONS = 256
MAX_REPLAY_SCOPES = 1024
MAX_LINEAGES = 4096

ROLE_LIMIT_SECONDS = MappingProxyType(
    {
        "root": 365 * 24 * 60 * 60,
        "targets": 90 * 24 * 60 * 60,
        "snapshot": 24 * 60 * 60,
        "timestamp": 6 * 60 * 60,
        "artifact": 30 * 24 * 60 * 60,
        "package-index": 30 * 24 * 60 * 60,
        "emergency/recovery": 7 * 24 * 60 * 60,
    }
)

ROLE_TO_SIGNER = MappingProxyType(
    {
        "board-admission": "targets",
        "manifest-release": "targets",
        "qualification-lab": "targets",
        "installer-planner": "targets",
        "boot-runtime": "artifact",
        "boot-success-marker": "artifact",
        "dtb-authority": "artifact",
        "owner-authorization": "emergency/recovery",
    }
)

ERROR_DETAILS = MappingProxyType(
    {
        "TRUST_INPUT_TOO_LARGE": "metadata input exceeds the bounded limit",
        "TRUST_IO_LIMIT": "bounded input read failed",
        "TRUST_UTF8_INVALID": "input is not valid UTF-8",
        "TRUST_JSON_INVALID": "input is not valid JSON",
        "TRUST_DUPLICATE_KEY": "duplicate object key",
        "TRUST_NONCANONICAL": "input is not canonical JSON",
        "TRUST_SCHEMA_INVALID": "trust object shape is invalid",
        "TRUST_ANCHOR_MISMATCH": "root anchors are unavailable or inconsistent",
        "TRUST_ANCHORS_UNPROVISIONED": "production root anchors are unprovisioned",
        "TRUST_KEY_ID_INVALID": "public key identifier is invalid",
        "TRUST_UNKNOWN_ROLE": "role is not in the closed policy",
        "TRUST_SCOPE_MISMATCH": "scope is not authorized by delegation",
        "TRUST_DELEGATION_INVALID": "delegation is invalid",
        "TRUST_SIGNATURE_INVALID": "Ed25519 signature verification failed",
        "TRUST_THRESHOLD_UNMET": "signature threshold is not met",
        "TRUST_CONTEXT_MISMATCH": "signed context does not match policy",
        "TRUST_DIGEST_MISMATCH": "digest binding does not match",
        "TRUST_ARTIFACT_MISSING": "required artifact bytes are missing",
        "TRUST_ARTIFACT_SIZE": "artifact byte count does not match",
        "TRUST_ARTIFACT_DIGEST": "artifact digest does not match",
        "TRUST_NOT_YET_VALID": "metadata is not yet valid",
        "TRUST_EXPIRED": "metadata has expired",
        "TRUST_REVOKED_KEY": "signing key is revoked",
        "TRUST_FROZEN": "scope is frozen",
        "TRUST_REPLAY": "metadata sequence or digest was replayed",
        "TRUST_ROLLBACK": "rollback is not explicitly authorized",
        "TRUST_ROTATION_INVALID": "key rotation is invalid",
        "TRUST_RECOVERY_REQUIRED": "emergency recovery authorization is required",
        "TRUST_REPLAY_STATE_UNAVAILABLE": "replay state is unavailable or divergent",
        "TRUST_INTERNAL": "trust verification failed closed",
    }
)


__all__ = [
    "AUTH_PREIMAGE_DOMAIN",
    "ERROR_DETAILS",
    "MAX_ARTIFACT_BYTES",
    "MAX_CLOCK_SKEW_SECONDS",
    "MAX_METADATA_BYTES",
    "ROLE_LIMIT_SECONDS",
    "ROLE_TO_SIGNER",
    "TRUST_FORMAT",
    "TRUST_PREIMAGE_DOMAIN",
]
