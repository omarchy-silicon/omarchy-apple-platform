# Factory rules

`PROGRAM.md` is the coordinator-owned source of truth. Workers may read it but must not edit its statuses, decision log, acceptance criteria, or progress log.

Every production slice starts with a design note and a coordinator ruling. No worker may merge its own branch, mark a slice DONE, broaden the support claim, or bypass a fail-closed guard.

Use one writer per branch and worktree. Reviewers are read-only and default to REJECT until they have constructed hostile cases, planted guard violations, and rerun the relevant gates themselves.

Unknown SoCs, boards, firmware schemas, artifact versions, manifest versions, and installer states must fail closed before privileged or destructive operations.

Hardware support is a board-level claim backed by physical evidence. Simulation, architecture checks, compilation, booting a kernel, or recognizing a compatible string are not sufficient evidence.

Markdown uses full lines with breaks only at structural boundaries. Use two spaces for indentation and no tabs.
