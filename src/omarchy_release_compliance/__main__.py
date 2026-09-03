"""Read-only command line interface for F-06 compliance."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import sys

from omarchy_platform.strictjson import parse
from omarchy_platform.errors import ValidationError
from omarchy_release_compliance.engine import ComplianceError, attest, evaluate, validate


def _read(path: str) -> object:
    raw = sys.stdin.buffer.read() if path == "-" else open(path, "rb").read()
    return parse(raw)


def _now(value: str | None) -> datetime:
    if value:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return datetime.now(timezone.utc)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omarchy_release_compliance")
    parser.add_argument("command", choices=("validate", "evaluate", "attest"))
    parser.add_argument("path", nargs="?", default="-", help="JSON file, or - for stdin")
    parser.add_argument("--now", help="evaluation time as UTC ISO-8601 timestamp")
    args = parser.parse_args(argv)
    try:
        bundle = _read(args.path)
        when = _now(args.now)
        if args.command == "validate":
            output = {"version": "release-compliance/v1", "decision": "allow", "code": "OK", "path": "$"}
            validate(bundle, now=when)
        elif args.command == "evaluate":
            output = evaluate(bundle, now=when)
        else:
            output = json.loads(attest(bundle, now=when))
        encoded = json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n"
        if output.get("decision") == "reject":
            sys.stderr.write(encoded)
            return 2
        sys.stdout.write(encoded)
        return 0
    except ComplianceError as error:
        sys.stderr.write(json.dumps({"version": "release-compliance/v1", "decision": "reject", **error.as_dict()}, sort_keys=True, separators=(",", ":")) + "\n")
        return 2
    except ValidationError as error:
        sys.stderr.write(json.dumps({"version": "release-compliance/v1", "decision": "reject", "code": error.code, "path": error.path, "detail": error.message}, sort_keys=True, separators=(",", ":")) + "\n")
        return 3
    except (OSError, ValueError, TypeError) as error:
        sys.stderr.write(json.dumps({"version": "release-compliance/v1", "decision": "reject", "code": "PARSE_OR_INPUT_FAILURE", "path": "$", "detail": str(error)}, sort_keys=True, separators=(",", ":")) + "\n")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
