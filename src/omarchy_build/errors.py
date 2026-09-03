"""Stable, redacted errors for the F-04 build and release seams."""


class BuildProvenanceError(Exception):
    """A deterministic failure that never includes secrets or host paths."""

    def __init__(self, code: str, path: str = "$", detail: str = "operation rejected"):
        self.code = code
        self.path = path
        self.detail = detail
        super().__init__(f"{code} at {path}: {detail}")

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "detail": self.detail}


class TrustRejection(BuildProvenanceError):
    """Typed rejection returned by the F-03 adapter boundary."""


class StoreError(BuildProvenanceError):
    """Typed immutable-store failure."""
