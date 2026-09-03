#!/usr/bin/env python3
"""Fail-closed F-04 schema, builder, and fixture drift check."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from omarchy_build import BuilderDefinition, Recipe, SourceClosure  # noqa: E402
from omarchy_build.util import digest_bytes, read_json  # noqa: E402


def fail(message: str) -> int:
    print(f"F04 DRIFT: FAIL {message}")
    return 1


def main() -> int:
    schema_dir = ROOT / "src/omarchy_build/schemas"
    schemas = sorted(schema_dir.glob("*.json"))
    if len(schemas) < 6:
        return fail("closed schema resource set is incomplete")
    for path in schemas:
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return fail(f"invalid schema JSON: {path.name}")
        if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
            return fail(f"schema is not closed: {path.name}")
    definitions = []
    for path in sorted((ROOT / "builders").glob("*/definition.json")):
        try:
            definition = BuilderDefinition.from_dict(read_json(str(path)))
        except Exception as error:  # noqa: BLE001 - drift must produce one stable failure
            return fail(f"builder definition rejected: {path}: {type(error).__name__}")
        definitions.append(definition)
    if len(definitions) != 2 or len({item.builder_id for item in definitions}) != 2 or len({item.definition_digest for item in definitions}) != 2:
        return fail("fixture builders are not two distinct pinned definitions")
    try:
        recipe = Recipe.from_dict(read_json(str(ROOT / "fixtures/build/recipe.json")))
        closure = SourceClosure.from_dict(read_json(str(ROOT / "fixtures/build/source-lock.json")))
    except Exception as error:  # noqa: BLE001
        return fail(f"fixture lock rejected: {type(error).__name__}")
    source = ROOT / "fixtures/build/source.bin"
    if digest_bytes(source.read_bytes()) != closure.inputs[0].digest:
        return fail("fixture source digest drift")
    if recipe.recipe_digest != closure.recipe_digest or recipe.recipe_id != closure.recipe_id:
        return fail("recipe/source closure binding drift")
    print(f"F04 DRIFT: PASS schemas={len(schemas)} builders=2 closure={closure.closure_digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
