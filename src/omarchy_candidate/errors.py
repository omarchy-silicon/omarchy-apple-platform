"""Stable fail-closed errors for F-05 candidate assembly."""


class CandidateAssemblyError(ValueError):
    """A deterministic, redacted rejection from the F-05 seam."""

    def __init__(self, code: str, path: str = "$", detail: str = "candidate assembly rejected"):
        self.code = code
        self.path = path
        self.detail = detail
        super().__init__(f"{code} at {path}: {detail}")

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "detail": self.detail}
