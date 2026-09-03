"""Executable accepted and hostile coverage for F-06."""

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

from omarchy_release_compliance import ComplianceError, attest, evaluate, validate

ROOT = Path(__file__).parents[1]
NOW = datetime(2026, 9, 3, tzinfo=timezone.utc)


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
    assert validate(bundle, now=NOW) is bundle
    result = evaluate(bundle, now=NOW)
    assert result["decision"] == "allow"
    assert result["code"] == "OK"
    assert result["path"] == "$"
    assert all(result[key].startswith("sha256:") for key in ("inventory_digest", "policy_digest", "bundle_digest"))


def test_attestation_is_repeatable_and_untrusted() -> None:
    bundle = accepted()
    first = attest(bundle, now=NOW)
    second = attest(bundle, now=NOW)
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
    result = evaluate(bundle, now=NOW)
    assert result["decision"] == "reject", probe_path.name
    assert result["code"] == probe["code"], (probe_path.name, result)
    assert result["path"].startswith("$")
    with pytest.raises(ComplianceError):
        validate(bundle, now=NOW)


def test_no_warning_success_or_mutation() -> None:
    bundle = accepted()
    before = deepcopy(bundle)
    result = evaluate(bundle, now=NOW)
    assert set(result) >= {"version", "decision", "code", "path", "detail"}
    assert bundle == before


def test_version_pinned_source_uri_is_immutable_without_embedded_digest() -> None:
    bundle = accepted()
    uri = "https://example.invalid/omarchy-base-v1.0.0.tar.gz"
    bundle["artifacts"][0]["source_uri"] = uri
    bundle["artifacts"][0]["source_offer"]["location"] = uri
    assert evaluate(bundle, now=NOW)["decision"] == "allow"


def test_cli_accepted_and_every_hostile_rejection() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "bundle.json"
        bundle = accepted()
        path.write_text(json.dumps(bundle))
        accepted_run = subprocess.run(
            [sys.executable, "-m", "omarchy_release_compliance", "evaluate", str(path), "--now", "2026-09-03T00:00:00Z"],
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
                [sys.executable, "-m", "omarchy_release_compliance", "evaluate", str(path), "--now", "2026-09-03T00:00:00Z"],
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
