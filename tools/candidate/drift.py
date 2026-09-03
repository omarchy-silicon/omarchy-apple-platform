#!/usr/bin/env python3
"""Offline F-05 schema, generated-binding, and fixture drift gate."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def fail(message: str) -> int:
    print(f"F05 DRIFT: FAIL {message}")
    return 1

from jsonschema import Draft202012Validator
from omarchy_candidate import CandidateAssemblyInput, CandidateManifest, digest_bytes, assemble_candidate  # noqa: E402
from omarchy_candidate.generated import INPUT_VERSION, OUTPUT_VERSION, REQUIRED_GATE_IDS, SCHEMA_DIGEST, VERSION  # noqa: E402
from omarchy_candidate.models import _VerifiedAuthority  # noqa: E402


def main() -> int:
    schema_path = ROOT / "schemas/candidate-assembly/v1/candidate-assembly.json"
    try:
        data = schema_path.read_bytes()
        schema = json.loads(data)
    except (OSError, ValueError):
        print("F05 DRIFT: FAIL schema is unreadable")
        return 1
    actual = "sha256:" + hashlib.sha256(data).hexdigest()
    if actual != SCHEMA_DIGEST:
        print("F05 DRIFT: FAIL generated binding is stale")
        return 1
    if schema.get("additionalProperties") is not False or schema.get("$defs", {}).get("gate", {}).get("additionalProperties") is not False:
        print("F05 DRIFT: FAIL candidate schema is not closed")
        return 1
    if VERSION != INPUT_VERSION or OUTPUT_VERSION != "candidate-manifest/v1" or tuple(REQUIRED_GATE_IDS) != tuple(sorted(REQUIRED_GATE_IDS)) or len(REQUIRED_GATE_IDS) != 9:
        print("F05 DRIFT: FAIL generated gate census drift")
        return 1
    fixture = json.loads((ROOT / "fixtures/candidate/accepted-input.json").read_text())
    try:
        Draft202012Validator(schema).validate(fixture)
        CandidateAssemblyInput.from_dict(fixture)
        output_schema = json.loads((ROOT / "schemas/candidate-assembly/v1/candidate-manifest.json").read_text())
        # The output is checked by the model round-trip; schema validation also
        # confirms the output uses the distinct manifest contract.
        class Authority:
            def verify_canonical(self, kind, source_bytes, **kwargs):
                return _VerifiedAuthority(kind, kwargs["subject"], kwargs["digest"], kwargs["board_id"], kwargs["profile_id"], kwargs["channel"], "2099-01-01T00:00:00Z", f"drift:{kind}", digest_bytes(source_bytes), kwargs["schema_set_digest"])
        class Artifacts:
            def read(self, digest):
                data = (ROOT / "fixtures/candidate/artifact.bin").read_bytes()
                if digest != digest_bytes(data):
                    raise OSError("missing fixture member")
                return data
        manifest = assemble_candidate(fixture, authority=Authority(), artifacts=Artifacts(), verification_time="2026-09-03T00:00:00Z")
        Draft202012Validator(output_schema).validate(manifest.to_dict())
        CandidateManifest.from_dict(manifest.to_dict())
        for hostile in sorted((ROOT / "fixtures/candidate/hostile").glob("*.json")):
            probe = json.loads(hostile.read_text())
            candidate = json.loads(json.dumps(fixture))
            bits = probe["path"].replace("]", "").replace("[", ".").split(".")
            cursor = candidate
            for bit in bits[:-1]:
                cursor = cursor[int(bit)] if bit.isdigit() else cursor[bit]
            if probe["mutation"] == "delete":
                cursor.pop(int(bits[-1]) if bits[-1].isdigit() else bits[-1])
            else:
                cursor[bits[-1]] = probe["value"]
            try:
                Draft202012Validator(schema).validate(candidate)
                CandidateAssemblyInput.from_dict(candidate)
                assemble_candidate(candidate, authority=Authority(), artifacts=Artifacts(), verification_time="2026-09-03T00:00:00Z")
            except Exception:
                continue
            return fail(f"hostile fixture unexpectedly validated: {hostile.name}")
    except Exception as error:
        return fail(f"fixture/model drift: {type(error).__name__}")
    print(f"F05 DRIFT: PASS schema={actual} gates={len(REQUIRED_GATE_IDS)} input={INPUT_VERSION} output={OUTPUT_VERSION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
