import base64
import copy
import json
from pathlib import Path

import pytest

from omarchy_qualification.canonical import digest_bytes
from omarchy_qualification.errors import QualificationValidationError
from omarchy_qualification.validate import load_inventory, validate_inventory, validate_record, validate_record_file

ROOT = Path(__file__).parents[1]
INVENTORY = ROOT / "data/qualification/inventory.json"
FIXTURE = ROOT / "fixtures/qualification/j313-unknown.json"


def values():
    return load_inventory(INVENTORY), json.loads(FIXTURE.read_text())


def rejects(record, code, inventory=None):
    if inventory is None:
        inventory, _ = values()
    with pytest.raises(QualificationValidationError, match=code):
        validate_record(record, inventory)


def test_initial_fixture_is_unknown_and_not_qualified():
    inventory, record = values()
    validate_record(record, inventory)
    assert record["outcome"] == "UNKNOWN"
    assert record["admission"] == "NOT_QUALIFIED"
    assert record["physical_units"] == []
    assert record["evidence"] == []
    assert len(record["capabilities"]) == 27


def test_inventory_has_closed_full_capability_criteria():
    inventory, _ = values()
    expected = {item["capability_id"] for item in inventory["boards"][0]["capabilities"]}
    assert len(expected) == 27
    assert all(item["evidence_modality"] in {"automated", "human-observed", "automated-and-human"} for item in inventory["boards"][0]["capabilities"])


def test_missing_capability_rejected():
    inventory, record = values()
    record["capabilities"].pop()
    rejects(record, "MISSING_CAPABILITIES")


def test_selector_profile_and_f02_bindings_rejected():
    inventory, record = values()
    record["board_selector"] = "j274"
    rejects(record, "BOARD_SELECTOR_MISMATCH")
    inventory, record = values()
    record["profile_id"] = "profile:j274"
    rejects(record, "PROFILE_MISMATCH")
    inventory, record = values()
    record["f02_schema_set_digest"] = "sha256:" + "2" * 64
    rejects(record, "F02_SCHEMA_MISMATCH")


def test_stale_schema_digest_and_n_a_contradiction_rejected():
    inventory, record = values()
    record["schema_set_digest"] = "sha256:" + "3" * 64
    rejects(record, "SCHEMA_DIGEST_MISMATCH")
    inventory, record = values()
    inventory["boards"][0]["capabilities"][0]["applicability"] = "not-applicable"
    rejects(record, "APPLICABILITY_CONTRADICTION", inventory)


def test_simulated_physical_and_missing_bytes_rejected():
    inventory, record = values()
    payload = b"simulated"
    record["evidence"] = [{"evidence_id": "evidence:fake", "bytes_b64": base64.b64encode(payload).decode(), "content_digest": digest_bytes(payload), "modality": "automated", "physical": True, "unit_ids": [], "observed_at": "2026-09-03T00:00:00Z", "tool_version": "tool-1", "redaction_ref": None}]
    rejects(record, "SIMULATED_AS_PHYSICAL")
    record["evidence"][0]["modality"] = "human-observed"
    rejects(record, "PHYSICAL_UNIT_COUNT", inventory)


def test_duplicate_and_reordered_ids_rejected():
    inventory, record = values()
    record["capabilities"][0], record["capabilities"][1] = record["capabilities"][1], record["capabilities"][0]
    rejects(record, "UNSORTED_COLLECTION")


def test_current_intake_digest_is_bound(tmp_path):
    inventory, record = values()
    record["intake_dataset_digest"] = "sha256:" + "4" * 64
    record_path = tmp_path / "record.json"
    record_path.write_bytes(json.dumps(record).encode())
    with pytest.raises(QualificationValidationError, match="INTAKE_DIGEST_MISMATCH"):
        validate_record_file(record_path, INVENTORY, intake_manifest=ROOT / "data/intake/manifest.json")


def test_full_and_qualified_are_fail_closed_without_manifest(tmp_path):
    inventory, record = values()
    record["outcome"] = "FULL"
    record["admission"] = "QUALIFIED"
    record_path = tmp_path / "record.json"
    record_path.write_bytes(json.dumps(record).encode())
    with pytest.raises(QualificationValidationError, match="MANIFEST_REQUIRED"):
        validate_record_file(record_path, INVENTORY)


def test_physical_identity_duplicates_rejected():
    inventory, record = values()
    unit = {"unit_id": "unit:a", "identity_digest": "sha256:" + "a" * 64, "board_id": "apple:j313", "profile_id": "profile:j313-macbookair10-1", "inventory_tag": "tag:a", "serial_pseudonym": "serial:a"}
    second = {**unit, "unit_id": "unit:b"}
    record["physical_units"] = [unit, second]
    rejects(record, "DUPLICATE_PHYSICAL_IDENTITY", inventory)


def test_inventory_rejects_alias_or_family_selector():
    inventory, _ = values()
    inventory["boards"][0]["selector"] = "m1"
    with pytest.raises(QualificationValidationError, match="SCHEMA_INVALID"):
        validate_inventory(inventory)


def test_full_requires_explicit_verification_time():
    inventory, record = values()
    record["outcome"] = "FULL"
    record["admission"] = "NOT_QUALIFIED"
    with pytest.raises(QualificationValidationError, match="VERIFICATION_TIME_REQUIRED"):
        validate_record(record, inventory)


def _full_fixture():
    inventory, record = values()
    manifest = json.loads((ROOT / "fixtures/accepted/platform-manifest-v1.json").read_text())
    for criterion in inventory["boards"][0]["capabilities"]:
        criterion["applicability"] = "applicable"
    record.update(outcome="FULL", admission="QUALIFIED", residuals=[], validated_at="2026-01-04T00:00:00Z", manifest_id="fixture-platform-manifest")
    record["redaction"]["residuals"] = []
    record["physical_units"] = [{"unit_id": f"unit:{i}", "identity_digest": "sha256:" + str(i) * 64, "board_id": "apple:j313", "profile_id": "profile:j313-macbookair10-1", "inventory_tag": f"tag:{i}", "serial_pseudonym": f"serial:{i}"} for i in (1, 2)]
    record["capabilities"] = []
    record["evidence"] = []
    for criterion in inventory["boards"][0]["capabilities"]:
        cid = criterion["capability_id"]
        payload = cid.encode()
        evidence_id = f"evidence:{cid}"
        record["capabilities"].append({"capability_id": cid, "applicability": "applicable", "status": "pass", "evidence_ids": [evidence_id], "threshold_met": True})
        record["evidence"].append({"evidence_id": evidence_id, "bytes_b64": base64.b64encode(payload).decode(), "content_digest": digest_bytes(payload), "modality": "automated-and-human", "physical": True, "unit_ids": ["unit:1", "unit:2"], "observed_at": "2026-01-02T00:00:00Z", "tool_version": "tool-1", "redaction_ref": None})
    manifest["payload"]["board_targets"] = ["apple:j313"]
    manifest["payload"]["board_identities"][0].update(board_id="apple:j313", linux_compatible="apple,j313")
    manifest["payload"]["qualification_bindings"][0].update(board_id="apple:j313", qualification_record_id=record["record_id"])
    from omarchy_platform.canonical import payload_digest
    record["manifest_digest"] = payload_digest(manifest["payload"])
    record["firmware_baseline"] = {"firmware_id": "firmware-bundle", "version": "1.0.0", "build": manifest["payload"]["components"]["firmware_bundle"]["source_digest"], "captured_at": "2026-01-02T00:00:00Z"}
    return inventory, record, manifest


def test_manifest_expiry_and_stale_firmware_rejected(tmp_path):
    inventory, record, manifest = _full_fixture()
    manifest["payload"]["expires_at"] = "2026-01-03T00:00:00Z"
    from omarchy_platform.canonical import payload_digest
    record["manifest_digest"] = payload_digest(manifest["payload"])
    record_path, inventory_path, manifest_path = tmp_path / "record.json", tmp_path / "inventory.json", tmp_path / "manifest.json"
    inventory_path.write_text(json.dumps(inventory)); record_path.write_text(json.dumps(record)); manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(QualificationValidationError, match="MANIFEST_EXPIRED"):
        validate_record_file(record_path, inventory_path, manifest=manifest_path, intake_manifest=ROOT / "data/intake/manifest.json", verification_time="2026-01-04T00:00:00Z")
    inventory, record, manifest = _full_fixture()
    record["firmware_baseline"]["captured_at"] = "2020-01-02T00:00:00Z"
    record_path.write_text(json.dumps(record)); manifest_path.write_text(json.dumps(manifest)); inventory_path.write_text(json.dumps(inventory))
    with pytest.raises(QualificationValidationError, match="FIRMWARE_BASELINE_WINDOW"):
        validate_record_file(record_path, inventory_path, manifest=manifest_path, intake_manifest=ROOT / "data/intake/manifest.json", verification_time="2026-01-04T00:00:00Z")
