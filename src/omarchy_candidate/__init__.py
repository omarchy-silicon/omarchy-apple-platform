"""Fail-closed F-05 candidate assembly foundation."""

from .assemble import assemble_candidate
from .consumer import guard_manifest
from .errors import CandidateAssemblyError
from .models import CandidateAssemblyInput, CandidateAuthority, CandidateManifest, digest_bytes, digest_value

__all__ = ["CandidateAssemblyError", "CandidateAssemblyInput", "CandidateAuthority", "CandidateManifest", "assemble_candidate", "digest_bytes", "digest_value", "guard_manifest"]
