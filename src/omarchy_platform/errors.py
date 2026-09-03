"""Stable, redacted errors for the untrusted parsing seam."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationError(Exception):
    code: str
    path: str
    phase: str
    message: str

    def __str__(self) -> str:
        return f"{self.code} at {self.path} ({self.phase}): {self.message}"


class ParseError(ValidationError):
    pass


class SchemaError(ValidationError):
    pass
