"""Read-only command line interface for F-06 compliance."""

from __future__ import annotations

import argparse
import json
import sys

from omarchy_platform.constants import LIMITS
from omarchy_platform.strictjson import parse
from omarchy_platform.errors import ValidationError
from omarchy_release_compliance.engine import ComplianceError, attest, evaluate, validate


def _read(path: str) -> object:
    if path == "-":
        raw = sys.stdin.buffer.read(LIMITS["max_input_bytes"] + 1)
    else:
        with open(path, "rb") as source:
            raw = source.read(LIMITS["max_input_bytes"] + 1)
    if len(raw) > LIMITS["max_input_bytes"]:
        raise ComplianceError("RESOURCE_LIMIT", "$", "input exceeds bounded max bytes")
    return parse(raw)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omarchy_release_compliance")
    parser.add_argument("command", choices=("validate", "evaluate", "attest"))
    parser.add_argument("path", nargs="?", default="-", help="JSON file, or - for stdin")
    args = parser.parse_args(argv)
    try:
        bundle = _read(args.path)
        if args.command == "validate":
            output = {"version": "release-compliance/v1", "decision": "allow", "code": "OK", "path": "$", "clock_trusted": False}
            validate(bundle)
        elif args.command == "evaluate":
            output = evaluate(bundle)
        else:
            output = json.loads(attest(bundle))
        encoded = json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n"
        if output.get("decision") == "reject":
            sys.stderr.write(encoded)
            return 2
        sys.stdout.write(encoded)
        return 0
    except ComplianceError as error:
        sys.stderr.write(json.dumps({"version": "release-compliance/v1", "decision": "reject", "clock_trusted": False, **error.as_dict()}, sort_keys=True, separators=(",", ":")) + "\n")
        return 2
    except ValidationError as error:
        sys.stderr.write(json.dumps({"version": "release-compliance/v1", "decision": "reject", "clock_trusted": False, "code": error.code, "path": error.path, "detail": error.message}, sort_keys=True, separators=(",", ":")) + "\n")
        return 3
    except (OSError, ValueError, TypeError) as error:
        sys.stderr.write(json.dumps({"version": "release-compliance/v1", "decision": "reject", "clock_trusted": False, "code": "PARSE_OR_INPUT_FAILURE", "path": "$", "detail": str(error)}, sort_keys=True, separators=(",", ":")) + "\n")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
