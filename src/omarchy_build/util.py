"""Shared bounded parsing, canonicalization, and closed-record helpers."""

from __future__ import annotations

import base64
import json
import re
from collections.abc import Mapping, Sequence
from hashlib import sha256
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import urlparse

from omarchy_platform.canonical import canonical_bytes as _canonical_bytes

from .errors import BuildProvenanceError

DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
ID_RE = re.compile(r"^[a-z][a-z0-9._:-]{0,127}$")
BUILDER_ID_RE = re.compile(r"^builder:[a-z0-9][a-z0-9._:-]{0,127}$")
RECIPE_ID_RE = re.compile(r"^recipe:[a-z0-9][a-z0-9._:-]{0,127}$")
INPUT_ID_RE = re.compile(r"^input:[a-z0-9][a-z0-9._:-]{0,127}$")
ARTIFACT_ID_RE = re.compile(r"^artifact:[a-z0-9][a-z0-9._:-]{0,127}$")

MAX_DOCUMENT_BYTES = 4 * 1024 * 1024
MAX_OUTPUT_BYTES = 32 * 1024 * 1024
MAX_LIST_LENGTH = 4096
MAX_PATH_BYTES = 512


def canonical_bytes(value: Any) -> bytes:
    return _canonical_bytes(value)


def digest_bytes(value: bytes) -> str:
    return "sha256:" + sha256(value).hexdigest()


def digest_value(domain: str, value: Any) -> str:
    return digest_bytes(domain.encode("ascii") + b"\x00" + canonical_bytes(value))


def read_json(path: str, *, max_bytes: int = MAX_DOCUMENT_BYTES) -> Any:
    from omarchy_platform.strictjson import parse

    try:
        with open(path, "rb") as stream:
            data = stream.read(max_bytes + 1)
    except OSError as error:
        raise BuildProvenanceError("INPUT_READ_FAILURE", "$", "input could not be read") from error
    if len(data) > max_bytes:
        raise BuildProvenanceError("RESOURCE_LIMIT", "$", "input byte limit exceeded")
    return parse(data)


def write_json(path: str, value: Any) -> None:
    data = canonical_bytes(value) + b"\n"
    if len(data) > MAX_DOCUMENT_BYTES:
        raise BuildProvenanceError("RESOURCE_LIMIT", "$", "output byte limit exceeded")
    try:
        with open(path, "wb") as stream:
            stream.write(data)
    except OSError as error:
        raise BuildProvenanceError("OUTPUT_WRITE_FAILURE", "$", "output could not be written") from error


def expect_object(value: Any, keys: Sequence[str], path: str = "$") -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BuildProvenanceError("TYPE_MISMATCH", path, "object required")
    expected = set(keys)
    actual = set(value)
    unknown = sorted(actual - expected)
    missing = sorted(expected - actual)
    if unknown:
        raise BuildProvenanceError("UNKNOWN_FIELD", f"{path}.{unknown[0]}", "field is not in the closed record")
    if missing:
        raise BuildProvenanceError("MISSING_FIELD", f"{path}.{missing[0]}", "required field is missing")
    return value


def expect_string(value: Any, path: str, *, pattern: re.Pattern[str] | None = None) -> str:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > MAX_PATH_BYTES:
        raise BuildProvenanceError("INVALID_STRING", path, "bounded non-empty string required")
    if pattern is not None and pattern.fullmatch(value) is None:
        raise BuildProvenanceError("INVALID_STRING", path, "string is outside the closed vocabulary")
    return value


def expect_digest(value: Any, path: str) -> str:
    if not isinstance(value, str) or DIGEST_RE.fullmatch(value) is None:
        raise BuildProvenanceError("INVALID_DIGEST", path, "lowercase sha256 digest required")
    return value


def expect_enum(value: Any, path: str, values: set[str]) -> str:
    value = expect_string(value, path)
    if value not in values:
        raise BuildProvenanceError("UNKNOWN_ENUM", path, "value is outside the closed vocabulary")
    return value


def expect_list(value: Any, path: str, *, nonempty: bool = False) -> list[Any]:
    if not isinstance(value, list) or len(value) > MAX_LIST_LENGTH or (nonempty and not value):
        raise BuildProvenanceError("INVALID_LIST", path, "bounded list required")
    return value


def sorted_unique(values: Sequence[str], path: str) -> tuple[str, ...]:
    if any(not isinstance(item, str) for item in values):
        raise BuildProvenanceError("INVALID_LIST", path, "string IDs required")
    if len(set(values)) != len(values):
        raise BuildProvenanceError("DUPLICATE_SEMANTIC_KEY", path, "IDs must be unique")
    if list(values) != sorted(values):
        raise BuildProvenanceError("UNSORTED_IDS", path, "IDs must be sorted")
    return tuple(values)


def safe_relative_path(value: Any, path: str) -> str:
    value = expect_string(value, path)
    if "\\" in value or value.startswith("/") or value.startswith("~"):
        raise BuildProvenanceError("UNSAFE_PATH", path, "relative POSIX path required")
    parsed = PurePosixPath(value)
    if value in {"", "."} or any(part in {"", ".", ".."} for part in parsed.parts):
        raise BuildProvenanceError("UNSAFE_PATH", path, "path traversal is not permitted")
    return value


def immutable_https_uri(value: Any, path: str) -> str:
    value = expect_string(value, path)
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password or parsed.port:
        raise BuildProvenanceError("MUTABLE_INPUT", path, "allowlisted HTTPS URI without authority ambiguity required")
    path_parts = parsed.path.split("/")
    if path_parts and path_parts[0] == "":
        path_parts = path_parts[1:]
    if parsed.query or parsed.fragment or not path_parts or any(part in {"", ".", ".."} for part in path_parts):
        raise BuildProvenanceError("MUTABLE_INPUT", path, "URI path/query is not immutable")
    lowered = value.lower()
    if any(token in lowered for token in ("/main", "/master", "/latest", "/head", "/branch", "refs/heads")):
        raise BuildProvenanceError("MUTABLE_INPUT", path, "mutable ref is not an input authority")
    return value


def parse_digest_b64(value: Any, path: str) -> bytes:
    value = expect_string(value, path)
    try:
        decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except ValueError as error:
        raise BuildProvenanceError("INVALID_SIGNATURE", path, "invalid base64url") from error
    return decoded


def ensure_mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise BuildProvenanceError("TYPE_MISMATCH", path, "mapping required")
    return value
