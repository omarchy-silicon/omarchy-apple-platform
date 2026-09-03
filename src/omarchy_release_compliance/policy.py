"""The closed policy vocabulary for F-06.

This is intentionally duplicated as a small immutable Python value so an
installed source tree does not need filesystem access to evaluate a bundle.
``tools/compliance/drift.py`` keeps it byte-for-byte aligned with the checked
in policy document.
"""

from copy import deepcopy

VOCABULARY = {
    "version": "f06-policy/v1",
    "artifact_classes": ["application", "asset", "firmware", "fork", "generated", "source", "system"],
    "spdx_expressions": ["Apache-2.0", "BSD-3-Clause", "GPL-2.0-only", "MIT", "NOASSERTION"],
    "redistribution": ["allowed", "direct-fetch-only", "prohibited", "unknown"],
    "asset_policy": ["not-applicable", "opaque-reference", "redistributable"],
    "firmware_policy": ["not-applicable", "opaque-reference", "redistributable"],
    "source_offer_status": ["not-required", "offered"],
    "provenance_version": "build-provenance/v1",
    "sbom_version": "sbom-ref/v1",
    "sbom_formats": ["cyclonedx-json", "spdx-json"],
    "notice_version": "notice/v1",
    "source_offer_version": "source-offer/v1",
    "owner_decision_version": "owner-decision/v1",
}


def vocabulary() -> dict:
    return deepcopy(VOCABULARY)
