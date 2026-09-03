"""Executable F-04 positive and hostile contract coverage."""

from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

from omarchy_build import (
    BuildProvenanceError,
    BuildResult,
    BuilderDefinition,
    FixtureBuilder,
    InputRef,
    LocalArtifactStore,
    PackageIndex,
    Recipe,
    SourceClosure,
    StoreError,
    TrustedTrustContext,
    compare_results,
    make_package_index,
)
from omarchy_build.metadata import verify_index_bytes
from omarchy_build.errors import TrustRejection
from omarchy_build.models import OutputRecord
from omarchy_build.provenance import make_provenance
from omarchy_build.sbom import make_sbom, validate_sbom
from omarchy_build.util import canonical_bytes, digest_bytes, digest_value, read_json

ROOT = Path(__file__).parents[1]


def _definition(name: str) -> BuilderDefinition:
    return BuilderDefinition.from_dict(read_json(str(ROOT / "builders" / name / "definition.json")))


def _inputs() -> tuple[SourceClosure, Recipe, dict[str, bytes]]:
    recipe = Recipe.from_dict(read_json(str(ROOT / "fixtures/build/recipe.json")))
    closure = SourceClosure.from_dict(read_json(str(ROOT / "fixtures/build/source-lock.json")))
    data = (ROOT / "fixtures/build/source.bin").read_bytes()
    return closure, recipe, {"input:source": data}


def _results():
    closure, recipe, source = _inputs()
    left = FixtureBuilder(_definition("fixture-a")).build(closure, recipe, source)
    right = FixtureBuilder(_definition("fixture-b")).build(closure, recipe, source)
    return closure, recipe, left, right


def _index(left: BuildResult, right: BuildResult, *, release_id: str = "fixture-release") -> PackageIndex:
    closure, _recipe, _left, _right = _results()
    sbom = make_sbom(left)
    provenance = make_provenance(left, _definition("fixture-a"), closure, sbom)
    # Both builders produce the same SBOM; use the provenance from the left
    # result and bind the index to the test platform manifest.
    return make_package_index(
        release_id=release_id,
        channel="edge",
        platform_manifest_id="manifest:fixture",
        platform_manifest_digest=digest_bytes(b"manifest"),
        schema_set_digest=digest_bytes(b"schema-set"),
        artifact_id="artifact:fixture",
        artifact_class="kernel",
        left=left,
        right=right,
        provenance=provenance,
        sbom=sbom,
        rollback_artifact_digests=(left.outputs[0].content_digest,),
    )


def _context(index: PackageIndex, *, channel: str, role: str = "artifact-release") -> TrustedTrustContext:
    return TrustedTrustContext(role, ("key:a",), 1, digest_bytes(canonical_bytes(index.to_dict())), index.schema_set_digest, channel, "2099-01-01T00:00:00Z", f"replay:{channel}")


def _seed_artifact(store: LocalArtifactStore, result: BuildResult) -> None:
    store.put(result.output_bytes[result.outputs[0].path], expected_digest=result.outputs[0].content_digest)


def test_two_independent_builders_match_at_byte_level() -> None:
    _closure, _recipe, left, right = _results()
    comparison = compare_results(left, right)
    assert comparison["decision"] == "match"
    assert comparison["artifact_set_digest"] == left.artifact_set_digest
    assert left.result_digest != right.result_digest


def test_result_round_trip_is_closed_and_digest_bound() -> None:
    _closure, _recipe, left, _right = _results()
    assert BuildResult.from_dict(left.to_dict()).result_digest == left.result_digest
    hostile = left.to_dict()
    hostile["unknown"] = True
    with pytest.raises(BuildProvenanceError) as caught:
        BuildResult.from_dict(hostile)
    assert caught.value.code == "UNKNOWN_FIELD"


def test_undeclared_recipe_read_rejects_before_output() -> None:
    _closure, recipe, source = _inputs()
    hostile = Recipe.create(recipe.recipe_id, recipe.input_ids, ("secret/host-file", "src/source.bin"), output_path=recipe.output_path, output_media_type=recipe.output_media_type, prefix=recipe.prefix)
    closure = SourceClosure.create(hostile.recipe_id, hostile.recipe_digest, _closure.inputs)
    with pytest.raises(BuildProvenanceError) as caught:
        FixtureBuilder(_definition("fixture-a")).build(closure, hostile, source)
    assert caught.value.code == "UNDECLARED_INPUT"


def test_mutable_fetch_and_digest_mismatch_reject() -> None:
    closure, _recipe, source = _inputs()
    item = closure.inputs[0].to_dict()
    item["uri"] = "https://example.invalid/source/main"
    with pytest.raises(BuildProvenanceError) as caught:
        InputRef.from_dict(item)
    assert caught.value.code == "MUTABLE_INPUT"
    source["input:source"] += b"tampered"
    with pytest.raises(BuildProvenanceError) as caught:
        FixtureBuilder(_definition("fixture-a")).build(closure, _recipe, source)
    assert caught.value.code == "INPUT_DIGEST_MISMATCH"


def test_changed_output_bytes_reject_even_when_records_look_equal() -> None:
    _closure, _recipe, left, right = _results()
    hostile = replace(right, output_bytes={right.outputs[0].path: b"different bytes"})
    with pytest.raises(BuildProvenanceError) as caught:
        compare_results(left, hostile)
    assert caught.value.code == "NONREPRODUCIBLE_OUTPUT"


def test_incomplete_sbom_rejects() -> None:
    _closure, _recipe, left, _right = _results()
    sbom = make_sbom(left)
    incomplete = replace(sbom, entries=tuple())
    with pytest.raises(BuildProvenanceError) as caught:
        validate_sbom(incomplete, left.outputs, left.artifact_set_digest)
    assert caught.value.code == "INCOMPLETE_SBOM"


def test_duplicate_sbom_paths_reject_before_mapping_collapse() -> None:
    _closure, _recipe, left, right = _results()
    sbom = make_sbom(left)
    duplicate = replace(sbom, entries=(sbom.entries[0], sbom.entries[0]))
    with pytest.raises(BuildProvenanceError) as caught:
        validate_sbom(duplicate, left.outputs, left.artifact_set_digest)
    assert caught.value.code == "INCOMPLETE_SBOM"
    with pytest.raises(BuildProvenanceError) as caught:
        make_package_index(
            release_id="duplicate-sbom",
            channel="edge",
            platform_manifest_id="manifest:fixture",
            platform_manifest_digest=digest_bytes(b"manifest"),
            schema_set_digest=digest_bytes(b"schema-set"),
            artifact_id="artifact:fixture",
            artifact_class="kernel",
            left=left,
            right=right,
            provenance=make_provenance(left, _definition("fixture-a"), _closure, sbom),
            sbom=duplicate,
            rollback_artifact_digests=(left.outputs[0].content_digest,),
        )
    assert caught.value.code == "INCOMPLETE_SBOM"


def test_store_is_content_addressed_and_no_overwrite() -> None:
    with tempfile.TemporaryDirectory() as directory:
        store = LocalArtifactStore(directory)
        payload = b"immutable fixture object"
        digest = store.put(payload)
        assert store.put(payload) == digest
        assert store.read(digest) == payload
        with pytest.raises(StoreError) as caught:
            store.put(b"other", expected_digest=digest)
        assert caught.value.code == "DIGEST_MISMATCH"
        path = Path(directory) / "objects" / "sha256" / digest.removeprefix("sha256:")
        path.write_bytes(b"tamper")
        with pytest.raises(StoreError) as caught:
            store.read(digest)
        assert caught.value.code == "DIGEST_MISMATCH"


def test_unsigned_index_and_stable_bypass_reject() -> None:
    _closure, _recipe, left, right = _results()
    index = _index(left, right)
    with tempfile.TemporaryDirectory() as directory:
        store = LocalArtifactStore(directory)
        with pytest.raises(StoreError) as caught:
            store.publish_index(index)
        assert caught.value.code == "TRUST_ADAPTER_REQUIRED"
        with pytest.raises(StoreError) as caught:
            store.promote("edge", "stable", index.release_id)
        assert caught.value.code == "TRUST_ADAPTER_REQUIRED"


def test_promotion_copies_existing_index_digest_and_rollback_does_not_rebuild() -> None:
    _closure, _recipe, left, right = _results()
    index = _index(left, right)
    context = _context(index, channel="edge")
    with tempfile.TemporaryDirectory() as directory:
        store = LocalArtifactStore(directory)
        _seed_artifact(store, left)
        store.publish_index(index, context=context)
        rc_context = _context(index, channel="rc")
        promoted_digest = store.promote("edge", "rc", index.release_id, context=rc_context)
        assert promoted_digest == store.read_channel("edge", index.release_id)["index_digest"]
        assert store.read_channel("rc", index.release_id)["index_digest"] == store.read_channel("edge", index.release_id)["index_digest"]
        with pytest.raises(StoreError) as caught:
            store.promote("rc", "stable", index.release_id, context=rc_context)
        assert caught.value.code == "STABLE_PROMOTION_REQUIRES_F07"


def test_promotion_never_invokes_a_builder(monkeypatch: pytest.MonkeyPatch) -> None:
    _closure, _recipe, left, right = _results()
    index = _index(left, right)
    with tempfile.TemporaryDirectory() as directory:
        store = LocalArtifactStore(directory)
        _seed_artifact(store, left)
        store.publish_index(index, context=_context(index, channel="edge"))

        def forbidden(*_args, **_kwargs):
            raise AssertionError("promotion rebuilt an artifact")

        monkeypatch.setattr(FixtureBuilder, "build", forbidden)
        store.promote("edge", "rc", index.release_id, context=_context(index, channel="rc"))


def test_f07_stable_context_is_required_and_binds_existing_bytes() -> None:
    _closure, _recipe, left, right = _results()
    index = _index(left, right)
    with tempfile.TemporaryDirectory() as directory:
        store = LocalArtifactStore(directory)
        _seed_artifact(store, left)
        store.publish_index(index, context=_context(index, channel="edge"))
        store.promote("edge", "stable", index.release_id, context=_context(index, channel="stable", role="promotion/f07"))
        assert store.read_channel("stable", index.release_id)["index_digest"] == store.read_channel("edge", index.release_id)["index_digest"]


def test_rollback_restores_retained_digest_and_rejects_missing_artifact() -> None:
    _closure, _recipe, left, right = _results()
    old_index = _index(left, right, release_id="old-release")
    failed_index = _index(left, right, release_id="failed-release")
    with tempfile.TemporaryDirectory() as directory:
        store = LocalArtifactStore(directory)
        _seed_artifact(store, left)
        store.publish_index(old_index, context=_context(old_index, channel="edge"))
        store.publish_index(failed_index, context=_context(failed_index, channel="edge"))
        restored = store.rollback("edge", "failed-release", "old-release", context=_context(old_index, channel="edge"))
        assert restored == store.read_channel("edge", "old-release")["index_digest"]

        # Remove the retained object only inside this disposable test store;
        # rollback must fail closed instead of rebuilding or fetching it.
        digest = left.outputs[0].content_digest
        object_path = Path(directory) / "objects" / "sha256" / digest.removeprefix("sha256:")
        object_path.unlink()
        with pytest.raises(StoreError) as caught:
            store.rollback("edge", "failed-release", "old-release", context=_context(old_index, channel="edge"))
        assert caught.value.code == "ROLLBACK_ARTIFACT_MISSING"


def test_rollback_rejects_forged_index_from_another_channel() -> None:
    _closure, _recipe, left, right = _results()
    edge_index = _index(left, right, release_id="edge-restore")
    rc_index = PackageIndex.create(
        release_id="rc-restore",
        channel="rc",
        platform_manifest_id=edge_index.platform_manifest_id,
        platform_manifest_digest=edge_index.platform_manifest_digest,
        schema_set_digest_value=edge_index.schema_set_digest,
        artifacts=edge_index.artifacts,
        rollback_artifact_digests=edge_index.rollback_artifact_digests,
    )
    failed_index = _index(left, right, release_id="edge-failed")
    with tempfile.TemporaryDirectory() as directory:
        store = LocalArtifactStore(directory)
        _seed_artifact(store, left)
        store.publish_index(rc_index, context=_context(rc_index, channel="rc"))
        store.publish_index(failed_index, context=_context(failed_index, channel="edge"))
        rc_record = store.read_channel("rc", "rc-restore")
        forged = {**rc_record, "channel": "edge", "release_id": "edge-restore"}
        forged["record_digest"] = digest_bytes(b"omarchy-channel-record/v1\x00" + canonical_bytes({key: value for key, value in forged.items() if key != "record_digest"}))
        store._put_channel_record("edge", "edge-restore", forged)
        context = TrustedTrustContext("artifact-release", ("key:a",), 1, digest_bytes(canonical_bytes(rc_index.to_dict())), rc_index.schema_set_digest, "edge", "2099-01-01T00:00:00Z", "replay:edge")
        with pytest.raises(StoreError) as caught:
            store.rollback("edge", "edge-failed", "edge-restore", context=context)
        assert caught.value.code == "ROLLBACK_BINDING_MISMATCH"


def test_rollback_missing_artifact_member_is_typed() -> None:
    _closure, _recipe, left, right = _results()
    restore_index = _index(left, right, release_id="restore-missing-member")
    failed_index = _index(left, right, release_id="failed-missing-member")
    with tempfile.TemporaryDirectory() as directory:
        store = LocalArtifactStore(directory)
        _seed_artifact(store, left)
        store.publish_index(failed_index, context=_context(failed_index, channel="edge"))
        malformed = restore_index.to_dict()
        del malformed["rollback_artifact_digests"]
        malformed_digest = store.put(canonical_bytes(malformed))
        record = {
            "version": "channel-record/v1",
            "channel": "edge",
            "release_id": restore_index.release_id,
            "index_digest": malformed_digest,
            "artifact_set_digest": restore_index.artifact_set_digest,
            "rollback_artifact_digests": list(restore_index.rollback_artifact_digests),
        }
        record["record_digest"] = digest_bytes(b"omarchy-channel-record/v1\x00" + canonical_bytes(record))
        store._put_channel_record("edge", restore_index.release_id, record)
        with pytest.raises(StoreError) as caught:
            store.rollback("edge", failed_index.release_id, restore_index.release_id, context=_context(restore_index, channel="edge"))
        assert caught.value.code == "ROLLBACK_ARTIFACT_MISSING"


def test_store_rejects_dangling_symlink_parent_and_channel_node_conflicts() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / "dangling"
        os.symlink(Path(directory) / "does-not-exist", root)
        with pytest.raises(StoreError) as caught:
            LocalArtifactStore(root)
        assert caught.value.code == "UNSAFE_PATH"

        parent_file = Path(directory) / "not-a-directory"
        parent_file.write_bytes(b"x")
        with pytest.raises(StoreError) as caught:
            LocalArtifactStore(parent_file / "child")
        assert caught.value.code == "UNSAFE_PATH"

        store = LocalArtifactStore(Path(directory) / "store")
        conflict = Path(directory) / "store" / "channels" / "edge" / "release.json"
        conflict.mkdir(parents=True)
        with pytest.raises(StoreError) as caught:
            store._put_channel_record("edge", "release", {"version": "channel-record/v1"})
        assert caught.value.code == "IMMUTABLE_CHANNEL_CONFLICT"

        symlink = Path(directory) / "store" / "channels" / "edge" / "symlink.json"
        os.symlink(Path(directory) / "outside", symlink)
        with pytest.raises(StoreError) as caught:
            store._put_channel_record("edge", "symlink", {"version": "channel-record/v1"})
        assert caught.value.code == "IMMUTABLE_CHANNEL_CONFLICT"


def test_f03_protocol_accepts_only_closed_matching_context() -> None:
    _closure, _recipe, left, right = _results()
    index = _index(left, right)
    metadata = canonical_bytes(index.to_dict())

    class Adapter:
        def verify_and_authorize(self, metadata_bytes: bytes, **kwargs):
            assert metadata_bytes == metadata
            return TrustedTrustContext("artifact-release", ("key:a", "key:b"), 2, digest_bytes(metadata), kwargs["schema_set_digest"], kwargs["channel"], kwargs["expires_at"], kwargs["replay_id"])

    assert verify_index_bytes(metadata, adapter=Adapter(), signer_role="artifact-release", channel="edge", expires_at="2099-01-01T00:00:00Z", replay_id="replay:fixture").index_digest == index.index_digest

    class ForgedAdapter:
        def verify_and_authorize(self, metadata_bytes: bytes, **kwargs):
            return TrustedTrustContext("artifact-release", ("key:a",), 1, digest_bytes(b"other"), kwargs["schema_set_digest"], kwargs["channel"], kwargs["expires_at"], kwargs["replay_id"])

    with pytest.raises(TrustRejection) as caught:
        verify_index_bytes(metadata, adapter=ForgedAdapter(), signer_role="artifact-release", channel="edge", expires_at="2099-01-01T00:00:00Z", replay_id="replay:fixture")
    assert caught.value.code == "TRUST_CONTEXT_MISMATCH"


def test_cli_build_and_compare_from_unrelated_working_directory() -> None:
    with tempfile.TemporaryDirectory() as directory:
        out_a, out_b = Path(directory) / "a.json", Path(directory) / "b.json"
        store_a, store_b = Path(directory) / "store-a", Path(directory) / "store-b"
        env = {"PYTHONPATH": str(ROOT / "src")}
        command = [sys.executable, "-m", "omarchy_build", "build", "--builder", str(ROOT / "builders/fixture-a/definition.json"), "--recipe", str(ROOT / "fixtures/build/recipe.json"), "--source-lock", str(ROOT / "fixtures/build/source-lock.json"), "--sources", str(ROOT / "fixtures/build/sources.json"), "--output", str(out_a), "--artifact-store", str(store_a)]
        run = subprocess.run(command, cwd=directory, env=env, text=True, capture_output=True)
        assert run.returncode == 0, run.stderr
        command[command.index("--builder") + 1] = str(ROOT / "builders/fixture-b/definition.json")
        command[command.index("--output") + 1] = str(out_b)
        command[command.index("--artifact-store") + 1] = str(store_b)
        run = subprocess.run(command, cwd=directory, env=env, text=True, capture_output=True)
        assert run.returncode == 0, run.stderr
        run = subprocess.run([sys.executable, "-m", "omarchy_build", "compare", "--left", str(out_a), "--right", str(out_b), "--left-store", str(store_a), "--right-store", str(store_b)], cwd=directory, env=env, text=True, capture_output=True)
        assert run.returncode == 0, run.stderr
        assert json.loads(run.stdout)["decision"] == "match"
        run = subprocess.run([sys.executable, "-m", "omarchy_build", "compare", "--left", str(out_a), "--right", str(out_b)], cwd=directory, env=env, text=True, capture_output=True)
        assert run.returncode == 2
        assert json.loads(run.stderr)["code"] == "OUTPUT_BYTES_UNAVAILABLE"


def test_closed_schema_resources_reject_unknown_properties() -> None:
    from jsonschema import Draft202012Validator

    schema_dir = ROOT / "src/omarchy_build/schemas"
    for schema_path in sorted(schema_dir.glob("*.json")):
        schema = json.loads(schema_path.read_text())
        assert schema.get("additionalProperties") is False, schema_path.name
