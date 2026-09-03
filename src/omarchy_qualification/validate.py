"""Fail-closed Q-01 inventory and qualification-record validation.

Q-00 remains the authority for intake observations and F-02 remains the
authority for authenticated document envelopes. This module only checks the
Q-01 physical qualification seam and exact references to those authorities.
"""

from __future__ import annotations

import base64
import json
import re
from datetime import datetime, timedelta
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from omarchy_intake.errors import IntakeValidationError
from omarchy_intake.validate import validate_dataset_file
from omarchy_platform.constants import SCHEMA_SET_DIGEST as F02_SCHEMA_SET_DIGEST
from omarchy_platform.errors import SchemaError
from omarchy_platform.validate import validate_foundation_document

from .canonical import canonical_bytes, digest_bytes
from .errors import QualificationValidationError

_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_ID = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,127}$")
_BOARD = re.compile(r"^apple:[a-z0-9][a-z0-9-]{0,63}$")
_SELECTOR = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
_PROFILE = re.compile(r"^profile:[a-z0-9][a-z0-9._:-]{0,127}$")
_UTC = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?Z$")
_CAPS = frozenset({
    "audio", "backlight", "bluetooth", "camera", "charging-battery", "ethernet",
    "external-display", "gpu", "internal-display", "keyboard", "media", "memory",
    "nvme", "recovery", "sd", "suspend-resume", "thermal-fan", "thunderbolt",
    "touch-id-sep", "trackpad", "usb", "virtualization", "wifi", "boot", "firmware",
    "kernel", "device-tree",
})
_MODALITIES = frozenset({"automated", "human-observed", "automated-and-human"})
_STATUSES = frozenset({"pass", "fail", "unknown"})
_MAX_INPUT_BYTES = 1_048_576
_MAX_FIRMWARE_AGE_DAYS = 180
_MAX_EVIDENCE_AGE_DAYS = 180


def _fail(code: str, path: str, message: str) -> None:
    raise QualificationValidationError(code, path, message)


def _closed(value: Any, fields: set[str], path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail("SCHEMA_INVALID", path, "object required")
    unknown = sorted(set(value) - fields)
    if unknown:
        _fail("UNKNOWN_FIELD", f"{path}.{unknown[0]}", "field is not in the closed schema")
    missing = sorted(fields - set(value))
    if missing:
        _fail("MISSING_FIELD", f"{path}.{missing[0]}", "required field is missing")
    return value


def _str(value: Any, path: str, pattern: re.Pattern[str] | None = None) -> str:
    if not isinstance(value, str) or (pattern and not pattern.fullmatch(value)):
        _fail("SCHEMA_INVALID", path, "invalid string")
    return value


def _digest(value: Any, path: str) -> str:
    return _str(value, path, _DIGEST)


def _timestamp(value: Any, path: str) -> str:
    value = _str(value, path, _UTC)
    try:
        datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError:
        _fail("SCHEMA_INVALID", path, "invalid UTC timestamp")
    return value


def _sorted_unique(items: list[Any], path: str, key) -> None:
    keys = [key(item) for item in items]
    if keys != sorted(keys):
        _fail("UNSORTED_COLLECTION", path, "collection must be lexicographically sorted")
    if len(keys) != len(set(keys)):
        _fail("DUPLICATE_SEMANTIC_KEY", path, "duplicate semantic key")


def _schema(name: str) -> dict[str, Any]:
    try:
        raw = resources.files("omarchy_qualification").joinpath("resources", name).read_text(encoding="utf-8")
        return json.loads(raw)
    except (OSError, ValueError, ModuleNotFoundError) as error:
        _fail("TOOLING_BLOCK", "$", f"Q-01 schema unavailable: {error}")


def q01_schema_set_digest() -> str:
    """Digest the exact packaged Q-01 schema inputs in stable order."""
    return digest_bytes(canonical_bytes([_schema("board-inventory-v1.schema.json"), _schema("qualification-record-q01-v1.schema.json")]))


def _schema_validate(value: dict[str, Any], schema_name: str) -> None:
    errors = sorted(Draft202012Validator(_schema(schema_name)).iter_errors(value), key=lambda e: list(e.absolute_path))
    if errors:
        error = errors[0]
        path = "$" + "".join(f"[{p}]" if isinstance(p, int) else f".{p}" for p in error.absolute_path)
        _fail("UNKNOWN_FIELD" if error.validator == "additionalProperties" else "SCHEMA_INVALID", path, error.message)


def _read_json(path: str | Path) -> Any:
    file_path = Path(path)
    try:
        if file_path.stat().st_size > _MAX_INPUT_BYTES:
            _fail("RESOURCE_LIMIT", "$", "input exceeds the bounded byte limit")
        raw = file_path.read_bytes()
    except OSError:
        _fail("IO_FAILURE", "$", "input could not be read")
    if len(raw) > _MAX_INPUT_BYTES:
        _fail("RESOURCE_LIMIT", "$", "input exceeds the bounded byte limit")
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        output: dict[str, Any] = {}
        for key, item in items:
            if key in output:
                _fail("DUPLICATE_KEY", "$", "duplicate object key")
            output[key] = item
        return output
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    except QualificationValidationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError):
        _fail("MALFORMED_JSON", "$", "input is not one complete JSON value")


def load_inventory(path: str | Path) -> dict[str, Any]:
    value = _read_json(path)
    validate_inventory(value)
    return value


def validate_inventory_file(path: str | Path) -> dict[str, Any]:
    return load_inventory(path)


def validate_inventory(value: Any) -> None:
    _schema_validate(value, "board-inventory-v1.schema.json")
    inventory = _closed(value, {"schema", "schema_set_digest", "inventory_id", "revision", "boards"}, "$")
    if inventory["schema"] != "qualification-board-inventory/v1":
        _fail("SCHEMA_INVALID", "$.schema", "unexpected inventory schema")
    _digest(inventory["schema_set_digest"], "$.schema_set_digest")
    if inventory["schema_set_digest"] != q01_schema_set_digest():
        _fail("SCHEMA_DIGEST_MISMATCH", "$.schema_set_digest", "inventory schema digest is stale")
    _str(inventory["inventory_id"], "$.inventory_id", _ID)
    _str(inventory["revision"], "$.revision", _ID)
    boards = inventory["boards"]
    _sorted_unique(boards, "$.boards", lambda item: item["board_id"])
    for index, board in enumerate(boards):
        path = f"$.boards[{index}]"
        board = _closed(board, {"board_id", "selector", "profile_ids", "capabilities"}, path)
        _str(board["board_id"], f"{path}.board_id", _BOARD)
        _str(board["selector"], f"{path}.selector", _SELECTOR)
        if board["selector"] != board["board_id"].removeprefix("apple:"):
            _fail("BOARD_SELECTOR_MISMATCH", f"{path}.selector", "selector must equal the canonical board-id suffix")
        _sorted_unique(board["profile_ids"], f"{path}.profile_ids", lambda x: x)
        for j, profile in enumerate(board["profile_ids"]):
            _str(profile, f"{path}.profile_ids[{j}]", _PROFILE)
        caps = board["capabilities"]
        _sorted_unique(caps, f"{path}.capabilities", lambda x: x["capability_id"])
        if not caps:
            _fail("MISSING_CAPABILITIES", f"{path}.capabilities", "every board requires the complete capability criteria")
        for j, criterion in enumerate(caps):
            q = f"{path}.capabilities[{j}]"
            criterion = _closed(criterion, {"capability_id", "applicability", "evidence_modality", "threshold"}, q)
            cap = _str(criterion["capability_id"], f"{q}.capability_id")
            if cap not in _CAPS:
                _fail("UNSUPPORTED_CAPABILITY", f"{q}.capability_id", "capability is outside the closed vocabulary")
            if criterion["applicability"] not in {"applicable", "not-applicable", "unknown"}:
                _fail("SCHEMA_INVALID", f"{q}.applicability", "invalid applicability")
            if criterion["evidence_modality"] not in _MODALITIES:
                _fail("SCHEMA_INVALID", f"{q}.evidence_modality", "invalid evidence modality")
            threshold = criterion["threshold"]
            if type(threshold) is not int or not 1 <= threshold <= 100:
                _fail("SCHEMA_INVALID", f"{q}.threshold", "threshold must be between 1 and 100")
        if {c["capability_id"] for c in caps} != _CAPS:
            _fail("MISSING_CAPABILITIES", f"{path}.capabilities", "criteria must cover every hardware category")


def _inventory_board(inventory: dict[str, Any], board_id: str) -> dict[str, Any]:
    for board in inventory["boards"]:
        if board["board_id"] == board_id:
            return board
    _fail("UNKNOWN_BOARD", "$.board_id", "board is not in the closed inventory")


def _modality_flags(modality: str) -> set[str]:
    return {"automated", "human-observed"} if modality == "automated-and-human" else {modality}


def _modality_satisfied(required: str, observed: set[str]) -> bool:
    return _modality_flags(required) <= observed


def _evidence(record: dict[str, Any], physical_units: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    evidence = record["evidence"]
    _sorted_unique(evidence, "$.evidence", lambda item: item["evidence_id"])
    result = {}
    for index, item in enumerate(evidence):
        path = f"$.evidence[{index}]"
        item = _closed(item, {"evidence_id", "bytes_b64", "content_digest", "modality", "physical", "unit_ids", "observed_at", "tool_version", "redaction_ref"}, path)
        evidence_id = _str(item["evidence_id"], f"{path}.evidence_id", _ID)
        if evidence_id in result:
            _fail("DUPLICATE_SEMANTIC_KEY", f"{path}.evidence_id", "duplicate evidence id")
        raw = item["bytes_b64"]
        if not isinstance(raw, str) or not raw:
            _fail("EVIDENCE_BYTES_MISSING", f"{path}.bytes_b64", "evidence bytes are required")
        try:
            decoded = base64.b64decode(raw, validate=True)
        except (ValueError, base64.binascii.Error):
            _fail("EVIDENCE_BYTES_INVALID", f"{path}.bytes_b64", "evidence bytes are not valid base64")
        digest = _digest(item["content_digest"], f"{path}.content_digest")
        if digest != digest_bytes(decoded):
            _fail("EVIDENCE_DIGEST_MISMATCH", f"{path}.content_digest", "digest does not match evidence bytes")
        if item["modality"] not in _MODALITIES:
            _fail("SCHEMA_INVALID", f"{path}.modality", "invalid evidence modality")
        if type(item["physical"]) is not bool:
            _fail("SCHEMA_INVALID", f"{path}.physical", "physical must be boolean")
        if item["physical"] and item["modality"] == "automated":
            _fail("SIMULATED_AS_PHYSICAL", f"{path}.physical", "automated evidence cannot establish a physical claim")
        _sorted_unique(item["unit_ids"], f"{path}.unit_ids", lambda x: x)
        for j, unit_id in enumerate(item["unit_ids"]):
            _str(unit_id, f"{path}.unit_ids[{j}]", _ID)
            if item["physical"] and unit_id not in physical_units:
                _fail("UNKNOWN_PHYSICAL_UNIT", f"{path}.unit_ids[{j}]", "physical evidence references unknown unit")
        _timestamp(item["observed_at"], f"{path}.observed_at")
        _str(item["tool_version"], f"{path}.tool_version", _ID)
        if item["redaction_ref"] is not None:
            _str(item["redaction_ref"], f"{path}.redaction_ref", _ID)
        result[evidence_id] = item
    return result


def validate_record(record: Any, inventory: dict[str, Any], *, check_intake: bool = True, verification_time: str | None = None) -> None:
    validate_inventory(inventory)
    _schema_validate(record, "qualification-record-q01-v1.schema.json")
    fields = {"schema", "schema_set_digest", "record_id", "board_id", "board_selector", "profile_id", "intake_dataset_digest", "intake_record_id", "intake_record_digest", "f02_schema_set_digest", "manifest_id", "manifest_digest", "firmware_baseline", "physical_units", "capabilities", "evidence", "tool_versions", "redaction", "residuals", "issued_at", "validated_at", "outcome", "admission"}
    record = _closed(record, fields, "$")
    if record["schema"] != "qualification-record/q01-v1":
        _fail("SCHEMA_INVALID", "$.schema", "unexpected Q-01 record schema")
    if (record["outcome"] == "FULL" or record["admission"] == "QUALIFIED") and verification_time is None:
        _fail("VERIFICATION_TIME_REQUIRED", "$.verification_time", "FULL or QUALIFIED validation requires an explicit verification time")
    checked_at = None
    if verification_time is not None:
        _timestamp(verification_time, "$.verification_time")
        checked_at = datetime.fromisoformat(verification_time.removesuffix("Z") + "+00:00")
    _digest(record["schema_set_digest"], "$.schema_set_digest")
    if record["schema_set_digest"] != q01_schema_set_digest():
        _fail("SCHEMA_DIGEST_MISMATCH", "$.schema_set_digest", "record schema digest is stale")
    _str(record["record_id"], "$.record_id", _ID)
    board = _inventory_board(inventory, _str(record["board_id"], "$.board_id", _BOARD))
    if record["board_selector"] != board["selector"]:
        _fail("BOARD_SELECTOR_MISMATCH", "$.board_selector", "selector does not match inventory board")
    _str(record["board_selector"], "$.board_selector", _SELECTOR)
    _str(record["profile_id"], "$.profile_id", _PROFILE)
    if record["profile_id"] not in board["profile_ids"]:
        _fail("PROFILE_MISMATCH", "$.profile_id", "profile is not admitted for this board")
    for key in ("intake_dataset_digest", "intake_record_digest", "f02_schema_set_digest", "manifest_digest"):
        _digest(record[key], f"$.{key}")
    if record["f02_schema_set_digest"] != F02_SCHEMA_SET_DIGEST:
        _fail("F02_SCHEMA_MISMATCH", "$.f02_schema_set_digest", "record is not bound to the current F-02 schema authority")
    _str(record["intake_record_id"], "$.intake_record_id", _ID)
    _str(record["manifest_id"], "$.manifest_id", _ID)
    baseline = _closed(record["firmware_baseline"], {"firmware_id", "version", "build", "captured_at"}, "$.firmware_baseline")
    for key in ("firmware_id", "version", "build"):
        _str(baseline[key], f"$.firmware_baseline.{key}", _ID)
    _timestamp(baseline["captured_at"], "$.firmware_baseline.captured_at")
    units = record["physical_units"]
    _sorted_unique(units, "$.physical_units", lambda item: item["unit_id"])
    unit_map = {}
    for index, unit in enumerate(units):
        path = f"$.physical_units[{index}]"
        unit = _closed(unit, {"unit_id", "identity_digest", "board_id", "profile_id", "inventory_tag", "serial_pseudonym"}, path)
        uid = _str(unit["unit_id"], f"{path}.unit_id", _ID)
        _digest(unit["identity_digest"], f"{path}.identity_digest")
        if unit["board_id"] != record["board_id"] or unit["profile_id"] != record["profile_id"]:
            _fail("PHYSICAL_UNIT_MISMATCH", path, "physical unit is bound to another board/profile")
        _str(unit["inventory_tag"], f"{path}.inventory_tag", _ID)
        _str(unit["serial_pseudonym"], f"{path}.serial_pseudonym", _ID)
        unit_map[uid] = unit
    if units and len(units) < 2:
        _fail("PHYSICAL_UNIT_COUNT", "$.physical_units", "physical claims require at least two independent units")
    if len({u["identity_digest"] for u in units}) != len(units) or len({u["inventory_tag"] for u in units}) != len(units) or len({u["serial_pseudonym"] for u in units}) != len(units):
        _fail("DUPLICATE_PHYSICAL_IDENTITY", "$.physical_units", "physical units must have distinct underlying identities")
    evidence = _evidence(record, unit_map)
    if checked_at is not None:
        for item in evidence.values():
            observed_at = datetime.fromisoformat(item["observed_at"].removesuffix("Z") + "+00:00")
            if observed_at > checked_at:
                _fail("EVIDENCE_FUTURE", "$.evidence", "qualification evidence cannot be observed after verification time")
            if (record["outcome"] == "FULL" or record["admission"] == "QUALIFIED") and checked_at - observed_at > timedelta(days=_MAX_EVIDENCE_AGE_DAYS):
                _fail("EVIDENCE_STALE", "$.evidence", "qualified evidence exceeds the closed freshness window")
    physical_evidence = [item for item in evidence.values() if item["physical"]]
    if physical_evidence and len(units) < 2:
        _fail("PHYSICAL_UNIT_COUNT", "$.physical_units", "any physical evidence requires at least two independent units")
    if physical_evidence and any(set(item["unit_ids"]) != set(unit_map) for item in physical_evidence):
        _fail("PHYSICAL_UNIT_BINDING", "$.evidence", "physical evidence must name both bound units")
    caps = record["capabilities"]
    _sorted_unique(caps, "$.capabilities", lambda item: item["capability_id"])
    expected = {item["capability_id"]: item for item in board["capabilities"]}
    if {item["capability_id"] for item in caps} != _CAPS:
        _fail("MISSING_CAPABILITIES", "$.capabilities", "record must contain every inventory capability")
    physical_claim = False
    for index, item in enumerate(caps):
        path = f"$.capabilities[{index}]"
        item = _closed(item, {"capability_id", "applicability", "status", "evidence_ids", "threshold_met"}, path)
        cid = item["capability_id"]
        criterion = expected[cid]
        if item["applicability"] != criterion["applicability"]:
            _fail("APPLICABILITY_CONTRADICTION", f"{path}.applicability", "record contradicts inventory applicability")
        if item["status"] not in _STATUSES:
            _fail("SCHEMA_INVALID", f"{path}.status", "invalid capability status")
        if type(item["threshold_met"]) is not bool:
            _fail("SCHEMA_INVALID", f"{path}.threshold_met", "threshold_met must be boolean")
        _sorted_unique(item["evidence_ids"], f"{path}.evidence_ids", lambda x: x)
        observed_modalities: set[str] = set()
        for j, evidence_id in enumerate(item["evidence_ids"]):
            if evidence_id not in evidence:
                _fail("EVIDENCE_REFERENCE_MISSING", f"{path}.evidence_ids[{j}]", "evidence id is not declared")
            if evidence[evidence_id]["physical"]:
                physical_claim = True
            observed_modalities |= _modality_flags(evidence[evidence_id]["modality"])
        if item["applicability"] == "not-applicable" and (item["status"] != "unknown" or item["evidence_ids"] or item["threshold_met"]):
            _fail("NA_CONTRADICTION", path, "not-applicable criteria cannot carry a pass, threshold, or evidence claim")
        if item["applicability"] == "applicable" and item["status"] == "pass" and not item["evidence_ids"]:
            _fail("EVIDENCE_REQUIRED", path, "applicable passing criteria require evidence")
        if item["applicability"] == "applicable" and item["status"] == "pass" and not _modality_satisfied(criterion["evidence_modality"], observed_modalities):
            _fail("MODALITY_MISMATCH", path, "evidence does not satisfy the criterion modality")
        if item["applicability"] == "applicable" and item["status"] == "pass" and not any(evidence[eid]["physical"] for eid in item["evidence_ids"]):
            _fail("PHYSICAL_EVIDENCE_REQUIRED", path, "applicable passing criteria require physical evidence")
        if item["status"] == "pass" and item["applicability"] == "unknown":
            _fail("UNKNOWN_FALLBACK", f"{path}.status", "unknown applicability cannot pass")
        if item["status"] == "pass" and not item["threshold_met"]:
            _fail("THRESHOLD_SHORTFALL", f"{path}.threshold_met", "passing capability must meet threshold")
    if physical_claim and len(units) != 2:
        _fail("PHYSICAL_UNIT_COUNT", "$.physical_units", "physical evidence requires two independent units")
    if record["outcome"] not in {"UNKNOWN", "NOT_QUALIFIED", "PARTIAL", "FULL"}:
        _fail("SCHEMA_INVALID", "$.outcome", "invalid outcome")
    if record["outcome"] == "FULL":
        if len(units) < 2 or any(item["applicability"] == "unknown" or (item["applicability"] == "applicable" and (item["status"] != "pass" or not item["threshold_met"])) for item in caps):
            _fail("FULL_NOT_EARNED", "$.outcome", "FULL requires every criterion to resolve, with every applicable row passing")
        if record["residuals"] or record["redaction"]["residuals"]:
            _fail("FULL_HAS_RESIDUALS", "$.residuals", "FULL cannot contain unknown or blocked residuals")
    if record["admission"] not in {"NOT_QUALIFIED", "QUALIFIED"}:
        _fail("SCHEMA_INVALID", "$.admission", "invalid admission state")
    if record["admission"] == "QUALIFIED" and record["outcome"] != "FULL":
        _fail("ADMISSION_MISMATCH", "$.admission", "only FULL can be admitted")
    if record["outcome"] in {"UNKNOWN", "NOT_QUALIFIED"} and record["admission"] != "NOT_QUALIFIED":
        _fail("ADMISSION_MISMATCH", "$.admission", "unknown or not-qualified records cannot be admitted")
    if record["admission"] == "QUALIFIED" and any(item["applicability"] == "unknown" or (item["applicability"] == "applicable" and item["status"] != "pass") for item in caps):
        _fail("ADMISSION_INCOMPLETE", "$.capabilities", "qualified admission requires complete resolved capability evidence")
    _closed(record["tool_versions"], {"validator", "schema"}, "$.tool_versions")
    for key, value in record["tool_versions"].items():
        _str(value, f"$.tool_versions.{key}", _ID)
    redaction = _closed(record["redaction"], {"policy", "applied", "residuals"}, "$.redaction")
    if redaction["policy"] not in {"none", "q01-redaction-v1"} or type(redaction["applied"]) is not bool:
        _fail("REDACTION_INVALID", "$.redaction", "invalid redaction declaration")
    _sorted_unique(redaction["residuals"], "$.redaction.residuals", lambda x: x)
    _sorted_unique(record["residuals"], "$.residuals", lambda x: x["residual_id"])
    for index, residual in enumerate(record["residuals"]):
        _closed(residual, {"residual_id", "reason", "state"}, f"$.residuals[{index}]")
        _str(residual["residual_id"], f"$.residuals[{index}].residual_id", _ID)
        _str(residual["reason"], f"$.residuals[{index}].reason")
        if residual["state"] not in {"unknown", "blocked", "not-covered"}:
            _fail("SCHEMA_INVALID", f"$.residuals[{index}].state", "invalid residual state")
    _timestamp(record["issued_at"], "$.issued_at")
    _timestamp(record["validated_at"], "$.validated_at")
    if checked_at is not None and datetime.fromisoformat(record["validated_at"].removesuffix("Z") + "+00:00") > checked_at:
        _fail("VERIFICATION_TIME_ORDER", "$.validated_at", "record validation cannot occur after verification time")


def validate_record_file(record_path: str | Path, inventory_path: str | Path, *, intake_manifest: str | Path | None = None, manifest: str | Path | None = None, verification_time: str | None = None) -> dict[str, Any]:
    inventory = load_inventory(inventory_path)
    record = _read_json(record_path)
    qualified = record.get("outcome") == "FULL" or record.get("admission") == "QUALIFIED"
    if manifest is None and qualified:
        _fail("MANIFEST_REQUIRED", "$.manifest", "FULL or QUALIFIED records require an authoritative F-02 platform manifest")
    validate_record(record, inventory, verification_time=verification_time)
    if intake_manifest is None:
        candidate = Path(inventory_path).resolve().parents[2] / "data/intake/manifest.json"
        if candidate.is_file():
            intake_manifest = candidate
    if intake_manifest is None and qualified:
        _fail("INTAKE_REQUIRED", "$.intake_manifest", "FULL or QUALIFIED records require the current Q-00 intake manifest")
    if intake_manifest is not None:
        intake_path = Path(intake_manifest)
        root = intake_path.resolve().parents[2]
        try:
            result = validate_dataset_file(intake_path, root=root)
        except IntakeValidationError as error:
            _fail("INTAKE_INVALID", "$.intake_dataset_digest", f"current Q-00 intake did not validate: {error.code}")
        if record["intake_dataset_digest"] != result.dataset_digest:
            _fail("INTAKE_DIGEST_MISMATCH", "$.intake_dataset_digest", "record does not name the current Q-00 dataset")
        dataset = _read_json(intake_path)
        matches = [item for item in dataset["records"] if item.get("record_id") == record["intake_record_id"]]
        if len(matches) != 1:
            _fail("INTAKE_RECORD_MISSING", "$.intake_record_id", "record is not present in current Q-00 intake")
        intake_record = matches[0]
        selectors = intake_record.get("apple_board_selectors", [])
        if len(selectors) != 1 or selectors[0] != record["board_selector"] or intake_record.get("record_id") != record["board_id"]:
            _fail("INTAKE_SELECTOR_MISMATCH", "$.board_selector", "selector must be the exact selector from the Q-00 record")
        projections = [item for item in dataset.get("projections", []) if item.get("projection_id") == record["board_id"]]
        if len(projections) != 1 or projections[0].get("record_digest") != record["intake_record_digest"]:
            _fail("INTAKE_PROJECTION_MISMATCH", "$.intake_record_digest", "Q-00 projection is not bound to this exact board record")
        projection_payload = projections[0].get("payload", {})
        if projection_payload.get("identity_match", {}).get("linux_compatible") != "apple," + record["board_selector"]:
            _fail("INTAKE_SELECTOR_MISMATCH", "$.board_selector", "selector is not the exact Q-00 device-tree selector")
        from omarchy_intake.canonical import intake_digest
        if record["intake_record_digest"] != intake_digest("record/v1", intake_record):
            _fail("INTAKE_RECORD_DIGEST_MISMATCH", "$.intake_record_digest", "record does not name current Q-00 record bytes")
    if manifest is not None:
        manifest_value = _read_json(manifest)
        try:
            checked_manifest = validate_foundation_document(manifest_value, "platform-manifest/v1")
        except SchemaError as error:
            _fail("MANIFEST_INVALID", "$.manifest", f"F-02 platform manifest did not validate: {error.code}")
        payload = checked_manifest.get("payload", checked_manifest)
        if (record["outcome"] == "FULL" or record["admission"] == "QUALIFIED") and manifest_value.get("format") != "omarchy-signed/v1":
            _fail("MANIFEST_SIGNATURE_REQUIRED", "$.manifest.format", "qualified records require the signed F-02 manifest envelope")
        if verification_time is not None and (record["outcome"] == "FULL" or record["admission"] == "QUALIFIED"):
            issued = datetime.fromisoformat(payload["issued_at"].removesuffix("Z") + "+00:00")
            expires = datetime.fromisoformat(payload["expires_at"].removesuffix("Z") + "+00:00")
            checked_at = datetime.fromisoformat(verification_time.removesuffix("Z") + "+00:00")
            if checked_at < issued:
                _fail("MANIFEST_NOT_YET_VALID", "$.manifest.issued_at", "manifest is not valid at verification time")
            if checked_at >= expires:
                _fail("MANIFEST_EXPIRED", "$.manifest.expires_at", "manifest is expired at verification time")
        if payload.get("schema_set_digest") != F02_SCHEMA_SET_DIGEST:
            _fail("F02_SCHEMA_MISMATCH", "$.manifest.schema_set_digest", "manifest is not bound to the current F-02 schema authority")
        if payload.get("document_id") != record["manifest_id"]:
            _fail("MANIFEST_BINDING_MISMATCH", "$.manifest_id", "record manifest id differs")
        from omarchy_platform.canonical import payload_digest
        if record["manifest_digest"] != payload_digest(payload):
            _fail("MANIFEST_DIGEST_MISMATCH", "$.manifest_digest", "record does not name current manifest bytes")
        targets = payload.get("board_targets", [])
        if targets != [record["board_id"]]:
            _fail("MANIFEST_BOARD_MISMATCH", "$.manifest.board_targets", "manifest must target exactly this board")
        identities = [item for item in payload.get("board_identities", []) if item.get("board_id") == record["board_id"]]
        if len(identities) != 1 or identities[0].get("linux_compatible") != "apple," + record["board_selector"]:
            _fail("MANIFEST_BOARD_MISMATCH", "$.manifest.board_identities", "manifest board selector does not match exactly")
        bindings = [item for item in payload.get("qualification_bindings", []) if item.get("board_id") == record["board_id"]]
        if len(bindings) != 1 or bindings[0].get("qualification_record_id") != record["record_id"] or bindings[0].get("required_outcome") != "pass":
            _fail("MANIFEST_QUALIFICATION_MISMATCH", "$.manifest.qualification_bindings", "manifest qualification binding does not match this record")
        if record["outcome"] == "FULL" or record["admission"] == "QUALIFIED":
            baseline = record["firmware_baseline"]
            if any(baseline[key] == "unknown" for key in ("firmware_id", "version", "build")):
                _fail("FIRMWARE_BASELINE_UNKNOWN", "$.firmware_baseline", "qualified records require a known firmware baseline")
            components = payload.get("components", {})
            firmware_component = components.get("firmware_bundle", {})
            artifact_id = (firmware_component.get("artifact_ids") or [None])[0]
            artifact = next((item for item in payload.get("artifacts", []) if item.get("artifact_id") == artifact_id), None)
            if firmware_component.get("source_digest") != baseline["build"] or baseline["firmware_id"] != "firmware-bundle" or not artifact or artifact.get("version") != baseline["version"]:
                _fail("FIRMWARE_BASELINE_MISMATCH", "$.firmware_baseline", "firmware baseline does not match the manifest firmware artifact")
            captured = datetime.fromisoformat(baseline["captured_at"].removesuffix("Z") + "+00:00")
            issued = datetime.fromisoformat(payload["issued_at"].removesuffix("Z") + "+00:00")
            expires = datetime.fromisoformat(payload["expires_at"].removesuffix("Z") + "+00:00")
            checked_at = datetime.fromisoformat(verification_time.removesuffix("Z") + "+00:00")
            if captured < issued or captured >= expires:
                _fail("FIRMWARE_BASELINE_WINDOW", "$.firmware_baseline.captured_at", "firmware baseline is outside manifest validity window")
            if captured > checked_at:
                _fail("FIRMWARE_BASELINE_FUTURE", "$.firmware_baseline.captured_at", "firmware baseline is after verification time")
            if checked_at - captured > timedelta(days=_MAX_FIRMWARE_AGE_DAYS):
                _fail("FIRMWARE_BASELINE_STALE", "$.firmware_baseline.captured_at", "firmware baseline exceeds the closed freshness window")
    return {"decision": "ACCEPT", "record_id": record["record_id"], "outcome": record["outcome"], "admission": record["admission"], "record_digest": digest_bytes(canonical_bytes(record))}
