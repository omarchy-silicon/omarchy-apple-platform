#!/usr/bin/env python3
"""Fail-closed schema set and generated-constant drift checker."""

import json
import sys
from hashlib import sha256
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse

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
LOCK_KEYS = {"lock_schema", "schema_set_id", "schema_entries", "vocabulary", "canonicalization", "limits", "generator_inputs", "parser_inputs", "toolchain_inputs"}
ENTRY_KEYS = {"schema_id", "schema_version", "source_path", "source_digest", "reference_digests"}
REFERENCE_KEYS = {"reference_path", "digest"}


def _local_reference_paths(source_path: str) -> list[str]:
    document = json.loads((ROOT / source_path).read_text(encoding="utf-8"))
    base = document["$id"]
    found = set()

    def walk(value):
        if isinstance(value, dict):
            ref = value.get("$ref")
            if isinstance(ref, str):
                target, _fragment = urldefrag(urljoin(base, ref))
                parsed = urlparse(target)
                if parsed.scheme != "https" or parsed.netloc != "omarchy.local" or not parsed.path.startswith("/schemas/"):
                    raise SystemExit(f"DRIFT: reference escapes local schema set: {source_path}: {ref}")
                candidate = (ROOT / parsed.path.removeprefix("/")).resolve()
                try:
                    relative = candidate.relative_to(ROOT.resolve()).as_posix()
                except ValueError:
                    raise SystemExit(f"DRIFT: reference escapes repository: {source_path}: {ref}") from None
                if relative not in EXPECTED.values() or not candidate.is_file():
                    raise SystemExit(f"DRIFT: reference target is not a declared schema: {source_path}: {ref}")
                found.add(relative)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(document)
    return sorted(found)


def main() -> int:
    lock_path = ROOT / "schemas/schema-input.lock"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if set(lock) != LOCK_KEYS:
        raise SystemExit("DRIFT: schema-input.lock has unexpected or missing keys")
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
        if set(entry) != ENTRY_KEYS:
            raise SystemExit(f"DRIFT: malformed schema entry {entry.get('schema_id', '$')}")
        expected_path = EXPECTED.get(entry["schema_id"])
        if expected_path != entry["source_path"]:
            raise SystemExit(f"DRIFT: wrong path for {entry['schema_id']}")
        actual = "sha256:" + sha256((ROOT / expected_path).read_bytes()).hexdigest()
        if actual != entry["source_digest"]:
            raise SystemExit(f"DRIFT: source digest mismatch for {expected_path}")
        expected_refs = [{"reference_path": path, "digest": "sha256:" + sha256((ROOT / path).read_bytes()).hexdigest()} for path in _local_reference_paths(expected_path)]
        if any(set(reference) != REFERENCE_KEYS for reference in entry["reference_digests"]):
            raise SystemExit(f"DRIFT: malformed reference digest entry for {expected_path}")
        if entry["reference_digests"] != expected_refs:
            raise SystemExit(f"DRIFT: reference digest mismatch for {expected_path}")
    output_lock = json.loads((ROOT / "bindings/generated-output.lock").read_text(encoding="utf-8"))
    if set(output_lock) != {"lock_schema", "schema_set_digest", "generated_entries"} or output_lock["lock_schema"] != "generated-output-lock/v1" or output_lock["generated_entries"] != []:
        raise SystemExit("DRIFT: generated-output.lock is not the exact residual foundation lock")
    computed = schema_set_digest(lock)
    if computed != SCHEMA_SET_DIGEST or computed != output_lock["schema_set_digest"]:
        raise SystemExit("DRIFT: schema-set digest does not match constants and output lock")
    print(f"DRIFT: PASS schema_set_digest={computed}; generator_inputs=[] (residual); parser_inputs=[] (residual); toolchain_inputs=[] (residual)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
