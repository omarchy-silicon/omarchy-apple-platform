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
- Resolve the board through the signed support registry.
- Produce a human-readable and machine-readable installation plan showing every partition/container change, download size, target release, encryption choice, rollback boundary, and recovery requirement.
- Perform no disk mutation during inventory or plan generation.

#### Stage 2 — owner confirmation and Apple platform provisioning

- Obtain explicit confirmation of the final storage plan.
- Use Apple's supported APFS and Recovery mechanisms to resize space; do not implement an independent APFS writer.
- Create the per-OS stub macOS/APFS container, RecoveryOS relationship, LocalPolicy authorization, and OS-specific ESP required by Apple's platform model.
- Acquire Apple-signed machine firmware from authoritative Apple sources, validate it, extract only the required artifacts, and record its provenance.
- Install the qualified m1n1 stage-1 payload through the owner-authorized boot policy flow.
- Journal every durable mutation so restart/resume derives state from disk rather than carrying transient process state.

#### Stage 3 — Omarchy boot environment

- Boot the exact signed m1n1 stage-2, U-Boot, device-tree, GRUB, kernel, initramfs, and firmware tuple named by the installer manifest.
- Validate board identity again inside Linux and compare it to the macOS-side plan.
- Refuse installation if identities, firmware schema, artifact digests, disk targets, or expected capabilities disagree.
- Provide an accessible graphical installer with a complete CLI path for diagnostics and recovery.

#### Stage 4 — system installation

- Install the qualified Omarchy ARM package set from mandatory-signature repositories.
- Create the selected Btrfs/LUKS2 layout while keeping boot artifacts in versioned boot slots outside root snapshots.
- Configure users without shipped default passwords.
- Install board-specific firmware, audio profiles, speaker protection, wireless data, display configuration, and capability policy from the signed board record.
- Run installation acceptance checks before selecting the new boot slot.

#### Stage 5 — first boot and attestation

- Start the new slot once while preserving the last-known-good installer/recovery path.
- Run the board's required hardware smoke suite and record the exact manifest, artifact, firmware, package, and source SHAs.
- Mark the slot successful only after the required boot-health contract passes.
- Present a precise capability report. Never translate a missing required component into a warning followed by “Install complete.”

#### Stage 6 — update, rollback, uninstall, and recovery

- Update the platform as an atomic compatibility tuple rather than unrelated packages.
- Write new boot and root artifacts to inactive/versioned slots, verify them, switch once, and require a boot-success marker.
- Automatically fall back after failed boot attempts and retain a user-selectable last-known-good entry.
- Provide clean removal that deletes only the Omarchy-owned APFS container, ESP, and Linux partitions after identity verification, then returns free space through Apple's supported tooling.
- Maintain a tested DFU recovery runbook and a recovery image whose version and supported boards are explicit.

### 4.2 Installer safety invariants

- Unknown or ambiguous board, SoC, firmware, manifest, disk, or transaction state fails closed before mutation.
- Every target block device and APFS object is resolved to stable identifiers and revalidated immediately before use.
- No destructive target is accepted from an unresolved environment variable, glob, user-provided raw device path, or mutable remote response.
- Existing macOS and unrelated APFS containers are outside the mutation authority.
- Every durable step is idempotent or has an explicit recovery transition.
- Installer logs redact credentials, owner tokens, recovery secrets, device identifiers not needed for support, and encryption material.
- Network loss, power loss, process death, full disk, stale metadata, signature failure, and unsupported firmware are explicit tested states.

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

The first design wave may propose details but may not create competing authorities. The intended interfaces are:

- `board-registry/v1`: exact board and SoC identity, firmware schema, physical capabilities, lifecycle state, and required qualification profile.
- `platform-manifest/v1`: exact source commits, build recipe digests, artifact hashes, package versions, inter-component constraints, signing identities, channel, and rollback compatibility.
- `installer-plan/v1`: read-only inventory, stable disk/APFS identifiers, proposed mutations, selected board record, release manifest, and explicit owner approvals.
- `qualification-record/v1`: physical board identity, firmware/macOS baseline, manifest SHA, performed tests, raw evidence references, failures, residuals, operator, and timestamps.
- `boot-health/v1`: selected slot, attempt counter, manifest SHA, health checks, success mark, failure reason, and fallback decision.

Only `omarchy-apple-platform` publishes these schemas. Consumer repositories generate language-native bindings or validators from the canonical schemas rather than copying field lists.

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
- Every build runs in a declared isolated builder with recorded toolchain/container digests.
- Reproducible artifacts are compared across independent builders for high-trust components.
- Packages, images, manifests, and boot bundles require project signatures. `Optional TrustAll` is forbidden in release channels.
- SBOMs, source provenance, build attestations, artifact hashes, license inventory, vulnerability results, and secret scans accompany every candidate.
- Edge, RC, and stable are distinct immutable release namespaces. Promotion copies an already-built digest; it never rebuilds from a moving branch.
- Revocation, key rotation, mirror compromise, expired metadata, and offline recovery are tested procedures.
- The complete boot/kernel/firmware/Mesa/userspace tuple remains available for rollback for the full support lifetime of a board.

## 9. Physical hardware lab and evidence

Representative boards may accelerate bring-up, but the final no-exception claim requires physical certification of every supported board/product topology.

The lab must provide:

- A catalog of each device, board ID, SoC, RAM/storage configuration class, firmware/macOS baselines, peripherals, location, and recovery status.
- A separate DFU host, controlled power, USB/UART capture where available, HDMI/DisplayPort capture, managed USB/TB devices, network endpoints, Bluetooth peripherals, storage/docks, audio measurement, thermal logging, and camera targets.
- Automated clean-install, encryption, first-boot, update, rollback, uninstall, cold-boot loop, suspend-cycle, thermal soak, battery/idle-drain, external-display, port, wireless, audio-safety, camera, media, and recovery scenarios.
- Raw logs and measurements retained by immutable evidence ID, with redaction and privacy rules.
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
- Restart-after-every-step transaction tests.
- Fault injection for network, power, disk-full, corrupt metadata, bad signatures, stale identities, and partial writes.
- Destructive tests only on disposable lab machines with rehearsed DFU recovery.

### Boot, kernel, Mesa, and platform releases

- Reproducible-build comparison and artifact byte/digest checks.
- Component ABI/manifest compatibility validation.
- Upstream test suites and subsystem-specific conformance.
- Per-board boot and hardware suites.
- Cross-repository candidate assembly and last-known-good rollback exercise.

## 12. Slice ledger

Only the coordinator changes a slice to DONE.

`HUMAN-ONLY BLOCKED` is not a completion state. It means the slice cannot enter the agent factory and remains blocked until a qualified human owner accepts it.

| ID | Repository | Deliverable | Depends on | Status |
|---|---|---|---|---|
| F-00 | organization | Create owned organization and seven repositories | none | DONE |
| F-01 | omarchy-apple-platform | Establish canonical program, acceptance contract, decisions, and progress log | F-00 | IN PROGRESS |
| F-02 | omarchy-apple-platform | Design and implement canonical schema package for board registry, platform manifest, installer plan, qualification record, and boot health | F-01 | TODO |
| F-03 | omarchy-apple-platform | Establish signed metadata trust root, key roles, expiry, rotation, and offline recovery | F-02 | TODO |
| F-04 | omarchy-apple-platform | Establish reproducible builder definitions, SBOM/provenance, channel promotion, and immutable artifact storage | F-02 | TODO |
| F-05 | omarchy-apple-platform | Build candidate assembly and cross-repository compatibility validator | F-03, F-04 | TODO |
| P-01 | omarchy-mac | Consume generated board registry and implement fail-closed pre-mutation admission | F-02 | TODO |
| P-02 | omarchy-mac | Replace warning-success behavior with typed required/optional capability outcomes | P-01 | TODO |
| P-03 | omarchy-mac | Complete command/application ARM parity census and tracked porting queue | F-01 | TODO |
| P-04 | omarchy-mac | Implement platform diagnostics and support-bundle export with privacy redaction | F-02 | TODO |
| P-05 | omarchy-mac | Integrate atomic platform update/rollback UX and remove independent version selection | F-05 | TODO |
| I-01 | omarchy-mac-installer | Threat model and design the installer transaction/state machine | F-01 | TODO |
| I-02 | omarchy-mac-installer | Brand and self-host a pinned installer build with signed immutable metadata | I-01, F-03 | TODO |
| I-03 | omarchy-mac-installer | Implement read-only board/disk/APFS inventory and plan generation | F-02, I-01 | TODO |
| I-04 | omarchy-mac-installer | Implement journaled Apple platform provisioning and resume | I-03 | TODO |
| I-05 | omarchy-mac-installer | Build the Omarchy ARM live/install image handoff | F-04, I-04 | TODO |
| I-06 | omarchy-mac-installer | Implement uninstall, rollback, recovery, and DFU runbook | I-04, I-05 | TODO |
| B-01 | m1n1-omarchy | Human owner defines reproducible build, artifact, firmware-schema, and debug contracts | F-02, F-04, human m1n1 owner | HUMAN-ONLY BLOCKED |
| B-02 | m1n1-omarchy | Human owner packages qualified M1/M2 stage-1 and stage-2 bundles | B-01, human m1n1 owner | HUMAN-ONLY BLOCKED |
| B-03 | u-boot-omarchy | Define reproducible Apple U-Boot and UEFI/slot contracts | F-02, F-04 | TODO |
| B-04 | u-boot-omarchy | Implement versioned boot-slot selection, success marking, and fallback | B-03 | TODO |
| K-01 | linux-omarchy | Define downstream kernel/DT configuration, patch-queue, ABI, and build contracts | F-02, F-04 | TODO |
| K-02 | linux-omarchy | Produce a qualified M1/M2 reference kernel/DT package set | K-01 | TODO |
| K-03 | linux-omarchy | M3 base/Pro/Max/Ultra subsystem bring-up and board qualification | K-02 | TODO |
| K-04 | linux-omarchy | M4 base/Pro/Max subsystem bring-up and board qualification | K-03 | TODO |
| K-05 | linux-omarchy | A18 Pro and M5 family subsystem bring-up and board qualification | K-04 | TODO |
| K-06 | linux-omarchy | M6 intake and subsystem bring-up | shipping hardware, K-05 | TODO |
| G-01 | mesa-omarchy | Establish authoritative mirror sync, downstream patch queue, reproducible build, and conformance contract | F-02, F-04 | TODO |
| G-02 | mesa-omarchy | Qualify M1/M2 graphics reference tuple | G-01, K-02 | TODO |
| G-03 | mesa-omarchy | Implement and qualify M3 graphics/display dependencies | G-02, K-03 | TODO |
| G-04 | mesa-omarchy | Implement and qualify M4 graphics/display dependencies | G-03, K-04 | TODO |
| G-05 | mesa-omarchy | Implement and qualify A18/M5/M6 graphics dependencies | G-04, K-05 | TODO |
| Q-01 | omarchy-apple-platform | Define board inventory and qualification-record schema | F-02 | TODO |
| Q-02 | omarchy-apple-platform | Build lab controller, evidence ingestion, redaction, and public ledger generation | Q-01 | TODO |
| Q-03 | hardware lab | Acquire and inventory every released Apple Silicon board topology | Q-01 | TODO |
| Q-04 | hardware lab | Certify M1/M2 reference and every M1/M2 board | B-02, B-04, K-02, G-02, I-06, Q-02 | TODO |
| Q-05 | hardware lab | Certify M3 boards | K-03, G-03, Q-02 | TODO |
| Q-06 | hardware lab | Certify M4 boards | K-04, G-04, Q-02 | TODO |
| Q-07 | hardware lab | Certify A18 Pro and M5 boards | K-05, G-05, Q-02 | TODO |
| Q-08 | hardware lab | Certify M6 boards | K-06, G-05, Q-02 | TODO |

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

No milestone has a calendar promise until its prerequisite discovery and physical-hardware gates have produced evidence. Literal all-board/full-feature support is expected to be a multi-year platform program.

## 14. Staffing model

A credible standing team includes dedicated owners for installer/APFS/Recovery, m1n1/boot firmware, kernel core/SoC, display/GPU, connectivity/peripherals, audio/media/camera, power/security, release/supply chain, product integration, and physical QA/lab automation.

Luna agents accelerate repository research, design, test construction, packaging, documentation, safe mechanical work, and review. Reverse engineering and physical qualification still require evidence from real hardware and coordinator-controlled promotion.

## 15. Risk register

| Risk | Required control |
|---|---|
| An architecture check is mistaken for hardware support | Board registry plus physical qualification record required for promotion |
| Installer damages macOS/APFS | Read-only plan, stable identifiers, Apple tools, property tests, journal, disposable-machine fault injection, DFU rehearsal |
| Cross-component update produces an unbootable tuple | Single signed platform manifest, inactive slots, boot-success marker, automatic fallback |
| Upstream changes outrun downstream patches | Pinned sources, automated sync reports, owned patch queues, reproducible builds, explicit requalification |
| Package or mirror compromise | Mandatory signatures, threshold/offline roles, expiry, provenance, SBOMs, revocation and rotation drills |
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
- Telemetry default and privacy policy.
- Stable-release publication and any support-level claim.
- Actions with irreversible external impact, including production deployment, destructive lab tests outside disposable targets, and public announcements.
- Appointment of qualified human m1n1 maintainers and reviewers who accept that repository's local contribution rules.

Technical details within the approved architecture are coordinator rulings unless they change these owner boundaries.

## 17. Program acceptance criteria

The program mission is complete only when:

1. A signed clean installer can start from supported macOS on every released Apple Silicon Mac board in scope.
2. The installer safely provisions, installs, encrypts, boots, updates, rolls back, uninstalls, and recovers on every board.
3. Every applicable hardware capability in Section 3 passes on physical hardware with immutable evidence.
4. Every installed artifact is reproducibly built, signed, traceable to pinned source, and selected by one qualified platform manifest.
5. Unknown or unsupported machines fail before privileged mutation and receive an honest diagnostic.
6. Stable promotion is structurally impossible without complete board qualification records and all required cross-repository gates.
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

## 19. Append-only progress log

Do not edit or delete existing rows. Corrections are new rows.

| Timestamp | Event | Evidence or result |
|---|---|---|
| 2026-09-02 | Organization and repositories created | `omarchy-silicon` contains `omarchy-mac`, `omarchy-mac-installer`, `omarchy-apple-platform`, `linux-omarchy`, `m1n1-omarchy`, `u-boot-omarchy`, and `mesa-omarchy` |
| 2026-09-02 | Repository ancestry verified | GitHub-native forks retain their parents; Mesa main history mirrors freedesktop.org at the verified upstream SHA from creation time |
| 2026-09-02 | Coordinator established the canonical program plan | This document defines the mission, ownership, interfaces, safety invariants, acceptance criteria, slice ledger, decisions, and factory rules |
| 2026-09-02 | m1n1 Luna design lane stopped before edits | Worker reported the repository-local AI/LLM prohibition; no design, code, checks, commit, or push occurred, and the coordinator broadcast a supersession fence to all active agents |
