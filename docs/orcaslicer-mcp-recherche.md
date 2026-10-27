# OrcaSlicer MCP and Skill Research

As of 2026-10-07.

## Current decision

OrcaSlicer's **official CLI** is used for final print validation. It slices the
exact 3MF projects, exports G-code, and provides time, material, layer, and
warning data without requiring an additional MCP server.

`ShreddyKrueger75/claude-orcaslicer-mcp`, commit
`b1a7cd13c853a733e09367f18d3c183f04c349d9`, was previously evaluated as an
MIT-licensed local integration. It remains a third-party option and is no longer
the project's default or automatically enabled solution.

Therefore, `.vscode/mcp.json` contains only a disabled OrcaSlicer template that
uses environment variables. Absolute installation paths, downloaded servers,
and personal profiles are not committed. Setup instructions and security rules
are in `docs/mcp-setup.md`.

## Evaluated alternative

`MaxEllis/orcaslicer-mcp`, licensed under AGPL-3.0, offers a more tightly
integrated live GUI. However, it requires a special OrcaSlicer fork with a local
remote API and token. Since the target system already runs standard OrcaSlicer,
it is not the project's default solution.

## Skill research

The research found, among others:

- `autonomous-ai/openharness/.../orcaslicer/SKILL.md`: a complete mesh-to-slicer
  handoff; used as a technical reference.
- `OrcaSlicer/OrcaSlicer/.claude/skills/orca-profiles/SKILL.md`: tailored to
  OrcaSlicer profile development in the OrcaSlicer source repository, so it was
  not adopted directly.

The shorter, project-specific skill is in
`.github/skills/orcaslicer-project-workflow/SKILL.md` and complements the
existing Anycubic and mesh validation rules.
