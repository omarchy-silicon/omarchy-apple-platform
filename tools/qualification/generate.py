#!/usr/bin/env python3
"""Generate the deterministic Q-01 inventory and intentionally unqualified fixture."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from omarchy_qualification.canonical import canonical_bytes, digest_bytes
from omarchy_platform.constants import SCHEMA_SET_DIGEST as F02_SCHEMA_SET_DIGEST

CAPABILITIES = ("audio", "backlight", "bluetooth", "boot", "camera", "charging-battery", "device-tree", "ethernet", "external-display", "firmware", "gpu", "internal-display", "kernel", "keyboard", "media", "memory", "nvme", "recovery", "sd", "suspend-resume", "thermal-fan", "thunderbolt", "touch-id-sep", "trackpad", "usb", "virtualization", "wifi")
SCHEMA = "qualification-board-inventory/v1"
NOW = "2026-09-03T00:00:00Z"


def schema_digest() -> str:
    values = []
    for name in ("board-inventory-v1.schema.json", "qualification-record-q01-v1.schema.json"):
        values.append(json.loads((ROOT / "src/omarchy_qualification/resources" / name).read_text(encoding="utf-8")))
    return digest_bytes(canonical_bytes(values))


def inventory() -> dict:
    return {"schema": SCHEMA, "schema_set_digest": schema_digest(), "inventory_id": "omarchy-apple-silicon-qualification", "revision": "2026-09-03.r1", "boards": [{"board_id": "apple:j313", "selector": "j313", "profile_ids": ["profile:j313-macbookair10-1"], "capabilities": [{"capability_id": cap, "applicability": "unknown", "evidence_modality": "automated-and-human", "threshold": 2} for cap in CAPABILITIES]}]}


def record(inv: dict) -> dict:
    q00 = json.loads((ROOT / "data/intake/manifest.lock.json").read_text(encoding="utf-8"))
    raw = json.loads((ROOT / "data/intake/records/apple-j313-r1.json").read_text(encoding="utf-8"))
    from omarchy_intake.canonical import intake_digest
    record_digest = intake_digest("record/v1", raw)
    capabilities = [{"capability_id": cap, "applicability": "unknown", "status": "unknown", "evidence_ids": [], "threshold_met": False} for cap in CAPABILITIES]
    return {"schema": "qualification-record/q01-v1", "schema_set_digest": inv["schema_set_digest"], "record_id": "qualification:apple-j313:2026-09-03.r1", "board_id": "apple:j313", "board_selector": "j313", "profile_id": "profile:j313-macbookair10-1", "intake_dataset_digest": q00["dataset_digest"], "intake_record_id": "apple:j313", "intake_record_digest": record_digest, "f02_schema_set_digest": F02_SCHEMA_SET_DIGEST, "manifest_id": "manifest:not-qualified", "manifest_digest": "sha256:" + "1" * 64, "firmware_baseline": {"firmware_id": "unknown", "version": "unknown", "build": "unknown", "captured_at": NOW}, "physical_units": [], "capabilities": capabilities, "evidence": [], "tool_versions": {"schema": "q01-v1", "validator": "omarchy-qualification-1.0"}, "redaction": {"policy": "none", "applied": False, "residuals": ["physical-evidence-not-collected"]}, "residuals": [{"residual_id": "firmware-baseline", "reason": "Firmware baseline is unknown until lab capture.", "state": "unknown"}, {"residual_id": "physical-evidence", "reason": "No physical units or evidence have been collected.", "state": "blocked"}], "issued_at": NOW, "validated_at": NOW, "outcome": "UNKNOWN", "admission": "NOT_QUALIFIED"}


def main() -> int:
    inv = inventory()
    (ROOT / "data/qualification").mkdir(exist_ok=True)
    (ROOT / "data/qualification/inventory.json").write_bytes(canonical_bytes(inv) + b"\n")
    (ROOT / "fixtures/qualification").mkdir(exist_ok=True)
    rec = record(inv)
    (ROOT / "fixtures/qualification/j313-unknown.json").write_bytes(canonical_bytes(rec) + b"\n")
    print(json.dumps({"inventory": "data/qualification/inventory.json", "fixture": "fixtures/qualification/j313-unknown.json", "schema_set_digest": inv["schema_set_digest"], "outcome": rec["outcome"], "admission": rec["admission"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
