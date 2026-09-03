"""Closed common-envelope validation for the executable F-02 seam.

Cross-document, signature, trust, and type-specific semantic validators are deliberately
not implemented here. They must be added at their owning gates rather than inferred.
"""

import base64
import re
from typing import Any

from .constants import AUTHENTICATED_PAYLOAD_TYPES, SCHEMA_SET_DIGEST, TYPE_CONTEXT
from .errors import SchemaError

_DOCUMENT = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,127}$")
_ISSUER = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,127}$")
_TIMESTAMP = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,3})?Z$")
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")

ENVELOPE_FIELDS = ("format", "payload_type", "payload_version", "domain", "context", "schema_set_digest", "payload", "signatures")
PAYLOAD_FIELDS = ("schema", "schema_set_digest", "document_id", "issuer", "issued_at", "expires_at", "semantic_validation")
SIGNATURE_FIELDS = ("key_id", "signer_role", "algorithm", "signature_format", "signature")


def _error(code: str, path: str, message: str) -> SchemaError:
    return SchemaError(code, path, "P1", message)


def _exact(value: dict[str, Any], fields: tuple[str, ...], path: str) -> None:
    unknown = sorted(set(value) - set(fields))
    if unknown:
        raise _error("UNKNOWN_FIELD", f"{path}.{unknown[0]}", "unknown property")
    missing = [field for field in fields if field not in value]
    if missing:
        raise _error("PARSE_SCHEMA_FAILURE", f"{path}.{missing[0]}", "required property is missing")


def _string(value: Any, path: str) -> None:
    if not isinstance(value, str):
        raise _error("PARSE_SCHEMA_FAILURE", path, "expected string")


def _match(value: Any, pattern: re.Pattern[str], path: str, label: str) -> None:
    _string(value, path)
    if not pattern.fullmatch(value):
        raise _error("PARSE_SCHEMA_FAILURE", path, f"invalid {label}")


def _signature(value: Any, path: str) -> None:
    if not isinstance(value, dict):
        raise _error("PARSE_SCHEMA_FAILURE", path, "expected object")
    _exact(value, SIGNATURE_FIELDS, path)
    _match(value["key_id"], _ISSUER, f"{path}.key_id", "key id")
    _match(value["signer_role"], _ISSUER, f"{path}.signer_role", "signer role")
    if value["algorithm"] != "ed25519":
        raise _error("PARSE_SCHEMA_FAILURE", f"{path}.algorithm", "unsupported algorithm")
    if value["signature_format"] != "raw-ed25519/v1":
        raise _error("PARSE_SCHEMA_FAILURE", f"{path}.signature_format", "unsupported signature format")
    _string(value["signature"], f"{path}.signature")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", value["signature"]):
        raise _error("PARSE_SCHEMA_FAILURE", f"{path}.signature", "invalid base64url")
    try:
        decoded = base64.urlsafe_b64decode(value["signature"] + "=" * (-len(value["signature"]) % 4))
    except ValueError:
        raise _error("PARSE_SCHEMA_FAILURE", f"{path}.signature", "invalid base64url") from None
    if len(decoded) != 64 or "=" in value["signature"]:
        raise _error("PARSE_SCHEMA_FAILURE", f"{path}.signature", "signature must be 64 unpadded bytes")


def validate_payload(payload: Any, payload_type: str) -> dict[str, Any]:
    if payload_type not in AUTHENTICATED_PAYLOAD_TYPES:
        raise _error("PARSE_SCHEMA_FAILURE", "$.payload_type", "unknown payload type")
    if not isinstance(payload, dict):
        raise _error("PARSE_SCHEMA_FAILURE", "$.payload", "expected object")
    _exact(payload, PAYLOAD_FIELDS, "$.payload")
    if payload["schema"] != payload_type:
        raise _error("SIGNATURE_CONTEXT_MISMATCH", "$.payload.schema", "schema and payload type differ")
    if payload["schema_set_digest"] != SCHEMA_SET_DIGEST:
        raise _error("CROSS_DOCUMENT_MISMATCH", "$.payload.schema_set_digest", "schema-set digest differs")
    _match(payload["document_id"], _DOCUMENT, "$.payload.document_id", "document id")
    _match(payload["issuer"], _ISSUER, "$.payload.issuer", "issuer")
    _match(payload["issued_at"], _TIMESTAMP, "$.payload.issued_at", "timestamp")
    _match(payload["expires_at"], _TIMESTAMP, "$.payload.expires_at", "timestamp")
    if payload["semantic_validation"] != "not-implemented":
        raise _error("PARSE_SCHEMA_FAILURE", "$.payload.semantic_validation", "semantic validators are not implemented")
    return payload


def validate_document(value: Any, payload_type: str) -> dict[str, Any]:
    """Validate a payload or its closed signed envelope; never returns partial data."""
    if payload_type not in AUTHENTICATED_PAYLOAD_TYPES:
        raise _error("PARSE_SCHEMA_FAILURE", "$.payload_type", "unknown payload type")
    if not isinstance(value, dict):
        raise _error("PARSE_SCHEMA_FAILURE", "$", "document must be an object")
    if "format" not in value:
        return validate_payload(value, payload_type)
    _exact(value, ENVELOPE_FIELDS, "$")
    if value["format"] != "omarchy-signed/v1":
        raise _error("PARSE_SCHEMA_FAILURE", "$.format", "unsupported envelope format")
    if value["payload_type"] != payload_type:
        raise _error("SIGNATURE_CONTEXT_MISMATCH", "$.payload_type", "declared type differs from requested type")
    if value["payload_version"] != "v1":
        raise _error("PARSE_SCHEMA_FAILURE", "$.payload_version", "unsupported payload version")
    domain, context, _role = TYPE_CONTEXT[payload_type]
    if value["domain"] != domain:
        raise _error("SIGNATURE_CONTEXT_MISMATCH", "$.domain", "wrong signing domain")
    if value["context"] != context:
        raise _error("SIGNATURE_CONTEXT_MISMATCH", "$.context", "wrong signing context")
    if value["schema_set_digest"] != SCHEMA_SET_DIGEST:
        raise _error("CROSS_DOCUMENT_MISMATCH", "$.schema_set_digest", "schema-set digest differs")
    validate_payload(value["payload"], payload_type)
    if value["payload"]["schema_set_digest"] != value["schema_set_digest"]:
        raise _error("SIGNATURE_CONTEXT_MISMATCH", "$.payload.schema_set_digest", "envelope and payload differ")
    if not isinstance(value["signatures"], list) or not value["signatures"]:
        raise _error("PARSE_SCHEMA_FAILURE", "$.signatures", "at least one signature is required")
    for index, signature in enumerate(value["signatures"]):
        _signature(signature, f"$.signatures[{index}]")
    return value
