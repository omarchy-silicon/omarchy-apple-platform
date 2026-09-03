import json
import subprocess
import sys
import shutil
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from omarchy_platform.canonical import canonical_bytes, payload_digest, schema_set_digest
from omarchy_platform.constants import AUTHENTICATED_PAYLOAD_TYPES, LIMITS, SCHEMA_SET_DIGEST
from omarchy_platform.errors import ParseError, SchemaError
from omarchy_platform.strictjson import parse
from omarchy_platform.validate import validate_foundation_document

ROOT = Path(__file__).parents[1]


def schema_registry(documents):
    registry = Registry()
    for _path, document in documents:
        registry = registry.with_resource(document["$id"], Resource.from_contents(document))
    return registry


class FoundationTests(unittest.TestCase):
    def test_draft_2020_12_schema_artifacts_execute_offline(self):
        schema_paths = sorted((ROOT / "schemas").glob("**/*.schema.json"))
        self.assertEqual(len(schema_paths), 11)
        documents = [(path, json.loads(path.read_text())) for path in schema_paths]
        registry = Registry()
        for _path, document in documents:
            Draft202012Validator.check_schema(document)
            registry = registry.with_resource(document["$id"], Resource.from_contents(document))
        signed = next(document for path, document in documents if path.name == "signed-document.schema.json")
        signed_validator = Draft202012Validator(signed, registry=registry)
        for payload_type in AUTHENTICATED_PAYLOAD_TYPES:
            fixture = json.loads((ROOT / "fixtures/accepted" / (payload_type.replace("/", "-") + ".json")).read_text())
            self.assertEqual(list(signed_validator.iter_errors(fixture)), [])
            payload_schema = next(document for path, document in documents if path.parent.parent.name == payload_type.split("/")[0])
            self.assertEqual(list(Draft202012Validator(payload_schema, registry=registry).iter_errors(fixture["payload"])), [])

    def test_schema_artifacts_reject_hostile_unknown_field_and_wrong_type(self):
        schema = json.loads((ROOT / "schemas/signed-document/v1/signed-document.schema.json").read_text())
        common = json.loads((ROOT / "schemas/common/v1/common.schema.json").read_text())
        registry = schema_registry([(Path("signed"), schema), (Path("common"), common)])
        validator = Draft202012Validator(schema, registry=registry)
        fixture = json.loads((ROOT / "fixtures/accepted/board-registry-v1.json").read_text())
        self.assertTrue(list(validator.iter_errors({**fixture, "unknown": True})))
        self.assertTrue(list(validator.iter_errors({**fixture, "payload_type": "not-a-payload/v9"})))
        for field, value in (("domain", "wrong-domain"), ("context", "wrong-context")):
            with self.subTest(field=field):
                self.assertTrue(list(validator.iter_errors({**fixture, field: value})))
        wrong_role = {**fixture, "signatures": [{**fixture["signatures"][0], "signer_role": "manifest-release"}]}
        self.assertTrue(list(validator.iter_errors(wrong_role)))

    def test_signature_role_order_uniqueness_and_base64url_are_closed(self):
        fixture = json.loads((ROOT / "fixtures/accepted/board-registry-v1.json").read_text())
        wrong_role = {**fixture, "signatures": [{**fixture["signatures"][0], "signer_role": "manifest-release"}]}
        with self.assertRaises(SchemaError) as caught:
            validate_foundation_document(wrong_role, "board-registry/v1")
        self.assertEqual(caught.exception.code, "SIGNATURE_CONTEXT_MISMATCH")
        first = {**fixture["signatures"][0], "key_id": "key-z"}
        second = {**fixture["signatures"][0], "key_id": "key-a"}
        with self.assertRaises(SchemaError) as caught:
            validate_foundation_document({**fixture, "signatures": [first, second]}, "board-registry/v1")
        self.assertEqual(caught.exception.code, "PARSE_SCHEMA_FAILURE")
        with self.assertRaises(SchemaError) as caught:
            validate_foundation_document({**fixture, "signatures": [first, first]}, "board-registry/v1")
        self.assertEqual(caught.exception.code, "DUPLICATE_SEMANTIC_KEY")
        noncanonical = {**fixture["signatures"][0], "signature": "A" * 85 + "B"}
        with self.assertRaises(SchemaError):
            validate_foundation_document({**fixture, "signatures": [noncanonical]}, "board-registry/v1")

    def test_all_eight_accepted_envelopes_validate(self):
        for payload_type in AUTHENTICATED_PAYLOAD_TYPES:
            path = ROOT / "fixtures/accepted" / (payload_type.replace("/", "-") + ".json")
            value = parse(path.read_bytes())
            self.assertEqual(validate_foundation_document(value, payload_type)["payload_type"], payload_type)

    def test_hostile_transport_inputs_fail_without_partial_value(self):
        cases = [
            (b"\xef\xbb\xbf{}", "PARSE_SCHEMA_FAILURE"), (b"\xff{}", "PARSE_SCHEMA_FAILURE"),
            (b'{"a":1}{"b":2}', "PARSE_SCHEMA_FAILURE"), (b'{"a":1,"a":2}', "DUPLICATE_SEMANTIC_KEY"),
            (b"-0", "PARSE_SCHEMA_FAILURE"), (b"-0.0", "PARSE_SCHEMA_FAILURE"),
            (b"1.0", "PARSE_SCHEMA_FAILURE"), (b"1e3", "PARSE_SCHEMA_FAILURE"),
            (b"NaN", "PARSE_SCHEMA_FAILURE"), (b"Infinity", "PARSE_SCHEMA_FAILURE"),
            (b"1e400", "PARSE_SCHEMA_FAILURE"), (b'{"x": "' + b"a" * 4097 + b'"}', "RESOURCE_LIMIT"),
        ]
        for data, code in cases:
            with self.subTest(data=data):
                with self.assertRaises(ParseError) as caught:
                    parse(data)
                self.assertEqual(caught.exception.code, code)
                self.assertTrue(caught.exception.path.startswith("$"))
                self.assertEqual(caught.exception.phase, "P0")
        self.assertEqual(parse(b" \t\n\r1\r\n \t"), 1)
        for whitespace in (b"\xc2\xa0", b"\xe2\x80\x83", b"\x0b", b"\x0c"):
            with self.subTest(whitespace=whitespace):
                with self.assertRaises(ParseError):
                    parse(b"1" + whitespace)
                with self.assertRaises(ParseError):
                    parse(b"[" + whitespace + b"1]")

    def test_resource_limits_are_inclusive_at_boundary(self):
        self.assertEqual(parse(str(LIMITS["max_integer_magnitude"]).encode()), LIMITS["max_integer_magnitude"])
        with self.assertRaises(ParseError) as caught:
            parse(str(LIMITS["max_integer_magnitude"] + 1).encode())
        self.assertEqual(caught.exception.code, "RESOURCE_LIMIT")
        self.assertEqual(len(parse(b"[" + b"0," * 1023 + b"0]")), 1024)
        with self.assertRaises(ParseError):
            parse(b"[" + b"0," * 1024 + b"0]")
        self.assertEqual(len(parse(b'{"x":"' + b"a" * 4096 + b'"}')["x"]), 4096)

    def test_depth_and_total_string_limits(self):
        nested = b"0"
        for _ in range(32):
            nested = b"[" + nested + b"]"
        self.assertIsNotNone(parse(nested))
        with self.assertRaises(ParseError):
            parse(b"[" * 33 + b"0" + b"]" * 33)
        many = {str(i): "x" * 4096 for i in range(64)}
        with self.assertRaises(ParseError) as caught:
            parse(json.dumps(many).encode())
        self.assertEqual(caught.exception.code, "RESOURCE_LIMIT")

    def test_canonical_order_and_digest_are_stable(self):
        self.assertEqual(canonical_bytes(parse(b'{"b":2,"a":1}')), b'{"a":1,"b":2}')
        self.assertEqual(canonical_bytes(1.0), b"1")
        self.assertEqual(canonical_bytes(parse(b"[3,2,1]")), b"[3,2,1]")
        self.assertEqual(payload_digest({"a": 1}), payload_digest({"a": 1}))
        a = parse((ROOT / "fixtures/canonicalization/order-a.json").read_bytes())
        b = parse((ROOT / "fixtures/canonicalization/order-b.json").read_bytes())
        self.assertEqual(canonical_bytes(a), canonical_bytes(b))
        self.assertEqual(canonical_bytes([1e-6, 1e-7, 1e20, 1e21]), b"[0.000001,1e-7,100000000000000000000,1e+21]")
        self.assertEqual(canonical_bytes({"é": "\u000a", "a": "😀"}), '{"a":"😀","é":"\\n"}'.encode())

    def test_schema_and_envelope_mismatch_fail_closed(self):
        fixture = json.loads((ROOT / "fixtures/accepted/board-registry-v1.json").read_text())
        with self.assertRaises(SchemaError) as caught:
            validate_foundation_document({**fixture, "payload_type": "boot-health/v1"}, "board-registry/v1")
        self.assertEqual(caught.exception.code, "SIGNATURE_CONTEXT_MISMATCH")
        bad = {**fixture, "payload": {**fixture["payload"], "unknown": True}}
        with self.assertRaises(SchemaError) as caught:
            validate_foundation_document(bad, "board-registry/v1")
        self.assertEqual(caught.exception.code, "UNKNOWN_FIELD")

    def test_schema_lock_digest_and_cli_smoke(self):
        lock = json.loads((ROOT / "schemas/schema-input.lock").read_text())
        self.assertEqual(schema_set_digest(lock), SCHEMA_SET_DIGEST)
        result = subprocess.run([sys.executable, "-m", "omarchy_platform", "schema", "list"], cwd=ROOT, text=True, capture_output=True, check=True)
        self.assertEqual(result.stdout.splitlines(), list(AUTHENTICATED_PAYLOAD_TYPES))
        result = subprocess.run([sys.executable, "-m", "omarchy_platform", "validate", "--type", "board-registry/v1", "--input", "fixtures/accepted/board-registry-v1.json"], cwd=ROOT, text=True, capture_output=True, check=True)
        self.assertIn('"foundation_valid": true', result.stdout)
        self.assertIn('"trusted": false', result.stdout)

    def test_drift_rejects_tampered_lock_reference_and_source(self):
        def run_tampered(mutator):
            with tempfile.TemporaryDirectory() as directory:
                copied = Path(directory) / "repo"
                shutil.copytree(ROOT, copied)
                mutator(copied)
                return subprocess.run([sys.executable, "tools/schema/drift.py"], cwd=copied, text=True, capture_output=True)

        def tamper_output_lock(copied):
            path = copied / "bindings/generated-output.lock"
            lock = json.loads(path.read_text())
            lock["extra"] = True
            path.write_text(json.dumps(lock))
        self.assertNotEqual(run_tampered(tamper_output_lock).returncode, 0)

        def tamper_reference(copied):
            path = copied / "schemas/schema-input.lock"
            lock = json.loads(path.read_text())
            lock["schema_entries"][0]["reference_digests"] = [{"reference_path": "schemas/common/v1/common.schema.json", "digest": "sha256:" + "0" * 64}]
            path.write_text(json.dumps(lock))
        self.assertNotEqual(run_tampered(tamper_reference).returncode, 0)

        def tamper_source(copied):
            path = copied / "schemas/common/v1/common.schema.json"
            path.write_bytes(path.read_bytes() + b" ")
        self.assertNotEqual(run_tampered(tamper_source).returncode, 0)


if __name__ == "__main__":
    unittest.main()
