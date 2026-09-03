"""Deterministic offline F-05 CLI; it never promotes or publishes."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from omarchy_platform.canonical import canonical_bytes
from omarchy_platform.strictjson import parse

from .assemble import assemble_candidate
from .errors import CandidateAssemblyError
from .models import CandidateManifest


def _read(path: str) -> object:
    try:
        data = Path(path).read_bytes()
        if len(data) > 4 * 1024 * 1024:
            raise CandidateAssemblyError("RESOURCE_LIMIT", "$", "input byte limit exceeded")
        return parse(data)
    except CandidateAssemblyError:
        raise
    except (OSError, ValueError, TypeError, UnicodeDecodeError) as error:
        raise CandidateAssemblyError("INPUT_INVALID", "$", "candidate input is invalid") from error


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omarchy-candidate")
    sub = parser.add_subparsers(dest="command", required=True)
    assemble = sub.add_parser("assemble")
    assemble.add_argument("--input", required=True)
    assemble.add_argument("--output")
    verify = sub.add_parser("verify")
    verify.add_argument("--input", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            manifest = CandidateManifest.from_dict(_read(args.input))
            sys.stdout.buffer.write(canonical_bytes({"decision": "ACCEPT", "candidate_digest": manifest.candidate_digest}) + b"\n")
            return 0
        manifest = assemble_candidate(_read(args.input))
        output = manifest.bytes() + b"\n"
        if args.output:
            Path(args.output).write_bytes(output)
        else:
            sys.stdout.buffer.write(output)
        return 0
    except CandidateAssemblyError as error:
        sys.stderr.buffer.write(canonical_bytes(error.as_dict()) + b"\n")
        return 2
    except OSError:
        sys.stderr.buffer.write(canonical_bytes({"code": "OUTPUT_WRITE_FAILURE", "path": "$.output", "detail": "output could not be written"}) + b"\n")
        return 2

