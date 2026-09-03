#!/usr/bin/env python3
"""Verify Q-01 resource, inventory, and fixture determinism."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
from omarchy_qualification.canonical import canonical_bytes, digest_bytes
from omarchy_qualification.validate import validate_inventory_file, validate_record_file
from tools.qualification.generate import build_outputs


def main() -> int:
    inv = ROOT / "data/qualification/inventory.json"
    fixture = ROOT / "fixtures/qualification/j313-unknown.json"
    outputs = build_outputs()
    for relative, expected in outputs.items():
        actual = (ROOT / relative).read_bytes()
        if actual != expected:
            raise SystemExit(f"DRIFT: generated artifact differs: {relative}")
    validate_inventory_file(inv)
    result = validate_record_file(fixture, inv)
    expected_inv = json.loads(outputs["data/qualification/inventory.json"])
    if result["outcome"] != "UNKNOWN" or result["admission"] != "NOT_QUALIFIED":
        raise SystemExit("DRIFT: initial fixture must remain UNKNOWN/NOT_QUALIFIED")
    if json.loads(fixture.read_bytes())["physical_units"] or json.loads(fixture.read_bytes())["evidence"]:
        raise SystemExit("DRIFT: initial fixture contains physical evidence")
    print(f"DRIFT: PASS inventory_digest={digest_bytes(canonical_bytes(expected_inv))} outcome=UNKNOWN admission=NOT_QUALIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
