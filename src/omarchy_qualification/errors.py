"""Stable fail-closed Q-01 validation errors."""

from dataclasses import dataclass


@dataclass(frozen=True)
class QualificationValidationError(Exception):
    code: str
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.code} at {self.path}: {self.message}"
