"""Offline F-03 policy, resource, and fixture drift gate."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from omarchy_platform.canonical import canonical_bytes
from omarchy_trust.constants import ROLE_LIMIT_SECONDS, ROLE_TO_SIGNER


def fail(message: str) -> None:
    raise SystemExit("TRUST DRIFT: " + message)


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"cannot load {path}: {error}")


def main() -> int:
    anchor_paths = [ROOT / "policy/trust/root-anchors.json", ROOT / "src/omarchy_trust/resources/root-anchors.json"]
    anchors = [load(path) for path in anchor_paths]
    if anchors[0] != anchors[1] or anchors[0] != {"format": "omarchy-trust-anchors/v1", "keys": [], "status": "UNPROVISIONED", "threshold": 3}:
        fail("root anchors must remain explicitly UNPROVISIONED")
    policy = load(ROOT / "policy/trust/role-policy.json")
    packaged_policy = load(ROOT / "src/omarchy_trust/resources/role-policy.json")
    if packaged_policy != policy:
        fail("packaged role policy drift")
    roles = {item["role"]: item for item in policy.get("roles", [])}
    if set(roles) != set(ROLE_LIMIT_SECONDS) or any(roles[name]["max_lifetime_seconds"] != seconds for name, seconds in ROLE_LIMIT_SECONDS.items()):
        fail("role lifetime policy drift")
    if any(roles[name]["threshold"] not in {2, 3} for name in roles):
        fail("role threshold policy drift")
    manifest = load(ROOT / "fixtures/trust/fixture-manifest.json")
    vectors = manifest.get("vectors")
    if manifest.get("format") != "omarchy-trust-fixtures/v1" or not isinstance(vectors, list) or len(vectors) != 19:
        fail("fixture manifest shape drift")
    names = []
    for item in vectors:
        if set(item) != {"name", "expected"} or not re.fullmatch(r"[a-z0-9-]+\.json", item["name"]):
            fail("fixture manifest entry drift")
        names.append(item["name"])
        fixture = ROOT / "fixtures/trust" / item["name"]
        if not fixture.is_file() or load(fixture) != {"expected": item["expected"], "format": "omarchy-trust-fixture/v1", "name": item["name"]}:
            fail(f"fixture mismatch: {item['name']}")
    if names != sorted(names) or len(set(names)) != len(names):
        fail("fixture names must be sorted and unique")
    if canonical_bytes(manifest) != (ROOT / "fixtures/trust/fixture-manifest.json").read_bytes().rstrip(b"\n"):
        fail("fixture manifest is not canonical")
    for path in [*anchor_paths, ROOT / "policy/trust/role-policy.json", ROOT / "src/omarchy_trust/resources/role-policy.json", ROOT / "policy/trust/trust-bundle.schema.json", ROOT / "policy/trust/replay-state.schema.json", *[ROOT / "fixtures/trust" / name for name in names]]:
        if re.search(rb"BEGIN (?:RSA|OPENSSH|EC|ED25519) PRIVATE KEY|(?:AKIA|ghp_)[A-Za-z0-9_-]{12,}", path.read_bytes()):
            fail(f"secret-like material in {path}")
    print(f"TRUST DRIFT PASS: {len(vectors)} fixture vectors, UNPROVISIONED anchors, {len(ROLE_TO_SIGNER)} F-02 mappings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
