"""Independent deterministic fixture subprocess builders."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .errors import BuildProvenanceError
from .models import BuildResult, BuilderDefinition, OutputRecord, Recipe, SourceClosure
from .provenance import make_provenance
from .sbom import make_sbom
from .util import MAX_OUTPUT_BYTES, canonical_bytes, digest_bytes, expect_digest, safe_relative_path

WORKER = Path(__file__).with_name("fixture_worker.py")


class FixtureBuilder:
    """Run the closed fixture recipe in a separate process and temporary root."""

    def __init__(self, definition: BuilderDefinition, *, python: str | None = None):
        if definition.backend != "fixture-subprocess/v1":
            raise BuildProvenanceError("UNKNOWN_BUILDER_BACKEND", "$.backend", "fixture backend required")
        if definition.network_policy != "denied" or definition.root_policy != "isolated-temp-root":
            raise BuildProvenanceError("BUILDER_POLICY_REJECTED", "$.builder_id", "fixture builder policy is not fail-closed")
        self.definition = definition
        self.python = python or sys.executable

    def build(self, closure: SourceClosure, recipe: Recipe, source_bytes: dict[str, bytes]) -> BuildResult:
        if closure.recipe_id != recipe.recipe_id or closure.recipe_digest != recipe.recipe_digest:
            raise BuildProvenanceError("SOURCE_RECIPE_MISMATCH", "$.recipe_digest", "source closure and recipe differ")
        inputs = {item.input_id: item for item in closure.inputs}
        if tuple(recipe.input_ids) != tuple(sorted(recipe.input_ids)):
            raise BuildProvenanceError("UNSORTED_IDS", "$.input_ids", "recipe input IDs must be sorted")
        if set(recipe.input_ids) != set(inputs):
            raise BuildProvenanceError("INPUT_CLOSURE_MISMATCH", "$.input_ids", "recipe and source closure input sets differ")
        if set(source_bytes) != set(inputs):
            raise BuildProvenanceError("INPUT_CLOSURE_MISMATCH", "$.sources", "provided source set differs from declared closure")
        for input_id, item in inputs.items():
            data = source_bytes.get(input_id)
            if not isinstance(data, bytes):
                raise BuildProvenanceError("INPUT_MISSING", f"$.inputs.{input_id}", "declared input bytes are missing")
            if digest_bytes(data) != item.digest:
                raise BuildProvenanceError("INPUT_DIGEST_MISMATCH", f"$.inputs.{input_id}", "declared input bytes differ")
        source_by_path = {inputs[input_id].relative_path: source_bytes[input_id] for input_id in inputs}
        if len(source_by_path) != len(inputs):
            raise BuildProvenanceError("INPUT_CLOSURE_MISMATCH", "$.inputs", "declared input paths must be unique")
        # The worker only receives declared bytes. An absent recipe read path therefore
        # proves an undeclared-input guard without exposing the host filesystem.
        payload = {"recipe": recipe.to_dict(), "source": {path: data.hex() for path, data in source_by_path.items()}}
        with tempfile.TemporaryDirectory(prefix="omarchy-f04-builder-") as root:
            root_path = Path(root)
            request = root_path / "request.json"
            response = root_path / "response.json"
            request.write_bytes(canonical_bytes(payload))
            env = {"PATH": os.environ.get("PATH", ""), "PYTHONHASHSEED": "0", "LC_ALL": "C", "TZ": "UTC", "SOURCE_DATE_EPOCH": "0", "OMARCHY_BUILD_NETWORK": "denied"}
            try:
                completed = subprocess.run(
                    [self.python, "-I", str(WORKER), str(request), str(response)],
                    cwd=root_path,
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                    timeout=15,
                )
            except (OSError, subprocess.TimeoutExpired) as error:
                raise BuildProvenanceError("BUILDER_EXECUTION_FAILURE", "$.builder_id", "fixture subprocess failed") from error
            if completed.returncode != 0:
                try:
                    detail = json.loads(completed.stderr.decode("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    detail = {}
                raise BuildProvenanceError(detail.get("code", "BUILDER_EXECUTION_FAILURE"), detail.get("path", "$"), detail.get("detail", "fixture subprocess rejected recipe"))
            try:
                output = json.loads(response.read_text(encoding="utf-8"))
                output_data = bytes.fromhex(output["data_hex"])
            except (OSError, ValueError, KeyError, TypeError) as error:
                raise BuildProvenanceError("BUILDER_OUTPUT_INVALID", "$.outputs", "fixture output is malformed") from error
        if len(output_data) > MAX_OUTPUT_BYTES:
            raise BuildProvenanceError("RESOURCE_LIMIT", "$.outputs", "output byte limit exceeded")
        output_record = OutputRecord(recipe.output_path, recipe.output_media_type, len(output_data), digest_bytes(output_data))
        outputs = (output_record,)
        sbom = make_sbom(
            BuildResult.create(
                builder_id=self.definition.builder_id,
                builder_definition_digest=self.definition.definition_digest,
                recipe_id=recipe.recipe_id,
                recipe_digest=recipe.recipe_digest,
                source_closure_digest=closure.closure_digest,
                toolchain_digest=self.definition.toolchain_digest,
                environment_digest=self.definition.environment_digest,
                outputs=outputs,
                provenance_digest=digest_bytes(b"provisional-provenance"),
                sbom_digest=digest_bytes(b"provisional-sbom"),
                output_bytes={recipe.output_path: output_data},
            )
        )
        provisional = BuildResult.create(
            builder_id=self.definition.builder_id,
            builder_definition_digest=self.definition.definition_digest,
            recipe_id=recipe.recipe_id,
            recipe_digest=recipe.recipe_digest,
            source_closure_digest=closure.closure_digest,
            toolchain_digest=self.definition.toolchain_digest,
            environment_digest=self.definition.environment_digest,
            outputs=outputs,
            provenance_digest=digest_bytes(b"provisional-provenance"),
            sbom_digest=sbom.sbom_digest,
            output_bytes={recipe.output_path: output_data},
        )
        provenance = make_provenance(provisional, self.definition, closure, sbom)
        return BuildResult.create(
            builder_id=self.definition.builder_id,
            builder_definition_digest=self.definition.definition_digest,
            recipe_id=recipe.recipe_id,
            recipe_digest=recipe.recipe_digest,
            source_closure_digest=closure.closure_digest,
            toolchain_digest=self.definition.toolchain_digest,
            environment_digest=self.definition.environment_digest,
            outputs=outputs,
            provenance_digest=provenance.provenance_digest,
            sbom_digest=sbom.sbom_digest,
            output_bytes={recipe.output_path: output_data},
        )
