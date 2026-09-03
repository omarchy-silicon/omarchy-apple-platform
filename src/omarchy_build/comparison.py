"""Byte-level comparison of independent build results."""

from __future__ import annotations

from collections.abc import Mapping

from .errors import BuildProvenanceError
from .models import BuildResult
from .util import digest_bytes


def compare_results(left: BuildResult, right: BuildResult) -> dict[str, object]:
    """Require two distinct builders to produce the same verified bytes."""

    if left.builder_id == right.builder_id:
        raise BuildProvenanceError("INDEPENDENT_BUILDERS_REQUIRED", "$.builder_id", "comparison requires distinct builder IDs")
    for field in ("recipe_id", "recipe_digest", "source_closure_digest", "toolchain_digest", "environment_digest", "artifact_set_digest"):
        if getattr(left, field) != getattr(right, field):
            raise BuildProvenanceError("BUILD_INPUT_MISMATCH", f"$.{field}", "independent build inputs differ")
    left_outputs = {item.path: item for item in left.outputs}
    right_outputs = {item.path: item for item in right.outputs}
    if set(left_outputs) != set(right_outputs):
        raise BuildProvenanceError("ARTIFACT_MISMATCH", "$.outputs", "independent output path sets differ")
    if not left.output_bytes or not right.output_bytes:
        raise BuildProvenanceError("OUTPUT_BYTES_UNAVAILABLE", "$.outputs", "byte-level comparison requires both output byte maps")
    for path in sorted(left_outputs):
        left_bytes = left.output_bytes.get(path)
        right_bytes = right.output_bytes.get(path)
        if not isinstance(left_bytes, bytes) or not isinstance(right_bytes, bytes):
            raise BuildProvenanceError("OUTPUT_BYTES_UNAVAILABLE", f"$.outputs[{path}]", "output bytes are missing")
        if left_bytes != right_bytes:
            raise BuildProvenanceError("NONREPRODUCIBLE_OUTPUT", f"$.outputs[{path}]", "independent output bytes differ")
        if digest_bytes(left_bytes) != left_outputs[path].content_digest or digest_bytes(right_bytes) != right_outputs[path].content_digest:
            raise BuildProvenanceError("ARTIFACT_MISMATCH", f"$.outputs[{path}]", "output bytes do not match declared digest")
        if left_outputs[path].byte_count != len(left_bytes) or right_outputs[path].byte_count != len(right_bytes):
            raise BuildProvenanceError("ARTIFACT_MISMATCH", f"$.outputs[{path}]", "output byte count differs")
    if left.artifact_set_digest != right.artifact_set_digest:
        raise BuildProvenanceError("ARTIFACT_MISMATCH", "$.artifact_set_digest", "aggregate artifact digest differs")
    return {"version": "build-comparison/v1", "decision": "match", "left_builder_id": left.builder_id, "right_builder_id": right.builder_id, "left_result_digest": left.result_digest, "right_result_digest": right.result_digest, "artifact_set_digest": left.artifact_set_digest}


def compare_output_maps(left: BuildResult, right: BuildResult, left_bytes: Mapping[str, bytes], right_bytes: Mapping[str, bytes]) -> dict[str, object]:
    """Attach externally stored bytes without weakening the closed result record."""

    return compare_results(
        BuildResult(**{**left.__dict__, "output_bytes": dict(left_bytes)}),
        BuildResult(**{**right.__dict__, "output_bytes": dict(right_bytes)}),
    )
