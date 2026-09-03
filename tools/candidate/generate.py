#!/usr/bin/env python3
"""Generate the checked-in F-05 consumer binding from the sole schema."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "schemas/candidate-assembly/v1/candidate-assembly.json"
OUTPUT = ROOT / "src/omarchy_candidate/generated.py"
OUTPUT_SCHEMA = ROOT / "schemas/candidate-assembly/v1/candidate-manifest.json"
GATES = ("artifact-cas", "f02-platform-manifest", "f03-trust", "f04-package-index", "f06-compliance", "q00-intake", "q01-qualification", "rollback-set", "tuple-abi")


def main() -> int:
    data = SCHEMA.read_bytes()
    schema = json.loads(data)
    output_schema = deepcopy(schema)
    output_schema["$id"] = "https://omarchy.invalid/schemas/candidate-manifest/v1"
    output_schema["title"] = "F-05 immutable candidate manifest"
    output_schema["required"] = [*schema["required"], "candidate_digest"]
    output_schema["properties"]["version"] = {"const": "candidate-manifest/v1"}
    output_schema["properties"]["candidate_digest"] = {"$ref": "#/$defs/digest"}
    OUTPUT_SCHEMA.write_text(json.dumps(output_schema, indent=2) + "\n", encoding="utf-8")
    digest = "sha256:" + hashlib.sha256(data).hexdigest()
    output_digest = "sha256:" + hashlib.sha256(OUTPUT_SCHEMA.read_bytes()).hexdigest()
    lines = ['"""Generated F-05 binding; regenerate with tools/candidate/generate.py."""', "", f"INPUT_SCHEMA_DIGEST = {digest!r}", f"OUTPUT_SCHEMA_DIGEST = {output_digest!r}", "SCHEMA_DIGEST = INPUT_SCHEMA_DIGEST", "INPUT_VERSION = 'candidate-assembly-input/v1'", "OUTPUT_VERSION = 'candidate-manifest/v1'", "VERSION = INPUT_VERSION", "REQUIRED_GATE_IDS = ("]
    lines.extend(f"    {gate!r}," for gate in GATES)
    lines.append(")")
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"F05 GENERATE: PASS schema={digest} gates={len(GATES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
