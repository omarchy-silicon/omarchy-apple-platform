"""Positive and hostile executable coverage for F-05 candidate assembly."""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

from omarchy_candidate import CandidateAssemblyError, CandidateAssemblyInput, CandidateManifest, assemble_candidate, digest_value, guard_manifest
from omarchy_candidate.models import _AuthorityCapability, _CAPABILITY_TOKEN, digest_bytes
from omarchy_platform.canonical import canonical_bytes
from jsonschema import Draft202012Validator

ROOT = Path(__file__).parents[1]


def accepted() -> dict:
    return json.loads((ROOT / "fixtures/candidate/accepted-input.json").read_text())


class FixtureAuthority:
    def validate_state(self, platform_bytes, intake_bytes, qualification_bytes, *, board_id, profile_id, verification_time):
        if board_id != "apple:j313" or profile_id != "profile:j313-synthetic":
            raise ValueError("synthetic state mismatch")

    def verify_canonical(self, kind, source_bytes, *, digest, board_id, profile_id, channel, schema_set_digest, verification_time, subject):
        fixture = accepted()
        if kind.startswith("gate:"):
            gate_id = kind.removeprefix("gate:")
            record = next(gate for gate in fixture["required_gates"] if gate["gate_id"] == gate_id)
            expected_digest = digest_value("omarchy-candidate-gate/v1", record)
        elif kind == "firmware":
            record, expected_digest = fixture["firmware"], digest_value("omarchy-candidate-firmware/v1", fixture["firmware"])
        elif kind == "source":
            record, expected_digest = fixture["source"], digest_value("omarchy-candidate-source/v1", fixture["source"])
        else:
            record = {"platform": fixture["platform"], "intake": fixture["intake"], "qualification": fixture["qualification"], "package": fixture["package"], "compliance": fixture["compliance"]}[kind]
            expected_digest = {"platform": fixture["platform"]["manifest_digest"], "intake": fixture["intake"]["dataset_digest"], "qualification": fixture["qualification"]["record_digest"], "package": fixture["package"]["index_digest"], "compliance": fixture["compliance"]["attestation_digest"]}[kind]
        if source_bytes != canonical_bytes(record) or digest != expected_digest:
            raise ValueError("fixture authority only authorizes the canonical accepted projection")
        return _AuthorityCapability(kind, subject, digest, board_id, profile_id, channel, "2099-01-01T00:00:00Z", f"replay:{kind}", digest_bytes(source_bytes), schema_set_digest, _token=_CAPABILITY_TOKEN)


class FixtureArtifacts:
    def verify(self, digest, kind):
        fixture = accepted()
        if kind.startswith("gate:"):
            gate_id = kind.removeprefix("gate:")
            gate = next((gate for gate in fixture["required_gates"] if gate["gate_id"] == gate_id), None)
            return gate is not None and digest == gate["evidence_digest"]
        return digest in {"sha256:" + ("b" * 64), "sha256:" + ("c" * 64), "sha256:" + ("1" * 64), "sha256:" + ("2" * 64)}

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


def test_top_level_rollback_is_independent_and_bound() -> None:
    value = accepted()
    value["rollback"] = []
    with pytest.raises(CandidateAssemblyError) as caught:
        assemble(value)
    assert caught.value.code == "ROLLBACK_SET_MISSING"
    value = accepted()
    value["rollback"] = ["sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"]
    with pytest.raises(CandidateAssemblyError) as caught:
        assemble(value)
    assert caught.value.code == "ROLLBACK_BINDING_MISMATCH"


def test_artifact_map_rejects_redundant_or_mismatched_identity() -> None:
    value = accepted()
    value["package"]["artifacts"]["artifact:kernel"]["artifact_id"] = "artifact:other"
    schema = json.loads((ROOT / "schemas/candidate-assembly/v1/candidate-assembly.json").read_text())
    with pytest.raises(Exception):
        Draft202012Validator(schema).validate(value)
    with pytest.raises(CandidateAssemblyError) as caught:
        assemble(value)
    assert caught.value.code == "UNKNOWN_FIELD"


def test_distinct_artifact_keys_may_share_component_id_in_schema_and_model() -> None:
    value = accepted()
    value["platform"]["artifact_ids"] = ["artifact:kernel", "artifact:mesa"]
    value["package"]["artifacts"]["artifact:mesa"] = deepcopy(value["package"]["artifacts"]["artifact:kernel"])
    value["package"]["artifacts"]["artifact:mesa"]["component_id"] = "linux-kernel"
    schema = json.loads((ROOT / "schemas/candidate-assembly/v1/candidate-assembly.json").read_text())
    Draft202012Validator(schema).validate(value)
    parsed = CandidateAssemblyInput.from_dict(value)
    assert parsed.package["artifacts"]["artifact:mesa"]["component_id"] == "linux-kernel"


@pytest.mark.parametrize("path", ["firmware.version", "source.tool_versions.schema", "required_gates[0].evidence_digest"])
def test_authority_only_accepts_exact_firmware_source_and_gate_projections(path: str) -> None:
    value = accepted()
    replacement = "1.0.1" if path == "firmware.version" else ("candidate-assembly-v2" if path == "source.tool_versions.schema" else "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    set_path(value, path, replacement)
    with pytest.raises(CandidateAssemblyError) as caught:
        assemble(value)
    assert caught.value.code == "AUTHORITY_REJECTED"


def test_timestamp_contract_rejects_date_only_and_forged_expiry() -> None:
    with pytest.raises(CandidateAssemblyError) as caught:
        assemble_candidate(accepted(), authority=FixtureAuthority(), artifacts=FixtureArtifacts(), verification_time="2026-09-03")
    assert caught.value.code == "INVALID_VERIFICATION_TIME"
    receipt = _AuthorityCapability("firmware", "firmware-bundle", digest_value("omarchy-candidate-firmware/v1", accepted()["firmware"]), "apple:j313", "profile:j313-synthetic", "edge", "2099-01-01T00:00:00Z", "forged", digest_bytes(canonical_bytes(accepted()["firmware"])), accepted()["platform"]["schema_set_digest"], _token=_CAPABILITY_TOKEN)
    object.__setattr__(receipt, "expires_at", 123)
    class ForgedAuthority(FixtureAuthority):
        def verify_canonical(self, *args, **kwargs):
            return receipt
    with pytest.raises(CandidateAssemblyError) as caught:
        assemble_candidate(accepted(), authority=ForgedAuthority(), artifacts=FixtureArtifacts(), verification_time="2026-09-03T00:00:00Z")
    assert caught.value.code in {"INVALID_TIMESTAMP", "AUTHORITY_UNTRUSTED"}


def test_timestamp_parser_rejects_string_subclass_without_virtual_calls() -> None:
    class HostileString(str):
        def removesuffix(self, suffix):
            raise RuntimeError("virtual timestamp operation must not run")

    with pytest.raises(CandidateAssemblyError) as caught:
        assemble_candidate(accepted(), authority=FixtureAuthority(), artifacts=FixtureArtifacts(), verification_time=HostileString("2026-09-03T00:00:00Z"))
    assert caught.value.code == "INVALID_VERIFICATION_TIME"


@pytest.mark.parametrize("mask", ["raise", "expiry"])
def test_evil_receipt_subclass_cannot_mask_invalid_or_expired_state(mask: str) -> None:
    base = FixtureAuthority().verify_canonical("firmware", canonical_bytes(accepted()["firmware"]), digest=digest_value("omarchy-candidate-firmware/v1", accepted()["firmware"]), board_id="apple:j313", profile_id="profile:j313-synthetic", channel="edge", schema_set_digest=accepted()["platform"]["schema_set_digest"], verification_time="2026-09-03T00:00:00Z", subject="firmware-bundle")

    class Evil(_AuthorityCapability):
        def __post_init__(self):
            raise RuntimeError("virtual validation must not run")

        def __getattribute__(self, name):
            if name == "expires_at":
                if mask == "raise":
                    raise RuntimeError("virtual receipt access must not run")
                return "2099-01-01T00:00:00Z"
            return super().__getattribute__(name)

    evil = object.__new__(Evil)
    for name in ("authority", "subject", "digest", "board_id", "profile_id", "channel", "replay_id", "metadata_digest", "schema_set_digest"):
        object.__setattr__(evil, name, getattr(base, name))
    object.__setattr__(evil, "expires_at", "2000-01-01T00:00:00Z")

    class EvilAuthority(FixtureAuthority):
        def verify_canonical(self, *args, **kwargs):
            if kwargs["subject"] == "firmware-bundle":
                return evil
            return super().verify_canonical(*args, **kwargs)

    with pytest.raises(CandidateAssemblyError) as caught:
        assemble_candidate(accepted(), authority=EvilAuthority(), artifacts=FixtureArtifacts(), verification_time="2026-09-03T00:00:00Z")
    assert caught.value.code == "AUTHORITY_UNTRUSTED"


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
    value["package"]["artifacts"]["artifact:kernel"]["content_digest"] = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    value["package"]["rollback_artifact_digests"] = [value["package"]["artifacts"]["artifact:kernel"]["content_digest"]]
    value["rollback"] = list(value["package"]["rollback_artifact_digests"])
    with pytest.raises(CandidateAssemblyError) as caught:
        assemble(value)
    assert caught.value.code == "AUTHORITY_REJECTED"


@pytest.mark.parametrize("probe_path", sorted((ROOT / "fixtures/candidate/hostile").glob("*.json")))
def test_checked_in_hostile_fixtures_reject(probe_path: Path) -> None:
    probe = json.loads(probe_path.read_text())
    value = accepted()
    apply_probe(value, probe)
    with pytest.raises(CandidateAssemblyError) as caught:
        assemble(value)
    assert caught.value.code == ("AUTHORITY_REJECTED" if probe_path.name == "missing-cas-member.json" else probe["code"])


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


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO support is unavailable")
def test_cli_rejects_fifo_and_symlinked_input_paths_without_blocking() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        fifo = root / "candidate.fifo"
        os.mkfifo(fifo)
        run = subprocess.run([sys.executable, "-m", "omarchy_candidate", "verify", "--input", str(fifo)], cwd=ROOT, text=True, capture_output=True, timeout=2)
        assert run.returncode == 2
        assert json.loads(run.stderr)["code"] == "INPUT_INVALID"
        real = root / "real"
        real.mkdir()
        valid = real / "manifest.json"
        valid.write_text("{}")
        leaf = root / "leaf"
        leaf.symlink_to(valid)
        result = subprocess.run([sys.executable, "-m", "omarchy_candidate", "verify", "--input", str(leaf)], cwd=ROOT, text=True, capture_output=True, timeout=2)
        assert result.returncode == 2
        assert json.loads(result.stderr)["code"] == "INPUT_INVALID"
        parent = root / "parent"
        parent.symlink_to(real, target_is_directory=True)
        result = subprocess.run([sys.executable, "-m", "omarchy_candidate", "verify", "--input", str(parent / "manifest.json")], cwd=ROOT, text=True, capture_output=True, timeout=2)
        assert result.returncode == 2
        assert json.loads(result.stderr)["code"] == "INPUT_INVALID"


def test_cli_malformed_invocation_and_unencodable_path_are_typed() -> None:
    malformed = subprocess.run([sys.executable, "-m", "omarchy_candidate", "verify"], cwd=ROOT, text=True, capture_output=True)
    assert malformed.returncode == 2
    assert json.loads(malformed.stderr)["code"] == "CLI_INVALID"
    from omarchy_candidate.cli import main
    assert main(["verify", "--input", "\ud800"]) == 2
