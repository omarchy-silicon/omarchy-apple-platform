from __future__ import annotations

import copy
import json
import socket
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from jsonschema import Draft202012Validator

from omarchy_intake import validate_dataset, validate_dataset_file
from omarchy_intake.errors import IntakeValidationError

ROOT = Path(__file__).parents[1]
MANIFEST = ROOT / "data/intake/manifest.json"


def dataset() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


class IntakeDatasetTests(unittest.TestCase):
    def test_bounded_dataset_accepts_and_lock_matches(self):
        result = validate_dataset_file(MANIFEST, root=ROOT)
        self.assertEqual((result.source_count, result.record_count, result.projection_count, result.residual_count), (3, 1, 1, 4))
        self.assertEqual(result.dataset_digest, json.loads((ROOT / "data/intake/manifest.lock.json").read_text())["dataset_digest"])

    def test_source_digest_mismatch_rejects(self):
        value = dataset()
        value["sources"][0]["content_digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(IntakeValidationError, "DIGEST_MISMATCH"):
            validate_dataset(value, root=ROOT)

    def test_apple_mutable_url_requires_snapshot_revision(self):
        value = dataset()
        value["sources"][0]["canonical_url"] += "?refresh=1"
        with self.assertRaisesRegex(IntakeValidationError, "SOURCE_URL_INVALID"):
            validate_dataset(value, root=ROOT)
        value = dataset()
        value["sources"][0]["revision"] = "document:live"
        with self.assertRaisesRegex(IntakeValidationError, "SOURCE_REVISION_INVALID"):
            validate_dataset(value, root=ROOT)

    def test_upstream_must_use_full_commit_url_and_matching_revision(self):
        value = dataset()
        source = next(item for item in value["sources"] if item["authority_class"] == "linux-upstream")
        source["canonical_url"] = source["canonical_url"].replace("b6935375d5360c166efcf2e755513caad2be6b01", "b693537")
        with self.assertRaisesRegex(IntakeValidationError, "SOURCE_REVISION_INVALID"):
            validate_dataset(value, root=ROOT)

    def test_unsupported_authority_rejects(self):
        value = dataset()
        value["sources"][0]["authority_class"] = "community-blog"
        with self.assertRaisesRegex(IntakeValidationError, "UNSUPPORTED_ENUM"):
            validate_dataset(value, root=ROOT)

    def test_uncited_and_cross_subject_claims_reject(self):
        value = dataset()
        claim = value["records"][0]["claims"][0]
        claim["source_refs"] = []
        with self.assertRaisesRegex(IntakeValidationError, "UNCITED_CLAIM"):
            validate_dataset(value, root=ROOT)
        value = dataset()
        value["records"][0]["claims"][0]["subject"] = "apple:j293"
        with self.assertRaisesRegex(IntakeValidationError, "CLAIM_SUBJECT_MISMATCH"):
            validate_dataset(value, root=ROOT)

    def test_conflicting_normalized_claims_reject_without_contradiction(self):
        value = dataset()
        original = value["records"][0]["claims"][0]
        conflict = copy.deepcopy(original)
        conflict["claim_id"] = "board-identity-alt"
        conflict["normalized_value"]["apple_board_selector"] = "j293"
        value["records"][0]["claims"].append(conflict)
        value["records"][0]["claims"].sort(key=lambda item: item["claim_id"])
        with self.assertRaisesRegex(IntakeValidationError, "CONFLICTING_CLAIMS"):
            validate_dataset(value, root=ROOT)

    def test_duplicate_and_reverse_semantic_arrays_reject(self):
        value = dataset()
        claims = value["records"][0]["claims"]
        claims.reverse()
        with self.assertRaisesRegex(IntakeValidationError, "UNSORTED_COLLECTION"):
            validate_dataset(value, root=ROOT)
        value = dataset()
        value["records"][0]["apple_board_selectors"].append("j313")
        with self.assertRaisesRegex(IntakeValidationError, "DUPLICATE_SEMANTIC_KEY"):
            validate_dataset(value, root=ROOT)

    def test_projection_staleness_and_board_laundering_reject(self):
        value = dataset()
        value["projections"][0]["dataset_digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(IntakeValidationError, "STALE_PROJECTION"):
            validate_dataset(value, root=ROOT)
        value = dataset()
        value["projections"][0]["payload"]["board_id"] = "apple:j293"
        with self.assertRaisesRegex(IntakeValidationError, "PROJECTION_MISMATCH"):
            validate_dataset(value, root=ROOT)

    def test_nested_unknown_field_is_rejected_by_schema(self):
        value = dataset()
        value["records"][0]["claims"][0]["normalized_value"]["unexpected"] = True
        with self.assertRaisesRegex(IntakeValidationError, "UNKNOWN_FIELD"):
            validate_dataset(value, root=ROOT)

    def test_schema_selects_claim_type_shape(self):
        value = dataset()
        claim = value["records"][0]["claims"][0]
        claim["normalized_value"] = {"soc_id": "t8103", "display_name": "Apple M1"}
        schema = json.loads((ROOT / "src/omarchy_intake/resources/intake-dataset.schema.json").read_text(encoding="utf-8"))
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(value)))

    def test_unreferenced_source_rejects(self):
        value = dataset()
        extra = copy.deepcopy(value["sources"][0])
        extra["source_id"] = "unused-source"
        value["sources"].append(extra)
        value["sources"].sort(key=lambda item: item["source_id"])
        value["source_index"].append({"source_id": "unused-source", "content_digest": extra["content_digest"]})
        value["source_index"].sort(key=lambda item: item["source_id"])
        with self.assertRaisesRegex(IntakeValidationError, "UNREFERENCED_SOURCE"):
            validate_dataset(value, root=ROOT)

    def test_no_network_side_effect(self):
        with mock.patch.object(socket, "socket", side_effect=AssertionError("network attempted")):
            result = validate_dataset_file(MANIFEST, root=ROOT)
        self.assertEqual(result.dataset_digest, json.loads((ROOT / "data/intake/manifest.lock.json").read_text())["dataset_digest"])

    def test_cli_is_deterministic_and_offline(self):
        command = [sys.executable, "-m", "omarchy_intake", "validate", "--manifest", str(MANIFEST), "--root", str(ROOT), "--offline"]
        first = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=True)
        second = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=True)
        self.assertEqual(first.stdout, second.stdout)
        self.assertIn('"decision":"ACCEPT"', first.stdout)


if __name__ == "__main__":
    unittest.main()
