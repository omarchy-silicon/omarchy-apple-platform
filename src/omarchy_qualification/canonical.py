"""Q-01 canonical JSON and domain-separated digests."""

from hashlib import sha256
from typing import Any

import rfc8785


def canonical_bytes(value: Any) -> bytes:
    return rfc8785.dumps(value)


def digest_bytes(value: bytes) -> str:
    return "sha256:" + sha256(value).hexdigest()


def domain_digest(domain: str, value: Any) -> str:
    return digest_bytes(domain.encode("ascii") + b"\x00" + canonical_bytes(value))
