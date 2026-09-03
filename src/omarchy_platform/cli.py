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
from .validate import admit_bundle, validate_foundation_document


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
    conformance = sub.add_parser("conformance")
    conformance_sub = conformance.add_subparsers(dest="conformance_command", required=True)
    conformance_validate = conformance_sub.add_parser("validate")
    for option, dest in (("--registry", "registry"), ("--manifest", "manifest"), ("--plan", "plan"), ("--qualification", "qualification"), ("--boot-health", "boot_health"), ("--owner-approval", "owner_approval"), ("--boot-success-mark", "boot_success_mark"), ("--dtb-envelope", "dtb_envelope")):
        conformance_validate.add_argument(option, dest=dest, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "schema":
            print("\n".join(AUTHENTICATED_PAYLOAD_TYPES))
            return 0
        if args.command == "conformance":
            names = {
                "board-registry/v1": args.registry,
                "platform-manifest/v1": args.manifest,
                "installer-plan/v1": args.plan,
                "qualification-record/v1": args.qualification,
                "boot-health/v1": args.boot_health,
                "owner-approval/v1": args.owner_approval,
                "boot-success-mark/v1": args.boot_success_mark,
                "dtb-mutation-envelope/v1": args.dtb_envelope,
            }
            result = admit_bundle({kind: parse(_read(path)) for kind, path in names.items()})
            if not result.conformant:
                raise ValidationError(result.code, result.path, "P6", result.message)
            print(json.dumps({"conformant": True, "trusted": False, "structural_only": True, "release_eligible": False, "decision": "STRUCTURAL_ONLY", "residual": "F-03 signatures, trust, and byte verification"}, sort_keys=True))
            return 0
        value = _document(args.input, args.type)
        if args.command == "validate":
            print(json.dumps({"foundation_valid": True, "semantic_validation": "type-specific", "trusted": False, "type": args.type}, sort_keys=True))
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
