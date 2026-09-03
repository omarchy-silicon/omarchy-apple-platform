#!/usr/bin/env python3
"""Check Q-00 generated outputs and schema/resource drift without network access."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from omarchy_intake.canonical import canonical_bytes, content_digest  # noqa: E402
from omarchy_intake.validate import validate_dataset_file  # noqa: E402
from tools.intake.generate import build  # noqa: E402


def main() -> int:
    manifest_path = ROOT / "data/intake/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = build()
    if canonical_bytes(manifest) != canonical_bytes(expected):
        raise SystemExit("DRIFT: manifest is not the deterministic generator output")
    package_schema = ROOT / "src/omarchy_intake/resources/intake-dataset.schema.json"
    if not package_schema.is_file():
        raise SystemExit("DRIFT: packaged schema is missing")
    result = validate_dataset_file(manifest_path, root=ROOT)
    referenced = {Path(source["snapshot_path"]).resolve() for source in manifest["sources"]}
    snapshot_dir = ROOT / "data/intake/sources"
    actual = {path.resolve() for path in snapshot_dir.iterdir() if path.is_file() and not path.is_symlink()}
    if actual != referenced:
        raise SystemExit("DRIFT: unindexed or missing source snapshot")
    print(f"DRIFT: PASS dataset_digest={result.dataset_digest}; sources={result.source_count}; records={result.record_count}; residuals={result.residual_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
