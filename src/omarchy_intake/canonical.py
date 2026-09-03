"""Canonical bytes and domain-separated Q-00 digests."""

from hashlib import sha256
from typing import Any

import rfc8785


def canonical_bytes(value: Any) -> bytes:
    return rfc8785.dumps(value)


def sha256_digest(data: bytes) -> str:
    return "sha256:" + sha256(data).hexdigest()


def intake_digest(kind: str, value: Any) -> str:
    return sha256_digest(b"omarchy-intake/" + kind.encode("ascii") + b"\x00" + canonical_bytes(value))


def content_digest(data: bytes) -> str:
    return sha256_digest(data)
