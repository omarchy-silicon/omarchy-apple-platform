# Omarchy Silicon Platform Program

Status: ACTIVE — foundation and design phase

Date established: 2026-09-02

Coordinator: primary Codex session acting for the project owner

Canonical organization: https://github.com/omarchy-silicon

## 1. Mission

Deliver a clean, trustworthy Omarchy installer that a Mac owner can launch from macOS and use to install Omarchy alongside macOS on every qualified Apple Silicon Mac. Omarchy Silicon will own the installer experience, platform manifest, downstream patch queues, builds, signing, release timing, rollback behavior, and physical qualification evidence.

The long-term target is literal hardware compatibility for every applicable function on every released Apple Silicon Mac board, not merely successful boot, SoC recognition, or a usable subset of features.

The project may reuse, fork, improve, and upstream open-source work. Ownership means that an upstream merge or another distribution's release is never the authority for an Omarchy release. Omarchy carries the necessary patches, produces the artifacts, qualifies the complete tuple, and supports the result.

## 2. Scope and dated target inventory

The support program covers every Apple Silicon Mac board released from M1 onward. As of 2026-09-02, the silicon intake includes M1, M1 Pro, M1 Max, M1 Ultra, M2, M2 Pro, M2 Max, M2 Ultra, M3, M3 Pro, M3 Max, M3 Ultra, M4, M4 Pro, M4 Max, M5, M5 Pro, M5 Max, M5 Ultra, the A18 Pro MacBook Neo, and the announced M6 Mac mini.

M6 is a target, not a supported board, until shipping hardware is acquired and completes qualification. New Apple announcements enter intake within one business day, but no marketing announcement changes the supported set by itself.

Support is keyed by exact board identity, SoC identity, device-tree compatibility records, firmware schema, and qualified platform release. Chip-family recognition is diagnostic metadata only.

### 2.1 Intake is not admission

CNVS audit task `5E649A10-4465-45DC-9D31-9164E554ECC8` reported 47 candidate M1-through-M4 intake rows and 12 candidate A18/M5/M6 intake rows. Those counts and findings are provisional research output, not a canonical dataset or install allowlist: no row is Omarchy-qualified and no row may authorize a privileged operation until Q-00 produces a cited, digest-addressed artifact and its selectors and evidence are encoded and validated through `board-registry/v1`.

Each intake row records the marketing product and year, Apple model identifier, Apple/Asahi board selector where independently evidenced, device-tree compatible string, SoC identifier, shipped/announced lifecycle, upstream evidence tier, Omarchy evidence tier, retrieval date, source references, contradictions, and unknowns. Unknown values are null or empty; they are never filled from the nearest chip family.

The worker reported unresolved selector gaps in the 12 newer candidate rows, contradictory M5 identity evidence, a model-identifier contradiction in the M3 Ultra candidate, incomplete device-tree evidence for M4 Pro/Max, and no physical Omarchy qualification record. Until Q-00 preserves the source bundle, retrieval metadata, record-level citations, contradictions, and content digest, every affected candidate is UNKNOWN and fails closed. A later evidence correction appends a superseding record; it never silently rewrites the historical observation.

## 3. Meaning of fully compatible

A board may be promoted to FULL only when every capability physically present on that board passes the applicable qualification rows:

- Safe installation beside macOS without modifying unrelated APFS containers.
- Native Apple boot-picker presence, owner authorization, LocalPolicy compatibility, startup-disk selection, uninstall, and DFU recovery.
- Encrypted and unencrypted boot, including interrupted-install and interrupted-update recovery.
- m1n1 stage 1 and stage 2, U-Boot, device trees, GRUB, kernel, initramfs, firmware, Mesa, and userspace validated as one release tuple.
- Cold boot, warm reboot, shutdown, boot-loop recovery, suspend/resume cycles, idle soak, and wake from supported inputs.
- CPU topology, interrupt controller, timers, DART/IOMMU, SMC, cpufreq, cpuidle, thermal control, fan behavior, charging, MagSafe where present, battery reporting, and acceptable idle drain.
- Internal display, backlight, notch geometry, HDR, VRR, local dimming where present, GPU acceleration, OpenGL/Vulkan conformance, compositor soak, and every supported external-display topology.
- USB 2/3/4, Thunderbolt, DisplayPort Alt Mode, HDMI, PCIe, NVMe, SD card, Ethernet, docks, hotplug, and sleep/wake interaction.
- Wi-Fi and Bluetooth across cold boot, roaming, suspend, reconnect, coexistence, regulatory data, and board-specific firmware/NVRAM.
- Keyboard, trackpad, keyboard backlight, Touch Bar where present, ambient light, camera, microphones, headphone output, HDMI/DP audio, speakers, DSP profiles, and speaker-protection enforcement.
- Hardware video decoding, encoding, AV1 where present, and ProRes where provided by the hardware.
- SEP and Touch ID where present, including enrollment, authentication, lockout, recovery, and security-boundary review.
- Neural Engine exposure and validated compute behavior where present.
- Virtualization behavior and guest boot appropriate to the board's supported platform facilities.
- Update from every supported prior stable release, automatic rollback after a failed boot, explicit downgrade rules, factory reset, and clean removal.
- No critical kernel faults, unsafe speaker state, silently disabled applicable feature, untracked qualification exception, or success message after a failed required step.

Until those rows pass, the board must be labeled DETECTED, BRINGUP, EXPERIMENTAL, or DAILY_DRIVER according to the narrower evidence. Only FULL satisfies the program mission.

## 4. Product experience: the clean installer

The final user experience is one signed Omarchy Silicon application or verified command launched from macOS. It replaces the current multi-product flow that requires installing an intermediary distribution, logging in with a default root account, and pasting a second bootstrap command.

The unavoidable Apple owner-authentication and Recovery steps remain visible, guided parts of one coherent transaction. They are not hidden, bypassed, or presented as unrelated manual troubleshooting.

### 4.1 Installer stages

#### Stage 0 — signed launch and immutable metadata

- Launch a signed and notarized macOS application with an equivalent auditable CLI.
- Load an immutable, signed installer release manifest from Omarchy-controlled infrastructure.
- Verify the manifest signature, schema version, release channel, expiry policy, and artifact digests before any privileged operation.
- Refuse moving branch URLs, unsigned scripts, unpinned package sources, or metadata that references an unqualified board.

#### Stage 1 — read-only inventory and plan

- Read exact Mac product/board and SoC identifiers, macOS version, boot firmware version, disk/APFS topology, FileVault state, free space, power/battery state, network readiness, and existing alternative-OS containers.
- Model FileVault state, Data-volume lock state, macOS administrator status, machine-owner authority, Linux encryption choice, and paired RecoveryOS/1TR state as distinct facts. Never infer one from another or describe all of them as an administrator password.
- Resolve the board through the signed support registry.
- Identify disks by stable media and APFS identifiers and display model, capacity, connection, boot role, and ownership. Never select the first internal disk or identify an external disk only by its display name and size.
- Produce a human-readable and machine-readable installation plan showing every partition/container change, exact byte allocation, macOS reserve, download size, target release, encryption choice, rollback boundary, Apple boot artifacts that may remain on internal storage, and recovery requirement.
- Fetch and verify every required signed artifact into a content-addressed cache before the destructive boundary, including the exact Apple firmware input, Recovery/stub inputs, Omarchy image, and human-produced opaque boot artifact envelope selected by the manifest. Show bytes, rate, ETA, provenance, pause, retry, resume, verification, and cache state; an offline claim requires a complete signed bundle.
- Perform no privileged operation, APFS or boot mutation, Recovery update, system configuration change, or target selection side effect during inventory, admission, artifact acquisition, verification, or plan generation. In particular, `updatePreboot` is a mutation and is forbidden before final consent.

#### Stage 2 — owner confirmation and Apple platform provisioning

- Present one final mutation summary and obtain explicit typed confirmation of every destructive operation. Approval binds the exact canonical `plan_digest`, `scope_digest`, schema-set digest, board-registry document ID and payload digest, platform-manifest document ID and payload digest, inventory/topology digest, target identifiers, ordered operations, actor identity, authority role binding, and expiry. The actor and role must resolve through the trusted authority context for the exact repository, slice, operation, and policy digest; an unbound, expired, replayed, or scope-mismatched approval is invalid. Any topology, identity, artifact, policy, schema set, authority, or operation change invalidates approval and returns to read-only planning. Security reduction, encryption, telemetry, and external-disk consequences require distinct decisions and may not be bundled into storage consent.
- Use an Apple-supported owner-authorization surface where available; never collect a macOS, FileVault, Recovery, or Linux password in an Omarchy text field, command argument, environment variable, or log.
- Use Apple's supported APFS and Recovery mechanisms to resize space; do not implement an independent APFS writer.
- Create the per-OS stub macOS/APFS container, RecoveryOS relationship, LocalPolicy authorization, and OS-specific ESP required by Apple's platform model.
- Deploy only the Apple-signed machine firmware already acquired and verified before consent; Stage 2 performs no network acquisition. Revalidate its build identity, digest, manifest binding, provenance, and target board immediately before use, then extract only the required artifacts.
- Install the qualified m1n1 stage-1 payload through the owner-authorized boot policy flow.
- Journal every durable mutation so restart/resume derives state from disk rather than carrying transient process state.

#### Stage 3 — Omarchy boot environment

- Boot the exact signed m1n1 stage-2, U-Boot, device-tree, GRUB, kernel, initramfs, and firmware tuple named by the installer manifest.
- Validate board identity again inside Linux and compare it to the macOS-side plan.
- Refuse installation if identities, firmware schema, artifact digests, disk targets, or expected capabilities disagree.
- Provide an accessible graphical installer with a complete CLI path for diagnostics and recovery.

#### Stage 4 — system installation

- Install the qualified Omarchy ARM package set only from the complete content-addressed cache acquired and verified before final consent. Repository metadata, indexes, packages, images, firmware, and boot inputs are immutable manifest-selected cache objects at this stage; Stage 4 runs with network acquisition denied and cannot refresh, substitute, or complete a missing input after the destructive boundary.
- Create the selected Btrfs/LUKS2 layout while keeping boot artifacts in versioned boot slots outside root snapshots.
- Configure users without shipped default passwords.
- Install board-specific firmware, audio profiles, speaker protection, wireless data, display configuration, and capability policy from the signed board record.
- Run installation acceptance checks before selecting the new boot slot.

#### Stage 5 — first boot and attestation

- Start the new slot once while preserving the last-known-good installer/recovery path.
- Run the board's required hardware smoke suite and record the exact manifest, artifact, firmware, package, and source SHAs.
- Mark the slot successful only after the required boot-health contract passes.
- Present a precise capability report containing the platform-manifest digest, component source and artifact digests, board identity, and required capability results. Never translate a missing required component into a warning followed by “Install complete.”

#### Stage 6 — update, rollback, uninstall, and recovery

- Update the platform as an atomic compatibility tuple rather than unrelated packages.
- Write new boot and root artifacts to inactive/versioned slots, verify them, switch once, and require a boot-success marker.
- Automatically fall back after failed boot attempts and retain a user-selectable last-known-good entry.
- Provide clean removal that resolves and previews the exact Omarchy-owned APFS container, ESP, and Linux partition identifiers recorded by the transaction journal, revalidates them, obtains explicit authorization, and returns free space through Apple's supported tooling. Pattern-based discovery or deletion is forbidden.
- Maintain a tested DFU recovery runbook and a recovery image whose version and supported boards are explicit.

### 4.2 Installer safety invariants

- Unknown or ambiguous board, SoC, firmware, manifest, disk, or transaction state fails closed before mutation.
- Mutable branches, moving tags, unpinned raw downloads, `TrustAll`, `skipinteg`, unsigned package databases, and successful network transport are never code or artifact authority. A hostile remote that returns valid-looking content must fail before privilege elevation.
- Every target block device and APFS object is resolved to stable identifiers and revalidated immediately before use.
- No destructive target is accepted from an unresolved environment variable, glob, user-provided raw device path, or mutable remote response.
- Existing macOS and unrelated APFS containers are outside the mutation authority.
- Every durable step is idempotent or has an explicit recovery transition.
- The transaction journal is a versioned, bounded, hash-chained record bound to the signed plan header and transaction verification material. It is evidence, never mutation authority. Missing, divergent, truncated, replayed, stale, or unauthenticated replicas permit only fresh observation and a typed hold/recovery decision; they can never supply a destructive target or silently recreate approval.
- Immediately before and after every mutation, the executor records and verifies the complete allowlisted identity/property snapshot for all targets and protected objects. A topology digest or object-property change invalidates approval; partial command output or an exit code cannot satisfy a postcondition.
- The clean installer creates the final Btrfs/LUKS2 layout directly. It must not use an ext4-to-Btrfs rebuild or in-place LUKS re-encryption as an installation step; any separately offered legacy migration requires its own preserved recovery root, versioned journal, before/after boot-configuration proof, restart-after-every-phase tests, and independent acceptance.
- A worker may not self-disarm or return success because it sees Btrfs, LUKS, an existing stub, or no pending low-level operation. Completion derives only from the full signed plan, journal, boot configuration, artifact identities, and postconditions.
- Installer logs redact credentials, owner tokens, recovery secrets, device identifiers not needed for support, and encryption material.
- Network loss, power loss, process death, full disk, stale metadata, signature failure, and unsupported firmware are explicit tested states.

### 4.3 Required user-visible state machine

The signed graphical application and equivalent CLI expose the same typed states and transitions. A restart, crash, or handoff to Recovery must resume by reading a versioned on-disk transaction journal and revalidating the machine, target identifiers, manifest, and artifacts.

| State | User-visible result | Mutation authority |
|---|---|---|
| Launch | Product identity, signing identity, release/channel, manifest source, and network disclosure | None |
| Readiness | Board, SoC, macOS/firmware, FileVault and Data-lock state, owner authority, power, network, disk topology, and existing OS inventory | Read-only |
| Admission | Exact support tier and reason; ambiguous, unknown, and unsupported machines exit safely | None |
| Storage plan | Stable target identifiers, exact byte changes, macOS reserve, Omarchy-owned objects, external-boot consequences, and rollback boundary | None |
| Artifact acquisition | Signed sources, sizes, progress, ETA, retry/resume, digest verification, and offline-bundle completeness | User-cache writes only |
| Consent | Final destructive-operation list plus separate security, encryption, telemetry, and external-disk decisions | Authorization only |
| Apple authorization | Clear machine-owner/Recovery requirement without Omarchy handling credentials | Apple-owned authorization surface |
| Provisioning | Before/after object identifiers and durable checkpoint for each APFS, RecoveryOS, LocalPolicy, firmware, and boot-policy operation | Only the consented plan |
| Recovery handoff | Persisted checkpoint, exact visual boot-picker/1TR instructions, and a safe path back to macOS | Only the recorded transition |
| Linux installation | Revalidated board, disk, manifest, artifacts, and approved layout | Only the consented plan |
| First boot | Required smoke-test and boot-health evidence; incomplete requirements block completion | Qualified boot-slot transition |
| Failure | Resume, rollback, safe macOS return, recovery image, and then explicit DFU escalation with second-host/cable checklist | Journal-defined recovery only |
| Uninstall | Exact identity-based deletion preview, authorization, removal, and Apple-supported space reclamation | Recorded Omarchy objects only |
| Support export | Local redacted bundle with a user-visible payload preview before save or upload | User-selected destination only |

### 4.4 Installer experience, privacy, and recovery gates

- The primary installer is a signed and notarized native macOS application. The CLI must be functionally equivalent for auditing, automation, diagnostics, and recovery; it is not a second, divergent installation path.
- Every screen and recovery instruction must pass VoiceOver, keyboard-only navigation, Switch Control, Dynamic Type, high-contrast, reduced-motion, and no-color-only-meaning checks. Terminal ANSI prompts, raw-mode one-letter choices, and a second-stage shell script launched in Terminal are not the release UX.
- All installer strings, errors, measurements, dates, recovery instructions, and support content are localizable. Apple-owned UI labels are quoted exactly so localized users can identify them.
- Reboot, boot-picker, 1TR, owner authorization, and return-to-macOS handoffs use persisted checkpoints and both visual and textual instructions; timing-dependent prose alone is insufficient.
- Telemetry is off by default. Artifact downloads disclose their endpoints and unavoidable server metadata but do not imply analytics consent. Optional metrics require a separate one-time opt-in, show the exact payload, never block installation, and exclude passwords, encryption material, owner tokens, serials, raw APFS identifiers, hostnames, usernames, home paths, MAC addresses, full partition maps, and raw command output.
- Support bundles are local and redacted by default, available after failures, and previewable before saving or uploading. Exact board identity, detailed disk data, and upload are separate user choices.
- Credential state is explicit and non-secret: FileVault status, Data-volume lock status, SecureToken/APFS crypto-user eligibility, macOS administrator status, machine-owner eligibility, Recovery authorization required/pending/accepted/cancelled/failed, paired RecoveryOS/1TR status, and Linux passphrase configured/verified/cleared. macOS, FileVault, machine-owner, SecureToken, APFS crypto-user, RecoveryOS, and 1TR secrets are entered only into Apple-owned authorization surfaces; Omarchy receives a typed result and never the secret. A Linux-encryption secret may enter only through a native secure-text control or a no-echo controlling-terminal read into bounded locked memory and may cross a process boundary only through a dedicated anonymous close-on-exec pipe opened for the single intended consumer, never general stdin, argv, environment, filesystem, cache, journal, telemetry, or logs. The buffer and pipe are zeroized and closed on success, cancellation, error, crash recovery, and timeout. Tests inject secrets into text fields, subprocess argv/environment/stdin and unintended descriptors, caches, swap/crash artifacts, structured events, journals, logs, telemetry, support bundles, and Apple-tool handoffs and require their absence outside that exact ephemeral channel.
- No all-board, offline, encrypted, accessible, localized, recovery-safe, or uninstall-safe claim is permitted until its corresponding automated and physical acceptance evidence exists.

## 5. System architecture

```text
Signed macOS installer
        |
        v
Signed installer manifest + board registry
        |
        v
Apple stub OS / RecoveryOS / LocalPolicy / firmware provisioning
        |
        v
m1n1 stage 1 -> m1n1 stage 2 + DT -> U-Boot -> GRUB
        |
        v
Omarchy Apple kernel + initramfs + firmware
        |
        v
Mesa/AGX + media + audio + wireless + Omarchy userspace
        |
        v
Boot-health attestation -> qualified release ledger
```

The platform manifest is the sole authority connecting these layers. A package manager may install the artifacts, but it may not independently choose incompatible versions.

## 6. Repository ownership and interfaces

### `omarchy-silicon/omarchy-apple-platform`

Owns the board registry, capability vocabulary, release-manifest schemas, component lockfiles, packaging recipes, build orchestration, signing policy, qualification schema, public support ledger, factory source of truth, and release promotion logic.

It does not vendor whole component histories. It pins exact commits in the component repositories and records their artifact digests.

### `omarchy-silicon/omarchy-mac`

Owns the Omarchy product/control plane: desktop integration, installer handoff, board-policy consumption, system configuration, migrations, package/application parity, diagnostics, update UX, and the command surface visible to users.

It must consume generated signed support data. It must not invent a second SoC map or infer support from `uname -m`.

### `omarchy-silicon/omarchy-mac-installer`

Owns the macOS/Recovery bootstrap, APFS plan, Apple firmware provisioning, installation transaction journal, image selection, uninstall, recovery handoff, branding, accessibility, and installer telemetry policy.

It consumes a signed installer manifest and board record. It must not decide platform component versions independently.

### `omarchy-silicon/m1n1-omarchy`

Owns Omarchy's downstream m1n1 patch queue, reproducible stage-1/stage-2 builds, board bring-up instrumentation, serial/debug artifacts, and release notes describing supported firmware schemas.

This repository is a HUMAN-ONLY workstream because its repository instructions prohibit AI/LLM use. Agents must not inspect, analyze, edit, test, or otherwise operate on its source. The automated factory treats human-produced m1n1 artifacts and signed metadata as opaque inputs and validates only their declared hashes, signatures, schemas, provenance, and behavior at the cross-repository/platform boundary.

### `omarchy-silicon/u-boot-omarchy`

Owns Omarchy's downstream U-Boot patch queue, Apple board configuration, UEFI behavior, boot-slot selection, recovery selection, boot-success/failure transport, and compatibility with the pinned m1n1/DT tuple.

### `omarchy-silicon/linux-omarchy`

Owns Omarchy's downstream Apple kernel patch queue, device trees, configuration, ABI policy, driver backports, firmware interfaces, debug builds, and per-board kernel qualification artifacts.

### `omarchy-silicon/mesa-omarchy`

Mirrors the authoritative freedesktop.org Mesa history and owns the minimal Omarchy downstream AGX patch queue, build configuration, conformance results, compositor regression results, and compatibility declarations for the pinned kernel/firmware tuple.

### Frozen cross-repository contracts

The first design wave may propose details but may not create competing authorities. F-02 owns one closed authenticated vocabulary of exactly eight payload types. Every object is canonical UTF-8 JSON under RFC 8785 JCS, carried in the common authenticated envelope, bound to the exact schema-set digest, and accepted by consumers only as a verified trusted type. Stable document IDs are never content digests; the envelope carries the separately computed payload digest.

- `board-registry/v1`: exact board and SoC identity, firmware schema, physical capabilities, lifecycle state, and required qualification profile.
- `platform-manifest/v1`: typed Linux-kernel, DTB-set, firmware-bundle/ABI, Mesa-stack, and boot-stack component records, their exact source/config/patch/toolchain/report/artifact locks, typed inter-component constraints, channel, required boot-health policy, and rollback compatibility.
- `installer-plan/v1`: read-only inventory, stable disk/APFS identifiers, proposed mutations, selected board record, release manifest, actor/role context, and approval requirements; the approval itself is a separate payload.
- `qualification-record/v1`: physical board identity, firmware/macOS baseline, manifest identity and digest, performed tests, raw evidence references, failures, residuals, operator, and timestamps.
- `boot-health/v1`: signed health core containing selected slot, generation and lineage, attempt counter, manifest-bound required checks, failure reason, and fallback set; it contains no embedded success marker.
- `owner-approval/v1`: exact plan/scope/registry/manifest/topology/schema-set/target/operation binding, actor, authority role, issuance, expiry, and replay identity.
- `boot-success-mark/v1`: separate authenticated success statement bound to the verified boot-health core, board, manifest, slot, generation, lineage, counter, source generation, required-check policy, and rollback set.
- `dtb-mutation-envelope/v1`: schema set, complete board/source identity, manifest, pre/post DTB digests, exact policy/tool/artifact locks, ordered authorized mutations, firmware bundle/schema, signer, expiry, and replay identity.

Authority and CI roles resolve only through the closed `AuthorityRoleBinding` inside `Trusted<TrustContext>` supplied by F-03; no consumer-local `owners.v1` or shadow role table may grant authority. Only `omarchy-apple-platform` publishes these schemas. Consumer repositories generate language-native bindings or validators from the canonical schemas rather than copying field lists.

## 7. Platform implementation domains

### Boot and early hardware

- SoC discovery and board identity.
- CPU start-up and topology.
- AIC interrupt controllers and timers.
- DART/IOMMU and memory mappings.
- UART, watchdog, GPIO, I2C, SPI, SPMI, PMU, and SMC.
- PCIe, NVMe, USB-PD, USB controllers, and boot storage.
- m1n1/U-Boot/DT/kernel version coupling and early diagnostics.

### Display and graphics

- DCP, internal panel, backlight, eDP/HDMI paths, DisplayPort Alt Mode, Thunderbolt displays, hotplug, multi-display, HDR, VRR, and local dimming.
- AGX GPU initialization, firmware interfaces, kernel DRM, Mesa OpenGL/Vulkan, compute exposure, memory pressure, reset/recovery, and Hyprland/Quickshell behavior.

### Media, camera, and audio

- Hardware video decode/encode, AV1 and ProRes where present.
- Apple ISP/camera firmware and V4L2/PipeWire integration.
- MCA, codecs, microphones, headphone, HDMI/DP audio, DSP profiles, safe volume models, and speakersafetyd fail-closed behavior.

### Connectivity and peripherals

- Board-specific Wi-Fi/Bluetooth firmware, NVRAM/CLM/regulatory data, N1-generation support, coexistence, roaming, and suspend behavior.
- USB/Thunderbolt docks, Ethernet variants, SD readers, keyboards, trackpads, Touch Bar, ambient sensors, and external devices.

### Power and security

- cpufreq, cpuidle, suspend, wake, charging, battery, thermal zones, fans, performance states, and power regression budgets.
- SEP, Touch ID, LocalPolicy, secure boot evolution, key handling, authentication recovery, and threat modeling.
- Neural Engine enablement and isolation where supported.

## 8. Release and supply-chain model

- Every source input is pinned by commit and fetched from an allowlisted repository.
- Every fork records its exact upstream repository, base commit, ordered downstream commits, attribution, contribution provenance, and upstream disposition. A branch name or repository owner is not provenance.
- Every build runs in a declared isolated builder with recorded toolchain/container digests.
- Reproducible artifacts are compared across independent builders for high-trust components.
- Packages, images, manifests, and boot bundles require project signatures. `Optional TrustAll` is forbidden in release channels.
- SBOMs, source provenance, build attestations, artifact hashes, per-file/component license inventory, third-party notices, corresponding-source offers, vulnerability results, and secret scans accompany every candidate.
- The release evidence maps each shipped binary, firmware blob, font, theme, artwork asset, package, and bundled source to its version, digest, origin, applicable license/notices, redistribution decision, source-offer location where required, and build or acquisition recipe.
- Apple firmware is fetched directly from authoritative Apple endpoints by default and is not mirrored or redistributed until an owner-approved legal and release-policy record authorizes the exact artifact class. Per-firmware redistributability is explicit; a permissive project license does not automatically cover bundled vendor firmware.
- The opaque human-produced boot artifact boundary must arrive with a human-signed artifact identity, license/notice inventory, provenance, redistribution decision, source-offer statement where applicable, and interface attestation. Automated consumers validate that envelope without inspecting the fenced source repository.
- Edge, RC, and stable are distinct immutable release namespaces. Promotion copies an already-built digest; it never rebuilds from a moving branch.
- Revocation, key rotation, mirror compromise, expired metadata, and offline recovery are tested procedures.
- Root, targets, snapshot, timestamp, artifact, package-index, and emergency/recovery signing roles have separated online/offline custody, thresholds, expiry, rollback/freeze protection, rotation, revocation, and incident exercises. One long-lived online key may not authorize every layer.
- The complete boot/kernel/firmware/Mesa/userspace tuple remains available for rollback for the full support lifetime of a board.

## 9. Physical hardware lab and evidence

Representative boards may accelerate bring-up, but the final no-exception claim requires physical certification of every supported board/product topology.

The lab must provide:

- A catalog of each device, board ID, SoC and bin, RAM/storage/GPU configuration class, firmware/macOS baselines, battery health, port map, peripherals, location, calibration state, and recovery status. Final promotion requires two independently serialized units for every materially distinct board/profile; laptop/desktop, port-count, display, die/bin, and materially different RAM/storage/GPU profiles do not substitute for one another.
- A separate DFU/recovery Mac with the correct direct cables and capture, controlled AC power, wattmeter and USB-PD analyzer, USB/UART capture where available, HDMI/DisplayPort capture, managed USB/TB devices, network endpoints, Bluetooth peripherals, storage/docks, audio loopback and calibrated SPL measurement, thermal chamber/controlled ambient and sensors, camera targets, and mechanical/input fixtures.
- Automated clean-install, encryption, first-boot, update, rollback, uninstall, cold-boot loop, suspend-cycle, thermal soak, battery/idle-drain, external-display, port, wireless, audio-safety, camera, media, and recovery scenarios.
- The initial minimum per exact profile is three clean installs per unit, encrypted and unencrypted paths where applicable, 50 cold/warm boot cycles for laptop profiles, five attach/detach cycles for every applicable port/device class, and ten complete update/rollback cycles. Any higher subsystem safety standard overrides these floors.
- Automated evidence covers exact artifacts/configuration, command outcomes, logs, power and thermal measurements, reset/fault injection, repeatability, and immutable hashes. Human-observed evidence separately covers visual artifacts, panel quality, speaker distortion, microphone intelligibility, input feel and fit, thermal comfort, fan character, vibration, RF behavior, physical DFU sequencing, destructive consent, and fixture correctness.
- Raw logs and measurements retained by immutable evidence ID, with redaction and privacy rules.
- Each record carries the board/profile ID, unit pseudonym, manifest and source/artifact digests, macOS/firmware baseline, fixture/calibration IDs, operator, timestamps, exact steps, expected/actual results, raw evidence hashes, failures, reruns, and residuals. Raw material is encrypted and access-controlled; public exports redact serials, personal accounts, usernames, home paths, SSIDs/BSSIDs, MAC/IP addresses, filesystem UUIDs, notifications, secrets, tokens, and customer data.
- Before execution, every quantitative capability row has an approved unit, procedure, fixture/calibration requirement, pass/fail threshold, measurement uncertainty, repetition count, and safety stop. Every qualitative human-observed row has a bounded rubric, required capture, two independent operators, disagreement/escalation rule, and named acceptance authority. Missing criteria, calibration, operator evidence, or a failed required row blocks promotion.
- Quarantine for boards with failed stable candidates and an incident path that prevents promotion across related boards until impact is understood.

Virtual machines, mocked device trees, static repository assertions, and compilation are useful lower gates but may never produce a physical qualification record.

## 10. Factory operating model

The primary session is the coordinator and sole DONE authority. Each slice follows DESIGN NOTE -> COORDINATOR RULING -> IMPLEMENTATION -> ADVERSARIAL REVIEW -> CORRECTION -> INTEGRATION -> FULL GATES -> DONE.

One writer owns one branch/worktree. Reviewers are read-only, work from throwaway detached worktrees, default to REJECT, plant violations to prove guards bite, and rerun the gates rather than trusting reports.

Repository-local instructions override factory assignments. `m1n1-omarchy` is excluded from all AI/LLM tasks and requires human design, implementation, review, and source-level verification. Agents may design and test only the external opaque-artifact contract without reading or operating on that repository.

Every lane reports its branch tip, changed-file census, exact gate outputs, explicit failure census, deviations, and residuals. A build, passing unit test, recognized chip, or booting desktop is never reported as a support completion.

The coordinator records rulings, integrations, rejections, incidents, and corrections in the append-only progress log. Existing log entries are never rewritten to hide errors.

## 11. Verification gates

### All repositories

- Clean status and exact base/tip SHA recorded.
- Formatter and static analysis for touched languages.
- Full relevant unit/integration suite with an explicit PASS/FAIL census.
- `git diff --check` and repository-wide conflict-marker scan.
- Secret scan and generated-artifact drift check.
- License and provenance check for new dependencies or copied code.
- Cache cleanup and free-disk check after heavy builds.

### `omarchy-mac`

- `./test/all`
- `bin/omarchy commands --check`
- Parser-aware syntax validation for every `bin/omarchy-*` command.
- Graphical acceptance tests in disposable Apple-capable environments where applicable.
- Running-UI visual verification for every visual change.

### Installer

- Pure planning tests over versioned disk/APFS fixtures.
- Property tests proving unrelated containers are never selected.
- State-matrix tests for FileVault on/off, locked Data, stale Preboot, missing machine owner, non-owner administrator, wrong paired RecoveryOS/1TR, multiple internal disks, and multiple external disks.
- Restart-after-every-step transaction tests.
- Fault injection for network, power, disk-full, corrupt metadata, bad signatures, stale identities, and partial writes.
- Download interruption, cache corruption, signed offline-bundle, and pre-destructive-boundary tests proving artifact readiness before APFS or boot changes.
- Identity-based uninstall property tests proving no unrecorded APFS or block object can be selected, including hostile labels and misleading partition names.
- Accessibility tests for VoiceOver, keyboard navigation, Switch Control, Dynamic Type, high contrast, reduced motion, and color-independent meaning, followed by physical UI verification.
- Localization completeness tests for strings, errors, units, dates, boot-picker/1TR guidance, recovery, uninstall, and support export.
- Support-bundle redaction fixtures proving prohibited credentials, identifiers, paths, partition maps, and raw output never enter the default bundle.
- Destructive tests only on disposable lab machines with rehearsed DFU recovery.

### Boot, kernel, Mesa, and platform releases

- Reproducible-build comparison and artifact byte/digest checks.
- Component ABI/manifest compatibility validation.
- Upstream test suites and subsystem-specific conformance.
- Per-board boot and hardware suites.
- Cross-repository candidate assembly and last-known-good rollback exercise.
- A hostile promotion test proves every stable-channel writer routes through F-07 and rejects a missing slice, incomplete product-integration parity, missing applicable board/profile, failed physical row, stale evidence, legal-policy failure, digest substitution, rollback omission, or public-ledger mismatch.

## 12. Slice ledger

Only the coordinator changes a slice to DONE.

`HUMAN-ONLY BLOCKED` is not a completion state. It means the slice cannot enter the agent factory and remains blocked until a qualified human owner accepts it.

Design prose is not an executable contract. F-02 through F-06 remain prerequisites until canonical schemas, generated bindings, positive and hostile test vectors, trust metadata, policy checks, candidate assembly, consumer guards, and CI gates run and fail closed. Component work may prepare isolated experiments, but no artifact can enter an Omarchy release candidate through a handwritten field list or an unenforced design note.

### 12.1 Foundation slice acceptance

| Slice | Required executable artifacts | Hard rejection conditions |
|---|---|---|
| F-02 | Canonical closed schemas, locked vocabulary, strict validators, canonicalization vectors, generated Python/Swift/bounded boot bindings, accepted and hostile fixtures, drift check, and cross-document conformance suite | Unknown/duplicate field accepted, inconsistent canonical bytes, stale binding, partial object returned after rejection, digest/identity mismatch admitted, or any consumer-specific shadow schema |
| F-03 | Signed trust-root bundle, artifact-to-role matrix, public key IDs, delegation and threshold policy, online/offline custody record, verification order, expiry/freeze/rollback rules, rotation/revocation ceremony, compromise drill, and offline recovery fixture | One unrestricted online key, threshold shortfall accepted, expired/replayed metadata accepted, untrusted key treated as valid, rollback/freeze possible, or recovery impossible without network |
| F-04 | Pinned builder definitions, two-builder comparison, source closure, SBOM and provenance attestations, immutable artifact store, signed package/index metadata, channel promotion and rollback exercise | Undeclared input, mutable fetch, artifact mismatch, rebuild during promotion, incomplete SBOM/provenance, unsigned index, missing rollback artifact, or non-reproducible high-trust component |
| F-05 | Candidate assembler, generated consumer packages, exact tuple/ABI validator, hostile cross-repository fixtures, required-gate census, deterministic rejection codes, immutable manifest output, and end-to-end consumer guard tests | Handwritten field mapping, missing component/gate, incompatible tuple accepted, unqualified board targeted, hostile fixture passes, consumer bypasses manifest, or failure becomes warning-success |
| F-06 | Per-artifact license/notice/source-offer inventory, consolidated NOTICE bundle, fork/upstream provenance, firmware/asset redistribution policy records, public source-offer index, policy engine, hostile fixtures, and release compliance attestation | `unknown`, `prohibited`, missing notice/source, unresolved provenance, direct-fetch-only artifact redistributed, license conflict, or policy result absent at candidate assembly |
| F-07 | One promotion command/API that recomputes the authoritative required-slice closure, exact candidate and rollback digests, every applicable signed qualification record, release-compliance attestation, public-ledger projection, and channel target before an atomic digest copy | Any prerequisite incomplete or non-terminal, any applicable board/profile absent or failed, candidate/rollback/legal/ledger mismatch, stale or replayed evidence, warning-success, rebuild during promotion, or any alternate stable-write path |

Every condition is enforced in CI and rerun from a clean checkout. A document, branch, build log, or coordinator intent does not satisfy these rows without the named artifacts and passing tests.

| ID | Repository | Deliverable | Depends on | Status |
|---|---|---|---|---|
| F-00 | organization | Create owned organization and seven repositories | none | DONE |
| F-01 | omarchy-apple-platform | Establish canonical program, acceptance contract, decisions, and progress log | F-00 | DONE |
| F-02 | omarchy-apple-platform | Design and implement canonical schema package for board registry, platform manifest, installer plan, qualification record, and boot health | F-01 | IN PROGRESS |
| F-03 | omarchy-apple-platform | Establish signed metadata trust root, key roles, expiry, rotation, and offline recovery | F-02 | IN PROGRESS |
| F-04 | omarchy-apple-platform | Establish reproducible builder definitions, SBOM/provenance, channel promotion, and immutable artifact storage | F-02 | IN PROGRESS |
| F-05 | omarchy-apple-platform | Build candidate assembly, hostile fixtures, generated consumer bindings, and cross-repository compatibility validator | F-03, F-04, F-06, Q-00, Q-01 | IN PROGRESS |
| F-06 | omarchy-apple-platform | Implement license/notice inventory, corresponding-source offers, redistribution decisions, fork provenance, policy enforcement, and release compliance bundle | F-01 | IN PROGRESS |
| F-07 | omarchy-apple-platform | Implement the sole stable-promotion terminal that recomputes the complete required-slice, product-integration parity, candidate, qualification, legal, rollback, and public-ledger closure before copying an immutable candidate digest | F-05, P-03, P-05, I-09, B-04, Q-04, Q-05, Q-06, Q-07, Q-08 | TODO |
| P-01 | omarchy-mac | Consume generated board registry and implement fail-closed pre-mutation admission | F-02, Q-00 | IN PROGRESS |
| P-02 | omarchy-mac | Replace warning-success behavior with typed required/optional capability outcomes | P-01 | IN PROGRESS |
| P-03 | omarchy-mac | Complete command/application ARM parity census and tracked porting queue | F-01 | IN PROGRESS |
| P-04 | omarchy-mac | Implement platform diagnostics and support-bundle export with privacy redaction | F-02 | IN PROGRESS |
| P-05 | omarchy-mac | Integrate atomic platform update/rollback UX and remove independent version selection | F-05 | TODO |
| P-06 | omarchy-mac | Remove legacy ext4/Btrfs/LUKS conversion commands and packages from the clean-install dependency graph and prove the installer cannot invoke them | P-02 | IN PROGRESS |
| P-07 | omarchy-mac | Retire legacy in-place conversion or implement it as a separately approved journaled migration with preserved recovery root and crash-safe boot commit | P-05, P-06 | TODO |
| I-01 | omarchy-mac-installer | Threat model and design the typed installer transaction/state machine, destructive boundary, and restart semantics | F-01 | IN PROGRESS |
| I-02 | omarchy-mac-installer | Build a signed/notarized native app and equivalent CLI with pinned immutable metadata and resumable pre-mutation artifact acquisition | I-01, F-03, F-06 | TODO |
| I-03 | omarchy-mac-installer | Implement pure read-only board/disk/APFS inventory, fail-closed admission, stable target identities, exact plan generation, and final consent | F-02, Q-00, I-01, I-07 | IN PROGRESS |
| I-04 | omarchy-mac-installer | Implement versioned journaled Apple platform provisioning, idempotent resume, and safe macOS return | I-02, I-03, I-07 | TODO |
| I-05 | omarchy-mac-installer | Build the Omarchy ARM live/install image handoff with identity and artifact revalidation | F-04, F-05, I-04 | TODO |
| I-06 | omarchy-mac-installer | Implement exact-identity uninstall, rollback, recovery image, and DFU escalation runbook | I-04, I-05 | TODO |
| I-07 | omarchy-mac-installer | Implement distinct FileVault, Data-lock, administrator, machine-owner, Linux-encryption, paired-RecoveryOS, and 1TR states with Apple-owned credential handling | I-01 | IN PROGRESS |
| I-08 | omarchy-mac-installer | Implement accessible and localized native UX, persisted reboot/Recovery guidance, progress, privacy consent, and redacted support export | I-01, I-07, P-04 | TODO |
| I-09 | omarchy-mac-installer | Pass pure-planner, restart, fault-injection, disk-selection, uninstall, privacy, accessibility, localization, clean-path dependency, and disposable-hardware acceptance suites | Q-00, I-02, I-03, I-04, I-05, I-06, I-07, I-08, P-06, P-07 | TODO |
| B-01 | m1n1-omarchy | Human owner defines reproducible build, artifact, firmware-schema, and debug contracts | F-02, F-04, human m1n1 owner | HUMAN-ONLY BLOCKED |
| B-02 | m1n1-omarchy | Human owner packages qualified M1/M2 stage-1 and stage-2 bundles | B-01, human m1n1 owner | HUMAN-ONLY BLOCKED |
| B-03 | u-boot-omarchy | Define reproducible Apple U-Boot and UEFI/slot contracts | F-02, F-04, F-06 | TODO |
| B-04 | u-boot-omarchy | Implement versioned boot-slot selection, success marking, and fallback | B-03 | TODO |
| K-01 | linux-omarchy | Define downstream kernel/DT configuration, patch-queue, ABI, and build contracts | F-02, F-04, F-06 | TODO |
| K-02 | linux-omarchy | Produce a qualified M1/M2 reference kernel/DT package set | K-01 | TODO |
| K-03 | linux-omarchy | M3 base/Pro/Max/Ultra subsystem bring-up and board qualification | K-02 | TODO |
| K-04 | linux-omarchy | M4 base/Pro/Max subsystem bring-up and board qualification | K-03 | TODO |
| K-05 | linux-omarchy | A18 Pro and M5 family subsystem bring-up and board qualification | K-04 | TODO |
| K-06 | linux-omarchy | M6 intake and subsystem bring-up | shipping hardware, K-05 | TODO |
| B-05 | m1n1-omarchy | Human owner packages qualified M3 stage-1 and stage-2 bundles | B-01, K-03, human m1n1 owner | HUMAN-ONLY BLOCKED |
| B-06 | m1n1-omarchy | Human owner packages qualified M4 stage-1 and stage-2 bundles | B-01, K-04, human m1n1 owner | HUMAN-ONLY BLOCKED |
| B-07 | m1n1-omarchy | Human owner packages qualified A18 Pro and M5-family stage-1 and stage-2 bundles | B-01, K-05, human m1n1 owner | HUMAN-ONLY BLOCKED |
| B-08 | m1n1-omarchy | Human owner packages qualified M6 stage-1 and stage-2 bundles | shipping hardware, B-01, K-06, human m1n1 owner | HUMAN-ONLY BLOCKED |
| G-01 | mesa-omarchy | Establish authoritative mirror sync, downstream patch queue, reproducible build, and conformance contract | F-02, F-04, F-06 | TODO |
| G-02 | mesa-omarchy | Qualify M1/M2 graphics reference tuple | G-01, K-02 | TODO |
| G-03 | mesa-omarchy | Implement and qualify M3 graphics/display dependencies | G-02, K-03 | TODO |
| G-04 | mesa-omarchy | Implement and qualify M4 graphics/display dependencies | G-03, K-04 | TODO |
| G-05 | mesa-omarchy | Implement and qualify A18/M5/M6 graphics dependencies | G-04, K-05 | TODO |
| Q-00 | omarchy-apple-platform | Produce a cited, immutable, digest-addressed Apple Silicon intake dataset and contradiction ledger from authoritative sources | F-02 | IN PROGRESS |
| Q-01 | omarchy-apple-platform | Define board inventory, capability criteria, and qualification-record schema | F-02, Q-00 | IN PROGRESS |
| Q-02 | omarchy-apple-platform | Build lab controller, evidence ingestion, redaction, and public ledger generation | Q-01 | TODO |
| Q-03 | hardware lab | Acquire, inventory, fixture, and recovery-certify two independent units of every materially distinct Apple Silicon board/profile | Q-00, Q-01 | TODO |
| Q-04 | hardware lab | Certify M1/M2 reference and every M1/M2 board | B-02, B-04, K-02, G-02, I-09, Q-02, Q-03 | TODO |
| Q-05 | hardware lab | Certify M3 boards | B-04, B-05, K-03, G-03, I-09, Q-02, Q-03 | TODO |
| Q-06 | hardware lab | Certify M4 boards | B-04, B-06, K-04, G-04, I-09, Q-02, Q-03 | TODO |
| Q-07 | hardware lab | Certify A18 Pro and M5 boards | B-04, B-07, K-05, G-05, I-09, Q-02, Q-03 | TODO |
| Q-08 | hardware lab | Certify M6 boards | B-04, B-08, K-06, G-05, I-09, Q-02, Q-03 | TODO |

## 13. Milestones and promotion gates

### Milestone A — governed foundation

- Canonical schemas approved and implemented.
- Unknown identities fail closed.
- Signed metadata root and immutable release channels exist.
- Every repository has explicit ownership, design, gates, and upstream-sync policy.
- No hardware-support expansion is claimed.

### Milestone B — clean M1/M2 reference installation

- One signed installer starts in macOS and reaches a qualified Omarchy desktop without an intermediary distro login.
- Install, encrypted boot, update, automatic rollback, uninstall, and DFU recovery pass on reference boards.
- All artifacts originate from the Omarchy release pipeline and one manifest.

### Milestone C — M1/M2 full-board qualification

- Every M1/M2 board completes the full applicable capability matrix.
- Remaining platform gaps such as Thunderbolt, DisplayPort, SEP/Touch ID, ANE, and hardware encoding are either implemented or the board is not labeled FULL.

### Milestone D — M3 qualification

- Base, Pro, Max, and Ultra SoCs and every M3 board complete the same gate without weakening criteria.

### Milestone E — M4 qualification

- M4, M4 Pro, and M4 Max move from ground-up bring-up through the same installer and qualification contract.

### Milestone F — A18/M5 qualification and continuous intake

- MacBook Neo A18 Pro and M5 family boards qualify.
- New-board intake, acquisition, bring-up, evidence, and release promotion operate as a standing program.

### Milestone G — M6 qualification

- Shipping M6 hardware is acquired and qualifies through unchanged safety and evidence gates.

### Milestone H — complete-program stable promotion

- F-07 recomputes the full graph and promotes the already-built immutable candidate digest only after P-03 product-integration parity, Q-04 through Q-08, the corresponding human-produced opaque boot bundles, installer acceptance, rollback, release compliance, and public-ledger projection all pass.
- Independent adversarial review proves there is no second stable-channel writer and plants one failure from every prerequisite class to demonstrate that the terminal gate bites.

No milestone has a calendar promise until its prerequisite discovery and physical-hardware gates have produced evidence. Literal all-board/full-feature support is expected to be a multi-year platform program.

## 14. Staffing model

A credible standing team includes dedicated owners for installer/APFS/Recovery, m1n1/boot firmware, kernel core/SoC, display/GPU, connectivity/peripherals, audio/media/camera, power/security, release/supply chain, product integration, and physical QA/lab automation.

Luna agents accelerate repository research, design, test construction, packaging, documentation, safe mechanical work, and review. Reverse engineering and physical qualification still require evidence from real hardware and coordinator-controlled promotion.

## 15. Risk register

| Risk | Required control |
|---|---|
| An architecture check is mistaken for hardware support | Board registry plus physical qualification record required for promotion |
| Installer damages macOS/APFS | Read-only plan, stable identifiers, Apple tools, property tests, journal, disposable-machine fault injection, DFU rehearsal |
| Installer mutates during inspection or before complete consent | Pure inventory/admission/planning seams, pre-mutation artifact verification, explicit destructive boundary, and tests rejecting pre-consent `updatePreboot` or storage changes |
| Credential states are conflated or secrets leak | Typed FileVault/owner/Recovery/Linux-encryption states, Apple-owned authorization UI, prohibited-secret fixtures, and redacted support exports |
| Uninstall selects unrelated user data | Journal-recorded object identities, read-only deletion preview, immediate revalidation, explicit authorization, and property tests forbidding label/pattern selection |
| Installer excludes users or strands them at Recovery | Native accessible UI, equivalent CLI, complete localization, persisted handoff checkpoints, safe macOS return, and DFU escalation rehearsal |
| Cross-component update produces an unbootable tuple | Single signed platform manifest, inactive slots, boot-success marker, automatic fallback |
| Upstream changes outrun downstream patches | Pinned sources, automated sync reports, owned patch queues, reproducible builds, explicit requalification |
| Package or mirror compromise | Mandatory signatures, threshold/offline roles, expiry, provenance, SBOMs, revocation and rotation drills |
| A license or redistribution gap blocks a release after engineering completes | Machine-enforced per-artifact license/notice/source-offer inventory, human decisions for uncertain firmware and opaque inputs, and F-06 before candidate assembly |
| Design-only interfaces drift across repositories | Canonical executable schemas, generated bindings, conformance vectors, hostile fixtures, consumer fail-closed tests, and F-05 assembly validation |
| Speakers or thermals are unsafe | Fail-closed board profiles, physical measurements, soak tests, no generic fallback |
| New chips are marketed as supported before evidence | Dated intake versus support states; only qualification ledger drives public support |
| Agent output overclaims completion | Coordinator-only DONE, empirical reviewer probes, explicit fail census, public residuals |
| Large repositories exhaust developer storage | Partial clones, dedicated build storage, cache budgets, automated cleanup and free-space gates |
| Permanent downstream divergence becomes unmaintainable | Minimal patch queues, continuous upstreaming, documented rebases, compatibility manifests |
| An agent violates a repository-local AI prohibition | Global stop fence, human-only slice state, no source inspection, opaque signed-artifact boundary, and coordinator audit |

## 16. Owner checkpoints

The project owner must decide or approve:

- Public product name, trademarks, visual identity, and domain.
- Signing identities, key custody, release authority membership, and incident contacts.
- Hardware acquisition budget and physical lab location.
- Apple firmware acquisition/redistribution policy, public corresponding-source hosting, trademark/branding clearance, and accountable release-compliance owner.
- Privacy policy text and any future proposal to change the coordinator-set telemetry-off default.
- Stable-release publication and any support-level claim.
- Actions with irreversible external impact, including production deployment, destructive lab tests outside disposable targets, and public announcements.
- Appointment of qualified human m1n1 maintainers and reviewers who accept that repository's local contribution rules.
- Whether to grant a one-time exception to the three-round correction limit for F-02; without an explicit exception, rejected tip `c315c7e79928d0041deb582bed79a61074361b21` remains frozen and cannot be treated as a settled downstream authority.

Technical details within the approved architecture are coordinator rulings unless they change these owner boundaries.

## 17. Program acceptance criteria

The program mission is complete only when:

1. A signed clean installer can start from supported macOS on every released Apple Silicon Mac board in scope.
2. The installer safely provisions, installs, encrypts, boots, updates, rolls back, uninstalls, and recovers on every board.
3. Every applicable hardware capability in Section 3 passes on physical hardware with immutable evidence.
4. Every installed artifact is reproducibly built, signed, traceable to pinned source, and selected by one qualified platform manifest.
5. Unknown or unsupported machines fail before privileged mutation and receive an honest diagnostic.
6. Stable promotion is structurally impossible outside the single F-07 terminal, and that terminal recomputes product-integration parity, complete board/profile qualification records, human-produced opaque boot-bundle evidence, installer acceptance, component/candidate compatibility, release compliance, rollback retention, and the public support ledger before copying an immutable candidate digest.
7. The public support ledger names exact boards, firmware baselines, release manifests, evidence, and residuals without implying broader compatibility.
8. An adversarial assembled-system review finds no untracked feature gap, unsafe fallback, false success, unsupported destructive path, or rollback hole.

## 18. Decision log

| Date | Decision | Reason |
|---|---|---|
| 2026-09-02 | Use `omarchy-silicon` as the owned GitHub organization | Matches the all-generation mission and avoids collision with the existing `omarchy-mac` organization |
| 2026-09-02 | Keep `omarchy-mac` as the product/control plane and split installer/platform/component ownership across repositories | Hardware enablement and clean installation require distinct release cadences and source histories |
| 2026-09-02 | Treat support as a board-level physical claim | SoC identity does not cover model-specific display, audio, wireless, port, power, camera, and thermal behavior |
| 2026-09-02 | Fork and carry required patches while continuously upstreaming | Omarchy owns release timing without abandoning shared open-source maintenance |
| 2026-09-02 | Build a clean native installer without an intermediary distro login | The user experience and recovery responsibility must be one Omarchy-owned transaction |
| 2026-09-02 | Require FULL to include all applicable hardware features | “No exception” cannot be represented honestly by a daily-driver subset |
| 2026-09-02 | Use CNVS Luna workers under coordinator review and SWE/QA/reviewer separation | The program is too broad and safety-critical for ungoverned single-agent changes |
| 2026-09-02 | Make m1n1 a human-only workstream and treat its outputs as opaque signed inputs to the agent-operated platform boundary | The repository's local instructions prohibit AI/LLM use and override the factory assignment |
| 2026-09-02 | Treat the clean-installer UX audit as release-blocking and adopt its state, accessibility, localization, privacy, and recovery gates | A terminal-driven multi-stage flow with pre-consent mutation, ambiguous disk selection, conflated credentials, or pattern-based deletion cannot satisfy the clean-installer or data-safety promise |
| 2026-09-02 | Define inventory, admission, acquisition, and plan generation as pure with respect to system/APFS/boot state; `updatePreboot` belongs after final consent | A supposedly read-only phase must not alter the machine or make recovery harder before the user accepts the complete mutation plan |
| 2026-09-02 | Make telemetry off by default and require separate inspectable consent for optional metrics and sensitive support data | Downloads must not silently become analytics consent, and installation cannot depend on telemetry |
| 2026-09-02 | Forbid pattern-based uninstall and require journal-recorded stable object identities | Names and disk ordering are ambiguous; deletion authority must be narrower than discovery authority |
| 2026-09-02 | Treat the worker-reported 59-row silicon research result as provisional and fail closed, not as a support or installer-admission list | The report is not locally auditable until Q-00 preserves the cited row-level dataset and digest; reported selector gaps and contradictions therefore remain UNKNOWN rather than canonical facts |
| 2026-09-02 | Exclude in-place ext4-to-Btrfs conversion and LUKS re-encryption from the clean-install path | Power loss can occur after irreversible storage work but before boot configuration and recovery state are durable; a clean install can create the final layout directly |
| 2026-09-02 | Require executable canonical contracts before cross-repository release integration | Frozen names in prose do not provide schemas, generated bindings, hostile fixtures, trust enforcement, or consumer guards |
| 2026-09-02 | Make license, notice, source-offer, redistribution, and fork provenance an enforced release artifact | A build can be technically reproducible while remaining legally undistributable or unable to satisfy downstream source obligations |
| 2026-09-02 | Require two independent physical units for each materially distinct board/profile and separate automated from human-observed evidence | A single unit or simulated result cannot expose unit variance, physical interaction failures, acoustic/visual defects, or recovery-operator errors |
| 2026-09-02 | Make F-07 the only stable-promotion authority and add explicit human boot-bundle slices for every hardware cohort | Acyclic component and qualification work is insufficient if a release writer can bypass intake, later-board opaque boot inputs, physical evidence, legal policy, rollback, or the public ledger |
| 2026-09-02 | Make P-03 product-integration parity a direct F-07 prerequisite | A stable release cannot be complete while the command/application ARM parity census and tracked porting queue remain outside the promotion terminal's transitive closure |
| 2026-09-02 | Route every agent-produced change through a repository pull request and keep rejected or unreviewed lanes in draft | Git-level mergeability is not design acceptance, implementation proof, qualification, or release readiness; each PR must carry its dependency and gate state before integration |
| 2026-09-02 | Freeze F-02 after its third rejected correction round pending an explicit owner exception | The repository workflow limits SWE-to-QA correction loops to three rounds; downstream contracts must not implement against known phase contradictions or silently start an unauthorized fourth loop |
| 2026-09-02 | Freeze the U-Boot B-03 design PR after its final bounded round-3 REJECT at head `81482543fee62b12ed2b30bfbca80850abb1b736`; a fourth design-correction round requires explicit owner exception | Repository AGENTS workflow caps SWE-to-QA rounds at three; structural/design progress cannot override unresolved contract defects, failing gates, absent implementation, or release evidence |
| 2026-09-02 | Freeze the F-06 release-compliance design PR after its final bounded round-3 REJECT at head `d9251a5938ce30ab39f72f75a687764eb7d3b7c1`; a fourth design-correction round requires explicit owner exception | Repository AGENTS workflow caps SWE-to-QA rounds at three; structural/design progress cannot override unresolved contract defects, failing gates, absent implementation, or release evidence |
| 2026-09-02 | Freeze the omarchy-mac Product integration/P-03 design PR after its final bounded round-3 REJECT at head `2192e3c49517e016ec44eb3f55265afae6d7f063`; a fourth design-correction round requires explicit owner exception | Repository AGENTS workflow caps SWE-to-QA rounds at three; structural/design progress cannot override unresolved contract defects, failing gates, absent implementation, or release evidence |
| 2026-09-02 | Freeze the program-integrity CI design PR #4 after its final bounded round-3 REJECT at head `410cc50ff85fcc4b01ef8c6ff699ae6a5836dc22`; any fourth design-correction round requires an explicit owner exception under the three-round workflow | This freeze applies only to that rejected design PR and does not freeze independent authorized preparation; no owner approval is claimed |
| 2026-09-03 | Coordinator accepted F-01 based on fresh independent review report `/Users/simonbourdon/Dropbox/GitHub/Omarchy-mac/.cnvs/reports/f01-closure-review-a5ebdc2-r1.md` with SHA-256 `f4092760533d11e94626543fa53f10fe132b7388badcea635a19d173bbb182eb` and canonical main/base SHA `a5ebdc29e395e94baf594130e8e048d31e4615f8` | This closes only F-01 documentation/governance scope; Program-integrity CI PR #4 remains rejected/frozen; no frozen design exception is granted; no other slice, implementation, compatibility, qualification, support, promotion, or release is completed |
| 2026-09-03 | Begin F-02 as bounded executable implementation increments rather than further dossier churn | The owner directed the coordinator to act and implement; each increment must remain fail closed, independently tested, and honest about residuals, while the rejected design tip remains non-authoritative and the opaque human-produced boot boundary remains untouched |

## 19. Append-only progress log

Do not edit or delete existing rows. Corrections are new rows.

| Timestamp | Event | Evidence or result |
|---|---|---|
| 2026-09-02 | Organization and repositories created | `omarchy-silicon` contains `omarchy-mac`, `omarchy-mac-installer`, `omarchy-apple-platform`, `linux-omarchy`, `m1n1-omarchy`, `u-boot-omarchy`, and `mesa-omarchy` |
| 2026-09-02 | Repository ancestry verified | GitHub-native forks retain their parents; Mesa main history mirrors freedesktop.org at the verified upstream SHA from creation time |
| 2026-09-02 | Coordinator established the canonical program plan | This document defines the mission, ownership, interfaces, safety invariants, acceptance criteria, slice ledger, decisions, and factory rules |
| 2026-09-02 | m1n1 Luna design lane stopped before edits | Worker reported the repository-local AI/LLM prohibition; no design, code, checks, commit, or push occurred, and the coordinator broadcast a supersession fence to all active agents |
| 2026-09-02 | Clean-installer UX audit rejected the current baseline | CNVS task `F3B211F9-6AB1-4E02-A610-DFD84B883A8B` found pre-consent mutation, ambiguous storage identity, credential-state conflation, no durable transaction journal, incomplete download/recovery UX, inaccessible and unlocalized terminal stages, unsafe pattern-based removal, and under-specified privacy; the coordinator converted every class into blocking contracts and slices I-01 through I-09 |
| 2026-09-02 | Installer transaction design published for review | `omarchy-mac-installer` branch `factory/design-installer-transaction` commit `1042ef04d65a7a59c46c7ea8b4d2a7c0db61869e` adds a design-only transaction document; no implementation or installer slice is DONE |
| 2026-09-02 | U-Boot release/slot design published for review | `u-boot-omarchy` branch `factory/design-uboot-slots` commit `e385874ca1987248b40aa150f10d3d3ad32fde02` adds a design-only document; its documentation build was blocked by the host GNU Make 3.81, and B-03/B-04 remain open |
| 2026-09-02 | Mesa downstream design published for review | `mesa-omarchy` branch `factory/design-mesa-release` commit `6221cee01fecb4f452bd56d4cb6ebc8db1391724` adds a design-only document above verified mirror base `d870cef8b7c8a4a11edc669669c9f18ae402314a`; implementation, conformance, and qualification remain open |
| 2026-09-02 | Kernel/DT bring-up design published for review | `linux-omarchy` branch `factory/design-linux-bringup` commit `e774b67114bdcb7e6d204b403f2ba380a5c51677` adds a design-only document above base `77cb8f24c2381a8abb7272d7bbdec548d6426a8a`; RST parsing passed, full docs build was blocked by host GNU Make 3.81, unrelated lane edits remain untouched, and K-01 through K-06 remain open |
| 2026-09-02 | Installer safety audit rejected the current product path | CNVS task `7ECBAEFD-CC63-4D33-A6DB-64DAC97F282E` found mutable unsigned root inputs, ambiguous/stale disk and ESP authority, missing APFS/RecoveryOS/LocalPolicy transaction states, and crash-unsafe legacy storage conversion; the coordinator added hard gates and P-06 |
| 2026-09-02 | Silicon intake audit rejected admission completeness | CNVS task `5E649A10-4465-45DC-9D31-9164E554ECC8` produced 47 M1-M4 and 12 A18/M5/M6 research rows but found selector gaps, contradictions, absent newer support matrices, and no physical Omarchy evidence; every row remains unqualified pending canonical import and review |
| 2026-09-02 | Licensing and upstream-compliance audit rejected release readiness | CNVS task `E42B4646-FCB8-4622-BD64-1C5729BADC89` found missing consolidated notices, SBOM/license closure, source offers, exact fork provenance, firmware redistribution decisions, and policy enforcement; F-06 now blocks candidate assembly |
| 2026-09-02 | Supply-chain audit rejected release readiness | CNVS task `52DCF525-FA95-4809-B165-5F63E1ADF865` found trust-root, signing-role, expiry, revocation, provenance, mirror, and offline-recovery controls are not yet executable; F-03 through F-05 remain blocking work |
| 2026-09-02 | Cross-repository interface audit rejected paper-only contracts | CNVS task `D4D2AC8D-7D8D-446E-9627-03A6A4F33BC0` found no implemented canonical schemas, trust root, assembly validator, or executable consumer guards; design documents cannot advance those foundation slices to DONE |
| 2026-09-02 | Physical fleet audit rejected qualification readiness | CNVS task `EF1DE608-FD7F-427E-83F1-50A633D7F523` found no physical hardware-in-loop evidence and incomplete board/peripheral coverage; the coordinator established fleet, fixture, numeric-cycle, evidence, and redaction minimums while keeping Q-03 through Q-08 open |
| 2026-09-02 | Canonical schema design published for review | `omarchy-apple-platform` branch `factory/design-platform-schema` commit `64970b3bbef7f30b492bedff3ba2615c2d4d1d25` adds the F-02 design note and passes its post-push documentation gates; no schema, validator, binding, fixture, trust root, or admission implementation exists yet |
| 2026-09-02 | Whole-program adversarial review rejected release readiness | CNVS task `AC5B6269-B98A-4FCE-BE55-733FD40F3342` confirmed that release authority, executable implementations, physical evidence, dependency closure, and acceptance gates remain absent; the honest public state remains design program with no new FULL support claim |
| 2026-09-02 | Corrected the central release graph after adversarial rejection | Q-00 now blocks board admission and installer acceptance; F-05 consumes canonical intake and qualification schema; I-05 consumes candidate assembly; I-09 consumes the retired-or-journaled legacy path; B-05 through B-08 require human-produced opaque boot bundles for M3 through M6; Q-05 through Q-08 require those bundles and B-04; F-07 is the sole stable-promotion terminal across all physical cohorts |
| 2026-09-02 | Second F-02 and K-01 reviews rejected their corrected design tips | CNVS tasks `7A652089-ECD7-441E-8D4E-E035859C4E6F` and `71F8B4E9-B9CE-4586-9626-5D8987C29C7B` found cross-contract manifest, provenance, authority, identity, firmware-envelope, AGX-census, and boot-health blockers; neither slice is DONE |
| 2026-09-02 | F-02 and K-01 correction round restarted after a headless launcher failure | CNVS tasks `1BF54709-38C9-4D17-B9C9-B5237B7C380B` and `E63C8FBD-F52B-4B6B-8B84-0527EA38EF55` run as isolated normal-terminal writers with exact branch, file, remote-tip, and dirty-state verification gates |
| 2026-09-02 | F-06 release-compliance design started | CNVS task `935604DA-1E6A-4C23-9BAE-A6B43FCF5B13` owns only `docs/design/release-compliance.md` in an isolated worktree; implementation, legal clearance, candidate admission, and DONE remain open |
| 2026-09-02 | PROGRAM review rejected incomplete promotion closure | CNVS task `C9840160-1BE2-405F-B9B6-68D49615A2C3` recomputed 52 nodes and exercised 27 hostile probes; structural guards rejected their planted violations, but F-07 reached only 51 nodes because P-03 was omitted, so the coordinator added P-03 as a direct prerequisite and kept release readiness REJECTED |
| 2026-09-02 | PROGRAM plan-integrity correction independently accepted | CNVS task `77526400-3505-4191-AE5C-A1CC54C0BCCA` verified the corrected F-07 closure reaches all 52 slices, planted graph violations fail closed, the append-only history remains intact, and release readiness remains REJECTED because executable implementation and physical proof are still absent |
| 2026-09-02 | Final bounded F-02 correction published and independently rejected | Branch `factory/design-platform-schema` tip `c315c7e79928d0041deb582bed79a61074361b21` is pushed and clean; CNVS tasks `CE4193DC-E633-465D-AB2D-CB623A00F473` and `672A1685-811A-4E46-8820-1E3A60362C96` verified the bounded change and then found contradictory phase assignments in accepted/error catalog rows plus absent executable schemas, bindings, validators, hostile fixtures, and CI; the three-round loop is exhausted, F-02 remains TODO, and downstream correction is held pending the owner checkpoint |
| 2026-09-02 | Corrected K-01 design independently rejected | Branch `factory/design-linux-bringup` tip `016633ae6a45a6f799eff1850dc95a395c802da7` is pushed; CNVS task `00A9120D-4196-424D-91F2-2E05FCA34796` recovered nine blockers across manifest identity, component leaves, compatibility and rollback relations, authority bindings, error vocabulary, boot-health semantics, DTB binding, and executable closure while preserving 13 unrelated dirty paths; K-01 remains TODO and held on F-02 |
| 2026-09-02 | Corrected installer transaction design independently rejected | Branch `factory/design-installer-transaction` tip `cfb68278ce6e90e0ef9351b44e184d92585cd136` is pushed and clean; CNVS task `C7E35F34-EBC2-49A7-AB90-93A6AD968E36` recovered ten blockers covering reclaim state, owner-approval and trusted-seam drift, stable identities, boot context, secret leakage, fixture evidence, handoff metadata, Apple baseline locks, and absent implementation or qualification; I-01 remains TODO and held on F-02 plus owner-approved Apple locks |
| 2026-09-02 | Corrected F-06 release-compliance design independently rejected | Branch `factory/design-release-compliance` tip `7c07a46f3587ce4bae87d346ef31c32e7924275f` is pushed and clean; CNVS task `EC15FAC5-3DF3-4C42-8A9F-7C80DB68E3D3` separated 13 design blockers from 15 implementation and enforcement residual classes and observed all nine hostile runtime attempts fail because no executable validator exists; F-06 remains TODO and held on F-02 |
| 2026-09-02 | Governed pull-request stack opened across the agent-operated repositories | Eight dependency-linked draft PRs now track PROGRAM, F-02, F-06, installer, Linux/DT, product integration, U-Boot, and Mesa designs; repositories without `main` target their existing integration branches (`quattro` for Omarchy and `asahi` for Linux and U-Boot), all PRs remain unmerged, and GitHub currently reports no status checks on the stack |
| 2026-09-02 | F-02 final-review evidence recovery expanded the rejection census | CNVS task `B2CEEBB5-2612-4637-A3C9-60D953F256BB` and durable key `F02_FINAL_REVIEW_C315C7E` supersede the preceding abbreviated result with 14 design blockers, including 11 Critical and 3 High; B01 through B12 are 0 PASS / 12 FAIL, the 154-row hostile catalog contains three phase violations and two positive rows, ten implementation residual classes remain, and nine downstream reconciliation classes block K-01, installer, and F-06; both design and release-readiness verdicts remain REJECT |
| 2026-09-02 | PROGRAM reviewer rejected on its own nonexistent target typo | CNVS task `CBE728D6-0D57-461B-BE7B-97F7A15D6F11` independently passed the 52-node ledger, 52/52 F-07 closure, eight planted graph violations, status census, PR-stack, Markdown, credential, and repository-hygiene probes against live tip `443074d2a96349721cf64cd05c2c11e3d6df6386`, but changed the requested final digit to nonexistent `...6387` and rejected that reviewer-created mismatch; the attached verifier passed the actual `...6386` tip, so the verdict is not integration authority and a fresh review is required |
| 2026-09-02 | U-Boot B-03 final bounded round-3 design review evidence | Report `.cnvs/reports/uboot-review-8148254-r1.md`, SHA-256 `6e0f25815c2f777409d4681ff337d3f02444f3812cb1587f8d0fd71ae74067b2`, eight blocker classes, `DESIGN_CONTRACT REJECT`, PR #1 comment https://github.com/omarchy-silicon/u-boot-omarchy/pull/1#issuecomment-5517498313, PR remains `OPEN/DRAFT`, B-03 remains `TODO` |
| 2026-09-02 | F-06 release-compliance final bounded round-3 design review evidence | Report `.cnvs/reports/f06-review-d9251a5-r1.md`, SHA-256 `9312333fbfc8e63afe6ebb96b6045e09c71d91885826fae24f97b6abbd204b2f`, 7 design blockers / 10 implementation-CI residual classes / 6 legal-qualification residual classes / 3 tooling-block classes, `DESIGN_CONTRACT REJECT`, PR #3 comment https://github.com/omarchy-silicon/omarchy-apple-platform/pull/3#issuecomment-5517551122, PR remains `OPEN/DRAFT`, F-06 remains `TODO` |
| 2026-09-02 | Product/P-03 final bounded round-3 design review evidence | Report `.cnvs/reports/product-review-2192e3c-r1.md`, SHA-256 `4403ade794fe332f4d0fea9f6a174dae54d0e1a6a13ed8773961c58cc59a020a`, 7 design blockers, exact repository QA commands failed/did not complete, `DESIGN_CONTRACT REJECT`, PR #1 comment https://github.com/omarchy-silicon/omarchy-mac/pull/1#issuecomment-5517568759, PR remains `OPEN/DRAFT`, P-03 remains `TODO` |
| 2026-09-02 | PR #5 integration event | https://github.com/omarchy-silicon/omarchy-apple-platform/pull/5 merged to main as merge commit `9b37e86bf6b26f18e53260e84e8539abf969d831` from reviewed head `b5f167e65bc85c1f9993b70e5cce05768b9bc765`; independent report `.cnvs/reports/program-freezes-review-b5f167e-r1.md` has SHA-256 `74df01d065b3834e28d62a7ec4c59f258db12e57e4549e55eda27d449cf53e9e` and ended `DELTA_CONTRACT PASS` / `VERDICT PASS`; coordinator battery ended `FAIL_CENSUS=0`. This was governance-only integration and did not mark B-03, F-06, P-03, implementation, qualification, support, promotion, release, or any additional slice `DONE` |
| 2026-09-02 | Program-integrity CI final round-3 review | Report `.cnvs/reports/program-ci-review-410cc50-r1.md`, SHA-256 `0907f026433469fd4f5d26c6fe5035e801c8173c45d2613be2263ce6d2386f20`, head `410cc50ff85fcc4b01ef8c6ff699ae6a5836dc22`, exactly six design blocker classes: incompatible PI_OK phases; missing signer registry/threshold/revocation authority; coordinator decision binding is byte-only rather than semantic; conflicting ReplayStore schemas with missing status census/output bounds; incomplete JCS/scalar vectors; and non-normative fixture-manifest/expected-result binding. Comment https://github.com/omarchy-silicon/omarchy-apple-platform/pull/4#issuecomment-5517584605. PR #4 remains `OPEN/DRAFT`; `DESIGN_CONTRACT REJECT` and `VERDICT REJECT`; nothing `DONE` |
| 2026-09-02 | F-02 owner-checkpoint dossier | Report `.cnvs/reports/f02-owner-exception-dossier-c315c7e.md`, SHA-256 `84bacd924942392cd27d58438333bccdfeb9585285ba52fd86c80e5901b9d40f`, pinned rejected head `c315c7e79928d0041deb582bed79a61074361b21`. Record 14 design blockers (11 Critical, 3 High), B01-B12 at 0 PASS/12 FAIL, 154-row catalog with 3 phase violations and 2 positive rows, 10 implementation residual classes, 9 downstream reconciliation classes, and a 45-slice dependent closure beyond F-02. Recommendation `KEEP FREEZE` and `OWNER_DECISION_REQUIRED YES`. No owner ruling has been made, no fourth correction is authorized, and no design/implementation/merge/support/release/qualification/`DONE` claim follows |
| 2026-09-03 | PR #6 merged integration | Merge commit `a5ebdc29e395e94baf594130e8e048d31e4615f8`; reviewed head `105ccc982d0fa263dcb41351ecdc0893af8faeae`; review report SHA-256 `8c04bd9d06ec57d0c109853dcfd4d4cb378408780599b8ac5d8f9a12d4f1fae2`; merge-gate comment https://github.com/omarchy-silicon/omarchy-apple-platform/pull/6#issuecomment-5517959500; coordinator `FAIL_CENSUS=0`. Governance-only/no-status-expansion scope |
| 2026-09-03 | F-01 governance-closure transition | Fresh independent review report `/Users/simonbourdon/Dropbox/GitHub/Omarchy-mac/.cnvs/reports/f01-closure-review-a5ebdc2-r1.md`; SHA-256 `f4092760533d11e94626543fa53f10fe132b7388badcea635a19d173bbb182eb`; `F01_CONTRACT: PASS`; `VERDICT: PASS` | Transition changes only F-01; overall release readiness remains `REJECT`; documentation/governance-only/no-status-expansion scope |
| 2026-09-03 | F-02 executable foundation merged | PR #8 https://github.com/omarchy-silicon/omarchy-apple-platform/pull/8 merged reviewed head `91f7de3b002e2c444dbb1d8b8575c2837d5a8692` to main as `7a058ed221efe7e6528957cd970caef88d7ebea0`; both GitHub Actions runs passed; independent Luna QA passed 11/11 tests, 11/11 schemas, 8/8 accepted fixtures, hostile transport/schema/signature/lock probes, CLI smoke, drift, and isolated wheel build | F-02 advances from `TODO` to `IN PROGRESS`; the merged code provides strict bounded JSON transport, the closed eight-type vocabulary, Draft 2020-12 schema inputs, pinned RFC 8785 canonicalization, signed-envelope foundation validation, read-only CLI, fixtures, drift enforcement, and CI; type-specific cross-document semantics, trust verification, generated Swift/Rust bindings, consumer integration, hardware qualification, support, release, and F-02 `DONE` remain open |
| 2026-09-03 | F-02 semantic implementation merged | PR #10 https://github.com/omarchy-silicon/omarchy-apple-platform/pull/10 merged reviewed head `a40fc9fafaeb256745abe0f15931834aaf2d65e1` to main as `0ad8cd18e6080e74b1e8424734858dffdada5e48`; both GitHub Actions checks passed; 19 Python 3.12 tests, 11 executable Draft schemas, drift, structural-only CLI, hostile cross-document probes, and isolated wheel build passed | F-02 remains `IN PROGRESS`; semantic validation, exact single-target qualification binding, immutable models, nested schema closure, canonical relation digests, and fail-closed `STRUCTURAL_ONLY` output are implemented, while authenticated trust, external byte verification, generated Swift/Rust bindings, multi-record qualification, consumer integration, hardware proof, support, release, and `DONE` remain open |
| 2026-09-03 | F-06 executable compliance implementation merged | PR #11 https://github.com/omarchy-silicon/omarchy-apple-platform/pull/11 merged reviewed head `0240ca544f421d94d6e25fa8db3ec26c04784d73` to main as `17328c61fd75cc5819cd6f0b35f9e60f39f8d047`; schema and compliance GitHub Actions checks passed; the rebased full battery passed 73 tests and 66 subtests, both drift gates, deterministic generation, and an installed-wheel smoke test from outside the repository | F-06 advances from `TODO` to `IN PROGRESS`; closed policy, exact provenance authority, immutable URI/digest binding, NOTICE and source-offer generation, hostile fixtures, deterministic unsigned attestations, and fail-closed consumer denial are implemented, while F-03 trust, F-07 promotion, legal/source evidence verification, qualification, support, release, and `DONE` remain open |
| 2026-09-03 | P-03 product parity implementation merged | PR #2 https://github.com/omarchy-silicon/omarchy-mac/pull/2 merged reviewed head `151fc037690396993125aba31b9098fb6c5d1785` to `quattro` as `828bf1041e6c05734c613e6ccc03b20a29322f42`; the new Apple Silicon parity GitHub Actions check passed; the executable census reconciles 454 commands, 222 applications, 680 source records, and 676 unique blocked queue rows with exact evidence binding and atomic one-item acceptance | P-03 advances from `TODO` to `IN PROGRESS`; every item remains blocked until its item-specific ARM receipt passes, and broader legacy macOS suite/tooling residuals, physical qualification, support, release, and `DONE` remain open |
| 2026-09-03 | F-03, F-04, and Q-00 executable implementation wave prepared for integration | Reviewed heads `ad42bb24f93db9680a81677a0c050cce7d07676f`, `20d4ab041b6568aa210507660304403340a3383a`, and `c8272d75bfc46959e538e961f1c4cc8dc971eaf9` pass their bounded independent Luna QA gates; the reconciled integration tree passes 124 Python 3.12 tests plus trust, build, intake, offline, and drift gates | F-03, F-04, and Q-00 advance from `TODO` to `IN PROGRESS` when this change reaches `main`; production root provisioning, production builders and artifact acquisition, complete board intake, physical qualification, support, promotion, release, and `DONE` remain open |
| 2026-09-03 | Q-01 qualification foundation prepared for integration | status transition: Q-01 from TODO to IN PROGRESS; reviewed source head `733e5f499229827fde2376d024482f417457d37c` passed 13 focused and 139 full tests, schema and drift checks, selector hostility, explicit-time validation, and firmware freshness and validity probes | The only fixture remains J313 with outcome `UNKNOWN` and admission `NOT_QUALIFIED`; physical qualification, board support, promotion, release, and terminal completion remain open |
| 2026-09-03 | I-01 installer transaction implementation merged | status transition: I-01 from TODO to IN PROGRESS; installer PR #2 https://github.com/omarchy-silicon/omarchy-mac-installer/pull/2 merged reviewed head `a6c9714488dddc3c068c9fb37bb864ce44da65a3` to `main` as `a13d9e0d928a7c21cef7039672d7b27f08e99a2c`; its exact post-merge transaction workflow passed | The pure state machine, consent, bounded journal, checkpoint, resume, and rollback foundations are implemented; native UI, disk mutation, live installation, physical qualification, release, and terminal completion remain open |
| 2026-09-03 | I-07 credential readiness implementation merged | status transition: I-07 from TODO to IN PROGRESS; installer PR #3 https://github.com/omarchy-silicon/omarchy-mac-installer/pull/3 merged reviewed head `2fe1d9badc2a6fb4585f9419401ed0e9d18d376c` to `main` as `cfe358827bc0536f554a578c0b2af7a0fb426d61`; all five PR checks and its exact post-merge Python 3.12 and 3.13 workflow passed | Distinct credential states and single-use authority-bound readiness attestations are implemented as a pure model; Apple-owned credential acquisition, native integration, hardware evidence, release, and terminal completion remain open |
| 2026-09-03 | I-03 read-only installer planner implementation merged | status transition: I-03 from TODO to IN PROGRESS; installer PR #4 https://github.com/omarchy-silicon/omarchy-mac-installer/pull/4 merged reviewed head `5630916d179dd6829093c88b145e386f13601b45` to `main` as `ac24e0ada2dc5f89129fcbb84b0c4b3409a032b4`; all seven PR checks and both exact post-merge workflows passed | Bounded inventory parsing, parent-local geometry, stable target identities, sealed in-process candidate admission, deterministic transaction plans, and exact single-use final consent are implemented as a pure model; live discovery, native integration, disk mutation, durable cross-process authority, hardware qualification, release, and terminal completion remain open |
| 2026-09-03 | P-01 product pre-mutation admission implementation merged | status transition: P-01 from TODO to IN PROGRESS; product PR #3 https://github.com/omarchy-silicon/omarchy-mac/pull/3 merged final reviewed head `3d57ab7c8708f68ec9c8b8d79e4eafae9ed4e803` to `quattro` as `07a36461912306bcabb6980f5570237b72597edb`; the exact PR and post-merge Apple Silicon parity workflows passed | The product now consumes the exact canonical J313 projection through a closed provenance lock and blocks every aarch64 hardware mutation behind fail-closed identity admission; the current J313 record remains `NOT_ADMISSIBLE`, its parity evidence remains pending, and physical qualification, support, promotion, release, and terminal completion remain open |
| 2026-09-03 | P-02 typed capability outcome implementation merged | status transition: P-02 from TODO to IN PROGRESS; product PR #4 https://github.com/omarchy-silicon/omarchy-mac/pull/4 merged final candidate head `910875c3e28eec10332887ad485985711f50a4d9` to `quattro` as `8595346052def67d761506d325b933949fc0c472`; exact PR workflow `33738093075` and exact post-merge workflow `33738172282` passed | Closed required, optional, and not-applicable capability results, aggregate validation, required Apple audio and ARM mirror failure propagation, optional application and Node outcomes, and pre-mutation emitter health guards are implemented; item-specific ARM receipts, full route coverage, physical qualification, support, promotion, release, and terminal completion remain open |
| 2026-09-03 | P-06 legacy clean-install conversion quarantine merged | status transition: P-06 from TODO to IN PROGRESS; product PR #5 https://github.com/omarchy-silicon/omarchy-mac/pull/5 merged final candidate head `57b5e9c3dd84e932b1012a9ede1300c312b0ae9e` to `quattro` as `b2dfd5c5d8700af093176f3922a1a13a8a2a4450`; exact PR workflow `33740048050` and exact post-merge workflow `33740098871` passed | The legacy guided adapter now fails before mutation, the Apple package staging path omits the three legacy conversion entrypoints with hostile path and symlink guards, and clean-install documentation no longer advertises conversion; standalone legacy utilities remain unresolved in their separate retirement or hardening slice, while native installer integration, physical qualification, support, promotion, release, and terminal completion remain open |
| 2026-09-03 | P-04 redacted platform diagnostics foundation merged | status transition: P-04 from TODO to IN PROGRESS; product PR #6 https://github.com/omarchy-silicon/omarchy-mac/pull/6 merged final candidate head `2ef0a92e5cb562a6a856fdd12444ad1ba492894d` to `quattro` as `9a05aa1d6a0110bc301fb686fdd18dfc70222615`; exact PR workflow `33742817208` and exact post-merge workflow `33742873964` passed | The product now projects closed capability aggregates into deterministic redacted local bundles, writes optional exports atomically with mode `0600` and no overwrite, holds upload without consent or network activity, and blocks legacy raw diagnostics and upload before collection on Apple, failed, or unknown architecture identity; live collection integration, approved upload policy and delivery, physical qualification, support, promotion, release, and terminal completion remain open |
| 2026-09-03 | F-05 fail-closed candidate assembly foundation merged | status transition: F-05 from TODO to IN PROGRESS; central PR #21 https://github.com/omarchy-silicon/omarchy-apple-platform/pull/21 merged final reviewed head `22e00d3dacdcaa720176b8b9d66b52808a5f1402` to `main` as `2eb8cc8d185a22f5d1182dd5b338f54f1d06621e`; exact PR F-05 workflow `33746266364` and exact post-merge F-05 workflow `33746339901` passed, with all 14 PR checks and all eight post-merge workflows green | Closed input and output schemas, generated consumer bindings, immutable canonical manifests, tuple and ABI validation, exact required-gate census, authority and CAS binding, rollback-set validation, deterministic typed errors, and hostile fixtures are implemented; verification remains `STRUCTURAL_ONLY`, while production authority adapters, live cross-repository integration, physical qualification, stable promotion, support, release, and terminal completion remain open |
