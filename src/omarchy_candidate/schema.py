"""Generated-schema consumer constants.

This module is intentionally tiny: the field contract is generated from
``candidate-assembly.schema.json`` by ``tools/candidate/generate.py`` and is
not a second handwritten schema owned by a downstream consumer.
"""

from .generated import INPUT_VERSION, OUTPUT_VERSION, REQUIRED_GATE_IDS, SCHEMA_DIGEST, VERSION

__all__ = ["INPUT_VERSION", "OUTPUT_VERSION", "REQUIRED_GATE_IDS", "SCHEMA_DIGEST", "VERSION"]
