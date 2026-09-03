"""Read-only diagnostic CLI for the bounded F-02 seam."""

import argparse
import json
import sys
from pathlib import Path

from .canonical import canonical_bytes, payload_digest
from .constants import AUTHENTICATED_PAYLOAD_TYPES
from .constants import LIMITS
from .errors import ValidationError
from .strictjson import parse
from .validate import validate_foundation_document


def _read(path: str) -> bytes:
    file_path = Path(path)
    if file_path.stat().st_size > LIMITS["max_input_bytes"]:
        raise ValidationError("RESOURCE_LIMIT", "$", "P0", "input file byte limit exceeded")
    with file_path.open("rb") as stream:
        data = stream.read(LIMITS["max_input_bytes"] + 1)
    if len(data) > LIMITS["max_input_bytes"]:
        raise ValidationError("RESOURCE_LIMIT", "$", "P0", "input file changed beyond byte limit")
    return data


def _document(path: str, type_name: str):
    return validate_foundation_document(parse(_read(path)), type_name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omarchy-platform")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("schema").add_subparsers(dest="schema_command", required=True).add_parser("list")
    validate = sub.add_parser("validate")
    validate.add_argument("--type", required=True, choices=AUTHENTICATED_PAYLOAD_TYPES)
    validate.add_argument("--input", required=True)
    canonicalize = sub.add_parser("canonicalize")
    canonicalize.add_argument("--type", required=True, choices=AUTHENTICATED_PAYLOAD_TYPES)
    canonicalize.add_argument("--input", required=True)
    canonicalize.add_argument("--output", required=True)
    digest = sub.add_parser("digest")
    digest.add_argument("--type", required=True, choices=AUTHENTICATED_PAYLOAD_TYPES)
    digest.add_argument("--input", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "schema":
            print("\n".join(AUTHENTICATED_PAYLOAD_TYPES))
            return 0
        value = _document(args.input, args.type)
        if args.command == "validate":
            print(json.dumps({"foundation_valid": True, "semantic_validation": "not-implemented", "trusted": False, "type": args.type}, sort_keys=True))
        elif args.command == "canonicalize":
            try:
                Path(args.output).write_bytes(canonical_bytes(value))
            except OSError as error:
                raise ValidationError("IO_FAILURE", "$", "P0", "output could not be written") from error
        else:
            payload = value.get("payload", value)
            print(payload_digest(payload))
        return 0
    except (OSError, ValidationError, ValueError) as error:
        if isinstance(error, ValidationError):
            print(json.dumps({"code": error.code, "path": error.path, "phase": error.phase, "message": error.message}, sort_keys=True), file=sys.stderr)
        else:
            message = "output could not be written" if args.command == "canonicalize" else "input could not be read"
            print(json.dumps({"code": "IO_FAILURE", "path": "$", "phase": "P0", "message": message}, sort_keys=True), file=sys.stderr)
        return 2
