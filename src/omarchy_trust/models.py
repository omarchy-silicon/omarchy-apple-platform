"""Immutable value objects returned by the F-03 verifier."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ReplaySnapshot:
    """Bounded monotonic state supplied by the caller; never written here."""

    entries: tuple[tuple[str, int, str, str], ...] = ()

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> "ReplaySnapshot":
        if not value:
            return cls()
        rows = []
        for key, raw in value.items():
            if not isinstance(key, str) or not isinstance(raw, Mapping):
                raise ValueError("invalid replay snapshot")
            sequence = raw.get("sequence")
            version = raw.get("version", "")
            digest = raw.get("metadata_digest", "")
            if not isinstance(sequence, int) or isinstance(sequence, bool):
                raise ValueError("invalid replay sequence")
            if not all(isinstance(item, str) for item in (version, digest)):
                raise ValueError("invalid replay value")
            if len(key.encode("utf-8")) > 4096 or len(version.encode("utf-8")) > 4096 or len(digest.encode("utf-8")) > 4096:
                raise ValueError("replay value limit exceeded")
            rows.append((key, sequence, version, digest))
        rows.sort()
        if len(rows) > 1024:
            raise ValueError("replay snapshot limit exceeded")
        return cls(tuple(rows))

    def lookup(self, replay_key: str) -> tuple[int, str, str] | None:
        for key, sequence, version, digest in self.entries:
            if key == replay_key:
                return sequence, version, digest
        return None


@dataclass(frozen=True)
class ReplayProposal:
    replay_key: str
    sequence: int
    version: str
    metadata_digest: str


@dataclass(frozen=True)
class TrustedTrustContext:
    """The only successful trust result; there is deliberately no bool flag."""

    accepted_role: str
    key_ids: tuple[str, ...]
    threshold: int
    metadata_digest: str
    schema_set_digest: str
    channel: str
    expires_at: str
    replay_id: str
    replay_proposal: ReplayProposal


@dataclass(frozen=True)
class TrustAnchors:
    """Public anchors. Production anchors are loaded from package data."""

    keys: tuple[tuple[str, bytes], ...]
    threshold: int = 3
    provisioned: bool = False

    @classmethod
    def from_public_keys(cls, public_keys: Mapping[str, bytes], threshold: int = 3) -> "TrustAnchors":
        return cls(tuple(sorted((key, bytes(value)) for key, value in public_keys.items())), threshold, True)

    def as_mapping(self) -> dict[str, bytes]:
        return dict(self.keys)


__all__ = ["ReplayProposal", "ReplaySnapshot", "TrustAnchors", "TrustedTrustContext"]
