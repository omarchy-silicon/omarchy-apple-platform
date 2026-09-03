"""Closed, redacted failures for the F-03 trust boundary."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TrustFailure(Exception):
    """A deterministic failure that never contains sensitive input."""

    code: str
    path: str
    detail: str

    def __str__(self) -> str:
        return f"{self.code} at {self.path}: {self.detail}"


__all__ = ["TrustFailure"]
