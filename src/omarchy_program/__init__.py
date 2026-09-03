"""Fail-closed integrity checks for the coordinator-owned PROGRAM.md ledger."""

from .validate import ProgramValidationError, validate_program

__all__ = ["ProgramValidationError", "validate_program"]
