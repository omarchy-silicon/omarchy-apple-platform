"""Fail-closed validation and projection for the Q-00 intake dataset."""

from __future__ import annotations

import json
import re
import stat
from dataclasses import dataclass
from datetime import datetime
from importlib import resources
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator

from .canonical import canonical_bytes, content_digest, intake_digest
from .errors import IntakeValidationError
from .strictjson import parse

SCHEMA = "intake-dataset/v1"
AUTHORITY_CLASSES = ("apple-official", "asahi-upstream", "linux-upstream")
CLAIM_TYPES = (
    "board-identity",
    "soc-identity",
    "firmware-schema",
    "boot-capability",
    "kernel-capability",
    "device-tree-capability",
    "graphics-capability",
)
CLAIM_STATES = ("confirmed", "unknown", "disputed")
EVIDENCE_TIERS = ("source-identity", "upstream-implementation", "observed-intake", "omarchy-qualified")
LIFECYCLES = ("shipping", "announced", "discontinued", "unknown")
CONTRADICTION_KINDS = ("identity", "selector", "lifecycle", "firmware", "boot", "kernel", "device-tree", "graphics")
CONTRADICTION_STATES = ("open", "superseded", "resolved-by-authority")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
MODEL_ID = re.compile(r"^[A-Za-z][A-Za-z0-9,._-]{1,63}$")
BOARD_SELECTOR = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
DT_COMPATIBLE = re.compile(r"^apple,[a-z][a-z0-9-]{1,63}$")
SOC_ID = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
REVISION = re.compile(r"^r[0-9]+$")
UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


@dataclass(frozen=True)
class IntakeResult:
    dataset_digest: str
    source_count: int
    record_count: int
    contradiction_count: int
    projection_count: int
    residual_count: int


def _fail(code: str, path: str, message: str) -> None:
    raise IntakeValidationError(code, path, message)


def _object(value: Any, path: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail("SCHEMA_INVALID", path, "object required")
    unknown = sorted(set(value) - keys)
    missing = sorted(keys - set(value))
    if unknown:
        _fail("UNKNOWN_FIELD", f"{path}.{unknown[0]}", "field is not in the closed schema")
    if missing:
        _fail("MISSING_FIELD", f"{path}.{missing[0]}", "required field is missing")
    return value


def _string(value: Any, path: str, pattern: re.Pattern[str] | None = None) -> str:
    if not isinstance(value, str) or (pattern is not None and not pattern.fullmatch(value)):
        _fail("SCHEMA_INVALID", path, "string has an invalid value")
    return value


def _enum(value: Any, path: str, choices: tuple[str, ...]) -> str:
    if not isinstance(value, str) or value not in choices:
        _fail("UNSUPPORTED_ENUM", path, "value is outside the closed vocabulary")
    return value


def _digest(value: Any, path: str) -> str:
    return _string(value, path, DIGEST)


def _timestamp(value: Any, path: str) -> str:
    value = _string(value, path, UTC)
    try:
        datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError:
        _fail("SCHEMA_INVALID", path, "timestamp is not a valid UTC instant")
    return value


def _sorted_strings(value: Any, path: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        _fail("SCHEMA_INVALID", path, "array of strings required")
    if value != sorted(value):
        _fail("UNSORTED_COLLECTION", path, "array must be lexicographically sorted")
    if len(value) != len(set(value)):
        _fail("DUPLICATE_SEMANTIC_KEY", path, "array contains duplicate values")
    return value


def _sorted_ids(value: Any, path: str) -> list[str]:
    values = _sorted_strings(value, path)
    for index, item in enumerate(values):
        _string(item, f"{path}[{index}]", ID)
    return values


def _sorted_objects(value: Any, path: str, key: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        _fail("SCHEMA_INVALID", path, "array of objects required")
    keys = [item.get(key) for item in value]
    if any(not isinstance(item, str) for item in keys):
        _fail("MISSING_FIELD", path, f"every object requires string key {key}")
    if keys != sorted(keys):
        _fail("UNSORTED_COLLECTION", path, f"objects must be sorted by {key}")
    if len(keys) != len(set(keys)):
        _fail("DUPLICATE_SEMANTIC_KEY", path, f"duplicate {key}")
    return value


def _relative_snapshot(root: Path, value: Any, path: str) -> Path:
    rel = _string(value, path)
    raw = Path(rel)
    source_root = root / "data/intake/sources"
    if raw.is_absolute() or any(part in ("", ".", "..") for part in raw.parts):
        _fail("SNAPSHOT_PATH_INVALID", path, "snapshot path must be a normalized relative path")
    if raw.parts[:3] != ("data", "intake", "sources") or len(raw.parts) <= 3:
        _fail("SNAPSHOT_PATH_INVALID", path, "snapshot path must be below data/intake/sources")
    # Inspect every existing component without following links. This closes
    # both a symlinked source root and a symlink hidden in a nested snapshot
    # path before realpath containment is evaluated.
    current = root
    for index, part in enumerate(raw.parts):
        current = current / part
        try:
            info = current.lstat()
        except OSError:
            _fail("SNAPSHOT_MISSING", path, "checked-in source snapshot is missing")
        if stat.S_ISLNK(info.st_mode):
            _fail("SNAPSHOT_PATH_INVALID", path, "source snapshot path components may not be symlinks")
        if index < len(raw.parts) - 1 and not stat.S_ISDIR(info.st_mode):
            _fail("SNAPSHOT_MISSING", path, "snapshot path parent is not a directory")
    source_info = source_root.lstat()
    if not stat.S_ISDIR(source_info.st_mode):
        _fail("SNAPSHOT_PATH_INVALID", path, "designated source root must be a real directory")
    candidate_raw = root / raw
    candidate = candidate_raw.resolve()
    try:
        candidate.relative_to(source_root.resolve())
    except ValueError:
        _fail("SNAPSHOT_PATH_INVALID", path, "snapshot escapes source directory")
    if not stat.S_ISREG(current.lstat().st_mode):
        _fail("SNAPSHOT_MISSING", path, "checked-in source snapshot is missing")
    return candidate


def _url(value: Any, path: str) -> tuple[str, str, str]:
    value = _string(value, path)
    parsed = urlsplit(value)
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.query or parsed.fragment:
        _fail("SOURCE_URL_INVALID", path, "source URL must be HTTPS without credentials, query, or fragment")
    try:
        host = parsed.hostname or ""
        port = parsed.port
    except ValueError:
        _fail("SOURCE_URL_INVALID", path, "source URL has invalid authority")
    if host != host.lower() or port is not None:
        _fail("SOURCE_URL_INVALID", path, "source URL must use lowercase host and default HTTPS port")
    if not parsed.path or "//" in parsed.path or any(part in (".", "..") for part in parsed.path.split("/")):
        _fail("SOURCE_URL_INVALID", path, "source URL path is not canonical")
    return value, host, parsed.path


def _load_schema(schema_root: Path | None) -> dict[str, Any]:
    schema_path = (schema_root / "schemas/intake-dataset/v1/intake-dataset.schema.json") if schema_root else None
    if schema_path is not None and schema_path.is_file():
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            _fail("TOOLING_BLOCK", "$", f"dataset schema cannot be loaded: {error}")
    else:
        try:
            schema = json.loads(resources.files("omarchy_intake").joinpath("resources/intake-dataset.schema.json").read_text(encoding="utf-8"))
        except (FileNotFoundError, ModuleNotFoundError, json.JSONDecodeError, OSError) as error:
            _fail("TOOLING_BLOCK", "$", f"dataset schema is unavailable: {error}")
    return schema


def _validate_schema(dataset: dict[str, Any], schema_root: Path | None, schema: dict[str, Any] | None = None) -> None:
    if schema is None:
        schema = _load_schema(schema_root)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(dataset), key=lambda item: (list(item.absolute_path), item.validator, item.message))
    if errors:
        error = errors[0]
        path = "$" + "".join(f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.absolute_path)
        code = "UNKNOWN_FIELD" if error.validator == "additionalProperties" else "SCHEMA_INVALID"
        _fail(code, path, error.message)


def _validate_response_metadata(value: Any, path: str, snapshot_size: int) -> None:
    metadata = _object(value, path, {"status_code", "content_type", "content_length", "etag", "last_modified"})
    if type(metadata["status_code"]) is not int or metadata["status_code"] != 200:
        _fail("SOURCE_RESPONSE_INVALID", f"{path}.status_code", "source snapshot must record a successful response")
    _string(metadata["content_type"], f"{path}.content_type")
    if type(metadata["content_length"]) is not int or metadata["content_length"] != snapshot_size:
        _fail("SOURCE_RESPONSE_INVALID", f"{path}.content_length", "response length does not match snapshot")
    for key in ("etag", "last_modified"):
        if metadata[key] is not None:
            _string(metadata[key], f"{path}.{key}")


def _validate_sources(dataset: dict[str, Any], root: Path) -> dict[str, dict[str, Any]]:
    values = _sorted_objects(dataset["sources"], "$.sources", "source_id")
    sources: dict[str, dict[str, Any]] = {}
    for index, source in enumerate(values):
        path = f"$.sources[{index}]"
        _object(source, path, {"source_id", "authority_class", "canonical_url", "revision", "retrieved_at", "content_digest", "media_type", "locator", "subject_refs", "snapshot_path", "response_metadata"})
        source_id = _string(source["source_id"], f"{path}.source_id", ID)
        _enum(source["authority_class"], f"{path}.authority_class", AUTHORITY_CLASSES)
        url, host, url_path = _url(source["canonical_url"], f"{path}.canonical_url")
        _timestamp(source["retrieved_at"], f"{path}.retrieved_at")
        digest = _digest(source["content_digest"], f"{path}.content_digest")
        _string(source["media_type"], f"{path}.media_type")
        locator = _object(source["locator"], f"{path}.locator", {"section", "lines"})
        _string(locator["section"], f"{path}.locator.section")
        lines = locator["lines"]
        if type(lines) is not list or len(lines) != 2 or any(type(line) is not int or line < 1 for line in lines) or lines[0] > lines[1]:
            _fail("SCHEMA_INVALID", f"{path}.locator.lines", "locator requires an increasing two-line range")
        subject_refs = _sorted_ids(source["subject_refs"], f"{path}.subject_refs")
        candidate = _relative_snapshot(root, source["snapshot_path"], f"{path}.snapshot_path")
        try:
            snapshot = candidate.read_bytes()
        except OSError as error:
            _fail("SNAPSHOT_MISSING", f"{path}.snapshot_path", str(error))
        actual_digest = content_digest(snapshot)
        if actual_digest != digest:
            _fail("DIGEST_MISMATCH", f"{path}.content_digest", "snapshot bytes do not match content digest")
        if source["authority_class"] == "apple-official":
            if host not in {"support.apple.com", "developer.apple.com", "www.apple.com"}:
                _fail("SOURCE_AUTHORITY_INVALID", f"{path}.canonical_url", "Apple authority requires an Apple publisher host")
            if source["revision"] != "snapshot:" + digest:
                _fail("SOURCE_REVISION_INVALID", f"{path}.revision", "Apple pages require a matching snapshot revision")
        else:
            if host != "github.com":
                _fail("SOURCE_AUTHORITY_INVALID", f"{path}.canonical_url", "upstream authority requires GitHub source")
            parts = url_path.strip("/").split("/")
            if len(parts) < 4 or parts[2] not in {"blob", "commit"} or (parts[2] == "blob" and len(parts) < 5) or not HEX40.fullmatch(parts[3]):
                _fail("SOURCE_REVISION_INVALID", f"{path}.canonical_url", "upstream URL must contain a full 40-hex commit")
            if source["revision"] != "commit:" + parts[3]:
                _fail("SOURCE_REVISION_INVALID", f"{path}.revision", "revision must equal the URL commit")
            owner = parts[0].lower()
            if source["authority_class"] == "asahi-upstream" and owner != "asahilinux":
                _fail("SOURCE_AUTHORITY_INVALID", f"{path}.canonical_url", "Asahi authority requires the AsahiLinux owner")
            if source["authority_class"] == "linux-upstream" and owner not in {"torvalds", "asahilinux"}:
                _fail("SOURCE_AUTHORITY_INVALID", f"{path}.canonical_url", "Linux authority requires an upstream Linux owner")
        try:
            snapshot_text = snapshot.decode("utf-8")
        except UnicodeDecodeError:
            _fail("SOURCE_CITATION_MISMATCH", f"{path}.snapshot_path", "source snapshot must be UTF-8")
        if url.encode("utf-8") not in snapshot:
            _fail("SOURCE_CITATION_MISMATCH", f"{path}.canonical_url", "snapshot does not contain the declared source URL")
        snapshot_lines = snapshot_text.splitlines()
        if lines[1] > len(snapshot_lines):
            _fail("SOURCE_CITATION_MISMATCH", f"{path}.locator.lines", "locator is outside the snapshot")
        if locator["section"].encode("utf-8") not in snapshot:
            _fail("SOURCE_CITATION_MISMATCH", f"{path}.locator.section", "locator section is absent from snapshot")
        _validate_response_metadata(source["response_metadata"], f"{path}.response_metadata", len(snapshot))
        sources[source_id] = source
        _ = url
    return sources


def _validate_claim_evidence(claim: dict[str, Any], source_refs: list[str], sources: dict[str, dict[str, Any]], record_id: str, root: Path, path: str) -> None:
    evidence = _sorted_objects(claim["evidence"], f"{path}.evidence", "source_id")
    if claim["state"] == "unknown":
        if evidence:
            _fail("UNKNOWN_CLAIM_POPULATED", f"{path}.evidence", "unknown claim may not carry evidence")
        return
    if [item["source_id"] for item in evidence] != source_refs:
        _fail("EVIDENCE_SET_MISMATCH", f"{path}.evidence", "claim evidence must equal claim citations")
    cited_content: list[str] = []
    for index, item in enumerate(evidence):
        epath = f"{path}.evidence[{index}]"
        _object(item, epath, {"source_id", "content_digest", "locator", "assertion"})
        source_id = _string(item["source_id"], f"{epath}.source_id", ID)
        if source_id not in sources:
            _fail("CITATION_MISSING", f"{epath}.source_id", "evidence cites an unknown source")
        source = sources[source_id]
        if record_id not in source["subject_refs"]:
            _fail("CITATION_SUBJECT_MISMATCH", f"{epath}.source_id", "source is not bound to this record")
        if item["content_digest"] != source["content_digest"]:
            _fail("EVIDENCE_DIGEST_MISMATCH", f"{epath}.content_digest", "evidence is not bound to the source snapshot")
        if item["locator"] != source["locator"]:
            _fail("EVIDENCE_LOCATOR_MISMATCH", f"{epath}.locator", "evidence locator must equal the source locator")
        assertion = _string(item["assertion"], f"{epath}.assertion")
        snapshot = _relative_snapshot(root, source["snapshot_path"], f"{epath}.snapshot_path")
        try:
            lines = snapshot.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError) as error:
            _fail("SOURCE_CITATION_MISMATCH", epath, f"cannot read cited snapshot: {error}")
        first, last = source["locator"]["lines"]
        bounded_content = "\n".join(lines[first - 1:last])
        if assertion not in bounded_content:
            _fail("SOURCE_CITATION_MISMATCH", f"{epath}.assertion", "assertion is absent from cited locator content")
        cited_content.append(bounded_content)
    normalized = claim["normalized_value"]
    if isinstance(normalized, dict):
        expected = [str(value) for key, value in normalized.items() if key != "state" and isinstance(value, str)]
        joined = "\n".join(cited_content)
        for value in expected:
            alternatives = [value]
            if value.endswith(" GPU"):
                alternatives.append(value.removesuffix(" GPU"))
            if not any(candidate in joined for candidate in alternatives):
                _fail("CLAIM_EVIDENCE_UNBOUND", f"{path}.evidence", "bounded evidence does not contain the normalized claim value")


def _validate_normalized_claim(claim_type: str, value: Any, path: str) -> None:
    if not isinstance(value, dict):
        _fail("SCHEMA_INVALID", path, "normalized claim value must be an object")
    shapes = {
        "board-identity": {"apple_model_identifier", "apple_board_selector", "device_tree_compatible"},
        "soc-identity": {"soc_id", "display_name"},
        "firmware-schema": {"schema_id", "state"},
        "boot-capability": {"component", "state"},
        "kernel-capability": {"interface", "state"},
        "device-tree-capability": {"compatible", "source_path", "state"},
        "graphics-capability": {"accelerator", "state"},
    }
    _object(value, path, shapes[claim_type])
    for key, item in value.items():
        _string(item, f"{path}.{key}")
    if claim_type == "board-identity":
        _string(value["apple_model_identifier"], f"{path}.apple_model_identifier", MODEL_ID)
        _string(value["apple_board_selector"], f"{path}.apple_board_selector", BOARD_SELECTOR)
        _string(value["device_tree_compatible"], f"{path}.device_tree_compatible", DT_COMPATIBLE)
    elif claim_type == "soc-identity":
        _string(value["soc_id"], f"{path}.soc_id", SOC_ID)
        _string(value["display_name"], f"{path}.display_name")
    elif claim_type == "device-tree-capability":
        _string(value["compatible"], f"{path}.compatible", DT_COMPATIBLE)
        _string(value["source_path"], f"{path}.source_path", re.compile(r"^[A-Za-z0-9_./-]{1,255}$"))
    else:
        _string(value[next(key for key in value if key != "state")], path)
    if claim_type not in {"board-identity", "soc-identity"}:
        _enum(value["state"], f"{path}.state", ("documented", "implemented", "unknown"))


def _validate_records(dataset: dict[str, Any], sources: dict[str, dict[str, Any]], root: Path) -> tuple[dict[str, dict[str, Any]], dict[tuple[str, str], dict[str, Any]], dict[str, list[str]]]:
    values = _sorted_objects(dataset["records"], "$.records", "record_id")
    records: dict[str, dict[str, Any]] = {}
    claims: dict[tuple[str, str], dict[str, Any]] = {}
    conflicts: dict[str, list[str]] = {}
    for index, record in enumerate(values):
        path = f"$.records[{index}]"
        _object(record, path, {"record_id", "record_revision", "supersedes_record_digest", "supersedes_record_revision", "marketing_product", "marketing_year", "apple_model_identifiers", "apple_board_selectors", "device_tree_compatibles", "soc_identities", "lifecycle", "evidence_tier", "claims", "source_refs", "contradiction_refs", "unknowns"})
        record_id = _string(record["record_id"], f"{path}.record_id", ID)
        revision = _string(record["record_revision"], f"{path}.record_revision", REVISION)
        if revision == "r1":
            if record["supersedes_record_digest"] is not None or record["supersedes_record_revision"] is not None:
                _fail("SUPERSESSION_INVALID", path, "r1 record cannot supersede an earlier record")
        else:
            _digest(record["supersedes_record_digest"], f"{path}.supersedes_record_digest")
            _string(record["supersedes_record_revision"], f"{path}.supersedes_record_revision", REVISION)
            if record["supersedes_record_digest"] is None or record["supersedes_record_revision"] is None:
                _fail("SUPERSESSION_INVALID", path, "revised record requires its prior digest and revision")
        _string(record["marketing_product"], f"{path}.marketing_product")
        if type(record["marketing_year"]) is not int or not 2000 <= record["marketing_year"] <= 2100:
            _fail("SCHEMA_INVALID", f"{path}.marketing_year", "marketing year is outside bounds")
        for key in ("apple_model_identifiers", "apple_board_selectors", "device_tree_compatibles", "soc_identities"):
            _sorted_strings(record[key], f"{path}.{key}")
        _sorted_ids(record["source_refs"], f"{path}.source_refs")
        _sorted_ids(record["contradiction_refs"], f"{path}.contradiction_refs")
        for item in record["apple_model_identifiers"]:
            _string(item, f"{path}.apple_model_identifiers", MODEL_ID)
        for item in record["apple_board_selectors"]:
            _string(item, f"{path}.apple_board_selectors", BOARD_SELECTOR)
        for item in record["device_tree_compatibles"]:
            _string(item, f"{path}.device_tree_compatibles", DT_COMPATIBLE)
        for item in record["soc_identities"]:
            _string(item, f"{path}.soc_identities", SOC_ID)
        _enum(record["lifecycle"], f"{path}.lifecycle", LIFECYCLES)
        _enum(record["evidence_tier"], f"{path}.evidence_tier", EVIDENCE_TIERS)
        if record["evidence_tier"] == "omarchy-qualified":
            _fail("QUALIFICATION_REQUIRED", f"{path}.evidence_tier", "Q-00 cannot assert omarchy-qualified evidence without a Q-01 binding")
        unknowns = _sorted_objects(record["unknowns"], f"{path}.unknowns", "field")
        for uindex, unknown in enumerate(unknowns):
            upath = f"{path}.unknowns[{uindex}]"
            _object(unknown, upath, {"field", "reason"})
            _string(unknown["field"], f"{upath}.field")
            _string(unknown["reason"], f"{upath}.reason")
        record_claims = _sorted_objects(record["claims"], f"{path}.claims", "claim_id")
        record_source_refs: set[str] = set()
        by_type: dict[str, tuple[str, bytes]] = {}
        for cindex, claim in enumerate(record_claims):
            cpath = f"{path}.claims[{cindex}]"
            _object(claim, cpath, {"claim_id", "claim_type", "subject", "state", "normalized_value", "source_refs", "evidence", "observed_at", "residual_reason"})
            claim_id = _string(claim["claim_id"], f"{cpath}.claim_id", ID)
            claim_type = _enum(claim["claim_type"], f"{cpath}.claim_type", CLAIM_TYPES)
            if claim["subject"] != record_id:
                _fail("CLAIM_SUBJECT_MISMATCH", f"{cpath}.subject", "claim subject must equal its containing record")
            _enum(claim["state"], f"{cpath}.state", CLAIM_STATES)
            source_refs = _sorted_ids(claim["source_refs"], f"{cpath}.source_refs")
            _timestamp(claim["observed_at"], f"{cpath}.observed_at")
            if claim["state"] == "unknown":
                _validate_claim_evidence(claim, source_refs, sources, record_id, root, cpath)
                if claim["normalized_value"] is not None or source_refs:
                    _fail("UNKNOWN_CLAIM_POPULATED", cpath, "unknown claim may not carry a value or citation")
                _string(claim["residual_reason"], f"{cpath}.residual_reason")
            else:
                if claim["residual_reason"] is not None:
                    _fail("SCHEMA_INVALID", f"{cpath}.residual_reason", "confirmed/disputed claim cannot carry residual reason")
                if not source_refs:
                    _fail("UNCITED_CLAIM", f"{cpath}.source_refs", "confirmed/disputed claim requires a citation")
                _validate_normalized_claim(claim_type, claim["normalized_value"], f"{cpath}.normalized_value")
                normalized_value = claim["normalized_value"]
                if claim_type == "board-identity":
                    if normalized_value["apple_model_identifier"] not in record["apple_model_identifiers"] or normalized_value["apple_board_selector"] not in record["apple_board_selectors"] or normalized_value["device_tree_compatible"] not in record["device_tree_compatibles"]:
                        _fail("CLAIM_RECORD_MISMATCH", f"{cpath}.normalized_value", "board identity must match the record selectors and identifiers")
                elif claim_type == "soc-identity" and normalized_value["soc_id"] not in record["soc_identities"]:
                    _fail("CLAIM_RECORD_MISMATCH", f"{cpath}.normalized_value.soc_id", "SoC identity must match the record declaration")
                elif claim_type == "device-tree-capability" and normalized_value["compatible"] not in record["device_tree_compatibles"]:
                    _fail("CLAIM_RECORD_MISMATCH", f"{cpath}.normalized_value.compatible", "device-tree capability must match the record declaration")
                _validate_claim_evidence(claim, source_refs, sources, record_id, root, cpath)
                for source_id in source_refs:
                    if source_id not in sources:
                        _fail("CITATION_MISSING", f"{cpath}.source_refs", "claim cites an unknown source")
                    if record_id not in sources[source_id]["subject_refs"]:
                        _fail("CITATION_SUBJECT_MISMATCH", f"{cpath}.source_refs", "source is not bound to this record")
                classes = {sources[source_id]["authority_class"] for source_id in source_refs}
                if claim_type in {"board-identity", "soc-identity"} and "apple-official" not in classes:
                    _fail("AUTHORITY_INSUFFICIENT", cpath, "identity claim requires an Apple official citation")
                if claim_type in {"board-identity", "soc-identity"} and not classes.intersection({"asahi-upstream", "linux-upstream"}):
                    _fail("AUTHORITY_INSUFFICIENT", cpath, "identity claim requires an upstream citation")
                if claim_type == "device-tree-capability" and not classes.intersection({"asahi-upstream", "linux-upstream"}):
                    _fail("AUTHORITY_INSUFFICIENT", cpath, "device-tree claim requires an upstream citation")
                record_source_refs.update(source_refs)
                previous = by_type.get(claim_type)
                normalized = canonical_bytes(claim["normalized_value"])
                if previous is not None and previous[1] != normalized:
                    conflicts.setdefault(record_id, [previous[0]]).append(claim_id)
                else:
                    by_type.setdefault(claim_type, (claim_id, normalized))
            key = (record_id, claim_id)
            if key in claims:
                _fail("DUPLICATE_SEMANTIC_KEY", f"{cpath}.claim_id", "duplicate claim identifier")
            claims[key] = claim
        if set(record["source_refs"]) != record_source_refs:
            _fail("CITATION_SET_MISMATCH", f"{path}.source_refs", "record citations must equal cited claim sources")
        records[record_id] = record
    return records, claims, conflicts


def _validate_contradictions(dataset: dict[str, Any], records: dict[str, dict[str, Any]], claims: dict[tuple[str, str], dict[str, Any]], sources: dict[str, dict[str, Any]], conflicts: dict[str, list[str]]) -> dict[str, dict[str, Any]]:
    values = _sorted_objects(dataset["contradictions"], "$.contradictions", "contradiction_id")
    contradictions: dict[str, dict[str, Any]] = {}
    for index, contradiction in enumerate(values):
        path = f"$.contradictions[{index}]"
        _object(contradiction, path, {"contradiction_id", "record_id", "claim_refs", "kind", "description", "source_refs", "status", "opened_at", "supersedes", "resolution_claim_refs", "prior_record_digest", "prior_record_revision"})
        contradiction_id = _string(contradiction["contradiction_id"], f"{path}.contradiction_id", ID)
        record_id = _string(contradiction["record_id"], f"{path}.record_id", ID)
        if record_id not in records:
            _fail("CONTRADICTION_RECORD_MISSING", f"{path}.record_id", "contradiction references an unknown record")
        claim_refs = _sorted_ids(contradiction["claim_refs"], f"{path}.claim_refs")
        if len(claim_refs) < 2 or any((record_id, ref) not in claims for ref in claim_refs):
            _fail("CONTRADICTION_CLAIM_MISSING", f"{path}.claim_refs", "contradiction requires two claims from this record")
        _enum(contradiction["kind"], f"{path}.kind", CONTRADICTION_KINDS)
        _string(contradiction["description"], f"{path}.description")
        source_refs = _sorted_ids(contradiction["source_refs"], f"{path}.source_refs")
        if len(source_refs) < 2 or len(set(source_refs)) < 2:
            _fail("CONTRADICTION_UNCITED", f"{path}.source_refs", "contradiction requires two distinct citations")
        for source_id in source_refs:
            if source_id not in sources:
                _fail("CITATION_MISSING", f"{path}.source_refs", "contradiction cites an unknown source")
            if record_id not in sources[source_id]["subject_refs"]:
                _fail("CITATION_SUBJECT_MISMATCH", f"{path}.source_refs", "contradiction source is not bound to this record")
        resolution_claim_refs = _sorted_ids(contradiction["resolution_claim_refs"], f"{path}.resolution_claim_refs")
        if any((record_id, ref) not in claims for ref in resolution_claim_refs):
            _fail("CONTRADICTION_CLAIM_MISSING", f"{path}.resolution_claim_refs", "resolution claim is not part of this record")
        expected_claim_sources = {source_id for claim_id in claim_refs + resolution_claim_refs for source_id in claims[(record_id, claim_id)]["source_refs"] if (record_id, claim_id) in claims}
        if set(source_refs) != expected_claim_sources:
            _fail("CONTRADICTION_CITATION_MISMATCH", f"{path}.source_refs", "contradiction citations must equal its claim citations")
        _enum(contradiction["status"], f"{path}.status", CONTRADICTION_STATES)
        _timestamp(contradiction["opened_at"], f"{path}.opened_at")
        if contradiction["prior_record_digest"] is not None:
            _digest(contradiction["prior_record_digest"], f"{path}.prior_record_digest")
        if contradiction["prior_record_revision"] is not None:
            _string(contradiction["prior_record_revision"], f"{path}.prior_record_revision", REVISION)
        if contradiction["supersedes"] is not None:
            _string(contradiction["supersedes"], f"{path}.supersedes", ID)
            if contradiction["status"] != "superseded":
                _fail("SUPERSESSION_INVALID", f"{path}.supersedes", "only a superseded contradiction may point backward")
        if contradiction["status"] != "resolved-by-authority" and contradiction["resolution_claim_refs"]:
            _fail("SUPERSESSION_INVALID", f"{path}.resolution_claim_refs", "only an authority resolution may cite replacement claims")
        if contradiction["status"] != "resolved-by-authority" and (contradiction["prior_record_digest"] is not None or contradiction["prior_record_revision"] is not None):
            _fail("SUPERSESSION_INVALID", f"{path}.prior_record_digest", "prior record metadata is only valid for authority resolution")
        contradictions[contradiction_id] = contradiction
    for record_id, record in records.items():
        refs = set(record["contradiction_refs"])
        expected = {cid for cid, item in contradictions.items() if item["record_id"] == record_id}
        if refs != expected:
            _fail("CONTRADICTION_SET_MISMATCH", f"$.records[{record_id}].contradiction_refs", "record contradiction references are not reciprocal")
        for contradiction_id in refs:
            if contradictions[contradiction_id]["status"] == "open":
                kind = contradictions[contradiction_id]["kind"]
                if kind in {"identity", "selector", "lifecycle"}:
                    _fail("OPEN_CONTRADICTION", f"$.records[{record_id}].contradiction_refs", "open identity contradiction blocks intake admission")
        if record_id in conflicts:
            conflict_claims = set(conflicts[record_id])
            if not any(conflict_claims.issubset(set(item["claim_refs"])) for item in contradictions.values() if item["record_id"] == record_id):
                _fail("CONFLICTING_CLAIMS", f"$.records[{record_id}].claims", "conflicting normalized claims require an explicit contradiction record")
    incoming: dict[str, str] = {}
    for contradiction_id, contradiction in contradictions.items():
        if contradiction["status"] in {"superseded", "resolved-by-authority"}:
            superseded = contradiction["supersedes"]
            if superseded is None:
                _fail("SUPERSESSION_INVALID", f"$.contradictions[{contradiction_id}].supersedes", "resolved contradiction must name a prior contradiction")
            if superseded not in contradictions or superseded == contradiction_id:
                _fail("SUPERSESSION_INVALID", f"$.contradictions[{contradiction_id}].supersedes", "supersession must point to an existing earlier contradiction")
            if contradictions[superseded]["status"] != "open":
                _fail("SUPERSESSION_INVALID", f"$.contradictions[{contradiction_id}].supersedes", "only an open contradiction may be superseded")
            previous = incoming.get(superseded)
            if previous is not None:
                _fail("SUPERSESSION_MULTIPLE", f"$.contradictions[{contradiction_id}].supersedes", f"predecessor already has replacement {previous}")
            incoming[superseded] = contradiction_id
        if contradiction["status"] == "resolved-by-authority":
            path = f"$.contradictions[{contradiction_id}]"
            record = records[contradiction["record_id"]]
            if contradiction["prior_record_digest"] is None or contradiction["prior_record_revision"] is None:
                _fail("SUPERSESSION_INVALID", f"{path}.prior_record_digest", "authority resolution requires prior record digest and revision")
            if not contradiction["resolution_claim_refs"]:
                _fail("SUPERSESSION_INVALID", f"{path}.resolution_claim_refs", "authority resolution requires a new cited claim")
            if set(contradiction["claim_refs"]).intersection(contradiction["resolution_claim_refs"]):
                _fail("SUPERSESSION_INVALID", f"{path}.resolution_claim_refs", "resolution claims must be new claim identifiers")
            if record["supersedes_record_digest"] != contradiction["prior_record_digest"] or record["supersedes_record_revision"] != contradiction["prior_record_revision"]:
                _fail("SUPERSESSION_INVALID", f"{path}.prior_record_digest", "resolution prior record binding does not match the revised record")
            if record["record_revision"] <= contradiction["prior_record_revision"]:
                _fail("SUPERSESSION_INVALID", f"{path}.prior_record_revision", "replacement record revision must advance")
            target = contradictions[contradiction["supersedes"]]
            target_values = {canonical_bytes(claims[(target["record_id"], ref)]["normalized_value"]) for ref in target["claim_refs"]}
            for ref in contradiction["resolution_claim_refs"]:
                if (contradiction["record_id"], ref) not in claims:
                    _fail("SUPERSESSION_INVALID", f"{path}.resolution_claim_refs", "resolution claim is missing from the record")
                claim = claims[(contradiction["record_id"], ref)]
                if claim["state"] != "confirmed" or canonical_bytes(claim["normalized_value"]) in target_values:
                    _fail("SUPERSESSION_INVALID", f"{path}.resolution_claim_refs", "resolution must cite a new, changed confirmed claim")
            if not set(contradiction["source_refs"]).intersection({source_id for ref in contradiction["resolution_claim_refs"] for source_id in claims[(contradiction["record_id"], ref)]["source_refs"]}):
                _fail("SUPERSESSION_INVALID", f"{path}.source_refs", "resolution edge is not authority-backed")
    for contradiction_id in contradictions:
        trail: set[str] = set()
        current = contradiction_id
        while current in contradictions and contradictions[current]["supersedes"] is not None:
            if current in trail:
                _fail("SUPERSESSION_CYCLE", f"$.contradictions[{contradiction_id}].supersedes", "contradiction supersession graph must be acyclic")
            trail.add(current)
            current = contradictions[current]["supersedes"]
    return contradictions


def _projection_for(record: dict[str, Any], dataset_digest: str, record_digest: str) -> dict[str, Any]:
    identity = next((claim for claim in record["claims"] if claim["claim_type"] == "board-identity" and claim["state"] == "confirmed"), None)
    soc = next((claim for claim in record["claims"] if claim["claim_type"] == "soc-identity" and claim["state"] == "confirmed"), None)
    if identity is None or soc is None:
        _fail("PROJECTION_UNAVAILABLE", "$.projections", "projection requires confirmed board and SoC identity claims")
    value = identity["normalized_value"]
    soc_value = soc["normalized_value"]
    board_id = "apple:" + value["apple_board_selector"]
    return {
        "projection_id": board_id,
        "projection_type": "board-registry/v1",
        "dataset_digest": dataset_digest,
        "record_id": record["record_id"],
        "record_revision": record["record_revision"],
        "record_digest": record_digest,
        "payload": {
            "schema": "board-registry/v1",
            "dataset_digest": dataset_digest,
            "record_digest": record_digest,
            "record_revision": record["record_revision"],
            "board_id": board_id,
            "identity_match": {
                "macos_compatible": value["apple_model_identifier"].lower(),
                "linux_compatible": value["device_tree_compatible"],
            },
            "soc_id": "apple-soc:" + soc_value["soc_id"],
            "lifecycle": record["lifecycle"],
            "admissible": False,
        },
    }


def dataset_digest_for(dataset: dict[str, Any]) -> str:
    """Hash the source manifest preimage; generated projections do not self-hash."""
    preimage = dict(dataset)
    preimage["projections"] = []
    return intake_digest("dataset/v1", preimage)


def _validate_projections(dataset: dict[str, Any], records: dict[str, dict[str, Any]], record_digests: dict[str, str], dataset_digest: str) -> None:
    values = _sorted_objects(dataset["projections"], "$.projections", "projection_id")
    seen: set[str] = set()
    for index, projection in enumerate(values):
        path = f"$.projections[{index}]"
        _object(projection, path, {"projection_id", "projection_type", "dataset_digest", "record_id", "record_revision", "record_digest", "payload"})
        projection_id = _string(projection["projection_id"], f"{path}.projection_id", ID)
        if projection_id in seen:
            _fail("DUPLICATE_SEMANTIC_KEY", f"{path}.projection_id", "duplicate projection identifier")
        seen.add(projection_id)
        if projection["projection_type"] != "board-registry/v1":
            _fail("UNSUPPORTED_ENUM", f"{path}.projection_type", "only board-registry/v1 projection is supported")
        if projection["dataset_digest"] != dataset_digest:
            _fail("STALE_PROJECTION", f"{path}.dataset_digest", "projection is bound to a different dataset digest")
        record_id = _string(projection["record_id"], f"{path}.record_id", ID)
        if record_id not in records:
            _fail("PROJECTION_RECORD_MISSING", f"{path}.record_id", "projection references an unknown record")
        if projection["record_revision"] != records[record_id]["record_revision"] or projection["record_digest"] != record_digests[record_id]:
            _fail("STALE_PROJECTION", path, "projection record binding is stale")
        expected = _projection_for(records[record_id], dataset_digest, record_digests[record_id])
        if projection != expected:
            _fail("PROJECTION_MISMATCH", path, "projection is not the deterministic record projection")


def validate_dataset(dataset: Any, *, root: Path | None = None, expected_digest: str | None = None) -> IntakeResult:
    """Validate a complete local dataset and return its recomputed summary."""
    if not isinstance(dataset, dict):
        _fail("SCHEMA_INVALID", "$", "dataset must be an object")
    _object(dataset, "$", {"schema", "dataset_id", "dataset_revision", "schema_set_digest", "generated_at", "sources", "records", "contradictions", "projections", "residuals", "source_index", "record_index"})
    if dataset["schema"] != SCHEMA:
        _fail("SCHEMA_INVALID", "$.schema", "unexpected dataset schema")
    _string(dataset["dataset_id"], "$.dataset_id", ID)
    _string(dataset["dataset_revision"], "$.dataset_revision", re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$"))
    _digest(dataset["schema_set_digest"], "$.schema_set_digest")
    _timestamp(dataset["generated_at"], "$.generated_at")
    schema = _load_schema(root)
    expected_schema_digest = content_digest(canonical_bytes(schema))
    if dataset["schema_set_digest"] != expected_schema_digest:
        _fail("SCHEMA_SET_DIGEST_MISMATCH", "$.schema_set_digest", "manifest does not bind the packaged intake schema-set")
    if root is None:
        root = Path.cwd()
    sources = _validate_sources(dataset, root)
    records, claims, conflicts = _validate_records(dataset, sources, root)
    used_sources = {source_id for record in records.values() for source_id in record["source_refs"]}
    for source_id, source in sources.items():
        expected_subjects = sorted(record_id for record_id, record in records.items() if source_id in record["source_refs"])
        if source_id not in used_sources:
            _fail("UNREFERENCED_SOURCE", f"$.sources[{source_id}].source_id", "every source must support a normalized claim")
        if source["subject_refs"] != expected_subjects:
            _fail("CITATION_SET_MISMATCH", f"$.sources[{source_id}].subject_refs", "source subjects must equal citing records")
    contradictions = _validate_contradictions(dataset, records, claims, sources, conflicts)
    residuals = _sorted_objects(dataset["residuals"], "$.residuals", "residual_id")
    for index, residual in enumerate(residuals):
        path = f"$.residuals[{index}]"
        _object(residual, path, {"residual_id", "subject", "reason", "state"})
        _string(residual["residual_id"], f"{path}.residual_id", ID)
        _string(residual["subject"], f"{path}.subject", ID)
        _string(residual["reason"], f"{path}.reason")
        _enum(residual["state"], f"{path}.state", ("unknown", "not-covered", "blocked"))
    source_index = _sorted_objects(dataset["source_index"], "$.source_index", "source_id")
    expected_index = [{"source_id": source_id, "content_digest": source["content_digest"]} for source_id, source in sources.items()]
    if source_index != expected_index:
        _fail("MANIFEST_INDEX_MISMATCH", "$.source_index", "source index does not match source records")
    record_index = _sorted_objects(dataset["record_index"], "$.record_index", "record_id")
    record_digests = {record_id: intake_digest("record/v1", record) for record_id, record in records.items()}
    expected_index = [{"record_id": record_id, "record_revision": record["record_revision"], "record_digest": record_digests[record_id]} for record_id, record in records.items()]
    if record_index != expected_index:
        _fail("MANIFEST_INDEX_MISMATCH", "$.record_index", "record index does not match record records")
    _validate_schema(dataset, root, schema)
    dataset_digest = dataset_digest_for(dataset)
    if expected_digest is not None and dataset_digest != expected_digest:
        _fail("MANIFEST_DIGEST_MISMATCH", "$.dataset_digest", "manifest digest does not match lock")
    _validate_projections(dataset, records, record_digests, dataset_digest)
    return IntakeResult(dataset_digest, len(sources), len(records), len(contradictions), len(dataset["projections"]), len(residuals))


def load_dataset(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    try:
        raw = path.read_bytes()
    except OSError as error:
        _fail("IO_FAILURE", "$", f"dataset could not be read: {error}")
    value = parse(raw)
    if not isinstance(value, dict):
        _fail("SCHEMA_INVALID", "$", "dataset must be an object")
    return value


def validate_dataset_file(path: str | Path, *, root: str | Path | None = None, expected_digest: str | None = None) -> IntakeResult:
    path = Path(path)
    if root is None:
        root = path.resolve().parents[2] if len(path.resolve().parents) >= 3 else path.parent
    root = Path(root)
    if expected_digest is None:
        lock_path = path.with_name("manifest.lock.json")
        if lock_path.is_file():
            lock = load_dataset(lock_path)
            _object(lock, "$.lock", {"schema", "manifest_path", "dataset_digest"})
            if lock["schema"] != "intake-manifest-lock/v1":
                _fail("MANIFEST_LOCK_INVALID", "$.lock.schema", "unexpected manifest lock schema")
            _digest(lock["dataset_digest"], "$.lock.dataset_digest")
            try:
                manifest_rel = path.resolve().relative_to(root.resolve()).as_posix()
            except ValueError:
                _fail("MANIFEST_LOCK_INVALID", "$.lock.manifest_path", "manifest is outside the locked root")
            if lock["manifest_path"] != manifest_rel:
                _fail("MANIFEST_LOCK_INVALID", "$.lock.manifest_path", "lock does not name this manifest")
            expected_digest = lock["dataset_digest"]
    return validate_dataset(load_dataset(path), root=root, expected_digest=expected_digest)


def project_record(dataset: Any, record_id: str, *, root: Path | None = None) -> dict[str, Any]:
    result = validate_dataset(dataset, root=root)
    records = {record["record_id"]: record for record in dataset["records"]}
    if record_id not in records:
        _fail("RECORD_MISSING", "$.record_id", "requested record does not exist")
    digests = {key: intake_digest("record/v1", record) for key, record in records.items()}
    return _projection_for(records[record_id], result.dataset_digest, digests[record_id])
