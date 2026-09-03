"""Candidate-side promotion seam, intentionally unopened until F-03."""

from typing import Any

from omarchy_release_compliance.engine import ComplianceError


def guard_attestation(attestation: Any, expected: Any) -> None:
    """Fail closed for every input until F-03 provides verified trust output."""
    raise ComplianceError("ATTESTATION_TRUST_UNAVAILABLE", "$", "F-03/F-07 trust terminal is not implemented")
