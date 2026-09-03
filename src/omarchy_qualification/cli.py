"""Deterministic, offline-only Q-01 command line interface."""

from __future__ import annotations

import argparse
import sys

from .canonical import canonical_bytes, digest_bytes
from .errors import QualificationValidationError
from .validate import load_inventory, validate_inventory_file, validate_record_file


def _emit(value: object) -> None:
    sys.stdout.buffer.write(canonical_bytes(value) + b"\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omarchy-qualification")
    sub = parser.add_subparsers(dest="command", required=True)
    inv = sub.add_parser("inventory")
    inv_sub = inv.add_subparsers(dest="inventory_command", required=True)
    inv_validate = inv_sub.add_parser("validate")
    inv_validate.add_argument("--input", required=True)
    inv_digest = inv_sub.add_parser("digest")
    inv_digest.add_argument("--input", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--record", required=True)
    validate.add_argument("--inventory", required=True)
    validate.add_argument("--intake")
    validate.add_argument("--manifest")
    validate.add_argument("--verification-time")
    digest = sub.add_parser("digest")
    digest.add_argument("--record", required=True)
    digest.add_argument("--inventory", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "inventory":
            inventory = validate_inventory_file(args.input)
            if args.inventory_command == "digest":
                _emit({"inventory_digest": digest_bytes(canonical_bytes(inventory))})
            else:
                _emit({"decision": "ACCEPT", "inventory_id": inventory["inventory_id"], "boards": len(inventory["boards"])})
        elif args.command == "validate":
            result = validate_record_file(args.record, args.inventory, intake_manifest=args.intake, manifest=args.manifest, verification_time=args.verification_time)
            _emit(result)
        else:
            result = validate_record_file(args.record, args.inventory)
            _emit({"record_digest": result["record_digest"], "outcome": result["outcome"], "admission": result["admission"]})
        return 0
    except (QualificationValidationError, OSError) as error:
        if isinstance(error, QualificationValidationError):
            payload = {"code": error.code, "path": error.path, "message": error.message}
        else:
            payload = {"code": "IO_FAILURE", "path": "$", "message": "input could not be read"}
        sys.stderr.buffer.write(canonical_bytes(payload) + b"\n")
        return 2
