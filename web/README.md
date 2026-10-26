# 3D Printing Model Viewer (GitHub Pages)

This app is a GitHub Pages interface for viewing and downloading models from an
external catalog (`harrybin/3d-printing-models`). It shares the browser viewer
from `.github/extensions/stl-canvas/viewer-app.mjs`, so previews render the same
way in Pages and in the Copilot Canvas extension.

## Run locally

Set `CATALOG_ROOT` to an existing model-catalog checkout before running these
commands. The build reads its `catalog.json`, models, and images; an invalid path
is an error.

```bash
cd web
npm install
npm run dev
```

`predev` and `prebuild` automatically sync the viewer assets and update the
associated build files:

- `web/public/models/` and `models.json` from `CATALOG_ROOT/models/`;
  metadata comes from `CATALOG_ROOT/catalog.json`
  (`sync-models.mjs`)
- `web/public/build-info.json` (`write-build-info.mjs`)
- `web/public/app-config.json` with the repository and issue targets from the catalog
- `web/public/docs/images/` with project and support sidecars from the catalog

The viewer runtime itself reads `app-config.json` and files under
`web/public/models/`; other generated files are build metadata.

## Build

```bash
cd web
npm run build
```

## Deployment

The Pages build workflow runs automatically when changes affect these paths:

- `.github/extensions/stl-canvas/**`
- `.github/skills/**`
- `.github/workflows/copilot-agent.yml`
- `.github/workflows/pages-spa.yml`
- `web/**`
- `scripts/**`
- `docs/**`

The engine workflow checks out the catalog repository separately. The catalog
also has its own Pages workflow, which uses the same pinned engine version as its
Python dependency.

Before the Vite build, `node web/scripts/sync-models.mjs` syncs the model files
to `web/public/models/` so both `.stl` and `.3mf` files are included in the
deployment.

## Configuration

`web/public/app-config.json` is generated from the catalog during sync and is not
versioned. It controls only the viewer page metadata:

- App title and tagline
- Repository link
- Default branch for GitHub links

## Features

The Pages app provides:

- 3D previews of STL and 3MF files from `models/`
- Directly accessible support preview images for each 3MF plate. Clicking an
  image opens it at full size in the viewer dialog. Sidecars come from
  `docs/images/`; if a screenshot is missing, the corresponding button is
  disabled and explains why.
- Previews of individual unmerged PR or branch models using URL parameters such
  as `?repo=harrybin/3d-printing-models&ref=<branch>&model=<file.stl>` or
  `?url=<public-file-url>&label=<display-name>`
- Download of the currently selected file
- **Open 3MF** button: downloads the selected 3MF file so the operating system
  can open it with the default application registered for `.3mf`. Browsers cannot
  launch local applications directly.
- Link back to the repository
- Link to the `.github/ISSUE_TEMPLATE/model-request.yml` issue template

On mobile devices, the canvas pixel ratio is limited so large models load and
render noticeably faster.

## Not part of the Pages app

The former Copilot/workflow controls are no longer part of `web/`:

- No authentication or token entry
- No workflow dispatch
- No prompt, skill, or job controls in the UI
