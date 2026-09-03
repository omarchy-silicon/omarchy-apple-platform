"""Deterministic canonical JSON and F-02 domain-separated digests."""

from hashlib import sha256
from typing import Any

import rfc8785

def canonical_bytes(value: Any) -> bytes:
    """Encode the supported JSON domain with pinned RFC 8785 JCS."""
    return rfc8785.dumps(value)


def sha256_digest(data: bytes) -> str:
    return "sha256:" + sha256(data).hexdigest()


def domain_digest(domain: str, value: Any) -> str:
    return sha256_digest(domain.encode("ascii") + b"\x00" + canonical_bytes(value))


def payload_digest(payload: Any) -> str:
    return domain_digest("omarchy-payload/v1", payload)


def schema_set_digest(lock: Any) -> str:
    return domain_digest("omarchy-schema-set/v1", lock)


def auth_preimage(value: Any) -> bytes:
    return b"omarchy-auth-preimage/v1\x00" + canonical_bytes(value)
