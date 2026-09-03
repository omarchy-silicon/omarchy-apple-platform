"""Closed SBOM construction and completeness checks."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from .errors import BuildProvenanceError
from .models import BuildResult, OutputRecord, Sbom, SbomEntry
from .util import ARTIFACT_ID_RE
from .util import digest_bytes, expect_digest, expect_string


def make_sbom(
    result: BuildResult,
    *,
    component_id: str = "artifact:fixture",
    version: str = "0.0.0",
    notice_ref: str | None = None,
    dependencies: Mapping[str, Iterable[str]] | None = None,
) -> Sbom:
    """Create a complete fixture SBOM for every output in ``result``."""

    component_id = expect_string(component_id, "$.component_id", pattern=ARTIFACT_ID_RE)
    version = expect_string(version, "$.version")
    notice_ref = notice_ref or digest_bytes(b"omarchy-f04-fixture-notice/v1")
    expect_digest(notice_ref, "$.notice_ref")
    dependencies = dependencies or {}
    entries = tuple(
        SbomEntry(
            output_path=output.path,
            component_id=component_id,
            version=version,
            digest=output.content_digest,
            dependencies=tuple(sorted(set(dependencies.get(output.path, ())))),
            notice_ref=notice_ref,
        )
        for output in result.outputs
    )
    return Sbom.create(result.artifact_set_digest, entries)


def validate_sbom(sbom: Sbom, outputs: tuple[OutputRecord, ...], artifact_set_digest: str) -> None:
    """Reject absent, extra, duplicate, or mismatched output/dependency entries."""

    if sbom.artifact_set_digest != artifact_set_digest:
        raise BuildProvenanceError("SBOM_ARTIFACT_SET_MISMATCH", "$.artifact_set_digest", "SBOM is not bound to output set")
    expected = {item.path: item for item in outputs}
    actual = {item.output_path: item for item in sbom.entries}
    if set(expected) != set(actual):
        raise BuildProvenanceError("INCOMPLETE_SBOM", "$.entries", "every emitted output needs exactly one SBOM entry")
    for path, output in expected.items():
        entry = actual[path]
        if entry.digest != output.content_digest:
            raise BuildProvenanceError("INCOMPLETE_SBOM", f"$.entries[{path}].digest", "SBOM digest differs from emitted bytes")
        if not entry.component_id or not entry.version or not entry.notice_ref:
            raise BuildProvenanceError("INCOMPLETE_SBOM", f"$.entries[{path}]", "output identity and notice are required")
        for dependency in entry.dependencies:
            if not dependency or dependency != dependency.strip():
                raise BuildProvenanceError("INCOMPLETE_SBOM", f"$.entries[{path}].dependencies", "dependency identities must be complete")
