"""Deterministic canonical JSON and F-02 domain-separated digests."""

import json
import math
import re
from hashlib import sha256
from typing import Any


def _string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _number(value: int | float) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if not math.isfinite(value) or (value == 0.0 and math.copysign(1.0, value) < 0):
        raise ValueError("non-finite or negative-zero number")
    if value == 0:
        return "0"
    # Python's shortest-roundtrip repr has the same useful boundary behavior as
    # ECMAScript numbers. Normalize its exponent spelling to JCS form.
    text = repr(value).lower()
    if "e" not in text:
        return text[:-2] if text.endswith(".0") else text
    mantissa, exponent = text.split("e")
    exponent_value = int(exponent)
    if mantissa.endswith(".0"):
        mantissa = mantissa[:-2]
    # ECMAScript uses decimal notation for [1e-6, 1e21).
    absolute = abs(value)
    if 1e-6 <= absolute < 1e21:
        digits = mantissa.replace(".", "")
        decimal_position = (mantissa.find(".") if "." in mantissa else len(mantissa)) + exponent_value
        sign_prefix = "-" if digits.startswith("-") else ""
        digits = digits.lstrip("-")
        if decimal_position <= 0:
            return sign_prefix + "0." + "0" * (-decimal_position) + digits
        if decimal_position >= len(digits):
            return sign_prefix + digits + "0" * (decimal_position - len(digits))
        return sign_prefix + digits[:decimal_position] + "." + digits[decimal_position:]
    sign = "+" if exponent_value >= 0 else "-"
    return f"{mantissa}e{sign}{abs(exponent_value)}"


def canonical_bytes(value: Any) -> bytes:
    """Encode the supported JSON domain using RFC 8785-compatible ordering."""
    def encode(item: Any) -> str:
        if item is None:
            return "null"
        if item is True:
            return "true"
        if item is False:
            return "false"
        if isinstance(item, (int, float)) and not isinstance(item, bool):
            return _number(item)
        if isinstance(item, str):
            return _string(item)
        if isinstance(item, list):
            return "[" + ",".join(encode(child) for child in item) + "]"
        if isinstance(item, dict):
            keys = sorted(item, key=lambda key: key.encode("utf-16-be"))
            return "{" + ",".join(_string(key) + ":" + encode(item[key]) for key in keys) + "}"
        raise TypeError(f"unsupported JSON value: {type(item).__name__}")

    return encode(value).encode("utf-8")


def sha256_digest(data: bytes) -> str:
    return "sha256:" + sha256(data).hexdigest()


def domain_digest(domain: str, value: Any) -> str:
    return sha256_digest(domain.encode("ascii") + b"\x00" + canonical_bytes(value))


def payload_digest(payload: Any) -> str:
    return domain_digest("omarchy-payload/v1", payload)


def schema_set_digest(lock: Any) -> str:
    return domain_digest("omarchy-schema-set/v1", lock)


def auth_preimage(value: Any) -> bytes:
    return b"omarchy-auth-preimage/v1\x00" + canonical_bytes(value)
