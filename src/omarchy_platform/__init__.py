"""F-02 platform schema implementation foundation."""

from .canonical import canonical_bytes, domain_digest, payload_digest, schema_set_digest
from .constants import AUTHENTICATED_PAYLOAD_TYPES, SCHEMA_INPUT_IDS
from .strictjson import parse
from .models import BoardRegistry, PlatformManifest, InstallerPlan, QualificationRecord, BootHealth, OwnerApproval, BootSuccessMark, DtbMutationEnvelope
from .validate import ConformanceResult, admit_bundle

__all__ = [
    "AUTHENTICATED_PAYLOAD_TYPES",
    "SCHEMA_INPUT_IDS",
    "canonical_bytes",
    "domain_digest",
    "parse",
    "payload_digest",
    "schema_set_digest",
    "BoardRegistry",
    "PlatformManifest",
    "InstallerPlan",
    "QualificationRecord",
    "BootHealth",
    "OwnerApproval",
    "BootSuccessMark",
    "DtbMutationEnvelope",
    "ConformanceResult",
    "admit_bundle",
]
