import json
import subprocess
import sys
import unittest
from pathlib import Path

from omarchy_platform.canonical import canonical_bytes, payload_digest, schema_set_digest
from omarchy_platform.constants import AUTHENTICATED_PAYLOAD_TYPES, LIMITS, SCHEMA_SET_DIGEST
from omarchy_platform.errors import ParseError, SchemaError
from omarchy_platform.strictjson import parse
from omarchy_platform.validate import validate_document

ROOT = Path(__file__).parents[1]


class FoundationTests(unittest.TestCase):
    def test_all_eight_accepted_envelopes_validate(self):
        for payload_type in AUTHENTICATED_PAYLOAD_TYPES:
            path = ROOT / "fixtures/accepted" / (payload_type.replace("/", "-") + ".json")
            value = parse(path.read_bytes())
            self.assertEqual(validate_document(value, payload_type)["payload_type"], payload_type)

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

    def test_schema_and_envelope_mismatch_fail_closed(self):
        fixture = json.loads((ROOT / "fixtures/accepted/board-registry-v1.json").read_text())
        with self.assertRaises(SchemaError) as caught:
            validate_document({**fixture, "payload_type": "boot-health/v1"}, "board-registry/v1")
        self.assertEqual(caught.exception.code, "SIGNATURE_CONTEXT_MISMATCH")
        bad = {**fixture, "payload": {**fixture["payload"], "unknown": True}}
        with self.assertRaises(SchemaError) as caught:
            validate_document(bad, "board-registry/v1")
        self.assertEqual(caught.exception.code, "UNKNOWN_FIELD")

    def test_schema_lock_digest_and_cli_smoke(self):
        lock = json.loads((ROOT / "schemas/schema-input.lock").read_text())
        self.assertEqual(schema_set_digest(lock), SCHEMA_SET_DIGEST)
        result = subprocess.run([sys.executable, "-m", "omarchy_platform", "schema", "list"], cwd=ROOT, text=True, capture_output=True, check=True)
        self.assertEqual(result.stdout.splitlines(), list(AUTHENTICATED_PAYLOAD_TYPES))
        result = subprocess.run([sys.executable, "-m", "omarchy_platform", "validate", "--type", "board-registry/v1", "--input", "fixtures/accepted/board-registry-v1.json"], cwd=ROOT, text=True, capture_output=True, check=True)
        self.assertIn('"valid": true', result.stdout)


if __name__ == "__main__":
    unittest.main()
