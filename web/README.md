# STL Canvas SPA (GitHub Pages)

Diese SPA hostet einen STL-Viewer auf GitHub Pages.

## Lokal starten

```bash
cd web
npm install
npm run dev
```

`npm run dev` und `npm run build` synchronisieren die STL-Dateien aus dem Repo-Ordner `models/` jetzt automatisch nach `web/public/models/` und erzeugen dabei `models.json`.

## Build

```bash
cd web
npm run build
```

## Deployment

Automatisch via GitHub Action bei Änderungen an:

- `.github/extensions/stl-canvas/**`
- `web/**`
- `models/**`

## Modelle

Die Action kopiert STL-Dateien aus dem Repo-Ordner `models/` nach `web/public/models/` während des Builds und erzeugt `models.json`.
