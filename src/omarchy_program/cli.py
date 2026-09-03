"""Command line entry point for PROGRAM integrity CI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .validate import validate_program


def _emit(value: object, stream) -> None:
    stream.write(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omarchy-program")
    parser.add_argument("--program", default="PROGRAM.md")
    parser.add_argument("--lock", default="data/program/program-integrity.lock.json")
    args = parser.parse_args(argv)
    try:
        _emit(validate_program(args.program, args.lock), sys.stdout)
        return 0
    except Exception as error:
        if hasattr(error, "code"):
            _emit({"code": error.code, "path": error.path, "message": error.message}, sys.stderr)
            return 2
        _emit({"code": "INTERNAL_FAILURE", "path": "$", "message": "validator failed closed"}, sys.stderr)
        return 2

