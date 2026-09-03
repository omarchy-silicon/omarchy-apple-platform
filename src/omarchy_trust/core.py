"""F-03 signed metadata verification with no network or mutation authority."""

from __future__ import annotations

import base64
import hashlib
import re
from datetime import datetime, timedelta, timezone
from importlib import resources
from typing import Any, BinaryIO, Mapping, Sequence

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from omarchy_platform.canonical import auth_preimage, canonical_bytes, domain_digest
from omarchy_platform.constants import AUTHENTICATED_PAYLOAD_TYPES
from omarchy_platform.errors import ParseError, SchemaError
from omarchy_platform.strictjson import parse
from omarchy_platform.validate import validate_foundation_document

from .constants import (
    ERROR_DETAILS,
    MAX_ARTIFACT_BYTES,
    MAX_CLOCK_SKEW_SECONDS,
    MAX_DELEGATIONS,
    MAX_KEYS,
    MAX_METADATA_BYTES,
    MAX_REVOCATIONS,
    MAX_REPLAY_SCOPES,
    MAX_SIGNATURES,
    ROLE_LIMIT_SECONDS,
    ROLE_TO_SIGNER,
    TRUST_FORMAT,
    TRUST_PREIMAGE_DOMAIN,
)
from .errors import TrustFailure
from .models import ReplayProposal, ReplaySnapshot, TrustAnchors, TrustedTrustContext

_ID = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,127}$")
_KEY_ID = re.compile(r"^ed25519:sha256:[0-9a-f]{64}$")
_REPOSITORY = re.compile(r"^[a-z0-9][a-z0-9._:/-]{0,127}$")
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_TIMESTAMP = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,3})?Z$")
_BASE64URL = re.compile(r"^[A-Za-z0-9_-]+$")
_ROLES = ("root", "targets", "snapshot", "timestamp", "artifact", "package-index", "emergency/recovery")
_ROLE_THRESHOLDS = {"root": 3, "targets": 2, "snapshot": 2, "timestamp": 2, "artifact": 2, "package-index": 2, "emergency/recovery": 3}
_ROLE_PAYLOADS = {
    "targets": frozenset(("board-registry/v1", "platform-manifest/v1", "qualification-record/v1", "installer-plan/v1")),
    "artifact": frozenset(("boot-health/v1", "boot-success-mark/v1", "dtb-mutation-envelope/v1")),
    "emergency/recovery": frozenset(("owner-approval/v1",)),
    "snapshot": frozenset(),
    "timestamp": frozenset(),
    "package-index": frozenset(),
    "root": frozenset(),
}
_REQUIRED_BUNDLE_FIELDS = (
    "format", "version", "sequence", "repository", "channel", "issued_at", "expires_at",
    "roles", "keys", "delegations", "revocations", "freeze", "rollback", "signatures",
)
_ROTATION_FIELDS = ("from_sequence", "to_sequence", "old_root_key_ids", "new_root_key_ids", "new_root_keys", "acknowledgement")
_ACK_FIELDS = ("format", "from_sequence", "to_sequence", "new_root_key_ids", "signatures")
_ROOT_KEY_FIELDS = ("key_id", "public_key")
_REQUIRED_ROLE_FIELDS = ("role", "threshold", "key_ids", "payload_types")
_REQUIRED_KEY_FIELDS = ("key_id", "public_key", "role", "custody", "repository", "channel", "path_prefix", "not_before", "not_after")
_REQUIRED_DELEGATION_FIELDS = ("key_id", "role", "custody", "repository", "channel", "path_prefix")
_REQUIRED_REVOCATION_FIELDS = ("key_id", "effective_at")
_REQUIRED_FREEZE_FIELDS = ("scope", "incident_id")
_REQUIRED_ROLLBACK_FIELDS = ("prior_metadata_digest", "board_id", "channel", "incident_id", "recovery_digest", "expires_at")
_REQUIRED_SIGNATURE_FIELDS = ("key_id", "algorithm", "signature_format", "signature")
_MISSING_REPLAY = object()


def _fail(code: str, path: str = "$") -> TrustFailure:
    return TrustFailure(code, path, ERROR_DETAILS.get(code, "trust verification failed closed"))


def _exact(value: Mapping[str, Any], fields: Sequence[str], path: str) -> None:
    if set(value) != set(fields):
        raise _fail("TRUST_SCHEMA_INVALID", path)


def _string(value: Any, path: str, pattern: re.Pattern[str] | None = None) -> str:
    if not isinstance(value, str) or (pattern is not None and not pattern.fullmatch(value)):
        raise _fail("TRUST_SCHEMA_INVALID", path)
    return value


def _integer(value: Any, path: str, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise _fail("TRUST_SCHEMA_INVALID", path)
    return value


def _array(value: Any, path: str, maximum: int) -> list[Any]:
    if not isinstance(value, list) or len(value) > maximum:
        raise _fail("TRUST_SCHEMA_INVALID", path)
    return value


def _digest(value: Any, path: str) -> str:
    result = _string(value, path, _DIGEST)
    if result == "sha256:" + "0" * 64:
        raise _fail("TRUST_SCHEMA_INVALID", path)
    return result


def _timestamp(value: Any, path: str) -> str:
    return _string(value, path, _TIMESTAMP)


def _parse_time(value: str, path: str) -> datetime:
    try:
        if "." in value:
            result = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
        else:
            result = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise _fail("TRUST_SCHEMA_INVALID", path) from None
    return result.replace(tzinfo=timezone.utc)


def _b64(value: Any, path: str, length: int) -> bytes:
    encoded = _string(value, path)
    if not _BASE64URL.fullmatch(encoded):
        raise _fail("TRUST_SCHEMA_INVALID", path)
    try:
        decoded = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
    except (ValueError, TypeError):
        raise _fail("TRUST_SCHEMA_INVALID", path) from None
    if len(decoded) != length or base64.urlsafe_b64encode(decoded).rstrip(b"=").decode("ascii") != encoded:
        raise _fail("TRUST_SCHEMA_INVALID", path)
    return decoded


def key_id(public_key: bytes) -> str:
    """Return the only accepted public-key identifier representation."""
    if len(public_key) != 32:
        raise ValueError("Ed25519 public keys are 32 bytes")
    return "ed25519:sha256:" + hashlib.sha256(public_key).hexdigest()


def _bounded_parse(value: bytes | bytearray | memoryview, path: str) -> dict[str, Any]:
    raw = bytes(value)
    if len(raw) > MAX_METADATA_BYTES:
        raise _fail("TRUST_INPUT_TOO_LARGE", path)
    try:
        parsed = parse(raw)
    except ParseError as error:
        if error.code == "DUPLICATE_SEMANTIC_KEY":
            raise _fail("TRUST_DUPLICATE_KEY", path) from None
        if error.code == "RESOURCE_LIMIT":
            raise _fail("TRUST_INPUT_TOO_LARGE", path) from None
        raise _fail("TRUST_JSON_INVALID", path) from None
    if canonical_bytes(parsed) != raw:
        raise _fail("TRUST_NONCANONICAL", path)
    if not isinstance(parsed, dict):
        raise _fail("TRUST_SCHEMA_INVALID", path)
    return parsed


def _value(value: bytes | bytearray | memoryview | Mapping[str, Any], path: str) -> dict[str, Any]:
    if isinstance(value, Mapping):
        result = dict(value)
        if not isinstance(result, dict):
            raise _fail("TRUST_SCHEMA_INVALID", path)
        return result
    return _bounded_parse(value, path)


def _preimage(value: Mapping[str, Any], domain: str) -> bytes:
    projection = {key: item for key, item in value.items() if key != "signatures"}
    return domain.encode("ascii") + b"\x00" + canonical_bytes(projection)


def _verify_signature(signature: Mapping[str, Any], public_key: bytes, preimage: bytes, path: str, expected_role: str | None = None) -> None:
    fields = _REQUIRED_SIGNATURE_FIELDS if expected_role is None else _REQUIRED_SIGNATURE_FIELDS + ("signer_role",)
    _exact(signature, fields, path)
    key_id_value = _string(signature["key_id"], path + ".key_id", _KEY_ID)
    if key_id_value != key_id(public_key):
        raise _fail("TRUST_KEY_ID_INVALID", path + ".key_id")
    if signature["algorithm"] != "ed25519" or signature["signature_format"] != "raw-ed25519/v1":
        raise _fail("TRUST_SCHEMA_INVALID", path)
    if expected_role is not None and signature["signer_role"] != expected_role:
        raise _fail("TRUST_CONTEXT_MISMATCH", path + ".signer_role")
    signature_bytes = _b64(signature["signature"], path + ".signature", 64)
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature_bytes, preimage)
    except (InvalidSignature, ValueError):
        raise _fail("TRUST_SIGNATURE_INVALID", path + ".signature") from None


def _check_window(issued: str, expires: str, role: str, now: datetime, path: str) -> None:
    issued_at = _parse_time(issued, path + ".issued_at")
    expires_at = _parse_time(expires, path + ".expires_at")
    if issued_at > now + timedelta(seconds=MAX_CLOCK_SKEW_SECONDS):
        raise _fail("TRUST_NOT_YET_VALID", path + ".issued_at")
    if expires_at <= now:
        raise _fail("TRUST_EXPIRED", path + ".expires_at")
    if expires_at - issued_at > timedelta(seconds=ROLE_LIMIT_SECONDS[role]):
        raise _fail("TRUST_SCHEMA_INVALID", path + ".expires_at")


def _scope_matches(value: str, expected: str) -> bool:
    return value == "*" or value == expected or (value.endswith("*") and expected.startswith(value[:-1]))


def _validate_signature_shape(value: Any, path: str) -> str:
    if not isinstance(value, dict):
        raise _fail("TRUST_SCHEMA_INVALID", path)
    _exact(value, _REQUIRED_SIGNATURE_FIELDS, path)
    return _string(value["key_id"], path + ".key_id", _KEY_ID)


def _validate_bundle(bundle: Mapping[str, Any], now: datetime) -> tuple[dict[str, Any], dict[str, bytes], dict[str, dict[str, Any]]]:
    expected_fields = set(_REQUIRED_BUNDLE_FIELDS)
    if "rotation" in bundle:
        expected_fields.add("rotation")
    if set(bundle) != expected_fields:
        raise _fail("TRUST_SCHEMA_INVALID", "$")
    if bundle["format"] != TRUST_FORMAT or bundle["version"] != "v1":
        raise _fail("TRUST_SCHEMA_INVALID", "$.format")
    sequence = _integer(bundle["sequence"], "$.sequence")
    if sequence == 0:
        raise _fail("TRUST_SCHEMA_INVALID", "$.sequence")
    if "rotation" in bundle:
        rotation = bundle["rotation"]
        if not isinstance(rotation, dict):
            raise _fail("TRUST_ROTATION_INVALID", "$.rotation")
        _exact(rotation, _ROTATION_FIELDS, "$.rotation")
        if _integer(rotation["from_sequence"], "$.rotation.from_sequence") >= _integer(rotation["to_sequence"], "$.rotation.to_sequence"):
            raise _fail("TRUST_ROTATION_INVALID", "$.rotation")
        if rotation["to_sequence"] != sequence:
            raise _fail("TRUST_ROTATION_INVALID", "$.rotation.to_sequence")
        for field in ("old_root_key_ids", "new_root_key_ids"):
            ids = _array(rotation[field], "$.rotation." + field, MAX_KEYS)
            if ids != sorted(set(ids)) or any(not _KEY_ID.fullmatch(item) for item in ids):
                raise _fail("TRUST_ROTATION_INVALID", "$.rotation." + field)
        new_root_keys = _array(rotation["new_root_keys"], "$.rotation.new_root_keys", MAX_KEYS)
        if [item.get("key_id") for item in new_root_keys if isinstance(item, dict)] != sorted(set(item.get("key_id") for item in new_root_keys if isinstance(item, dict))):
            raise _fail("TRUST_ROTATION_INVALID", "$.rotation.new_root_keys")
        decoded_new_keys: dict[str, bytes] = {}
        for index, item in enumerate(new_root_keys):
            path = f"$.rotation.new_root_keys[{index}]"
            if not isinstance(item, dict):
                raise _fail("TRUST_ROTATION_INVALID", path)
            _exact(item, _ROOT_KEY_FIELDS, path)
            kid = _string(item["key_id"], path + ".key_id", _KEY_ID)
            public = _b64(item["public_key"], path + ".public_key", 32)
            if key_id(public) != kid or kid in decoded_new_keys:
                raise _fail("TRUST_ROTATION_INVALID", path + ".key_id")
            decoded_new_keys[kid] = public
        if set(decoded_new_keys) != set(rotation["new_root_key_ids"]):
            raise _fail("TRUST_ROTATION_INVALID", "$.rotation.new_root_keys")
        acknowledgement = rotation["acknowledgement"]
        if not isinstance(acknowledgement, dict):
            raise _fail("TRUST_ROTATION_INVALID", "$.rotation.acknowledgement")
        _exact(acknowledgement, _ACK_FIELDS, "$.rotation.acknowledgement")
        if acknowledgement["format"] != "omarchy-root-ack/v1" or acknowledgement["from_sequence"] != rotation["from_sequence"] or acknowledgement["to_sequence"] != rotation["to_sequence"] or acknowledgement["new_root_key_ids"] != rotation["new_root_key_ids"]:
            raise _fail("TRUST_ROTATION_INVALID", "$.rotation.acknowledgement")
        acknowledgement_signatures = _array(acknowledgement["signatures"], "$.rotation.acknowledgement.signatures", MAX_SIGNATURES)
        ack_ids = [_validate_signature_shape(item, f"$.rotation.acknowledgement.signatures[{index}]") for index, item in enumerate(acknowledgement_signatures)]
        if ack_ids != sorted(set(ack_ids)):
            raise _fail("TRUST_ROTATION_INVALID", "$.rotation.acknowledgement.signatures")
    repository = _string(bundle["repository"], "$.repository", _REPOSITORY)
    channel = _string(bundle["channel"], "$.channel", re.compile(r"^(?:edge|rc|stable|\*)$"))
    issued = _timestamp(bundle["issued_at"], "$.issued_at")
    expires = _timestamp(bundle["expires_at"], "$.expires_at")
    _check_window(issued, expires, "root", now, "$")

    roles = _array(bundle["roles"], "$.roles", len(_ROLES))
    if len(roles) != len(_ROLES):
        raise _fail("TRUST_SCHEMA_INVALID", "$.roles")
    role_map: dict[str, dict[str, Any]] = {}
    for index, role in enumerate(roles):
        path = f"$.roles[{index}]"
        if not isinstance(role, dict):
            raise _fail("TRUST_SCHEMA_INVALID", path)
        _exact(role, _REQUIRED_ROLE_FIELDS, path)
        name = _string(role["role"], path + ".role")
        if name not in _ROLES or name in role_map or name != _ROLES[index]:
            raise _fail("TRUST_SCHEMA_INVALID", path + ".role")
        threshold = _integer(role["threshold"], path + ".threshold", 1)
        if threshold != _ROLE_THRESHOLDS[name]:
            raise _fail("TRUST_DELEGATION_INVALID", path + ".threshold")
        key_ids = _array(role["key_ids"], path + ".key_ids", MAX_KEYS)
        if len(key_ids) < threshold:
            raise _fail("TRUST_DELEGATION_INVALID", path + ".key_ids")
        for item_index, item in enumerate(key_ids):
            _string(item, f"{path}.key_ids[{item_index}]", _KEY_ID)
        if key_ids != sorted(set(key_ids)):
            raise _fail("TRUST_SCHEMA_INVALID", path + ".key_ids")
        payload_types = _array(role["payload_types"], path + ".payload_types", len(AUTHENTICATED_PAYLOAD_TYPES))
        if payload_types != sorted(set(payload_types)) or any(item not in AUTHENTICATED_PAYLOAD_TYPES for item in payload_types):
            raise _fail("TRUST_SCHEMA_INVALID", path + ".payload_types")
        if frozenset(payload_types) != _ROLE_PAYLOADS[name]:
            raise _fail("TRUST_DELEGATION_INVALID", path + ".payload_types")
        role_map[name] = role

    keys = _array(bundle["keys"], "$.keys", MAX_KEYS)
    if len(keys) > MAX_KEYS:
        raise _fail("TRUST_SCHEMA_INVALID", "$.keys")
    key_map: dict[str, bytes] = {}
    key_roles: dict[str, str] = {}
    for index, item in enumerate(keys):
        path = f"$.keys[{index}]"
        if not isinstance(item, dict):
            raise _fail("TRUST_SCHEMA_INVALID", path)
        _exact(item, _REQUIRED_KEY_FIELDS, path)
        kid = _string(item["key_id"], path + ".key_id", _KEY_ID)
        public = _b64(item["public_key"], path + ".public_key", 32)
        if key_id(public) != kid or kid in key_map:
            raise _fail("TRUST_KEY_ID_INVALID", path + ".key_id")
        role_name = _string(item["role"], path + ".role")
        if role_name not in _ROLES or role_name == "root":
            raise _fail("TRUST_UNKNOWN_ROLE", path + ".role")
        custody = _string(item["custody"], path + ".custody")
        if custody not in {"offline", "online-constrained"}:
            raise _fail("TRUST_DELEGATION_INVALID", path + ".custody")
        if role_name in {"root", "emergency/recovery"} and custody != "offline":
            raise _fail("TRUST_DELEGATION_INVALID", path + ".custody")
        if role_name in {"snapshot", "timestamp"} and custody != "online-constrained":
            raise _fail("TRUST_DELEGATION_INVALID", path + ".custody")
        _string(item["repository"], path + ".repository", _REPOSITORY)
        _string(item["channel"], path + ".channel", re.compile(r"^(?:edge|rc|stable|\*)$"))
        _string(item["path_prefix"], path + ".path_prefix")
        not_before = _timestamp(item["not_before"], path + ".not_before")
        not_after = _timestamp(item["not_after"], path + ".not_after")
        if _parse_time(not_after, path + ".not_after") <= _parse_time(not_before, path + ".not_before"):
            raise _fail("TRUST_SCHEMA_INVALID", path + ".not_after")
        key_map[kid] = public
        key_roles[kid] = role_name
    if list(key_map) != sorted(key_map):
        raise _fail("TRUST_SCHEMA_INVALID", "$.keys")

    delegations = _array(bundle["delegations"], "$.delegations", MAX_DELEGATIONS)
    if len(delegations) != len(keys):
        raise _fail("TRUST_DELEGATION_INVALID", "$.delegations")
    delegation_ids = []
    for index, delegation in enumerate(delegations):
        path = f"$.delegations[{index}]"
        if not isinstance(delegation, dict):
            raise _fail("TRUST_SCHEMA_INVALID", path)
        _exact(delegation, _REQUIRED_DELEGATION_FIELDS, path)
        kid = _string(delegation["key_id"], path + ".key_id", _KEY_ID)
        if kid not in key_map or delegation["role"] != key_roles[kid]:
            raise _fail("TRUST_DELEGATION_INVALID", path)
        for field in ("role", "custody", "repository", "channel", "path_prefix"):
            key_item = keys[next(i for i, candidate in enumerate(keys) if candidate["key_id"] == kid)]
            if field == "role":
                expected = key_roles[kid]
            else:
                expected = key_item[field]
            if delegation[field] != expected:
                raise _fail("TRUST_DELEGATION_INVALID", path + "." + field)
        delegation_ids.append(kid)
    if delegation_ids != sorted(delegation_ids) or len(set(delegation_ids)) != len(delegation_ids):
        raise _fail("TRUST_SCHEMA_INVALID", "$.delegations")
    for role_name, role in role_map.items():
        if any(key_id_value not in key_map for key_id_value in role["key_ids"] if role_name != "root"):
            raise _fail("TRUST_DELEGATION_INVALID", "$.roles")
        if role_name != "root" and any(key_roles[key_id_value] != role_name for key_id_value in role["key_ids"]):
            raise _fail("TRUST_DELEGATION_INVALID", "$.roles")
        role_custody = [keys[next(i for i, candidate in enumerate(keys) if candidate["key_id"] == key_id_value)]["custody"] for key_id_value in role["key_ids"] if key_id_value in key_map]
        if role_name in {"targets", "artifact", "package-index"} and role_custody.count("online-constrained") >= role["threshold"]:
            raise _fail("TRUST_DELEGATION_INVALID", "$.roles")

    revocations = _array(bundle["revocations"], "$.revocations", MAX_REVOCATIONS)
    revoked: dict[str, datetime] = {}
    for index, item in enumerate(revocations):
        path = f"$.revocations[{index}]"
        if not isinstance(item, dict):
            raise _fail("TRUST_SCHEMA_INVALID", path)
        _exact(item, _REQUIRED_REVOCATION_FIELDS, path)
        kid = _string(item["key_id"], path + ".key_id", _KEY_ID)
        if kid in revoked or (kid not in key_map and kid not in role_map["root"]["key_ids"]):
            raise _fail("TRUST_SCHEMA_INVALID", path + ".key_id")
        revoked[kid] = _parse_time(_timestamp(item["effective_at"], path + ".effective_at"), path + ".effective_at")
    if list(revoked) != sorted(revoked):
        raise _fail("TRUST_SCHEMA_INVALID", "$.revocations")

    freezes = _array(bundle["freeze"], "$.freeze", MAX_REVOCATIONS)
    for index, item in enumerate(freezes):
        path = f"$.freeze[{index}]"
        if not isinstance(item, dict):
            raise _fail("TRUST_SCHEMA_INVALID", path)
        _exact(item, _REQUIRED_FREEZE_FIELDS, path)
        _string(item["scope"], path + ".scope")
        _string(item["incident_id"], path + ".incident_id", _ID)

    rollbacks = _array(bundle["rollback"], "$.rollback", MAX_REVOCATIONS)
    for index, item in enumerate(rollbacks):
        path = f"$.rollback[{index}]"
        if not isinstance(item, dict):
            raise _fail("TRUST_SCHEMA_INVALID", path)
        _exact(item, _REQUIRED_ROLLBACK_FIELDS, path)
        _digest(item["prior_metadata_digest"], path + ".prior_metadata_digest")
        _string(item["board_id"], path + ".board_id", _ID)
        _string(item["channel"], path + ".channel", re.compile(r"^(?:edge|rc|stable)$"))
        _string(item["incident_id"], path + ".incident_id", _ID)
        _digest(item["recovery_digest"], path + ".recovery_digest")
        _timestamp(item["expires_at"], path + ".expires_at")

    signatures = _array(bundle["signatures"], "$.signatures", MAX_SIGNATURES)
    if not signatures:
        raise _fail("TRUST_SCHEMA_INVALID", "$.signatures")
    signature_ids = [_validate_signature_shape(item, f"$.signatures[{index}]") for index, item in enumerate(signatures)]
    if signature_ids != sorted(set(signature_ids)):
        raise _fail("TRUST_SCHEMA_INVALID", "$.signatures")
    return dict(bundle), key_map, role_map


def _load_default_anchors() -> TrustAnchors:
    try:
        raw = resources.files("omarchy_trust").joinpath("resources/root-anchors.json").read_bytes()
        # Package resources are source-controlled text and may carry one terminal newline;
        # untrusted caller metadata remains strictly canonical in `_bounded_parse`.
        value = _bounded_parse(raw.rstrip(b"\n"), "$.anchors")
    except (OSError, ModuleNotFoundError):
        raise _fail("TRUST_ANCHOR_MISMATCH", "$.anchors") from None
    if value.get("format") != "omarchy-trust-anchors/v1" or value.get("status") != "UNPROVISIONED" or value.get("keys") != []:
        raise _fail("TRUST_ANCHOR_MISMATCH", "$.anchors")
    raise _fail("TRUST_ANCHORS_UNPROVISIONED", "$.anchors")


def _rotation_ack_preimage(bundle: Mapping[str, Any]) -> bytes:
    projection = {key: item for key, item in bundle.items() if key != "signatures"}
    rotation = dict(projection["rotation"])
    acknowledgement = dict(rotation["acknowledgement"])
    acknowledgement.pop("signatures", None)
    rotation["acknowledgement"] = acknowledgement
    projection["rotation"] = rotation
    return b"omarchy-next-root-ack-preimage/v1\x00" + canonical_bytes(projection)


def _verify_rotation_ack(bundle: Mapping[str, Any], roles: Mapping[str, Mapping[str, Any]], anchors: TrustAnchors, now: datetime) -> None:
    if bundle["sequence"] <= 1:
        return
    rotation = bundle.get("rotation")
    if not isinstance(rotation, Mapping):
        raise _fail("TRUST_ROTATION_INVALID", "$.rotation")
    old_ids = set(rotation["old_root_key_ids"])
    new_ids = set(rotation["new_root_key_ids"])
    if len(old_ids & new_ids) < 2 or not set(anchors.as_mapping()).issubset(old_ids):
        raise _fail("TRUST_ROTATION_INVALID", "$.rotation")
    key_bytes = {
        item["key_id"]: _b64(item["public_key"], "$.rotation.new_root_keys", 32)
        for item in rotation["new_root_keys"]
    }
    acknowledgement = rotation["acknowledgement"]
    used: set[str] = set()
    revoked = {
        item["key_id"]: _parse_time(item["effective_at"], "$.revocations")
        for item in bundle["revocations"]
    }
    preimage = _rotation_ack_preimage(bundle)
    for index, signature in enumerate(acknowledgement["signatures"]):
        kid = signature["key_id"]
        if kid not in new_ids or kid in used or kid not in key_bytes:
            raise _fail("TRUST_ROTATION_INVALID", f"$.rotation.acknowledgement.signatures[{index}].key_id")
        if kid in revoked and now >= revoked[kid]:
            raise _fail("TRUST_REVOKED_KEY", f"$.rotation.acknowledgement.signatures[{index}].key_id")
        _verify_signature(signature, key_bytes[kid], preimage, f"$.rotation.acknowledgement.signatures[{index}]")
        used.add(kid)
    if len(used) < roles["root"]["threshold"]:
        raise _fail("TRUST_THRESHOLD_UNMET", "$.rotation.acknowledgement.signatures")


def _verify_root_bundle(bundle: Mapping[str, Any], anchors: TrustAnchors, now: datetime) -> tuple[dict[str, Any], dict[str, bytes], dict[str, dict[str, Any]], set[str]]:
    if not anchors.provisioned or not anchors.keys:
        raise _fail("TRUST_ANCHORS_UNPROVISIONED", "$.anchors")
    normalized, key_map, roles = _validate_bundle(bundle, now)
    anchor_map = anchors.as_mapping()
    if anchors.threshold != roles["root"]["threshold"]:
        raise _fail("TRUST_ANCHOR_MISMATCH", "$.roles[0].threshold")
    root_ids = set(roles["root"]["key_ids"])
    if not root_ids.issuperset(anchor_map) or len(anchor_map) < anchors.threshold:
        raise _fail("TRUST_ANCHOR_MISMATCH", "$.roles[0].key_ids")
    revoked = {
        item["key_id"]: _parse_time(item["effective_at"], "$.revocations")
        for item in normalized["revocations"]
    }
    valid = 0
    used: set[str] = set()
    preimage = _preimage(normalized, TRUST_PREIMAGE_DOMAIN)
    for index, signature in enumerate(normalized["signatures"]):
        kid = signature["key_id"]
        if kid not in anchor_map:
            continue
        if kid in revoked and now >= revoked[kid]:
            continue
        _verify_signature(signature, anchor_map[kid], preimage, f"$.signatures[{index}]")
        used.add(kid)
        valid += 1
    if valid < roles["root"]["threshold"]:
        raise _fail("TRUST_THRESHOLD_UNMET", "$.signatures")
    _verify_rotation_ack(normalized, roles, anchors, now)
    return normalized, key_map, roles, used


def _check_rotation(current: Mapping[str, Any], previous: Mapping[str, Any], anchors: TrustAnchors, now: datetime) -> None:
    """Require an explicit higher-sequence overlap when a prior root is supplied."""
    previous_value = _value(previous, "$.previous_root_bundle")
    old_bundle, _, old_roles, _ = _verify_root_bundle(previous_value, anchors, now)
    if current["sequence"] <= old_bundle["sequence"]:
        raise _fail("TRUST_ROTATION_INVALID", "$.sequence")
    rotation = current.get("rotation")
    if not isinstance(rotation, dict) or rotation["from_sequence"] != old_bundle["sequence"]:
        raise _fail("TRUST_ROTATION_INVALID", "$.rotation")
    old_ids = set(old_roles["root"]["key_ids"])
    new_ids = set(current["roles"][0]["key_ids"])
    if set(rotation["old_root_key_ids"]) != old_ids or set(rotation["new_root_key_ids"]) != new_ids:
        raise _fail("TRUST_ROTATION_INVALID", "$.rotation")
    if len(old_ids & new_ids) < 2:
        raise _fail("TRUST_ROTATION_INVALID", "$.rotation")


def _coerce_replay_snapshot(value: ReplaySnapshot | Mapping[str, Any] | None) -> ReplaySnapshot:
    if value is _MISSING_REPLAY or value is None:
        raise _fail("TRUST_REPLAY_STATE_UNAVAILABLE", "$.replay_state")
    if isinstance(value, ReplaySnapshot):
        return value
    try:
        return ReplaySnapshot.from_mapping(value)
    except (AttributeError, TypeError, ValueError):
        raise _fail("TRUST_REPLAY_STATE_UNAVAILABLE", "$.replay_state") from None


def _parse_document(value: bytes | bytearray | memoryview | Mapping[str, Any], payload_type: str, path: str) -> dict[str, Any]:
    document = _value(value, path)
    try:
        return validate_foundation_document(document, payload_type)
    except (SchemaError, ValueError):
        raise _fail("TRUST_SCHEMA_INVALID", path) from None


def _version(value: Any) -> tuple[int, ...] | tuple[str]:
    if not isinstance(value, str):
        return (0,)
    parts = value.split(".")
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        return (1, *(int(part) for part in parts))
    return (0, value)


def _document_channel(document: Mapping[str, Any], bundle_channel: str, requested: str | None) -> str:
    payload = document.get("payload")
    if not isinstance(payload, Mapping):
        raise _fail("TRUST_SCHEMA_INVALID", "$.document.payload")
    signed = payload.get("channel")
    if signed is not None:
        if not isinstance(signed, str) or (requested is not None and requested != signed):
            raise _fail("TRUST_CONTEXT_MISMATCH", "$.payload.channel")
        value = signed
    else:
        if bundle_channel == "*" and requested is None:
            raise _fail("TRUST_CONTEXT_MISMATCH", "$.channel")
        if requested is not None and bundle_channel != "*" and requested != bundle_channel:
            raise _fail("TRUST_CONTEXT_MISMATCH", "$.channel")
        value = requested or bundle_channel
    if value not in {"edge", "rc", "stable"}:
        raise _fail("TRUST_CONTEXT_MISMATCH", "$.payload.channel")
    return value


def _verify_proof_set(
    values: Sequence[bytes | bytearray | memoryview | Mapping[str, Any]],
    payload_type: str,
    bundle: Mapping[str, Any],
    key_map: Mapping[str, bytes],
    roles: Mapping[str, Mapping[str, Any]],
    now: datetime,
    repository: str,
    channel: str,
) -> tuple[dict[str, Any], tuple[str, ...], int]:
    if not values or len(values) > MAX_SIGNATURES:
        raise _fail("TRUST_THRESHOLD_UNMET", "$.proof")
    documents = [_parse_document(value, payload_type, f"$.proof[{index}]") for index, value in enumerate(values)]
    preimages = [auth_preimage({key: item for key, item in document.items() if key != "signatures"}) for document in documents]
    if any(item != preimages[0] for item in preimages[1:]):
        raise _fail("TRUST_DIGEST_MISMATCH", "$.proof")
    first = documents[0]
    payload = first["payload"]
    signer_role = first["signatures"][0]["signer_role"]
    delegated_role = ROLE_TO_SIGNER.get(signer_role)
    if delegated_role is None or payload_type not in roles[delegated_role]["payload_types"]:
        raise _fail("TRUST_UNKNOWN_ROLE", "$.signatures[0].signer_role")
    role = roles[delegated_role]
    signature_ids: list[str] = []
    for index, document in enumerate(documents):
        signature = document["signatures"][0]
        if signature["signer_role"] != signer_role:
            raise _fail("TRUST_CONTEXT_MISMATCH", f"$.proof[{index}].signatures[0].signer_role")
        kid = signature["key_id"]
        if kid in signature_ids:
            raise _fail("TRUST_THRESHOLD_UNMET", f"$.proof[{index}].signatures[0].key_id")
        signature_ids.append(kid)
        if kid not in role["key_ids"] or kid not in key_map:
            raise _fail("TRUST_SCOPE_MISMATCH", f"$.proof[{index}].signatures[0].key_id")
        key_index = next(item_index for item_index, item in enumerate(bundle["keys"]) if item["key_id"] == kid)
        key_record = bundle["keys"][key_index]
        if not _scope_matches(key_record["repository"], repository) or not _scope_matches(key_record["channel"], channel) or not _scope_matches(key_record["path_prefix"], payload_type):
            raise _fail("TRUST_SCOPE_MISMATCH", f"$.proof[{index}].signatures[0].key_id")
        if not (_parse_time(key_record["not_before"], "$.keys") <= now < _parse_time(key_record["not_after"], "$.keys")):
            raise _fail("TRUST_REVOKED_KEY", f"$.proof[{index}].signatures[0].key_id")
        _verify_signature(signature, key_map[kid], preimages[0], f"$.proof[{index}].signatures[0]", signer_role)
    if signature_ids != sorted(signature_ids):
        raise _fail("TRUST_SCHEMA_INVALID", "$.proof")
    revoked = {item["key_id"]: _parse_time(item["effective_at"], "$.revocations") for item in bundle["revocations"]}
    if any(kid in revoked and now >= revoked[kid] for kid in signature_ids):
        raise _fail("TRUST_REVOKED_KEY", "$.proof")
    if len(signature_ids) < role["threshold"]:
        raise _fail("TRUST_THRESHOLD_UNMET", "$.proof")
    _check_window(payload["issued_at"], payload["expires_at"], delegated_role, now, "$.payload")
    if not _scope_matches(bundle["repository"], repository) or not _scope_matches(bundle["channel"], channel):
        raise _fail("TRUST_SCOPE_MISMATCH", "$.scope")
    return first, tuple(signature_ids), role["threshold"]


def _check_freeze(bundle: Mapping[str, Any], repository: str, channel: str, payload_type: str) -> None:
    scope = f"{repository}:{channel}:{payload_type}"
    for index, item in enumerate(bundle["freeze"]):
        if _scope_matches(item["scope"], scope):
            raise _fail("TRUST_FROZEN", f"$.freeze[{index}].scope")


def _declared_artifacts(document: Mapping[str, Any]) -> dict[str, str]:
    """Extract only the closed F-02 artifact members, never paths or guesses."""
    payload_type = document["payload_type"]
    payload = document["payload"]
    declared: dict[str, str] = {}
    if payload_type in {"platform-manifest/v1", "installer-plan/v1"}:
        records = payload.get("artifacts", [])
        for index, record in enumerate(records):
            if not isinstance(record, Mapping) or "artifact_id" not in record or "content_digest" not in record:
                raise _fail("TRUST_SCHEMA_INVALID", f"$.payload.artifacts[{index}]")
            artifact_id = record["artifact_id"]
            digest = record["content_digest"]
            if artifact_id in declared:
                raise _fail("TRUST_SCHEMA_INVALID", f"$.payload.artifacts[{index}].artifact_id")
            declared[artifact_id] = digest
    elif payload_type == "dtb-mutation-envelope/v1":
        digest = payload.get("artifact_digest")
        if digest is not None:
            declared[digest] = digest
    return declared


def _verify_declared_artifacts(document: Mapping[str, Any], artifact_streams: Mapping[str, BinaryIO | tuple[BinaryIO, int]] | None) -> None:
    declared = _declared_artifacts(document)
    if not declared:
        if artifact_streams:
            raise _fail("TRUST_ARTIFACT_MISSING", "$.artifacts")
        return
    if artifact_streams is None:
        raise _fail("TRUST_ARTIFACT_MISSING", "$.artifacts")
    if set(artifact_streams) != set(declared):
        raise _fail("TRUST_ARTIFACT_MISSING", "$.artifacts")
    streams: set[int] = set()
    for artifact_id in sorted(declared):
        supplied = artifact_streams[artifact_id]
        if isinstance(supplied, tuple):
            if len(supplied) != 2 or not hasattr(supplied[0], "read"):
                raise _fail("TRUST_ARTIFACT_SIZE", "$.artifacts")
            stream, expected_size = supplied
        else:
            stream, expected_size = supplied, None
        if not hasattr(stream, "read"):
            raise _fail("TRUST_ARTIFACT_MISSING", "$.artifacts")
        identity = id(stream)
        if identity in streams:
            raise _fail("TRUST_ARTIFACT_MISSING", "$.artifacts")
        streams.add(identity)
        verify_artifact_bytes(stream, declared[artifact_id], expected_size)


def verify_artifact_bytes(stream: BinaryIO, expected_digest: str, expected_size: int | None = None) -> str:
    """Verify exact bytes from a bounded caller-owned stream."""
    _digest(expected_digest, "$.artifact.content_digest")
    if expected_size is not None and (not isinstance(expected_size, int) or isinstance(expected_size, bool) or expected_size < 0 or expected_size > MAX_ARTIFACT_BYTES):
        raise _fail("TRUST_ARTIFACT_SIZE", "$.artifact.size")
    digest = hashlib.sha256()
    remaining = expected_size
    total = 0
    while remaining is None or remaining:
        try:
            chunk = stream.read(min(1024 * 1024, remaining) if remaining is not None else 1024 * 1024)
        except (OSError, ValueError):
            raise _fail("TRUST_IO_LIMIT", "$.artifact") from None
        if not isinstance(chunk, (bytes, bytearray, memoryview)):
            raise _fail("TRUST_ARTIFACT_SIZE", "$.artifact.size")
        chunk_bytes = bytes(chunk)
        if not chunk_bytes:
            if remaining is not None:
                raise _fail("TRUST_ARTIFACT_SIZE", "$.artifact.size")
            break
        if remaining is not None and len(chunk_bytes) > remaining:
            raise _fail("TRUST_ARTIFACT_SIZE", "$.artifact.size")
        digest.update(chunk_bytes)
        total += len(chunk_bytes)
        if total > MAX_ARTIFACT_BYTES:
            raise _fail("TRUST_ARTIFACT_SIZE", "$.artifact.size")
        if remaining is not None:
            remaining -= len(chunk_bytes)
    if expected_size is not None:
        try:
            extra = stream.read(1)
        except (OSError, ValueError):
            raise _fail("TRUST_IO_LIMIT", "$.artifact") from None
        if extra not in (b"", bytearray(), memoryview(b"")):
            raise _fail("TRUST_ARTIFACT_SIZE", "$.artifact.size")
    actual = "sha256:" + digest.hexdigest()
    if actual != expected_digest:
        raise _fail("TRUST_ARTIFACT_DIGEST", "$.artifact.content_digest")
    return actual


def verify_document(
    document: bytes | bytearray | memoryview | Mapping[str, Any],
    root_bundle: bytes | bytearray | memoryview | Mapping[str, Any],
    *,
    proof: Sequence[bytes | bytearray | memoryview | Mapping[str, Any]] = (),
    replay_snapshot: ReplaySnapshot | Mapping[str, Any] | None | object = _MISSING_REPLAY,
    repository: str | None = None,
    channel: str | None = None,
    now: datetime | None = None,
    anchors: TrustAnchors | None = None,
    previous_bundle: bytes | bytearray | memoryview | Mapping[str, Any] | None = None,
    artifact_streams: Mapping[str, BinaryIO | tuple[BinaryIO, int]] | None = None,
) -> TrustedTrustContext:
    """Verify one F-02 document plus optional threshold copies."""
    clock = now or datetime.now(timezone.utc)
    if not isinstance(clock, datetime) or clock.tzinfo is None:
        raise _fail("TRUST_CONTEXT_MISMATCH", "$.now")
    clock = clock.astimezone(timezone.utc)
    snapshot = _coerce_replay_snapshot(replay_snapshot)
    active_anchors = anchors if anchors is not None else _load_default_anchors()
    bundle_value = _value(root_bundle, "$.root_bundle")
    bundle, key_map, roles, _ = _verify_root_bundle(bundle_value, active_anchors, clock)
    if previous_bundle is not None:
        _check_rotation(bundle, previous_bundle, active_anchors, clock)
    first_value = _value(document, "$.document")
    payload_type = first_value.get("payload_type") if isinstance(first_value, dict) else None
    if payload_type not in AUTHENTICATED_PAYLOAD_TYPES:
        raise _fail("TRUST_SCHEMA_INVALID", "$.document.payload_type")
    requested_repository = repository or bundle["repository"]
    requested_channel = _document_channel(first_value, bundle["channel"], channel)
    all_documents = (document,) + tuple(proof)
    first, signer_ids, threshold = _verify_proof_set(all_documents, payload_type, bundle, key_map, roles, clock, requested_repository, requested_channel)
    _check_freeze(bundle, requested_repository, requested_channel, payload_type)
    _verify_declared_artifacts(first, artifact_streams)
    payload = first["payload"]
    metadata_digest = domain_digest("omarchy-trusted-metadata/v1", {key: item for key, item in first.items() if key != "signatures"})
    scope = f"{requested_repository}:{requested_channel}:{payload_type}"
    replay_id = domain_digest("omarchy-replay-id/v1", {"scope": scope, "sequence": bundle["sequence"], "metadata_digest": metadata_digest})
    version = payload.get("release_version", payload.get("version", ""))
    existing = snapshot.lookup(scope)
    if existing is not None:
        old_sequence, old_version, old_digest, _old_lineage = existing
        if bundle["sequence"] < old_sequence or (bundle["sequence"] == old_sequence and metadata_digest != old_digest):
            raise _fail("TRUST_REPLAY", "$.root_bundle.sequence")
        if bundle["sequence"] > old_sequence and _version(version) < _version(old_version):
            raise _fail("TRUST_ROLLBACK", "$.payload.release_version")
    lineage_digest = domain_digest("omarchy-replay-lineage/v1", {"scope": scope, "sequence": bundle["sequence"], "metadata_digest": metadata_digest})
    proposal = ReplayProposal(scope, bundle["sequence"], version, metadata_digest, lineage_digest)
    return TrustedTrustContext(
        accepted_role=ROLE_TO_SIGNER[first["signatures"][0]["signer_role"]],
        key_ids=tuple(sorted(signer_ids)),
        threshold=threshold,
        metadata_digest=metadata_digest,
        schema_set_digest=first["schema_set_digest"],
        channel=requested_channel,
        expires_at=payload["expires_at"],
        replay_id=replay_id,
        replay_proposal=proposal,
    )


def verify_root_bundle(
    root_bundle: bytes | bytearray | memoryview | Mapping[str, Any],
    *,
    now: datetime | None = None,
    anchors: TrustAnchors | None = None,
) -> TrustedTrustContext:
    """Verify the root policy itself and expose the same typed trust result."""
    clock = now or datetime.now(timezone.utc)
    if not isinstance(clock, datetime) or clock.tzinfo is None:
        raise _fail("TRUST_CONTEXT_MISMATCH", "$.now")
    clock = clock.astimezone(timezone.utc)
    active_anchors = anchors if anchors is not None else _load_default_anchors()
    bundle, _, roles, used = _verify_root_bundle(_value(root_bundle, "$.root_bundle"), active_anchors, clock)
    metadata_digest = domain_digest("omarchy-trusted-metadata/v1", {key: item for key, item in bundle.items() if key != "signatures"})
    scope = f"{bundle['repository']}:{bundle['channel']}:root"
    replay_id = domain_digest("omarchy-replay-id/v1", {"scope": scope, "sequence": bundle["sequence"], "metadata_digest": metadata_digest})
    lineage_digest = domain_digest("omarchy-replay-lineage/v1", {"scope": scope, "sequence": bundle["sequence"], "metadata_digest": metadata_digest})
    proposal = ReplayProposal(scope, bundle["sequence"], "v1", metadata_digest, lineage_digest)
    trust_schema_digest = domain_digest("omarchy-trust-root-schema/v1", {"format": TRUST_FORMAT, "version": "v1"})
    return TrustedTrustContext("root", tuple(sorted(used)), roles["root"]["threshold"], metadata_digest, trust_schema_digest, bundle["channel"], bundle["expires_at"], replay_id, proposal)


__all__ = ["key_id", "verify_artifact_bytes", "verify_document", "verify_root_bundle"]
