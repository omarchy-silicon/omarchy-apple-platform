import copy
import json
import unittest
from pathlib import Path

from omarchy_platform.models import BoardRegistry, PlatformManifest
import omarchy_platform.models as models
from omarchy_platform.validate import admit_bundle, validate_foundation_document
from omarchy_platform.errors import SchemaError

ROOT = Path(__file__).parents[1]
KINDS = ("board-registry/v1", "platform-manifest/v1", "installer-plan/v1", "qualification-record/v1", "boot-health/v1", "owner-approval/v1", "boot-success-mark/v1", "dtb-mutation-envelope/v1")


def bundle():
    return {kind: json.loads((ROOT / "fixtures/accepted" / f"{kind.replace('/', '-')}.json").read_text()) for kind in KINDS}


class ConformanceTests(unittest.TestCase):
    def test_accepted_bundle_is_conformant_but_untrusted(self):
        result = admit_bundle(bundle())
        self.assertEqual((result.conformant, result.trusted, result.code), (True, False, "ACCEPT"))

    def test_missing_and_extra_inputs_fail_closed(self):
        docs = bundle()
        docs.pop("boot-health/v1")
        result = admit_bundle(docs)
        self.assertFalse(result.conformant)
        self.assertEqual(result.code, "PARSE_SCHEMA_FAILURE")
        docs = bundle()
        docs["unexpected/v1"] = {}
        self.assertFalse(admit_bundle(docs).conformant)

    def test_cross_document_hostile_cases(self):
        cases = []
        docs = bundle()
        docs["platform-manifest/v1"]["payload"]["board_registry_digest"] = "sha256:" + "0" * 64
        cases.append(docs)
        docs = bundle()
        docs["installer-plan/v1"]["payload"]["selection"]["manifest_id"] = "transplanted"
        cases.append(docs)
        docs = bundle()
        docs["qualification-record/v1"]["payload"]["outcome"] = "blocked"
        cases.append(docs)
        docs = bundle()
        docs["boot-health/v1"]["payload"]["checks"][0]["status"] = "fail"
        cases.append(docs)
        docs = bundle()
        docs["boot-success-mark/v1"]["payload"]["core_digest"] = "sha256:" + "1" * 64
        cases.append(docs)
        docs = bundle()
        docs["dtb-mutation-envelope/v1"]["payload"]["source_digest"] = "sha256:" + "2" * 64
        cases.append(docs)
        for hostile in cases:
            self.assertFalse(admit_bundle(hostile).conformant)

    def test_shape_hostiles_and_immutable_models(self):
        value = bundle()["board-registry/v1"]["payload"]
        with self.assertRaises(SchemaError) as caught:
            validate_foundation_document({**value, "unexpected": True}, "board-registry/v1")
        self.assertEqual(caught.exception.code, "UNKNOWN_FIELD")
        hostile = copy.deepcopy(value)
        hostile["boards"].append(copy.deepcopy(hostile["boards"][0]))
        with self.assertRaises(SchemaError) as caught:
            BoardRegistry.from_payload(hostile)
        self.assertEqual(caught.exception.code, "DUPLICATE_SEMANTIC_KEY")
        model = PlatformManifest.from_document(bundle()["platform-manifest/v1"])
        with self.assertRaises(AttributeError):
            model.payload = {}
        with self.assertRaises(TypeError):
            BoardRegistry(value)

    def test_recursive_type_fuzz_is_deterministic_for_all_payloads(self):
        for kind in KINDS:
            for hostile in (None, [], {}, {"schema": []}, {"schema": kind, "boards": [None]}, {"schema": kind, "checks": [None]}):
                with self.subTest(kind=kind, hostile=hostile):
                    try:
                        validate_foundation_document(hostile, kind)
                    except SchemaError as error:
                        self.assertIn(error.code, {"PARSE_SCHEMA_FAILURE", "UNKNOWN_FIELD", "RESOURCE_LIMIT", "CROSS_DOCUMENT_MISMATCH", "SIGNATURE_CONTEXT_MISMATCH"})

    def test_constructor_token_and_direct_type_probes_are_closed(self):
        self.assertFalse(hasattr(models, "_TOKEN"))
        model = BoardRegistry.from_document(bundle()["board-registry/v1"])
        with self.assertRaises(TypeError):
            type(model)(model.payload)
