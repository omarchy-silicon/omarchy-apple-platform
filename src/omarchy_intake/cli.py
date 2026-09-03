"""Deterministic offline Q-00 command line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .canonical import canonical_bytes
from .errors import IntakeValidationError
from .validate import load_dataset, project_record, validate_dataset_file


def _output(value: object) -> None:
    sys.stdout.buffer.write(canonical_bytes(value) + b"\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omarchy-intake")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--manifest", required=True)
    validate.add_argument("--root", required=True)
    validate.add_argument("--expected-digest")
    validate.add_argument("--offline", action="store_true", required=True)
    project = sub.add_parser("project")
    project.add_argument("--manifest", required=True)
    project.add_argument("--root", required=True)
    project.add_argument("--record", required=True)
    project.add_argument("--offline", action="store_true", required=True)
    digest = sub.add_parser("digest")
    digest.add_argument("--manifest", required=True)
    digest.add_argument("--root", required=True)
    digest.add_argument("--offline", action="store_true", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            result = validate_dataset_file(args.manifest, root=args.root, expected_digest=args.expected_digest)
            _output({"decision": "ACCEPT", "dataset_digest": result.dataset_digest, "sources": result.source_count, "records": result.record_count, "contradictions": result.contradiction_count, "projections": result.projection_count, "residuals": result.residual_count, "offline": True})
        elif args.command == "digest":
            result = validate_dataset_file(args.manifest, root=args.root)
            _output({"dataset_digest": result.dataset_digest})
        else:
            validate_dataset_file(args.manifest, root=args.root)
            dataset = load_dataset(args.manifest)
            result = project_record(dataset, args.record, root=Path(args.root))
            _output(result)
        return 0
    except (IntakeValidationError, OSError) as error:
        if isinstance(error, IntakeValidationError):
            payload = {"code": error.code, "path": error.path, "message": error.message}
        else:
            payload = {"code": "IO_FAILURE", "path": "$", "message": "dataset could not be read"}
        sys.stderr.buffer.write(canonical_bytes(payload) + b"\n")
        return 2
