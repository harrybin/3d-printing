# Engine development

This is `harrybin/3d-printing`, the reusable engine. Read `README.md` first.
Model work belongs in `harrybin/3d-printing-models`: do not add model outputs,
model-specific generators, reference assets, measurements or final renders here.

## Source boundaries

- `scripts/`: generic mesh, joint, rendering, contact-sheet and GenAI tools.
- `scripts/printforge/`: installable engine CLI and catalog bootstrap/verification.
- `.github/skills/`: authoritative modeling and printer policies.
- `.github/extensions/stl-canvas/` and `web/`: reusable viewers.
- `docs/`: engine setup/architecture docs only.
- `tests/`: engine tests with temporary fixture geometry/catalogs.

The catalog pins a released engine. `printforge bootstrap` materializes ignored
engine files there, preserving the paths referenced by existing skills and model
scripts. Do not independently modify or commit those materialized copies.
Modify the engine source, publish a version, then update the catalog pin.
Keep `setup.py`, `MANIFEST.in` and the bootstrap resource list consistent.

## Python and validation

Use the local `.venv`. Install with `python -m pip install .` after environment
creation. For source changes, run the smallest relevant existing tests first.
Before release, build the wheel and test bootstrap from the installed wheel,
not only from the source tree. Run the viewer suite for viewer changes.

```powershell
.\.venv\Scripts\python.exe scripts\compact_output.py run --log build\tests.log -- .\.venv\Scripts\python.exe -m unittest discover -s tests
npm --prefix web test
.\.venv\Scripts\python.exe -m pip wheel --no-deps . --wheel-dir dist
```

Use `scripts/compact_output.py` for verbose output and retain complete logs under
`build/`. Summaries are heuristic: inspect targeted log evidence for failures,
unknown warnings and omitted diagnostic kinds. Do not truncate arbitrary output.

## Compatibility and safety

- Preserve existing generic module imports and CLI behavior across catalogs.
- Resolve catalog assets from explicit `CATALOG_ROOT`, never package/site-packages.
- Do not silently fall back when an explicitly configured catalog is invalid.
- Bootstrap must protect user edits and never overwrite catalog-owned models.
- Never regenerate or reslice production models merely to test packaging.
- Preserve printer/fit/validation rules in `.github/skills/`; update relevant
  skill policy alongside any intentional behavioral change.
- Python owns measured geometry; controlled Blender owns approved organic work.
  Catalog-specific `AGENTS.md` governs the model workflow and evidence.
- Keep secrets, downloaded tools, personal profiles and absolute machine paths
  out of Git. Do not silently install/enable optional MCP or GenAI systems.
- Keep model geometry and print-profile claims unchanged during migrations.

## Release and PR output

Keep `pyproject.toml` and `scripts/printforge/__init__.py` versions aligned.
Catalog Python dependency and Pages checkout must select the same tested engine
revision. Preserve the pull request template and record exact commands/results.
Engine-only changes do not need model previews when delivered geometry is
unchanged. Document cross-repo requirements and any unverified remote deployment.
