"""Stable errors emitted by the PROGRAM integrity validator."""

from __future__ import annotations


class ProgramValidationError(Exception):
    """A deterministic, fail-closed validation error."""

    def __init__(self, code: str, path: str, message: str):
        super().__init__(message)
        self.code = code
        self.path = path
        self.message = message

