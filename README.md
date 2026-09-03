<p align="center">
  <img src="docs/assets/omarchy-silicon-logo.png" alt="Omarchy Silicon Apple platform initiative logo" width="760">
</p>

# Omarchy platform schema foundation

This checkout is the executable F-02 implementation increment. It provides a bounded Python 3.12 JSON transport parser, eight closed Draft 2020-12 type schemas, immutable typed payload views, RFC 8785 canonical bytes, domain-separated SHA-256 helpers, pure cross-document structural conformance, a read-only diagnostic CLI, accepted fixtures, hostile boundary tests, and schema-lock drift checking. Conformance is deliberately unsigned, byte-unverified, and never release-eligible.

Trust roots, signature verification, generated Swift/Rust bindings, storage and installer execution, hardware/physical qualification, and release/support completion remain outside this increment. The schema lock's generator, parser, and toolchain input arrays remain residuals. The numeric policy remains bounded by RFC 8785/I-JSON's `2**53-1` safe-integer rule. A parsed or conformant document is not trusted and no command authorizes mutation.

Install locally with `python3.12 -m pip install -e .`; run `python -m unittest discover -s tests -v`, `omarchy-platform schema list`, and `python tools/schema/drift.py`.
