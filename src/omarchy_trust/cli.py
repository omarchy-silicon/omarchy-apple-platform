"""Read-only F-03 verifier CLI."""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import ExitStack
from dataclasses import asdict
from pathlib import Path
from typing import Any

from omarchy_platform.strictjson import parse

from .constants import MAX_METADATA_BYTES
from .core import verify_document
from .errors import TrustFailure
from .models import ReplaySnapshot


def _read(path: str) -> bytes:
    file_path = Path(path)
    try:
        with file_path.open("rb") as stream:
            data = stream.read(MAX_METADATA_BYTES + 1)
    except OSError:
        raise TrustFailure("TRUST_IO_LIMIT", "$", "bounded input read failed") from None
    if len(data) > MAX_METADATA_BYTES:
        raise TrustFailure("TRUST_INPUT_TOO_LARGE", "$", "metadata input exceeds the bounded limit")
    return data


def _json(path: str) -> Any:
    try:
        return parse(_read(path))
    except TrustFailure:
        raise
    except Exception:
        raise TrustFailure("TRUST_JSON_INVALID", "$", "input is not valid JSON") from None


def _artifact_args(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        if value.count("=") != 1:
            raise TrustFailure("TRUST_SCHEMA_INVALID", "$.artifacts", "trust object shape is invalid")
        artifact_id, path = value.split("=", 1)
        if not artifact_id or not path or artifact_id in result:
            raise TrustFailure("TRUST_ARTIFACT_MISSING", "$.artifacts", "required artifact bytes are missing")
        result[artifact_id] = path
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omarchy-trust")
    sub = parser.add_subparsers(dest="command", required=True)
    trust = sub.add_parser("trust")
    trust_sub = trust.add_subparsers(dest="trust_command", required=True)
    verify = trust_sub.add_parser("verify")
    verify.add_argument("--root-bundle", required=True)
    verify.add_argument("--document", required=True)
    verify.add_argument("--proof", action="append", default=[])
    verify.add_argument("--replay-state", required=True)
    verify.add_argument("--artifact", action="append", default=[], metavar="ID=FILE")
    verify.add_argument("--repository")
    verify.add_argument("--channel")
    args = parser.parse_args(argv)
    try:
        if args.command != "trust" or args.trust_command != "verify":
            raise TrustFailure("TRUST_SCHEMA_INVALID", "$", "unsupported trust command")
        replay = _json(args.replay_state)
        if not isinstance(replay, dict):
            raise TrustFailure("TRUST_REPLAY_STATE_UNAVAILABLE", "$.replay_state", "replay state is unavailable or divergent")
        try:
            replay_snapshot = ReplaySnapshot.from_mapping(replay)
        except ValueError:
            raise TrustFailure("TRUST_REPLAY_STATE_UNAVAILABLE", "$.replay_state", "replay state is unavailable or divergent") from None
        artifact_paths = _artifact_args(args.artifact)
        with ExitStack() as stack:
            artifact_streams = {}
            for artifact_id, path in artifact_paths.items():
                try:
                    file_path = Path(path)
                    size = file_path.stat().st_size
                    stream = stack.enter_context(file_path.open("rb"))
                    artifact_streams[artifact_id] = (stream, size)
                except OSError:
                    raise TrustFailure("TRUST_IO_LIMIT", "$.artifacts", "bounded input read failed") from None
            context = verify_document(
                _read(args.document),
                _read(args.root_bundle),
                proof=tuple(_read(path) for path in args.proof),
                replay_snapshot=replay_snapshot,
                repository=args.repository,
                channel=args.channel,
                artifact_streams=artifact_streams,
            )
        print(json.dumps({"decision": "TRUSTED", **asdict(context)}, sort_keys=True, separators=(",", ":")))
        return 0
    except TrustFailure as error:
        print(json.dumps({"code": error.code, "path": error.path, "detail": error.detail}, sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 2
    except (OSError, ValueError):
        print(json.dumps({"code": "TRUST_IO_LIMIT", "path": "$", "detail": "bounded input read failed"}, sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 3


__all__ = ["main"]
