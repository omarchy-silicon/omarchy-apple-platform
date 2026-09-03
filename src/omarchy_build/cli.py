"""Bounded deterministic ``omarchy-build`` command line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .builders import FixtureBuilder
from .comparison import compare_results
from .errors import BuildProvenanceError, StoreError, TrustRejection
from .metadata import make_package_index
from .models import BuildResult, BuilderDefinition, Recipe, SourceClosure
from .store import LocalArtifactStore
from .util import MAX_DOCUMENT_BYTES, canonical_bytes, read_json

EXIT_OK = 0
EXIT_REJECT = 2
EXIT_INPUT = 3


def _load(path: str, loader):
    return loader(read_json(path))


def _write(path: str, value: object) -> None:
    output = canonical_bytes(value) + b"\n"
    if len(output) > MAX_DOCUMENT_BYTES:
        raise BuildProvenanceError("RESOURCE_LIMIT", "$.output", "output byte limit exceeded")
    try:
        Path(path).write_bytes(output)
    except OSError as error:
        raise BuildProvenanceError("OUTPUT_WRITE_FAILURE", "$.output", "output could not be written") from error


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omarchy-build")
    sub = parser.add_subparsers(dest="command", required=True)
    lock = sub.add_parser("lock")
    lock_sub = lock.add_subparsers(dest="lock_command", required=True)
    lock_check = lock_sub.add_parser("check")
    lock_check.add_argument("--builder", required=True)
    lock_check.add_argument("--recipe", required=True)
    lock_check.add_argument("--source-lock", required=True)
    build = sub.add_parser("build")
    build.add_argument("--builder", required=True)
    build.add_argument("--recipe", required=True)
    build.add_argument("--source-lock", required=True)
    build.add_argument("--sources", required=True, help="JSON map from input ID to source file path")
    build.add_argument("--output", required=True)
    build.add_argument("--artifact-store")
    compare = sub.add_parser("compare")
    compare.add_argument("--left", required=True)
    compare.add_argument("--right", required=True)
    compare.add_argument("--output")
    compare.add_argument("--left-store")
    compare.add_argument("--right-store")
    store = sub.add_parser("store")
    store_sub = store.add_subparsers(dest="store_command", required=True)
    verify = store_sub.add_parser("verify")
    verify.add_argument("--root", required=True)
    verify.add_argument("--digest", required=True)
    promote = sub.add_parser("promote")
    promote.add_argument("--root", required=True)
    promote.add_argument("--source-channel", required=True)
    promote.add_argument("--target-channel", required=True)
    promote.add_argument("--release-id", required=True)
    promote.add_argument("--f07-authorized", action="store_true", help=argparse.SUPPRESS)
    metadata = sub.add_parser("metadata")
    metadata_sub = metadata.add_subparsers(dest="metadata_command", required=True)
    metadata_sub.add_parser("verify")
    rollback = sub.add_parser("rollback")
    rollback.add_argument("--root", required=True)
    rollback.add_argument("--channel", required=True)
    rollback.add_argument("--failed-release-id", required=True)
    rollback.add_argument("--restore-release-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "lock":
            definition = _load(args.builder, BuilderDefinition.from_dict)
            recipe = _load(args.recipe, Recipe.from_dict)
            closure = _load(args.source_lock, SourceClosure.from_dict)
            if closure.recipe_id != recipe.recipe_id or closure.recipe_digest != recipe.recipe_digest:
                raise BuildProvenanceError("SOURCE_RECIPE_MISMATCH", "$.recipe_digest", "source closure and recipe differ")
            print(json.dumps({"version": "f04-lock-check/v1", "decision": "allow", "builder_definition_digest": definition.definition_digest, "recipe_digest": recipe.recipe_digest, "source_closure_digest": closure.closure_digest}, sort_keys=True, separators=(",", ":")))
            return EXIT_OK
        if args.command == "build":
            definition = _load(args.builder, BuilderDefinition.from_dict)
            recipe = _load(args.recipe, Recipe.from_dict)
            closure = _load(args.source_lock, SourceClosure.from_dict)
            source_paths = read_json(args.sources)
            if not isinstance(source_paths, dict):
                raise BuildProvenanceError("TYPE_MISMATCH", "$.sources", "source map required")
            source_bytes = {}
            for input_id, path in source_paths.items():
                if not isinstance(path, str):
                    raise BuildProvenanceError("TYPE_MISMATCH", "$.sources", "source path must be string")
                try:
                    source_path = Path(path)
                    if not source_path.is_absolute():
                        source_path = Path(args.sources).resolve().parent / source_path
                    source_bytes[input_id] = source_path.read_bytes()
                except OSError as error:
                    raise BuildProvenanceError("INPUT_READ_FAILURE", f"$.sources.{input_id}", "source could not be read") from error
            result = FixtureBuilder(definition).build(closure, recipe, source_bytes)
            if args.artifact_store:
                store = LocalArtifactStore(args.artifact_store)
                for output in result.outputs:
                    store.put(result.output_bytes[output.path], expected_digest=output.content_digest)
            _write(args.output, result.to_dict())
            print(json.dumps({"version": "f04-build/v1", "decision": "allow", "result_digest": result.result_digest, "artifact_set_digest": result.artifact_set_digest}, sort_keys=True, separators=(",", ":")))
            return EXIT_OK
        if args.command == "compare":
            left = _load(args.left, BuildResult.from_dict)
            right = _load(args.right, BuildResult.from_dict)
            if args.left_store or args.right_store:
                if not args.left_store or not args.right_store:
                    raise BuildProvenanceError("OUTPUT_BYTES_UNAVAILABLE", "$.store", "both independent output stores are required")
                left_store = LocalArtifactStore(args.left_store)
                right_store = LocalArtifactStore(args.right_store)
                left = BuildResult(**{**left.__dict__, "output_bytes": {output.path: left_store.read(output.content_digest) for output in left.outputs}})
                right = BuildResult(**{**right.__dict__, "output_bytes": {output.path: right_store.read(output.content_digest) for output in right.outputs}})
            result = compare_results(left, right)
            if args.output:
                _write(args.output, result)
            print(json.dumps(result, sort_keys=True, separators=(",", ":")))
            return EXIT_OK
        if args.command == "store":
            if args.store_command != "verify":
                raise BuildProvenanceError("COMMAND_INVALID", "$.command", "unsupported store command")
            data = LocalArtifactStore(args.root).read(args.digest)
            print(json.dumps({"version": "f04-store-verify/v1", "decision": "allow", "digest": args.digest, "byte_count": len(data)}, sort_keys=True, separators=(",", ":")))
            return EXIT_OK
        if args.command == "promote":
            if args.target_channel == "stable" and not args.f07_authorized:
                raise StoreError("STABLE_PROMOTION_REQUIRES_F07", "$.target_channel", "stable promotion is F-07-only")
            raise StoreError("TRUST_ADAPTER_REQUIRED", "$.context", "CLI promotion requires an F-03 context adapter; no boolean bypass exists")
        if args.command == "rollback":
            raise StoreError("TRUST_ADAPTER_REQUIRED", "$.context", "CLI rollback requires an F-03 context adapter")
        raise BuildProvenanceError("COMMAND_INVALID", "$.command", "unsupported command")
    except (BuildProvenanceError, StoreError, TrustRejection) as error:
        print(json.dumps({"version": "f04-result/v1", "decision": "reject", **error.as_dict()}, sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return EXIT_REJECT
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({"version": "f04-result/v1", "decision": "reject", "code": "INPUT_INVALID", "path": "$", "detail": "input could not be parsed"}, sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return EXIT_INPUT
