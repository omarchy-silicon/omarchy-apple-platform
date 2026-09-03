#!/usr/bin/env python3
"""Materialize deterministic, evidence-only release compliance artifacts."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "src"))

from omarchy_platform.canonical import canonical_bytes, domain_digest
from omarchy_platform.strictjson import parse
from omarchy_release_compliance.engine import _set_test_clock, attest, evaluate

FIXED_CLOCK = datetime(2026, 1, 1, tzinfo=timezone.utc)
OUT = ROOT / "fixtures/compliance/generated"


def _load_bundle() -> dict:
    return parse((ROOT / "fixtures/compliance/accepted.json").read_bytes())


def outputs() -> dict[str, bytes]:
    bundle = _load_bundle()
    _set_test_clock(lambda: FIXED_CLOCK)
    result = evaluate(bundle)
    if result["decision"] != "allow":
        raise ValueError("accepted fixture no longer evaluates as allow")
    header = [
        "F-06 NOTICE BUNDLE v1",
        f"inventory_digest={result['inventory_digest']}",
        f"policy_digest={result['policy_digest']}",
        f"candidate_digest={result['candidate_digest']}",
        f"manifest_digest={result['manifest_digest']}",
        f"schema_set_digest={result['schema_set_digest']}",
        "signed=false",
        "trusted=false",
        "promotable=false",
        "",
    ]
    notices = []
    for artifact in bundle["artifacts"]:
        for notice in artifact["copyright_notice"]:
            notices.append(f"[{artifact['artifact_id']}/{notice['id']}] {notice['text']}")
    notice_bytes = ("\n".join(header + sorted(notices)) + "\n").encode("utf-8")
    offers = {
        "version": "f06-source-offers/v1",
        "signed": False,
        "trusted": False,
        "promotable": False,
        "inventory_digest": result["inventory_digest"],
        "policy_digest": result["policy_digest"],
        "candidate_digest": result["candidate_digest"],
        "manifest_digest": result["manifest_digest"],
        "schema_set_digest": result["schema_set_digest"],
        "offers": [
            {"artifact_id": a["artifact_id"], "location": a["source_offer"]["location"], "digest": a["source_offer"]["digest"], "expires_at": a["source_offer"]["expires_at"]}
            for a in bundle["artifacts"]
        ],
    }
    return {"NOTICE.txt": notice_bytes, "source-offers.json": canonical_bytes(offers), "attestation.json": attest(bundle)}


def main(argv: list[str] | None = None) -> int:
    mode = "check" if not argv else argv[0]
    if mode not in {"check", "write"}:
        print(json.dumps({"version": "f06-generated/v1", "decision": "reject", "failures": ["mode must be check or write"]}, separators=(",", ":")))
        return 2
    expected = outputs()
    failures = []
    for name, data in expected.items():
        path = OUT / name
        if mode == "write":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        elif not path.exists() or path.read_bytes() != data:
            failures.append(name)
    if mode == "write":
        return 0
    manifest = json.loads((ROOT / "fixtures/compliance/manifest.json").read_text())
    for name, expected_hash in manifest.get("generated_sha256", {}).items():
        actual = hashlib.sha256(expected[name]).hexdigest()
        if "sha256:" + actual != expected_hash:
            failures.append(f"manifest hash {name}")
    print(json.dumps({"version": "f06-generated/v1", "decision": "reject" if failures else "allow", "failures": failures}, sort_keys=True, separators=(",", ":")))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
