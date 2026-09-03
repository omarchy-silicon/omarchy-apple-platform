import copy
import json
import unittest
from pathlib import Path

from omarchy_platform.models import BoardRegistry, PlatformManifest
import omarchy_platform.models as models
from jsonschema import Draft202012Validator
from omarchy_platform.validate import admit_bundle, validate_foundation_document
from omarchy_platform.errors import SchemaError

ROOT = Path(__file__).parents[1]
KINDS = ("board-registry/v1", "platform-manifest/v1", "installer-plan/v1", "qualification-record/v1", "boot-health/v1", "owner-approval/v1", "boot-success-mark/v1", "dtb-mutation-envelope/v1")


def bundle():
    return {kind: json.loads((ROOT / "fixtures/accepted" / f"{kind.replace('/', '-')}.json").read_text()) for kind in KINDS}


class ConformanceTests(unittest.TestCase):
    def test_accepted_bundle_is_conformant_but_untrusted(self):
        result = admit_bundle(bundle())
        self.assertEqual((result.conformant, result.trusted, result.code, result.structural_only, result.release_eligible), (True, False, "STRUCTURAL_ONLY", True, False))

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

    def test_every_target_has_its_own_qualification_record(self):
        docs = bundle()
        manifest = docs["platform-manifest/v1"]["payload"]
        second = copy.deepcopy(docs["board-registry/v1"]["payload"]["boards"][1])
        manifest["board_targets"].append(second["board_id"])
        manifest["board_identities"].append({"board_id": second["board_id"], **second["identity_match"], "soc_id": second["soc_id"]})
        manifest["qualification_bindings"].append({"board_id": second["board_id"], "qualification_record_id": docs["qualification-record/v1"]["payload"]["document_id"], "required_outcome": "pass"})
        self.assertFalse(admit_bundle(docs).conformant)

        docs = bundle()
        docs["platform-manifest/v1"]["payload"]["qualification_bindings"].append({"board_id": "apple:j293", "qualification_record_id": "extra-record", "required_outcome": "pass"})
        self.assertFalse(admit_bundle(docs).conformant)

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

    def test_schema_python_parity_for_missing_unknown_zero_and_empty_fields(self):
        signed = json.loads((ROOT / "schemas/signed-document/v1/signed-document.schema.json").read_text())
        from referencing import Registry, Resource
        registry = Registry()
        for path in sorted((ROOT / "schemas").glob("**/*.schema.json")):
            document = json.loads(path.read_text())
            registry = registry.with_resource(document["$id"], Resource.from_contents(document))
        validator = Draft202012Validator(signed, registry=registry)
        fixture = bundle()["board-registry/v1"]
        missing = json.loads(json.dumps(fixture)); del missing["payload"]["boards"]
        self.assertTrue(list(validator.iter_errors(missing)))
        self.assertTrue(list(validator.iter_errors({**fixture, "payload": {**fixture["payload"], "unexpected": True}})))
        zero = json.loads(json.dumps(fixture)); zero["payload"]["schema_set_digest"] = "sha256:" + "0" * 64
        self.assertTrue(list(validator.iter_errors(zero)))
        empty = json.loads(json.dumps(fixture)); empty["payload"]["boards"][0]["physical_capabilities"] = []
        board_schema = json.loads((ROOT / "schemas/board-registry/v1/board-registry.schema.json").read_text())
        board_validator = Draft202012Validator(board_schema, registry=registry)
        self.assertTrue(list(board_validator.iter_errors(empty["payload"])))
        comma_revision = json.loads(json.dumps(fixture)); comma_revision["payload"]["registry_revision"] = "rev,comma"
        unknown_capability = json.loads(json.dumps(fixture)); unknown_capability["payload"]["capability_vocabulary"] = ["zzz"]
        self.assertTrue(list(board_validator.iter_errors(comma_revision["payload"])))
        self.assertTrue(list(board_validator.iter_errors(unknown_capability["payload"])))
        nested_missing = json.loads(json.dumps(fixture)); del nested_missing["payload"]["boards"][0]["soc_id"]
        nested_unknown = json.loads(json.dumps(fixture)); nested_unknown["payload"]["boards"][0]["unexpected"] = True
        self.assertTrue(list(validator.iter_errors(nested_missing)))
        self.assertTrue(list(validator.iter_errors(nested_unknown)))
        for value, kind in ((missing["payload"], "board-registry/v1"), (zero["payload"], "board-registry/v1"), (empty["payload"], "board-registry/v1")):
            with self.assertRaises(Exception):
                validate_foundation_document(value, kind)
        manifest = json.loads(json.dumps(bundle()["platform-manifest/v1"]))
        manifest["payload"]["artifacts"][0]["component_id"] = "unknown-component"
        manifest_schema = json.loads((ROOT / "schemas/platform-manifest/v1/platform-manifest.schema.json").read_text())
        manifest_validator = Draft202012Validator(manifest_schema, registry=registry)
        self.assertTrue(list(manifest_validator.iter_errors(manifest["payload"])))
        with self.assertRaises(Exception):
            validate_foundation_document(manifest, "platform-manifest/v1")
