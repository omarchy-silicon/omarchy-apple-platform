"""Immutable value objects returned by the F-03 verifier."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from omarchy_platform.canonical import domain_digest

from .constants import MAX_REPLAY_SCOPES


@dataclass(frozen=True)
class ReplaySnapshot:
    """Bounded monotonic state supplied by the caller; never written here."""

    entries: tuple[tuple[str, int, str, str, str], ...] = ()

    def __post_init__(self) -> None:
        if len(self.entries) > MAX_REPLAY_SCOPES:
            raise ValueError("replay snapshot entry limit exceeded")
        scopes = [row[0] for row in self.entries]
        if scopes != sorted(set(scopes)):
            raise ValueError("replay scopes must be sorted and unique")
        lineages = set()
        for row in self.entries:
            if len(row) != 5:
                raise ValueError("replay entry shape is closed")
            scope, sequence, version, digest, lineage = row
            if not isinstance(scope, str) or not scope or len(scope.encode("utf-8")) > 4096 or not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 0 or sequence > 9_007_199_254_740_991 or not isinstance(version, str) or len(version.encode("utf-8")) > 4096:
                raise ValueError("invalid replay entry")
            if not all(isinstance(item, str) and len(item) == 71 and item.startswith("sha256:") and item != "sha256:" + "0" * 64 and all(char in "0123456789abcdef" for char in item[7:]) for item in (digest, lineage)):
                raise ValueError("invalid replay digest")
            expected = domain_digest("omarchy-replay-lineage/v1", {"scope": scope, "sequence": sequence, "metadata_digest": digest})
            if lineage != expected or lineage in lineages:
                raise ValueError("divergent replay lineage")
            lineages.add(lineage)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> "ReplaySnapshot":
        if value is None:
            return cls()
        if set(value) != {"format", "version", "entries"} or value.get("format") != "omarchy-replay-state/v1" or value.get("version") != "v1":
            raise ValueError("replay state shape is closed")
        raw_entries = value.get("entries")
        if not isinstance(raw_entries, list) or len(raw_entries) > MAX_REPLAY_SCOPES:
            raise ValueError("replay state entry limit exceeded")
        rows = []
        lineage_ids = set()
        for raw in raw_entries:
            if not isinstance(raw, Mapping) or set(raw) != {"scope", "sequence", "version", "metadata_digest", "lineage_digest"}:
                raise ValueError("replay entry shape is closed")
            key = raw["scope"]
            sequence = raw["sequence"]
            version = raw["version"]
            digest = raw["metadata_digest"]
            lineage = raw["lineage_digest"]
            if not isinstance(key, str) or not key or len(key.encode("utf-8")) > 4096:
                raise ValueError("invalid replay scope")
            if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 0 or sequence > 9_007_199_254_740_991:
                raise ValueError("invalid replay sequence")
            if not all(isinstance(item, str) for item in (version, digest, lineage)):
                raise ValueError("invalid replay value")
            if len(version.encode("utf-8")) > 4096 or not digest.startswith("sha256:") or len(digest) != 71 or digest == "sha256:" + "0" * 64 or any(char not in "0123456789abcdef" for char in digest[7:]) or not lineage.startswith("sha256:") or len(lineage) != 71 or lineage == "sha256:" + "0" * 64 or any(char not in "0123456789abcdef" for char in lineage[7:]):
                raise ValueError("invalid replay digest")
            expected_lineage = domain_digest("omarchy-replay-lineage/v1", {"scope": key, "sequence": sequence, "metadata_digest": digest})
            if lineage != expected_lineage or lineage in lineage_ids:
                raise ValueError("divergent replay lineage")
            lineage_ids.add(lineage)
            rows.append((key, sequence, version, digest, lineage))
        if [row[0] for row in rows] != sorted(set(row[0] for row in rows)):
            raise ValueError("replay scopes must be sorted and unique")
        return cls(tuple(rows))

    def lookup(self, replay_key: str) -> tuple[int, str, str, str] | None:
        for key, sequence, version, digest, lineage in self.entries:
            if key == replay_key:
                return sequence, version, digest, lineage
        return None


@dataclass(frozen=True)
class ReplayProposal:
    replay_key: str
    sequence: int
    version: str
    metadata_digest: str
    lineage_digest: str


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
