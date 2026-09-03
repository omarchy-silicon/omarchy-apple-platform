"""Executable accepted and hostile coverage for F-06."""

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

from omarchy_release_compliance import ComplianceError, attest, evaluate, guard_attestation, validate
from omarchy_release_compliance.engine import _set_test_clock

ROOT = Path(__file__).parents[1]
NOW = datetime(2026, 9, 3, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def fixed_private_clock():
    _set_test_clock(lambda: NOW)
    yield


def accepted() -> dict:
    return json.loads((ROOT / "fixtures/compliance/accepted.json").read_text())


def set_path(value: dict, path: str, replacement: object) -> None:
    bits = path.replace("]", "").replace("[", ".").split(".")
    cursor = value
    for bit in bits[:-1]:
        cursor = cursor[int(bit)] if bit.isdigit() else cursor[bit]
    last = bits[-1]
    if last.isdigit():
        cursor[int(last)] = replacement
    else:
        cursor[last] = replacement


def apply_probe(bundle: dict, probe: dict) -> None:
    mutation, path = probe["mutation"], probe["path"]
    if mutation == "delete":
        bits = path.replace("]", "").replace("[", ".").split(".")
        cursor = bundle
        for bit in bits[:-1]:
            cursor = cursor[int(bit)] if bit.isdigit() else cursor[bit]
        cursor.pop(bits[-1])
    elif mutation == "add":
        bits = path.replace("]", "").replace("[", ".").split(".")
        cursor = bundle
        for bit in bits[:-1]:
            cursor = cursor[int(bit)] if bit.isdigit() else cursor[bit]
        cursor[bits[-1]] = probe["value"]
    elif mutation == "reverse":
        bundle["artifacts"].reverse()
    elif mutation == "duplicate":
        bundle["artifacts"].append(deepcopy(bundle["artifacts"][0]))
    else:
        set_path(bundle, path, probe["value"])


def test_accepted_bundle_and_closed_result() -> None:
    bundle = accepted()
    assert validate(bundle) is bundle
    result = evaluate(bundle)
    assert result["decision"] == "allow"
    assert result["code"] == "OK"
    assert result["path"] == "$"
    assert all(result[key].startswith("sha256:") for key in ("inventory_digest", "policy_digest", "bundle_digest"))


def test_attestation_is_repeatable_and_untrusted() -> None:
    bundle = accepted()
    first = attest(bundle)
    second = attest(bundle)
    assert first == second
    projection = json.loads(first)
    assert projection["signed"] is False
    assert projection["trusted"] is False
    assert projection["promotable"] is False


@pytest.mark.parametrize("probe_path", sorted((ROOT / "fixtures/compliance/hostile").glob("*.json")))
def test_hostile_probe_rejects(probe_path: Path) -> None:
    probe = json.loads(probe_path.read_text())
    bundle = accepted()
    apply_probe(bundle, probe)
    result = evaluate(bundle)
    assert result["decision"] == "reject", probe_path.name
    assert result["code"] == probe["code"], (probe_path.name, result)
    assert result["path"].startswith("$")
    with pytest.raises(ComplianceError):
        validate(bundle)


def test_no_warning_success_or_mutation() -> None:
    bundle = accepted()
    before = deepcopy(bundle)
    result = evaluate(bundle)
    assert set(result) >= {"version", "decision", "code", "path", "detail"}
    assert bundle == before


def test_cli_accepted_and_every_hostile_rejection() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "bundle.json"
        bundle = accepted()
        path.write_text(json.dumps(bundle))
        accepted_run = subprocess.run(
            [sys.executable, "-m", "omarchy_release_compliance", "evaluate", str(path)],
            cwd=ROOT, text=True, capture_output=True,
        )
        assert accepted_run.returncode == 0
        assert json.loads(accepted_run.stdout)["decision"] == "allow"
        for probe_path in sorted((ROOT / "fixtures/compliance/hostile").glob("*.json")):
            probe = json.loads(probe_path.read_text())
            hostile = accepted()
            apply_probe(hostile, probe)
            path.write_text(json.dumps(hostile))
            run = subprocess.run(
                [sys.executable, "-m", "omarchy_release_compliance", "evaluate", str(path)],
                cwd=ROOT, text=True, capture_output=True,
            )
            assert run.returncode == 2
            assert json.loads(run.stderr)["decision"] == "reject"
            assert json.loads(run.stderr)["code"] == probe["code"]


def test_cli_transport_failure_is_structured() -> None:
    run = subprocess.run(
        [sys.executable, "-m", "omarchy_release_compliance", "evaluate"],
        cwd=ROOT, input='{"version":1}{"trailing":true}', text=True, capture_output=True,
    )
    assert run.returncode == 3
    assert json.loads(run.stderr)["code"] == "PARSE_SCHEMA_FAILURE"


def test_cli_bounded_input_and_caller_clock_are_closed() -> None:
    oversized = b"{" + b"\"x\":\"" + b"a" * (1024 * 1024) + b"\"}"
    run = subprocess.run([sys.executable, "-m", "omarchy_release_compliance", "evaluate"], cwd=ROOT, input=oversized, capture_output=True)
    assert run.returncode == 2
    assert json.loads(run.stderr)["code"] == "RESOURCE_LIMIT"
    no_clock = subprocess.run([sys.executable, "-m", "omarchy_release_compliance", "evaluate", "--now", "2030-01-01T00:00:00Z"], cwd=ROOT, input=b"{}", capture_output=True)
    assert no_clock.returncode != 0


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("candidate.digest", None, "INVALID_DIGEST"),
        ("artifacts[0].content_digest", None, "INVALID_DIGEST"),
        ("artifacts[0].source_digest", None, "INVALID_DIGEST"),
        ("artifacts[0].upstream_digest", None, "FORK_UPSTREAM_AMBIGUOUS"),
        ("artifacts[0].owner_decision.evidence_digest", None, "INVALID_DIGEST"),
        ("artifacts[1].build_provenance.environment_digest", None, "INVALID_DIGEST"),
        ("artifacts[1].sbom_ref.digest", None, "INVALID_DIGEST"),
    ],
)
def test_null_digest_and_record_guards(field: str, value: object, code: str) -> None:
    bundle = accepted()
    set_path(bundle, field, value)
    assert evaluate(bundle)["code"] == code


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("artifacts[0].source_uri", "https://EXAMPLE.invalid/x/sha256:4444444444444444444444444444444444444444444444444444444444444444-content-sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.tar.gz"),
        ("artifacts[0].source_uri", "https://example.invalid:443/x/sha256:4444444444444444444444444444444444444444444444444444444444444444-content-sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.tar.gz"),
        ("artifacts[0].source_uri", "https://user@example.invalid/x/sha256:4444444444444444444444444444444444444444444444444444444444444444-content-sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.tar.gz"),
        ("artifacts[0].source_uri", "https://example.invalid/x/../sha256:4444444444444444444444444444444444444444444444444444444444444444-content-sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.tar.gz"),
        ("artifacts[0].source_uri", "https://example.invalid/x//sha256:4444444444444444444444444444444444444444444444444444444444444444-content-sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.tar.gz"),
        ("artifacts[0].source_uri", "https://example.invalid/x/%2e%2e/sha256:4444444444444444444444444444444444444444444444444444444444444444-content-sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.tar.gz"),
        ("artifacts[0].source_uri", "https://example.invalid/x/sha256:4444444444444444444444444444444444444444444444444444444444444444.tar.gz"),
    ],
)
def test_strict_immutable_uri_guards(field: str, value: str) -> None:
    bundle = accepted()
    set_path(bundle, field, value)
    assert evaluate(bundle)["code"] in {"MUTABLE_SOURCE_URI", "DIGEST_MISMATCH"}


def test_nested_record_closure() -> None:
    for field, value, code in (
        ("artifacts[0].copyright_notice[0].extra", True, "UNKNOWN_FIELD"),
        ("artifacts[0].source_offer.extra", True, "UNKNOWN_FIELD"),
        ("artifacts[0].owner_decision.extra", True, "UNKNOWN_FIELD"),
        ("artifacts[1].build_provenance.extra", True, "UNKNOWN_FIELD"),
        ("artifacts[1].sbom_ref.extra", True, "UNKNOWN_FIELD"),
    ):
        bundle = accepted()
        set_path(bundle, field, value)
        assert evaluate(bundle)["code"] == code
    bundle = accepted()
    bundle["artifacts"][0]["upstream_digest"] = None
    bundle["artifacts"][0]["fork_digest"] = None
    assert evaluate(bundle)["code"] == "FORK_UPSTREAM_AMBIGUOUS"


def test_consumer_guard_rejects_unsigned_generated_attestation() -> None:
    bundle = accepted()
    result = evaluate(bundle)
    expected = {key: result[key] for key in ("inventory_digest", "policy_digest", "candidate_digest", "manifest_digest", "schema_set_digest", "bundle_digest")}
    with pytest.raises(ComplianceError) as caught:
        guard_attestation(attest(bundle), expected)
    assert caught.value.code == "ATTESTATION_NON_PROMOTABLE"


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("signed", False, "ATTESTATION_UNSIGNED"),
        ("trusted", False, "ATTESTATION_UNTRUSTED"),
        ("decision", "reject", "ATTESTATION_NOT_ALLOW"),
        ("inventory_digest", "sha256:" + "0" * 64, "ATTESTATION_DIGEST_MISMATCH"),
        ("valid_until", "2020-01-01T00:00:00Z", "ATTESTATION_STALE"),
    ],
)
def test_consumer_guard_rejects_each_promotion_exploit(field: str, value: object, code: str) -> None:
    bundle = accepted()
    result = evaluate(bundle)
    expected = {key: result[key] for key in ("inventory_digest", "policy_digest", "candidate_digest", "manifest_digest", "schema_set_digest", "bundle_digest")}
    projection = json.loads(attest(bundle))
    projection.update({"signed": True, "trusted": True, "promotable": True, "clock_trusted": True})
    projection[field] = value
    with pytest.raises(ComplianceError) as caught:
        guard_attestation(projection, expected)
    assert caught.value.code == code


def test_consumer_guard_rejects_missing_and_open_attestation() -> None:
    bundle = accepted()
    result = evaluate(bundle)
    expected = {key: result[key] for key in ("inventory_digest", "policy_digest", "candidate_digest", "manifest_digest", "schema_set_digest", "bundle_digest")}
    projection = json.loads(attest(bundle))
    projection.pop("bundle_digest")
    with pytest.raises(ComplianceError) as caught:
        guard_attestation(projection, expected)
    assert caught.value.code == "ATTESTATION_MISSING_OR_OPEN"


def test_drift_tamper_payload_and_manifest_cannot_rewrite_oracle() -> None:
    import shutil
    with tempfile.TemporaryDirectory() as directory:
        copied = Path(directory) / "repo"
        shutil.copytree(ROOT, copied)
        probe_path = copied / "fixtures/compliance/hostile/incomplete.json"
        probe = json.loads(probe_path.read_text())
        probe["code"] = "OK"
        probe_path.write_text(json.dumps(probe))
        manifest_path = copied / "fixtures/compliance/manifest.json"
        manifest = json.loads(manifest_path.read_text())
        next(entry for entry in manifest["hostile"] if entry["name"] == "incomplete")["code"] = "OK"
        manifest_path.write_text(json.dumps(manifest))
        run = subprocess.run([sys.executable, "tools/compliance/drift.py"], cwd=copied, text=True, capture_output=True)
        assert run.returncode != 0
