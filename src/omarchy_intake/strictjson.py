"""Bounded duplicate-key rejecting JSON input."""

import json
from typing import Any

from .errors import IntakeValidationError


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise IntakeValidationError("DUPLICATE_KEY", "$", "duplicate object key")
        result[key] = value
    return result


def parse(data: bytes | bytearray | memoryview | str) -> Any:
    try:
        return json.loads(data, object_pairs_hook=_pairs, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    except IntakeValidationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError) as error:
        raise IntakeValidationError("MALFORMED_JSON", "$", "input is not one complete JSON value") from error
