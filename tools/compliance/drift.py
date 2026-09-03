#!/usr/bin/env python3
"""Detect policy-vocabulary and compliance-fixture drift."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "src"))

from omarchy_platform.canonical import canonical_bytes
from omarchy_release_compliance.policy import vocabulary


def main() -> int:
    policy_path = ROOT / "policy/vocabulary.json"
    manifest_path = ROOT / "fixtures/compliance/manifest.json"
    policy = json.loads(policy_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    failures: list[str] = []
    if canonical_bytes(policy) != canonical_bytes(vocabulary()):
        failures.append("policy/vocabulary.json differs from executable vocabulary")
    hostile_dir = ROOT / "fixtures/compliance/hostile"
    names = [entry["name"] for entry in manifest["hostile"]]
    if len(names) != len(set(names)):
        failures.append("fixture manifest contains duplicate hostile names")
    actual = {path.stem for path in hostile_dir.glob("*.json")}
    if actual != set(names):
        failures.append("fixture manifest does not exactly cover hostile fixture files")
    if len(names) < 15:
        failures.append("fewer than 15 hostile fixtures are declared")
    for entry in manifest["hostile"]:
        path = hostile_dir / f"{entry['name']}.json"
        if not path.exists():
            continue
        probe = json.loads(path.read_text())
        if probe.get("code") != entry["code"]:
            failures.append(f"fixture code drift: {entry['name']}")
    result = {"version": "f06-drift/v1", "decision": "reject" if failures else "allow", "failures": failures}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
