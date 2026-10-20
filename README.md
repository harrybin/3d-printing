# 3D Printing Engine

Reusable FDM modeling tools, agent skills and the STL/3MF viewer for the
Anycubic Kobra S1 Combo + ACE Pro (250 x 250 mm bed). This repository is the
engine, **not the model catalog**.

Models, model-specific generators, measurements, source licenses, assembly
audits, Blender sources, print projects and previews live in
[`harrybin/3d-printing-models`](https://github.com/harrybin/3d-printing-models).
The catalog retains the original relative paths and filtered model history.
Its `catalog.json` records the original source commit and asset SHA-256 hashes.
Existing geometry, print-profile status and license notices are not changed
or newly certified by the repository split.

## Install the engine

Python 3.11 or newer is required.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\python.exe -m printforge --version
```

The distribution is `harrybin-printforge`; the CLI is `printforge`. Existing
shared Python imports such as `mesh_kit`, `fdm_joints` and `mesh_tool` remain
available so model generators need no geometry-affecting rewrites.

## Work on models

Open the **model catalog** and install its pinned `requirements.txt`. Run these
commands from its root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m printforge bootstrap .
.\.venv\Scripts\python.exe -m printforge verify-catalog .
```

Bootstrap materializes ignored engine tools, skills, Canvas extension, MCP
template and setup docs at the legacy paths used by existing model instructions.
Those copies are caches, not independently maintained sources. Re-run bootstrap
after explicitly updating the engine pin. It refuses to overwrite unmanaged or
locally edited files. Model generators, docs and assets remain catalog-owned.

`printforge run --catalog <directory> <script> [arguments]` executes a
catalog-owned script with the catalog as its working directory, sets
`CATALOG_ROOT`, and propagates its exit code. `printforge tool <module>
[arguments]` runs an installed engine tool without materializing it.
`printforge --help` lists the supported commands.

## Engine boundaries

| Here: engine | Model catalog |
| --- | --- |
| Mesh validation, booleans, FDM joints, SDF helpers | Specific geometry, mechanisms and generators |
| Contact sheets, generic 3MF/G-code rendering | References, measurements, licenses and final previews |
| Optional local GenAI tooling and safe MCP setup | Model provenance, audits and test-print risks |
| Skills, Canvas extension, web viewer | STL/3MF outputs and model regression tests |
| Engine tests and Python package releases | Pinned engine dependency and catalog Pages deployment |

Project-specific slicing/export/verification scripts stay with their models;
they are not treated as general APIs merely because they use generic tools.
The catalog uses normal Git for binary assets, preserving existing direct
downloads without an additional LFS requirement.

## External catalog and viewer

Set `CATALOG_ROOT` to the absolute model-catalog directory when using engine-side
rendering, the Canvas extension or web builds. Relative values are resolved
against the engine repository for the web build, or the current workspace for
Canvas. An explicit invalid catalog fails rather than showing an empty gallery.
In a catalog workspace, Canvas uses that workspace by default.

The web build copies catalog STL/3MF files, model metadata and the exact
`docs/images/<stem>-preview.png` / per-plate support sidecars into static assets.
Repository and issue links come from the catalog manifest, not the engine repo.
See [web/README.md](web/README.md).

The catalog's workflow publishes its pinned viewer at
<https://harrybin.github.io/3d-printing-models/>. The existing engine Pages
workflow also checks out the external catalog, preserving the former viewer URL.
GitHub Actions' `COPILOT_GITHUB_TOKEN` and allowlist, if used, must be configured
separately in the model repository; secrets are never copied between repos.

## Validation and releases

```powershell
.\.venv\Scripts\python.exe scripts\compact_output.py run --log build\tests.log -- .\.venv\Scripts\python.exe -m unittest discover -s tests
npm --prefix web test
.\.venv\Scripts\python.exe -m pip wheel --no-deps . --wheel-dir dist
```

The compact runner preserves exit codes and full logs; its heuristic summaries
are not proof that omitted warnings are harmless. Engine CI checks the generic
Python suite, viewer suite and wheel build independently of production models.
`tests/test_printforge.py` exercises a temporary fixture catalog.

Publish engine changes as versioned releases. Update both package version
declarations, tag the tested commit, then explicitly update the catalog's
Python dependency and Pages viewer ref together. Never point production model
work at a floating engine branch. See [docs/repository-split.md](docs/repository-split.md)
for migration ownership and rollback.

## Setup references

- [Reusable skills](.github/skills/README.md)
- [Blender / OrcaSlicer MCP setup](docs/mcp-setup.md)
- [Optional local 3D GenAI setup](docs/local-3d-genai-setup.md)
- [OrcaSlicer integration research](docs/orcaslicer-mcp-recherche.md)

The repository MIT license is unchanged. Reused assets retain their own licenses
and attribution requirements in the model catalog.
