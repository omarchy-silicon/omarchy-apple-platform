#!/usr/bin/env python3
"""Run the Q-00 acceptance path with all socket creation denied."""

from __future__ import annotations

import socket
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from omarchy_intake.cli import main  # noqa: E402


def main_offline() -> int:
    manifest = str(ROOT / "data/intake/manifest.json")
    argv = ["validate", "--manifest", manifest, "--root", str(ROOT), "--offline"]
    with mock.patch.object(socket, "socket", side_effect=AssertionError("Q-00 attempted network access")), mock.patch.object(socket, "create_connection", side_effect=AssertionError("Q-00 attempted network access")):
        return main(argv)


if __name__ == "__main__":
    raise SystemExit(main_offline())
