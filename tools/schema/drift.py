#!/usr/bin/env python3
"""Fail-closed schema set and generated-constant drift checker."""

import json
import sys
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from omarchy_platform.canonical import domain_digest, schema_set_digest  # noqa: E402
from omarchy_platform.constants import AUTHENTICATED_PAYLOAD_TYPES, LIMITS, SCHEMA_INPUT_IDS, SCHEMA_SET_DIGEST  # noqa: E402

EXPECTED = {
    "common/v1": "schemas/common/v1/common.schema.json",
    "vocabularies/v1": "schemas/common/v1/vocabularies.schema.json",
    "signed-document/v1": "schemas/signed-document/v1/signed-document.schema.json",
    **{f"{name}/v1": f"schemas/{name}/v1/{name}.schema.json" for name in (
        "board-registry", "platform-manifest", "installer-plan", "qualification-record",
        "boot-health", "owner-approval", "boot-success-mark", "dtb-mutation-envelope")},
}


def main() -> int:
    lock_path = ROOT / "schemas/schema-input.lock"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if tuple(lock["vocabulary"]["payload_types"]) != AUTHENTICATED_PAYLOAD_TYPES:
        raise SystemExit("DRIFT: vocabulary does not match generated constants")
    vocabulary = lock["vocabulary"]
    vocabulary_preimage = {key: value for key, value in vocabulary.items() if key != "vocabulary_digest"}
    expected_vocabulary_digest = domain_digest("omarchy-authenticated-payload-vocabulary/v1", vocabulary_preimage)
    if expected_vocabulary_digest != vocabulary["vocabulary_digest"]:
        raise SystemExit("DRIFT: vocabulary digest mismatch")
    if any(lock["limits"][name] != value for name, value in LIMITS.items()):
        raise SystemExit("DRIFT: parser limits do not match generated constants")
    canonical_source = "sha256:" + sha256((ROOT / "src/omarchy_platform/canonical.py").read_bytes()).hexdigest()
    if canonical_source != lock["canonicalization"]["implementation_source_digest"]:
        raise SystemExit("DRIFT: canonicalization implementation source digest mismatch")
    if tuple(entry["schema_id"] for entry in lock["schema_entries"]) != SCHEMA_INPUT_IDS:
        raise SystemExit("DRIFT: schema entry IDs/path set is incomplete or out of order")
    if any(lock[name] for name in ("generator_inputs", "parser_inputs", "toolchain_inputs")):
        raise SystemExit("DRIFT: non-empty generator/parser/toolchain inputs require their pinned residual implementation")
    for entry in lock["schema_entries"]:
        expected_path = EXPECTED.get(entry["schema_id"])
        if expected_path != entry["source_path"]:
            raise SystemExit(f"DRIFT: wrong path for {entry['schema_id']}")
        actual = "sha256:" + sha256((ROOT / expected_path).read_bytes()).hexdigest()
        if actual != entry["source_digest"]:
            raise SystemExit(f"DRIFT: source digest mismatch for {expected_path}")
    computed = schema_set_digest(lock)
    if computed != SCHEMA_SET_DIGEST or computed != json.loads((ROOT / "bindings/generated-output.lock").read_text())["schema_set_digest"]:
        raise SystemExit("DRIFT: schema-set digest does not match constants and output lock")
    print(f"DRIFT: PASS schema_set_digest={computed}; generator_inputs=[] (residual); parser_inputs=[] (residual); toolchain_inputs=[] (residual)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
