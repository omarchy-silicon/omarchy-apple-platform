# Omarchy platform schema foundation

This checkout is the executable F-02 implementation foundation. It provides a bounded Python 3.12 JSON transport parser, closed eight-value vocabulary, Draft 2020-12 schema inputs, deterministic canonical bytes, domain-separated SHA-256 helpers, a read-only diagnostic CLI, accepted fixtures, hostile boundary tests, and schema-lock drift checking.

The implementation intentionally stops at the common authenticated envelope and conservative payload stubs. Type-specific cross-document semantics, trust roots and signatures, generated Swift/Rust bindings, storage and installer execution, hardware/physical qualification, and release/support completion are not implemented. A parsed document is not trusted and no command authorizes mutation.

Install locally with `python3.12 -m pip install -e .`; run `python -m unittest discover -s tests -v`, `omarchy-platform schema list`, and `python tools/schema/drift.py`.
