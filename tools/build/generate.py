#!/usr/bin/env python3
"""Emit a deterministic fixture build inventory without network or signing."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from omarchy_build import BuilderDefinition, Recipe, SourceClosure  # noqa: E402
from omarchy_build.util import canonical_bytes, read_json  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="f04-generate")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    definitions = [BuilderDefinition.from_dict(read_json(str(path))) for path in sorted((ROOT / "builders").glob("*/definition.json"))]
    recipe = Recipe.from_dict(read_json(str(ROOT / "fixtures/build/recipe.json")))
    closure = SourceClosure.from_dict(read_json(str(ROOT / "fixtures/build/source-lock.json")))
    inventory = {"version": "f04-fixture-inventory/v1", "builders": [{"builder_id": item.builder_id, "definition_digest": item.definition_digest} for item in definitions], "recipe_id": recipe.recipe_id, "recipe_digest": recipe.recipe_digest, "source_closure_digest": closure.closure_digest}
    output = canonical_bytes(inventory) + b"\n"
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(output)
    else:
        sys.stdout.buffer.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
