"""Check PROGRAM against the immutable baseline and emit stable JSON."""

from __future__ import annotations

import argparse
import json
import sys

from omarchy_program.validate import ProgramValidationError, validate_program


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--program", default="PROGRAM.md")
    parser.add_argument("--lock", default="data/program/program-integrity.lock.json")
    args = parser.parse_args(argv)
    try:
        result = validate_program(args.program, args.lock)
    except ProgramValidationError as error:
        print(json.dumps({"code": error.code, "path": error.path, "message": error.message}, sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 2
    print(json.dumps({"decision": "ACCEPT", "lock": args.lock, "slice_count": result["slice_count"], "progress_rows": result["progress_rows"]}, sort_keys=True, separators=(",", ":")) )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
