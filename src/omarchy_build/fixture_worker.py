"""Minimal closed worker used only by the deterministic fixture backend."""

from __future__ import annotations

import json
import sys
from hashlib import sha256
from pathlib import Path


def fail(code: str, path: str, detail: str) -> int:
    sys.stderr.write(json.dumps({"code": code, "path": path, "detail": detail}, sort_keys=True))
    return 2


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        return fail("BUILDER_INVOCATION_INVALID", "$", "bounded fixture invocation required")
    request_path, response_path = map(Path, argv[1:])
    try:
        request = json.loads(request_path.read_text(encoding="utf-8"))
        recipe = request["recipe"]
        source = {str(key): bytes.fromhex(value) for key, value in request["source"].items()}
        chunks = []
        for read_path in recipe["read_paths"]:
            if read_path not in source:
                return fail("UNDECLARED_INPUT", "$.read_paths", "recipe requested a path absent from the declared closure")
            chunks.append(source[read_path])
        prefix = recipe["prefix"].encode("utf-8")
        data = prefix + b"\n" + sha256(b"".join(chunks)).hexdigest().encode("ascii") + b"\n"
        response_path.write_text(json.dumps({"data_hex": data.hex()}, sort_keys=True), encoding="utf-8")
        return 0
    except (OSError, ValueError, KeyError, TypeError):
        return fail("BUILDER_OUTPUT_INVALID", "$", "fixture request is malformed")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
