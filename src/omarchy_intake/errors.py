"""Stable errors for the fail-closed Q-00 parsing and validation seam."""

from dataclasses import dataclass


@dataclass(frozen=True)
class IntakeValidationError(Exception):
    code: str
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.code} at {self.path}: {self.message}"
