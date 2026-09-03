"""Generate the canonical PROGRAM integrity lock deterministically."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from omarchy_program.validate import build_lock, parse_for_lock


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--program", default="PROGRAM.md")
    parser.add_argument("--output", default="data/program/program-integrity.lock.json")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    slices, progress = parse_for_lock(args.program)
    lock = build_lock(slices, progress)
    encoded = json.dumps(lock, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.write:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
