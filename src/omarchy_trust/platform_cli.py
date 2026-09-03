"""Compatibility dispatch that adds ``omarchy-platform trust`` without editing F-02."""

from __future__ import annotations

import sys

from omarchy_platform.cli import main as foundation_main

from .cli import main as trust_main


def main(argv: list[str] | None = None) -> int:
    selected = sys.argv[1:] if argv is None else argv
    if selected and selected[0] == "trust":
        return trust_main(selected)
    return foundation_main(selected)


__all__ = ["main"]
