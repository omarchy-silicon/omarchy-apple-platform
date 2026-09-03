#!/usr/bin/env python3
"""Build the checked-in Q-00 manifest and deterministic board projection offline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from omarchy_intake.canonical import canonical_bytes, content_digest, intake_digest  # noqa: E402
from omarchy_intake.validate import _projection_for, dataset_digest_for  # noqa: E402

GENERATED_AT = "2026-09-03T00:00:00Z"
RECORD_ID = "apple:j313"
SOURCES = {
    "apple-air-m1-model": {
        "authority_class": "apple-official",
        "canonical_url": "https://support.apple.com/en-la/102869",
        "section": "MacBook Air (M1, 2020)",
        "lines": [1, 1],
        "path": "data/intake/sources/apple-air-m1-model.json",
    },
    "apple-air-m1-specs": {
        "authority_class": "apple-official",
        "canonical_url": "https://support.apple.com/en-asia/111883",
        "section": "Chip",
        "lines": [1, 1],
        "path": "data/intake/sources/apple-air-m1-specs.json",
    },
    "linux-t8103-j313": {
        "authority_class": "linux-upstream",
        "canonical_url": "https://github.com/torvalds/linux/blob/b6935375d5360c166efcf2e755513caad2be6b01/arch/arm64/boot/dts/apple/t8103-j313.dts",
        "section": "compatible and model",
        "lines": [1, 1],
        "path": "data/intake/sources/linux-t8103-j313.json",
    },
}


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build() -> dict:
    sources = []
    for source_id, metadata in sorted(SOURCES.items()):
        snapshot = (ROOT / metadata["path"]).read_bytes()
        digest = content_digest(snapshot)
        sources.append({
            "source_id": source_id,
            "authority_class": metadata["authority_class"],
            "canonical_url": metadata["canonical_url"],
            "revision": "snapshot:" + digest if metadata["authority_class"] == "apple-official" else "commit:b6935375d5360c166efcf2e755513caad2be6b01",
            "retrieved_at": GENERATED_AT,
            "content_digest": digest,
            "media_type": "application/json",
            "locator": {"section": metadata["section"], "lines": metadata["lines"]},
            "subject_refs": [RECORD_ID],
            "snapshot_path": metadata["path"],
            "response_metadata": {"status_code": 200, "content_type": "application/json", "content_length": len(snapshot), "etag": None, "last_modified": None},
        })
    records = [_load(path) for path in sorted((ROOT / "data/intake/records").glob("*.json"))]
    schema = _load(ROOT / "src/omarchy_intake/resources/intake-dataset.schema.json")
    schema_set_digest = content_digest(canonical_bytes(schema))
    dataset = {
        "schema": "intake-dataset/v1",
        "dataset_id": "omarchy-apple-silicon-intake",
        "dataset_revision": "2026-09-03.r1",
        "schema_set_digest": schema_set_digest,
        "generated_at": GENERATED_AT,
        "sources": sources,
        "source_index": [{"source_id": source["source_id"], "content_digest": source["content_digest"]} for source in sources],
        "records": records,
        "record_index": [],
        "contradictions": [],
        "projections": [],
        "residuals": [
            {"residual_id": "coverage-newer-silicon", "subject": "apple-silicon-program", "reason": "Only the independently cited M1 J313 identity slice is imported in this bounded release.", "state": "not-covered"},
            {"residual_id": "firmware-boot-kernel", "subject": RECORD_ID, "reason": "Firmware schema, boot behavior, and Omarchy kernel capability evidence remain unverified.", "state": "unknown"},
            {"residual_id": "graphics-hardware", "subject": RECORD_ID, "reason": "Apple documentation identifies the GPU but no physical graphics qualification is asserted.", "state": "unknown"},
            {"residual_id": "qualification-physical", "subject": RECORD_ID, "reason": "No Q-01 physical qualification record exists; this dataset cannot establish support.", "state": "blocked"},
        ],
    }
    dataset["record_index"] = [{"record_id": record["record_id"], "record_revision": record["record_revision"], "record_digest": intake_digest("record/v1", record)} for record in records]
    dataset_digest = dataset_digest_for(dataset)
    dataset["projections"] = [_projection_for(record, dataset_digest, intake_digest("record/v1", record)) for record in records if any(claim["claim_type"] == "board-identity" and claim["state"] == "confirmed" for claim in record["claims"])]
    return dataset


def main() -> int:
    dataset = build()
    manifest = ROOT / "data/intake/manifest.json"
    manifest.write_bytes(canonical_bytes(dataset) + b"\n")
    lock = {"schema": "intake-manifest-lock/v1", "manifest_path": "data/intake/manifest.json", "dataset_digest": dataset_digest_for(dataset)}
    (ROOT / "data/intake/manifest.lock.json").write_bytes(canonical_bytes(lock) + b"\n")
    print(json.dumps({"manifest": str(manifest.relative_to(ROOT)), "dataset_digest": lock["dataset_digest"], "records": len(dataset["records"]), "sources": len(dataset["sources"]), "projections": len(dataset["projections"]), "residuals": len(dataset["residuals"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
