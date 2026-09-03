#!/usr/bin/env python3
"""Detect policy-vocabulary and compliance-fixture drift."""

from __future__ import annotations

import json
import hashlib
import re
from pathlib import Path
import sys

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "src"))

from omarchy_platform.canonical import canonical_bytes
from omarchy_release_compliance.policy import vocabulary

ORACLE = {
    "candidate-transplant": "TARGET_BINDING_MISMATCH", "digest-mismatch": "DIGEST_MISMATCH",
    "direct-fetch-only": "REDISTRIBUTION_DIRECT_FETCH_ONLY", "duplicate-artifact-id": "DUPLICATE_ID",
    "fork-upstream-ambiguous": "FORK_UPSTREAM_AMBIGUOUS", "incomplete": "INCOMPLETE_INVENTORY",
    "manifest-transplant": "TARGET_BINDING_MISMATCH", "mutable-uri": "MUTABLE_SOURCE_URI",
    "notice-missing": "NOTICE_MISSING", "owner-decision-expired": "OWNER_DECISION_EXPIRED",
    "owner-decision-missing": "OWNER_DECISION_MISSING", "prohibited-redistribution": "REDISTRIBUTION_PROHIBITED",
    "provenance-missing": "PROVENANCE_MISSING", "sbom-missing": "SBOM_MISSING",
    "schema-set-transplant": "TARGET_BINDING_MISMATCH", "source-offer-expired": "SOURCE_OFFER_EXPIRED",
    "source-offer-missing": "SOURCE_OFFER_MISSING", "unknown-field": "UNKNOWN_FIELD",
    "unknown-redistribution": "REDISTRIBUTION_UNKNOWN", "unsorted-artifacts": "UNSORTED_IDS",
}
_PATH = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\[\d+\]|\.[A-Za-z_][A-Za-z0-9_]*)*(?:\.[A-Za-z_][A-Za-z0-9_]*)?$")


def main() -> int:
    policy_path = ROOT / "policy/vocabulary.json"
    manifest_path = ROOT / "fixtures/compliance/manifest.json"
    policy = json.loads(policy_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    failures: list[str] = []
    if set(manifest) != {"version", "accepted", "accepted_sha256", "policy_sha256", "generated_sha256", "hostile"}:
        failures.append("fixture manifest has an open top-level schema")
    if manifest.get("version") != "f06-fixtures/v1":
        failures.append("unsupported fixture manifest version")
    if canonical_bytes(policy) != canonical_bytes(vocabulary()):
        failures.append("policy/vocabulary.json differs from executable vocabulary")
    policy_hash = "sha256:" + hashlib.sha256(canonical_bytes(policy)).hexdigest()
    accepted_path = ROOT / "fixtures/compliance" / manifest.get("accepted", "")
    if manifest.get("policy_sha256") != policy_hash:
        failures.append("policy hash drift")
    if not accepted_path.exists() or manifest.get("accepted_sha256") != "sha256:" + hashlib.sha256(canonical_bytes(json.loads(accepted_path.read_text()))).hexdigest():
        failures.append("accepted fixture hash drift")
    hostile_dir = ROOT / "fixtures/compliance/hostile"
    names = [entry.get("name") for entry in manifest.get("hostile", [])]
    if len(names) != len(set(names)):
        failures.append("fixture manifest contains duplicate hostile names")
    actual = {path.stem for path in hostile_dir.glob("*.json")}
    if actual != set(names):
        failures.append("fixture manifest does not exactly cover hostile fixture files")
    if set(names) != set(ORACLE):
        failures.append("hostile fixture oracle/file set is not closed")
    if names != sorted(names):
        failures.append("hostile fixture manifest is not deterministically sorted")
    if manifest.get("accepted") != "accepted.json":
        failures.append("accepted fixture path is not closed")
    if len(names) < 15:
        failures.append("fewer than 15 hostile fixtures are declared")
    for entry in manifest["hostile"]:
        if set(entry) != {"name", "code", "sha256", "mutation", "path"}:
            failures.append(f"hostile manifest record schema drift: {entry.get('name')}")
            continue
        if entry["name"] not in ORACLE or entry["code"] != ORACLE.get(entry["name"]):
            failures.append(f"hostile oracle mismatch: {entry.get('name')}")
        if entry["mutation"] not in {"delete", "add", "set", "reverse", "duplicate"} or not _PATH.fullmatch(entry["path"]):
            failures.append(f"hostile mutation grammar drift: {entry.get('name')}")
        path = hostile_dir / f"{entry['name']}.json"
        if not path.exists():
            continue
        probe = json.loads(path.read_text())
        probe_without_hash = dict(probe)
        probe_without_hash.pop("sha256", None)
        if probe.get("code") != ORACLE.get(entry["name"]):
            failures.append(f"fixture code drift: {entry['name']}")
        if entry["sha256"] != "sha256:" + hashlib.sha256(canonical_bytes(probe_without_hash)).hexdigest():
            failures.append(f"fixture hash drift: {entry['name']}")
        if set(probe) != {"code", "mutation", "path", "value", "sha256"}:
            failures.append(f"fixture probe schema drift: {entry['name']}")
    generated_dir = ROOT / "fixtures/compliance/generated"
    generated_names = set(manifest.get("generated_sha256", {}))
    compliance_files = {p.name for p in (ROOT / "fixtures/compliance").iterdir()}
    if compliance_files != {"accepted.json", "manifest.json", "hostile", "generated"}:
        failures.append("compliance fixture top-level file set drift")
    if generated_names != {"NOTICE.txt", "source-offers.json", "attestation.json"} or not generated_dir.exists() or {p.name for p in generated_dir.iterdir()} != generated_names:
        failures.append("generated fixture file set drift")
    for name, expected_hash in manifest.get("generated_sha256", {}).items():
        path = generated_dir / name
        if not path.exists() or "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
            failures.append(f"generated hash drift: {name}")
    result = {"version": "f06-drift/v1", "decision": "reject" if failures else "allow", "failures": failures}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
