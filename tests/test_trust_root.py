from __future__ import annotations

import base64
import copy
import io
import json
import subprocess
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from omarchy_platform.canonical import auth_preimage, canonical_bytes
from omarchy_trust import ReplaySnapshot, TrustAnchors, TrustFailure, TrustedTrustContext, key_id, verify_artifact_bytes, verify_document, verify_root_bundle
from omarchy_trust.constants import ROLE_TO_SIGNER, TRUST_PREIMAGE_DOMAIN

ROOT = Path(__file__).parents[1]
NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)
REPOSITORY = "omarchy-silicon/omarchy-apple-platform"


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _sign(private: Ed25519PrivateKey, value: dict, domain: str, key: str, role: str | None = None) -> dict:
    preimage = (domain.encode("ascii") + b"\x00" + canonical_bytes({name: item for name, item in value.items() if name != "signatures"}))
    signature = {
        "key_id": key,
        "algorithm": "ed25519",
        "signature_format": "raw-ed25519/v1",
        "signature": _b64(private.sign(preimage)),
    }
    if role is not None:
        signature["signer_role"] = role
    return signature


class TrustRootTests(unittest.TestCase):
    def setUp(self):
        self.root_keys = [Ed25519PrivateKey.generate() for _ in range(5)]
        self.role_keys = {role: [Ed25519PrivateKey.generate() for _ in range(3)] for role in ("targets", "snapshot", "timestamp", "artifact", "package-index", "emergency/recovery")}
        self.root_public = {key_id(key.public_key().public_bytes_raw()): key.public_key().public_bytes_raw() for key in self.root_keys}
        self.anchors = TrustAnchors.from_public_keys(self.root_public)
        self.bundle, self.private_by_id = self._bundle()
        self.document = self._document()

    def _bundle(self, *, sequence: int = 1, issued: str = "2026-01-01T00:00:00Z", expires: str = "2026-12-01T00:00:00Z"):
        role_ids = {}
        private_by_id = {}
        for role, keys in self.role_keys.items():
            role_ids[role] = sorted(key_id(key.public_key().public_bytes_raw()) for key in keys)
            for key in keys:
                private_by_id[key_id(key.public_key().public_bytes_raw())] = key
        keys = []
        for role, ids in role_ids.items():
            for kid in ids:
                public = private_by_id[kid].public_key().public_bytes_raw()
                custody = "online-constrained" if role in {"snapshot", "timestamp"} or (role in {"targets", "artifact", "package-index"} and kid == ids[-1]) else "offline"
                keys.append({"key_id": kid, "public_key": _b64(public), "role": role, "custody": custody, "repository": REPOSITORY, "channel": "stable", "path_prefix": "*", "not_before": "2026-01-01T00:00:00Z", "not_after": "2029-01-01T00:00:00Z"})
        keys.sort(key=lambda item: item["key_id"])
        roles = []
        payloads = {
            "targets": ["board-registry/v1", "installer-plan/v1", "platform-manifest/v1", "qualification-record/v1"],
            "artifact": ["boot-health/v1", "boot-success-mark/v1", "dtb-mutation-envelope/v1"],
            "emergency/recovery": ["owner-approval/v1"],
            "snapshot": [], "timestamp": [], "package-index": [], "root": [],
        }
        for role in ("root", "targets", "snapshot", "timestamp", "artifact", "package-index", "emergency/recovery"):
            ids = sorted(self.root_public) if role == "root" else role_ids[role]
            roles.append({"role": role, "threshold": {"root": 3, "targets": 2, "snapshot": 2, "timestamp": 2, "artifact": 2, "package-index": 2, "emergency/recovery": 3}[role], "key_ids": ids, "payload_types": sorted(payloads[role])})
        delegations = [{"key_id": item["key_id"], "role": item["role"], "custody": item["custody"], "repository": item["repository"], "channel": item["channel"], "path_prefix": item["path_prefix"]} for item in keys]
        bundle = {"format": "omarchy-trust-root/v1", "version": "v1", "sequence": sequence, "repository": REPOSITORY, "channel": "stable", "issued_at": issued, "expires_at": expires, "roles": roles, "keys": keys, "delegations": delegations, "revocations": [], "freeze": [], "rollback": [], "signatures": []}
        signatures = [_sign(private, bundle, TRUST_PREIMAGE_DOMAIN, key_id(private.public_key().public_bytes_raw())) for private in sorted(self.root_keys, key=lambda item: key_id(item.public_key().public_bytes_raw()))[:3]]
        bundle["signatures"] = sorted(signatures, key=lambda item: item["key_id"])
        return bundle, private_by_id

    def _document(self):
        document = json.loads((ROOT / "fixtures/accepted/board-registry-v1.json").read_text())
        document["payload"]["issued_at"] = "2026-01-01T00:00:00Z"
        document["payload"]["expires_at"] = "2026-03-01T00:00:00Z"
        document["signatures"] = []
        docs = []
        role_private = sorted(self.role_keys["targets"], key=lambda item: key_id(item.public_key().public_bytes_raw()))
        for private in role_private[:2]:
            kid = key_id(private.public_key().public_bytes_raw())
            signed = copy.deepcopy(document)
            signed["signatures"] = [_sign(private, signed, "omarchy-auth-preimage/v1", kid, "board-admission")]
            docs.append(signed)
        return docs

    def test_real_ed25519_threshold_returns_immutable_context(self):
        context = verify_document(self.document[0], self.bundle, proof=(self.document[1],), replay_snapshot=ReplaySnapshot(), now=NOW, anchors=self.anchors)
        self.assertIsInstance(context, TrustedTrustContext)
        self.assertEqual(context.accepted_role, "targets")
        self.assertEqual(context.key_ids, tuple(sorted(context.key_ids)))
        self.assertEqual(context.threshold, 2)
        self.assertFalse(hasattr(context, "trusted"))
        with self.assertRaises(Exception):
            context.key_ids += ("bad",)

    def test_root_bundle_returns_typed_context(self):
        context = verify_root_bundle(self.bundle, now=NOW, anchors=self.anchors)
        self.assertEqual(context.accepted_role, "root")
        self.assertEqual(context.threshold, 3)
        self.assertTrue(context.schema_set_digest.startswith("sha256:"))

    def test_signature_mutation_and_threshold_shortfall_reject(self):
        bad = copy.deepcopy(self.document[0])
        bad["payload"]["document_id"] = "changed"
        with self.assertRaises(TrustFailure) as caught:
            verify_document(bad, self.bundle, proof=(self.document[1],), now=NOW, anchors=self.anchors)
        self.assertEqual(caught.exception.code, "TRUST_DIGEST_MISMATCH")
        with self.assertRaises(TrustFailure) as caught:
            verify_document(self.document[0], self.bundle, now=NOW, anchors=self.anchors)
        self.assertEqual(caught.exception.code, "TRUST_THRESHOLD_UNMET")

    def test_duplicate_signer_and_noncanonical_bytes_reject(self):
        with self.assertRaises(TrustFailure) as caught:
            verify_document(self.document[0], self.bundle, proof=(self.document[0],), now=NOW, anchors=self.anchors)
        self.assertEqual(caught.exception.code, "TRUST_THRESHOLD_UNMET")
        with self.assertRaises(TrustFailure) as caught:
            verify_document(canonical_bytes(self.document[0]) + b"\n", canonical_bytes(self.bundle), now=NOW, anchors=self.anchors)
        self.assertEqual(caught.exception.code, "TRUST_NONCANONICAL")

    def test_expiry_freeze_and_replay_are_fail_closed(self):
        expired, _ = self._bundle(expires="2026-01-14T00:00:00Z")
        with self.assertRaises(TrustFailure) as caught:
            verify_document(self.document[0], expired, proof=(self.document[1],), now=NOW, anchors=self.anchors)
        self.assertEqual(caught.exception.code, "TRUST_EXPIRED")
        frozen = copy.deepcopy(self.bundle)
        frozen["freeze"] = [{"scope": f"{REPOSITORY}:stable:board-registry/v1", "incident_id": "incident:one"}]
        frozen["signatures"] = [_sign(private, frozen, TRUST_PREIMAGE_DOMAIN, key_id(private.public_key().public_bytes_raw())) for private in sorted(self.root_keys, key=lambda item: key_id(item.public_key().public_bytes_raw()))[:3]]
        with self.assertRaises(TrustFailure) as caught:
            verify_document(self.document[0], frozen, proof=(self.document[1],), now=NOW, anchors=self.anchors)
        self.assertEqual(caught.exception.code, "TRUST_FROZEN")
        replay = ReplaySnapshot.from_mapping({f"{REPOSITORY}:stable:board-registry/v1": {"sequence": 2, "version": "", "metadata_digest": "sha256:" + "a" * 64}})
        with self.assertRaises(TrustFailure) as caught:
            verify_document(self.document[0], self.bundle, proof=(self.document[1],), replay_snapshot=replay, now=NOW, anchors=self.anchors)
        self.assertEqual(caught.exception.code, "TRUST_REPLAY")

    def test_unprovisioned_default_anchors_and_exact_artifacts(self):
        with self.assertRaises(TrustFailure) as caught:
            verify_document(self.document[0], self.bundle, proof=(self.document[1],), now=NOW)
        self.assertEqual(caught.exception.code, "TRUST_ANCHORS_UNPROVISIONED")
        payload = b"signed artifact"
        digest = "sha256:" + __import__("hashlib").sha256(payload).hexdigest()
        self.assertEqual(verify_artifact_bytes(io.BytesIO(payload), digest, len(payload)), digest)
        with self.assertRaises(TrustFailure) as caught:
            verify_artifact_bytes(io.BytesIO(payload + b"!"), digest, len(payload))
        self.assertEqual(caught.exception.code, "TRUST_ARTIFACT_SIZE")

    def test_rotation_requires_higher_sequence_and_overlap(self):
        rotated, _ = self._bundle(sequence=2)
        old_ids = sorted(self.root_public)
        rotated["rotation"] = {"from_sequence": 1, "to_sequence": 2, "old_root_key_ids": old_ids, "new_root_key_ids": old_ids}
        rotated["signatures"] = [_sign(private, rotated, TRUST_PREIMAGE_DOMAIN, key_id(private.public_key().public_bytes_raw())) for private in sorted(self.root_keys, key=lambda item: key_id(item.public_key().public_bytes_raw()))[:3]]
        context = verify_document(self.document[0], rotated, proof=(self.document[1],), now=NOW, anchors=self.anchors, previous_bundle=self.bundle)
        self.assertEqual(context.replay_proposal.sequence, 2)
        broken = copy.deepcopy(rotated)
        broken["rotation"]["from_sequence"] = 0
        broken["signatures"] = [_sign(private, broken, TRUST_PREIMAGE_DOMAIN, key_id(private.public_key().public_bytes_raw())) for private in sorted(self.root_keys, key=lambda item: key_id(item.public_key().public_bytes_raw()))[:3]]
        with self.assertRaises(TrustFailure) as caught:
            verify_document(self.document[0], broken, proof=(self.document[1],), now=NOW, anchors=self.anchors, previous_bundle=self.bundle)
        self.assertEqual(caught.exception.code, "TRUST_ROTATION_INVALID")

    def test_fixture_manifest_is_canonical_and_complete(self):
        manifest = json.loads((ROOT / "fixtures/trust/fixture-manifest.json").read_text())
        self.assertEqual(canonical_bytes(manifest), (ROOT / "fixtures/trust/fixture-manifest.json").read_bytes().rstrip(b"\n"))
        self.assertEqual(len(manifest["vectors"]), 18)


if __name__ == "__main__":
    unittest.main()
