# STL Canvas SPA (GitHub Pages)

This SPA hosts an STL viewer on GitHub Pages.

## Run locally

```bash
cd web
npm install
npm run dev
```

`npm run dev` and `npm run build` now automatically sync STL files from the repo's `models/` directory into `web/public/models/`; `models.json` is generated and the `*.stl` files are copied there.

## Build

```bash
cd web
npm run build
```

## Deployment

Automatically via GitHub Actions when these paths change:

- `.github/extensions/stl-canvas/**`
- `web/**`
- `models/**`

## Models

The workflow copies STL files from the repo-root `models/` directory into `web/public/models/` during the build and generates `models.json`.
