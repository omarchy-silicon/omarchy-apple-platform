"""F-04 reproducible build and provenance contract."""

from .builders import FixtureBuilder
from .comparison import compare_output_maps, compare_results
from .errors import BuildProvenanceError, StoreError, TrustRejection
from .metadata import make_package_index, verify_index_bytes
from .models import (
    BuildResult,
    BuilderDefinition,
    InputRef,
    OutputRecord,
    PackageArtifact,
    PackageIndex,
    Provenance,
    Recipe,
    Sbom,
    SbomEntry,
    SourceClosure,
    TrustedTrustContext,
    artifact_set_digest,
)
from .sbom import make_sbom, validate_sbom
from .store import ArtifactStore, LocalArtifactStore
from .trust import TrustAdapter, require_trusted_context

__all__ = [
    "ArtifactStore",
    "BuildProvenanceError",
    "BuildResult",
    "BuilderDefinition",
    "FixtureBuilder",
    "InputRef",
    "LocalArtifactStore",
    "OutputRecord",
    "PackageArtifact",
    "PackageIndex",
    "Provenance",
    "Recipe",
    "Sbom",
    "SbomEntry",
    "SourceClosure",
    "StoreError",
    "TrustAdapter",
    "TrustRejection",
    "TrustedTrustContext",
    "artifact_set_digest",
    "compare_output_maps",
    "compare_results",
    "make_package_index",
    "make_sbom",
    "require_trusted_context",
    "validate_sbom",
    "verify_index_bytes",
]
