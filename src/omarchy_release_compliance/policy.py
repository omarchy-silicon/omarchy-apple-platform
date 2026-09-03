"""The closed policy vocabulary for F-06.

This is intentionally duplicated as a small immutable Python value so an
the evaluator uses the separately packaged immutable provenance resource rather
than any caller-supplied policy field.
``tools/compliance/drift.py`` keeps it byte-for-byte aligned with the checked
in policy document.
"""

from copy import deepcopy
import ast
from importlib.resources import files

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


def packaged_provenance_lock() -> dict:
    """Read the sole lock from the installed package resource."""
    source = files("omarchy_release_compliance").joinpath("provenance_lock.py").read_text()
    module = ast.parse(source, filename="provenance_lock.py")
    assignment = next((node for node in module.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "LOCK" for t in node.targets)), None)
    if assignment is None:
        raise ValueError("packaged provenance lock assignment missing")
    value = ast.literal_eval(assignment.value)
    if not isinstance(value, dict):
        raise ValueError("packaged provenance lock must be an object")
    return value
