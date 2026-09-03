"""Bounded JSON transport parser used before any schema or trust decision."""

import json
import math
from typing import Any

from .constants import LIMITS
from .errors import ParseError


class _DuplicateKey(ValueError):
    pass


class _BoundError(ValueError):
    def __init__(self, path: str, detail: str):
        self.path = path
        self.detail = detail


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    key_bytes = 0
    for key, value in pairs:
        if not isinstance(key, str):
            raise _BoundError("$", "object key must be a string")
        if any(0xD800 <= char <= 0xDFFF for char in map(ord, key)):
            raise _BoundError("$", "unpaired surrogate is not permitted")
        size = len(key.encode("utf-8"))
        if size > LIMITS["max_string_bytes"]:
            raise _BoundError("$", "string length limit exceeded")
        key_bytes += size
        if key_bytes > LIMITS["max_total_string_bytes"]:
            raise _BoundError("$", "total string limit exceeded")
        if key in result:
            raise _DuplicateKey()
        result[key] = value
    if len(result) > LIMITS["max_object_properties"]:
        raise _BoundError("$", "object property limit exceeded")
    return result


def _parse_int(token: str) -> int:
    value = int(token)
    if abs(value) > LIMITS["max_integer_magnitude"]:
        raise _BoundError("$", "integer magnitude limit exceeded")
    if token.startswith("-") and value == 0:
        raise _BoundError("$", "negative zero is not permitted")
    return value


def _parse_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise _BoundError("$", "non-finite number is not permitted")
    if value == 0.0 and token.startswith("-"):
        raise _BoundError("$", "negative zero is not permitted")
    # The transport accepts only the spelling that this implementation will emit
    # as JCS. This prevents a distinct numeric spelling from crossing the seam.
    from .canonical import canonical_bytes
    if token != canonical_bytes(value).decode("ascii"):
        raise _BoundError("$", "non-canonical number spelling is not permitted")
    return value


def _walk(value: Any, path: str, depth: int, total_strings: list[int]) -> None:
    if depth > LIMITS["max_depth"]:
        raise _BoundError(path, "nesting depth limit exceeded")
    if isinstance(value, dict):
        if len(value) > LIMITS["max_object_properties"]:
            raise _BoundError(path, "object property limit exceeded")
        for key, child in value.items():
            if any(0xD800 <= ord(char) <= 0xDFFF for char in key):
                raise _BoundError(path, "unpaired surrogate is not permitted")
            key_size = len(key.encode("utf-8"))
            if key_size > LIMITS["max_string_bytes"]:
                raise _BoundError(path, "string length limit exceeded")
            total_strings[0] += key_size
            if total_strings[0] > LIMITS["max_total_string_bytes"]:
                raise _BoundError(path, "total string limit exceeded")
            child_path = f"{path}.{key}" if path != "$" else f"$.{key}"
            _walk(child, child_path, depth + 1, total_strings)
    elif isinstance(value, list):
        if len(value) > LIMITS["max_array_length"]:
            raise _BoundError(path, "array length limit exceeded")
        for index, child in enumerate(value):
            _walk(child, f"{path}[{index}]", depth + 1, total_strings)
    elif isinstance(value, str):
        if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
            raise _BoundError(path, "unpaired surrogate is not permitted")
        size = len(value.encode("utf-8"))
        if size > LIMITS["max_string_bytes"]:
            raise _BoundError(path, "string length limit exceeded")
        total_strings[0] += size
        if total_strings[0] > LIMITS["max_total_string_bytes"]:
            raise _BoundError(path, "total string limit exceeded")


def parse(data: bytes | bytearray | memoryview) -> Any:
    """Parse complete UTF-8 JSON and return no value when any boundary fails."""
    raw = bytes(data)
    if len(raw) > LIMITS["max_input_bytes"]:
        raise ParseError("RESOURCE_LIMIT", "$", "P0", "input byte limit exceeded")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ParseError("PARSE_SCHEMA_FAILURE", "$", "P0", "UTF-8 BOM is not permitted")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise ParseError("PARSE_SCHEMA_FAILURE", "$", "P0", "input is not valid UTF-8") from None
    decoder = json.JSONDecoder(
        object_pairs_hook=_pairs,
        parse_int=_parse_int,
        parse_float=_parse_float,
        parse_constant=lambda token: (_ for _ in ()).throw(
            _BoundError("$", "non-finite number is not permitted")
        ),
    )
    try:
        start = 0
        while start < len(text) and text[start] in " \t\n\r":
            start += 1
        value, end = decoder.raw_decode(text, start)
        trailing = text[end:]
        if any(char not in " \t\n\r" for char in trailing):
            raise ParseError("PARSE_SCHEMA_FAILURE", "$", "P0", "trailing data is not permitted")
        _walk(value, "$", 0, [0])
        return value
    except ParseError:
        raise
    except _DuplicateKey as error:
        raise ParseError("DUPLICATE_SEMANTIC_KEY", "$", "P0", "duplicate object key") from None
    except _BoundError as error:
        code = "RESOURCE_LIMIT"
        if "negative zero" in error.detail or "non-finite" in error.detail or "surrogate" in error.detail or "non-canonical number" in error.detail:
            code = "PARSE_SCHEMA_FAILURE"
        raise ParseError(code, error.path, "P0", error.detail) from None
    except (json.JSONDecodeError, ValueError):
        raise ParseError("PARSE_SCHEMA_FAILURE", "$", "P0", "invalid JSON") from None
