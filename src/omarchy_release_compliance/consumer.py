"""Candidate-side promotion seam, sealed until F-03 trust verification."""

from __future__ import annotations

from typing import Any

from omarchy_release_compliance.engine import ComplianceError


class VerifiedComplianceAttestation:
    """Opaque F-03 output; no production constructor exists in F-06."""

    __slots__ = ("_payload",)

    def __new__(cls, *args: Any, **kwargs: Any):
        raise TypeError("VerifiedComplianceAttestation is constructible only by future F-03 verification")

    @classmethod
    def _from_f03(cls, payload: dict[str, Any], seal: object) -> "VerifiedComplianceAttestation":
        if seal is not _F03_SEAL:
            raise TypeError("F-03 verification seal required")
        value = object.__new__(cls)
        value._payload = payload
        return value


_F03_SEAL = object()


def guard_attestation(attestation: Any, expected: dict[str, str]) -> VerifiedComplianceAttestation:
    """Refuse all raw mappings/bytes; only a future F-03 typed result can pass."""
    if not isinstance(attestation, VerifiedComplianceAttestation):
        raise ComplianceError("ATTESTATION_TYPE_REQUIRED", "$", "promotion requires sealed F-03 verification output")
    raise ComplianceError("ATTESTATION_TRUST_UNAVAILABLE", "$", "F-03/F-07 trust terminal is not implemented")
