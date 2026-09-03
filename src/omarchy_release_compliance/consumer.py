"""Candidate-side promotion guard for F-06 evidence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from omarchy_platform.strictjson import parse
from omarchy_release_compliance.engine import ComplianceError, _DIGEST, _UTC, _utc_now

_FIELDS = {
    "version", "decision", "signed", "trusted", "promotable", "clock_trusted", "valid_until",
    "inventory_digest", "policy_digest", "candidate_digest", "manifest_digest", "schema_set_digest", "bundle_digest",
}


def guard_attestation(attestation: bytes | bytearray | memoryview | dict[str, Any], expected: dict[str, str], *, max_age_seconds: int = 3600) -> dict[str, Any]:
    """Reject any evidence that cannot be trusted by a future promotion terminal."""
    try:
        if isinstance(attestation, (bytes, bytearray, memoryview)):
            value = parse(attestation)
        elif isinstance(attestation, dict):
            value = attestation
        else:
            raise TypeError("attestation must be JSON bytes or object")
        if not isinstance(value, dict) or set(value) != _FIELDS:
            raise ComplianceError("ATTESTATION_MISSING_OR_OPEN", "$", "attestation fields are incomplete or open")
        if value["version"] != "f06-compliance-attestation/v1":
            raise ComplianceError("ATTESTATION_VERSION", "$.version", "unsupported attestation version")
        for field in ("inventory_digest", "policy_digest", "candidate_digest", "manifest_digest", "schema_set_digest", "bundle_digest"):
            if not isinstance(value[field], str) or not _DIGEST.fullmatch(value[field]):
                raise ComplianceError("ATTESTATION_DIGEST_INVALID", f"$.{field}", "canonical digest required")
            if expected.get(field) != value[field]:
                raise ComplianceError("ATTESTATION_DIGEST_MISMATCH", f"$.{field}", "attestation is bound to a different release")
        if value["decision"] != "allow":
            raise ComplianceError("ATTESTATION_NOT_ALLOW", "$.decision", "only allow evidence may be considered")
        if value["promotable"] is not True:
            raise ComplianceError("ATTESTATION_NON_PROMOTABLE", "$.promotable", "F-06 evidence cannot promote")
        if value["signed"] is not True:
            raise ComplianceError("ATTESTATION_UNSIGNED", "$.signed", "unsigned evidence cannot promote")
        if value["trusted"] is not True:
            raise ComplianceError("ATTESTATION_UNTRUSTED", "$.trusted", "untrusted evidence cannot promote")
        if value["clock_trusted"] is not True:
            raise ComplianceError("ATTESTATION_CLOCK_UNTRUSTED", "$.clock_trusted", "clock is not trusted before F-03")
        if not isinstance(value["valid_until"], str) or not _UTC.fullmatch(value["valid_until"]):
            raise ComplianceError("ATTESTATION_INVALID", "$.valid_until", "canonical UTC timestamp required")
        when = datetime.fromisoformat(value["valid_until"].replace("Z", "+00:00"))
        if (_utc_now() - when).total_seconds() > 0 or max_age_seconds < 0:
            raise ComplianceError("ATTESTATION_STALE", "$.valid_until", "attestation is outside its freshness window")
        return value
    except ComplianceError:
        raise
    except Exception:
        raise ComplianceError("ATTESTATION_INVALID", "$", "attestation failed closed parsing") from None
