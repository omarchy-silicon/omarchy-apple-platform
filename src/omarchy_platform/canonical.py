"""Deterministic canonical JSON and F-02 domain-separated digests."""

from hashlib import sha256
import json
from typing import Any

import rfc8785

_SAFE_INTEGER = 2**53 - 1


def _has_large_integer(value: Any) -> bool:
    if isinstance(value, int) and not isinstance(value, bool):
        return abs(value) > _SAFE_INTEGER
    if isinstance(value, list):
        return any(_has_large_integer(item) for item in value)
    if isinstance(value, dict):
        return any(_has_large_integer(item) for item in value.values())
    return False


def _large_integer_fallback(value: Any) -> bytes:
    """Use JCS ordering with exact integer text beyond RFC8785's float domain."""
    def encode(item: Any) -> str:
        if isinstance(item, int) and not isinstance(item, bool):
            if abs(item) > _SAFE_INTEGER:
                return str(item)
            return rfc8785.dumps(item).decode("ascii")
        if isinstance(item, (str, float, bool)) or item is None:
            return rfc8785.dumps(item).decode("utf-8")
        if isinstance(item, list):
            return "[" + ",".join(encode(child) for child in item) + "]"
        if isinstance(item, dict):
            keys = sorted(item, key=lambda key: key.encode("utf-16-be"))
            return "{" + ",".join(json.dumps(key, ensure_ascii=False) + ":" + encode(item[key]) for key in keys) + "}"
        raise TypeError(f"unsupported JSON value: {type(item).__name__}")
    return encode(value).encode("utf-8")


def canonical_bytes(value: Any) -> bytes:
    """Encode the supported JSON domain with pinned RFC 8785 JCS."""
    if _has_large_integer(value):
        return _large_integer_fallback(value)
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
