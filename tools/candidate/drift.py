#!/usr/bin/env python3
"""Offline F-05 schema, generated-binding, and fixture drift gate."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from omarchy_candidate.generated import REQUIRED_GATE_IDS, SCHEMA_DIGEST, VERSION  # noqa: E402


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
    if VERSION != "candidate-assembly/v1" or tuple(REQUIRED_GATE_IDS) != tuple(sorted(REQUIRED_GATE_IDS)) or len(REQUIRED_GATE_IDS) != 9:
        print("F05 DRIFT: FAIL generated gate census drift")
        return 1
    print(f"F05 DRIFT: PASS schema={actual} gates={len(REQUIRED_GATE_IDS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
