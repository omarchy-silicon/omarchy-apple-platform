"""Generated, checked-in F-02 foundation constants.

This file is intentionally small. Full language bindings and semantic validators are
deferred to their owning slices; drift.py verifies these values against the lock.
"""

AUTHENTICATED_PAYLOAD_TYPES = (
    "board-registry/v1",
    "platform-manifest/v1",
    "installer-plan/v1",
    "qualification-record/v1",
    "boot-health/v1",
    "owner-approval/v1",
    "boot-success-mark/v1",
    "dtb-mutation-envelope/v1",
)

SCHEMA_INPUT_IDS = (
    "common/v1",
    "vocabularies/v1",
    "signed-document/v1",
    "board-registry/v1",
    "platform-manifest/v1",
    "installer-plan/v1",
    "qualification-record/v1",
    "boot-health/v1",
    "owner-approval/v1",
    "boot-success-mark/v1",
    "dtb-mutation-envelope/v1",
)

LIMITS = {
    "max_input_bytes": 1_048_576,
    "max_depth": 32,
    "max_object_properties": 128,
    "max_array_length": 1_024,
    "max_string_bytes": 4_096,
    "max_total_string_bytes": 262_144,
    "max_integer_magnitude": 9_223_372_036_854_775_807,
}

TYPE_CONTEXT = {
    "board-registry/v1": ("omarchy-board-registry", "board-registry-publication", "board-admission"),
    "platform-manifest/v1": ("omarchy-platform-manifest", "manifest-publication", "manifest-release"),
    "installer-plan/v1": ("omarchy-installer-plan", "installer-plan-proposal", "installer-planner"),
    "qualification-record/v1": ("omarchy-qualification-record", "qualification-result", "qualification-lab"),
    "boot-health/v1": ("omarchy-boot-runtime", "boot-health-core", "boot-runtime"),
    "owner-approval/v1": ("omarchy-owner-authorization", "installer-plan-execution", "owner-authorization"),
    "boot-success-mark/v1": ("omarchy-boot-runtime", "boot-success-marker", "boot-runtime"),
    "dtb-mutation-envelope/v1": ("omarchy-dtb-authority", "dtb-mutation-authorization", "dtb-authority"),
}

SCHEMA_SET_DIGEST = "sha256:74f4aae06e7dedac95f2d57a7b54cde32ba9583b529184fde9c7b0a71aca2fc1"
