# 3d-printing model viewer (GitHub Pages)

Diese App ist eine reine GitHub-Pages-Oberfläche zum Anzeigen und Herunterladen der
Modelle aus `models/`. Sie teilt den Browser-Viewer mit
`.github/extensions/stl-canvas/viewer-app.mjs`, damit Vorschauen in Pages und in der
Copilot-Canvas-Erweiterung gleich gerendert werden.

## Lokal starten

```bash
cd web
npm install
npm run dev
```

`predev` und `prebuild` erzeugen die benötigten statischen Dateien automatisch:

- `web/public/models/` und `models.json` aus dem Repo-Ordner `models/`
  (`sync-models.mjs`)
- `web/public/skills-manifest.json` aus `.github/skills/**` (`sync-skills.mjs`)
- `web/public/build-info.json` (`write-build-info.mjs`)

## Build

```bash
cd web
npm run build
```

## Deployment

Das Pages-Build-Workflow läuft automatisch, wenn sich diese Pfade ändern:

- `.github/extensions/stl-canvas/**`
- `.github/skills/**`
- `.github/workflows/copilot-agent.yml`
- `.github/workflows/pages-spa.yml`
- `web/**`
- `scripts/**`
- `models/**`

Im Workflow werden die Modell-Dateien vor dem Vite-Build mit
`node web/scripts/sync-models.mjs` nach `web/public/models/` gespiegelt, damit sowohl
`.stl` als auch `.3mf` im Deployment enthalten sind.

## Konfiguration

`web/public/app-config.json` steuert nur die Metadaten der Viewer-Seite:

- App-Titel und Tagline
- Repository-Link
- Standard-Branch für GitHub-Links

## Funktionsumfang

Die Pages-App bietet:

- 3D-Vorschau für STL- und 3MF-Dateien aus `models/`
- Download der aktuell gewählten Datei
- Link zurück zum Repository
- Link zum Issue-Template `.github/ISSUE_TEMPLATE/model-request.yml`

Auf Mobilgeräten wird das Canvas-Pixelverhältnis begrenzt, damit große Modelle
spürbar schneller laden und rendern.

## Nicht Teil der Pages-App

Die frühere Copilot-/Workflow-Steuerung gehört nicht mehr zu `web/`:

- keine Authentifizierung oder Token-Eingabe
- kein Workflow-Dispatch
- keine Prompt-, Skill- oder Job-Steuerung im UI
