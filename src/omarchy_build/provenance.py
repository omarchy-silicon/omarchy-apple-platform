"""Build provenance generation and closure checks."""

from __future__ import annotations

from collections.abc import Mapping

from .errors import BuildProvenanceError
from .models import BuildResult, BuilderDefinition, Provenance, Sbom, SourceClosure
from .sbom import validate_sbom
from .util import digest_bytes, expect_digest


def make_provenance(
    result: BuildResult,
    definition: BuilderDefinition,
    closure: SourceClosure,
    sbom: Sbom,
    *,
    log_bytes: bytes = b"omarchy-f04-fixture-build-log/v1\n",
) -> Provenance:
    if result.builder_id != definition.builder_id or result.builder_definition_digest != definition.definition_digest:
        raise BuildProvenanceError("PROVENANCE_BINDING_MISMATCH", "$.builder_id", "result and builder definition differ")
    if result.source_closure_digest != closure.closure_digest or result.recipe_digest != closure.recipe_digest:
        raise BuildProvenanceError("PROVENANCE_BINDING_MISMATCH", "$.source_closure_digest", "result and source closure differ")
    validate_sbom(sbom, result.outputs, result.artifact_set_digest)
    input_digests = tuple(sorted(item.digest for item in closure.inputs))
    return Provenance.create(
        builder_id=definition.builder_id,
        builder_definition_digest=definition.definition_digest,
        recipe_digest=closure.recipe_digest,
        source_closure_digest=closure.closure_digest,
        toolchain_digest=definition.toolchain_digest,
        environment_digest=definition.environment_digest,
        artifact_set_digest_value=result.artifact_set_digest,
        input_digests=input_digests,
        sbom_digest=sbom.sbom_digest,
        log_digest=digest_bytes(log_bytes),
    )


def verify_provenance(
    provenance: Provenance,
    result: BuildResult,
    definition: BuilderDefinition,
    closure: SourceClosure,
    sbom: Sbom,
) -> None:
    if provenance.builder_id != definition.builder_id or provenance.builder_definition_digest != definition.definition_digest:
        raise BuildProvenanceError("PROVENANCE_BINDING_MISMATCH", "$.builder_id", "provenance builder mismatch")
    if provenance.recipe_digest != closure.recipe_digest or provenance.source_closure_digest != closure.closure_digest:
        raise BuildProvenanceError("PROVENANCE_BINDING_MISMATCH", "$.recipe_digest", "provenance source mismatch")
    if provenance.toolchain_digest != definition.toolchain_digest or provenance.environment_digest != definition.environment_digest:
        raise BuildProvenanceError("PROVENANCE_BINDING_MISMATCH", "$.toolchain_digest", "provenance toolchain mismatch")
    if provenance.artifact_set_digest != result.artifact_set_digest or provenance.sbom_digest != sbom.sbom_digest:
        raise BuildProvenanceError("PROVENANCE_BINDING_MISMATCH", "$.artifact_set_digest", "provenance output mismatch")
    if provenance.provenance_digest != result.provenance_digest:
        raise BuildProvenanceError("PROVENANCE_BINDING_MISMATCH", "$.provenance_digest", "result provenance reference mismatch")
    expected = tuple(sorted(item.digest for item in closure.inputs))
    if provenance.input_digests != expected:
        raise BuildProvenanceError("UNDECLARED_INPUT", "$.input_digests", "provenance input closure mismatch")
    validate_sbom(sbom, result.outputs, result.artifact_set_digest)
