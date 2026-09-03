"""Positive and hostile executable coverage for F-05 candidate assembly."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

from omarchy_candidate import CandidateAssemblyError, CandidateManifest, assemble_candidate, guard_manifest
from omarchy_candidate.models import _AuthorityCapability, _CAPABILITY_TOKEN, digest_bytes

ROOT = Path(__file__).parents[1]


def accepted() -> dict:
    return json.loads((ROOT / "fixtures/candidate/accepted-input.json").read_text())


class FixtureAuthority:
    def validate_state(self, platform_bytes, intake_bytes, qualification_bytes, *, board_id, profile_id, verification_time):
        if board_id != "apple:j313" or profile_id != "profile:j313-synthetic":
            raise ValueError("synthetic state mismatch")

    def verify_canonical(self, kind, source_bytes, *, digest, board_id, profile_id, channel, schema_set_digest, verification_time, subject):
        return _AuthorityCapability(kind, subject, digest, board_id, profile_id, channel, "2099-01-01T00:00:00Z", f"replay:{kind}", digest_bytes(source_bytes), schema_set_digest, _token=_CAPABILITY_TOKEN)


class FixtureArtifacts:
    def verify(self, digest, kind):
        return True

    def read(self, digest):
        expected = digest_bytes((ROOT / "fixtures/candidate/artifact.bin").read_bytes())
        if digest != expected:
            raise FileNotFoundError(digest)
        return (ROOT / "fixtures/candidate/artifact.bin").read_bytes()


def assemble(value=None):
    return assemble_candidate(value or accepted(), authority=FixtureAuthority(), artifacts=FixtureArtifacts(), verification_time="2026-09-03T00:00:00Z")


def set_path(value: dict, path: str, replacement: object) -> None:
    cursor = value
    bits = path.replace("]", "").replace("[", ".").split(".")
    for bit in bits[:-1]:
        cursor = cursor[int(bit)] if bit.isdigit() else cursor[bit]
    cursor[bits[-1]] = replacement


def apply_probe(value: dict, probe: dict) -> None:
    bits = probe["path"].replace("]", "").replace("[", ".").split(".")
    cursor = value
    for bit in bits[:-1]:
        cursor = cursor[int(bit)] if bit.isdigit() else cursor[bit]
    if probe["mutation"] == "delete":
        cursor.pop(int(bits[-1]) if bits[-1].isdigit() else bits[-1])
    else:
        cursor[bits[-1]] = probe["value"]


def test_synthetic_fully_qualified_candidate_is_deterministic_and_immutable() -> None:
    first = assemble()
    second = assemble()
    assert first.bytes() == second.bytes()
    assert CandidateManifest.from_dict(first.to_dict()).candidate_digest == first.candidate_digest
    assert first.candidate_digest.startswith("sha256:")
    with pytest.raises(AttributeError):
        first.candidate_digest = "sha256:" + "0" * 64
    with pytest.raises(TypeError):
        first.body_value["channel"] = "stable"
    with pytest.raises(TypeError):
        CandidateManifest({}, "sha256:" + "0" * 64)
    assert guard_manifest(first.bytes(), expected_digest=first.candidate_digest, board_id="apple:j313", profile_id="profile:j313-synthetic", channel="edge").candidate_digest == first.candidate_digest
    with pytest.raises(CandidateAssemblyError) as caught:
        guard_manifest(first.bytes(), expected_digest=first.candidate_digest, board_id="apple:j313", profile_id="profile:other", channel="edge")
    assert caught.value.code == "IDENTITY_MISMATCH"


def test_real_q00_q01_anchor_is_not_a_positive_fixture() -> None:
    real = accepted()
    real["qualification"]["outcome"] = "UNKNOWN"
    real["qualification"]["admission"] = "NOT_QUALIFIED"
    with pytest.raises(CandidateAssemblyError) as caught:
        assemble_candidate(real, authority=FixtureAuthority(), artifacts=FixtureArtifacts())
    assert caught.value.code == "QUALIFICATION_REQUIRED"


@pytest.mark.parametrize(
    ("path", "replacement", "code"),
    [
        ("required_gates", [], "GATE_MISSING"),
        ("package.tuple_id", "tuple:other", "TUPLE_ABI_MISMATCH"),
        ("package.schema_set_digest", "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "SCHEMA_SET_MISMATCH"),
        ("package.rollback_artifact_digests", [], "ROLLBACK_SET_MISSING"),
        ("qualification.admission", "NOT_QUALIFIED", "QUALIFICATION_REQUIRED"),
        ("compliance.decision", "deny", "COMPLIANCE_DENIED"),
        ("source.commit", "main", "MUTABLE_SOURCE"),
    ],
)
def test_hostile_cross_repository_fields_reject(path: str, replacement: object, code: str) -> None:
    value = accepted()
    set_path(value, path, replacement)
    with pytest.raises(CandidateAssemblyError) as caught:
        assemble(value)
    assert caught.value.code == code


def test_missing_and_extra_gate_and_duplicate_order_reject() -> None:
    value = accepted()
    value["required_gates"] = value["required_gates"][1:]
    with pytest.raises(CandidateAssemblyError) as caught:
        assemble(value)
    assert caught.value.code == "GATE_MISSING"
    value = accepted()
    value["required_gates"].append(deepcopy(value["required_gates"][0]))
    with pytest.raises(CandidateAssemblyError) as caught:
        assemble(value)
    assert caught.value.code == "DUPLICATE_ID"
    value = accepted()
    value["required_gates"].reverse()
    with pytest.raises(CandidateAssemblyError) as caught:
        assemble(value)
    assert caught.value.code == "GATE_CENSUS_INVALID"


def test_authority_and_cas_bypass_reject() -> None:
    with pytest.raises(CandidateAssemblyError) as caught:
        assemble_candidate(accepted(), artifacts=FixtureArtifacts())
    assert caught.value.code == "AUTHORITY_REQUIRED"
    with pytest.raises(CandidateAssemblyError) as caught:
        assemble_candidate(accepted(), authority=FixtureAuthority())
    assert caught.value.code == "ARTIFACT_READER_REQUIRED"
    class Forged:
        def verify(self, *args, **kwargs):
            return {"trusted": True}
    with pytest.raises(CandidateAssemblyError) as caught:
        assemble_candidate(accepted(), authority=Forged(), artifacts=FixtureArtifacts(), verification_time="2026-09-03T00:00:00Z")
    assert caught.value.code == "STATE_VALIDATOR_REQUIRED"


def test_missing_or_substituted_artifact_bytes_reject() -> None:
    value = accepted()
    value["package"]["artifacts"][0]["content_digest"] = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    value["package"]["rollback_artifact_digests"] = [value["package"]["artifacts"][0]["content_digest"]]
    value["rollback"] = list(value["package"]["rollback_artifact_digests"])
    with pytest.raises(CandidateAssemblyError) as caught:
        assemble(value)
    assert caught.value.code == "PACKAGE_INDEX_BINDING_MISMATCH"


@pytest.mark.parametrize("probe_path", sorted((ROOT / "fixtures/candidate/hostile").glob("*.json")))
def test_checked_in_hostile_fixtures_reject(probe_path: Path) -> None:
    probe = json.loads(probe_path.read_text())
    value = accepted()
    apply_probe(value, probe)
    with pytest.raises(CandidateAssemblyError) as caught:
        assemble(value)
    assert caught.value.code == ("PACKAGE_ARTIFACT_BINDING_MISMATCH" if probe_path.name == "missing-cas-member.json" else probe["code"])


def test_cli_is_read_only_and_rejects_untrusted_repository_assembly() -> None:
    run = subprocess.run([sys.executable, "-m", "omarchy_candidate", "assemble", "--input", str(ROOT / "fixtures/candidate/accepted-input.json")], cwd=ROOT, text=True, capture_output=True)
    assert run.returncode == 2
    assert json.loads(run.stderr)["code"] == "AUTHORITY_REQUIRED"
    manifest = assemble()
    path = ROOT / "fixtures/candidate/.candidate-output-test.json"
    try:
        path.write_bytes(manifest.bytes() + b"\n")
        check = subprocess.run([sys.executable, "-m", "omarchy_candidate", "verify", "--input", str(path)], cwd=ROOT, text=True, capture_output=True)
        assert check.returncode == 0
        assert json.loads(check.stdout)["candidate_digest"] == manifest.candidate_digest
    finally:
        path.unlink(missing_ok=True)


def test_cli_transport_errors_and_output_are_fail_closed() -> None:
    with tempfile.TemporaryDirectory() as directory:
        malformed_path = Path(directory) / "malformed.json"
        malformed_path.write_text('{"version":1}{"trailing":true}')
        malformed = subprocess.run([sys.executable, "-m", "omarchy_candidate", "verify", "--input", str(malformed_path)], cwd=ROOT, text=True, capture_output=True)
        assert malformed.returncode == 2
        assert json.loads(malformed.stderr)["code"] == "PARSE_SCHEMA_FAILURE"
        output = Path(directory) / "manifest.json"
        from omarchy_candidate.cli import _exclusive_output
        _exclusive_output(str(output), b"immutable", permitted_root=directory)
        with pytest.raises(CandidateAssemblyError) as caught:
            _exclusive_output(str(output), b"changed", permitted_root=directory)
        assert caught.value.code == "OUTPUT_CONFLICT"
        symlink = Path(directory) / "link"
        symlink.symlink_to(output)
        with pytest.raises(CandidateAssemblyError) as caught:
            _exclusive_output(str(symlink), b"changed", permitted_root=directory)
        assert caught.value.code == "OUTPUT_CONFLICT"
