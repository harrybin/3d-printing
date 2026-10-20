# 3d-printing model viewer (GitHub Pages)

Diese App ist eine reine GitHub-Pages-Oberfläche zum Anzeigen und Herunterladen der
Modelle aus einem externen Katalog (`harrybin/3d-printing-models`). Sie teilt den Browser-Viewer mit
`.github/extensions/stl-canvas/viewer-app.mjs`, damit Vorschauen in Pages und in der
Copilot-Canvas-Erweiterung gleich gerendert werden.

## Lokal starten

`CATALOG_ROOT` muss auf den vorhandenen Katalog-Checkout zeigen. Der Build liest
dessen `catalog.json`, Modelle und Bilder; ein ungueltiger Pfad ist ein Fehler.
Die Variable vor den folgenden Befehlen in der Umgebung setzen.

```bash
cd web
npm install
npm run dev
```

`predev` und `prebuild` spiegeln die Viewer-Assets automatisch und aktualisieren die
begleitenden Build-Dateien:

- `web/public/models/` und `models.json` aus `CATALOG_ROOT/models/`;
  die Metadaten kommen aus `CATALOG_ROOT/catalog.json`
  (`sync-models.mjs`)
- `web/public/build-info.json` (`write-build-info.mjs`)
- `web/public/app-config.json` mit Repository-/Issue-Ziel aus dem Katalog
- `web/public/docs/images/` mit Projekt- und Support-Sidecars aus dem Katalog

Die Viewer-Laufzeit selbst liest `app-config.json` sowie die Dateien unter
`web/public/models/`; weitere erzeugte Dateien sind Build-Metadaten.

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
- `docs/**`

Im Engine-Workflow wird das Katalog-Repo separat ausgecheckt. Der Katalog hat
zusaetzlich einen eigenen Pages-Workflow, der den Viewer derselben gepinnten
Engine-Version wie seine Python-Abhaengigkeit verwendet.
Im Build werden die Modell-Dateien vor dem Vite-Build mit
`node web/scripts/sync-models.mjs` nach `web/public/models/` gespiegelt, damit sowohl
`.stl` als auch `.3mf` im Deployment enthalten sind.

## Konfiguration

`web/public/app-config.json` wird beim Sync aus dem Katalog generiert und nicht
versioniert. Es steuert nur die Metadaten der Viewer-Seite:

- App-Titel und Tagline
- Repository-Link
- Standard-Branch für GitHub-Links

## Funktionsumfang

Die Pages-App bietet:

- 3D-Vorschau für STL- und 3MF-Dateien aus `models/`
- direkt erreichbare Support-Vorschaubilder je 3MF-Platte; ein Klick öffnet das
  Bild groß im Viewer-Dialog. Die Sidecars kommen aus `docs/images/` und fehlen
  ohne Screenshot wird der betreffende Button deaktiviert und erklärt den Grund.
- Vorschau einzelner ungemergter PR-/Branch-Modelle über URL-Parameter wie
  `?repo=harrybin/3d-printing-models&ref=<branch>&model=<datei.stl>` oder
  `?url=<oeffentliche-datei-url>&label=<anzeige-name>`
- Download der aktuell gewählten Datei
- Button **3mf öffnen**: lädt die aktuell gewählte 3MF-Datei herunter, damit das
  Betriebssystem sie mit dem für `.3mf` registrierten Standardprogramm öffnet.
  Browser dürfen lokale Programme nicht direkt starten
- Link zurück zum Repository
- Link zum Issue-Template `.github/ISSUE_TEMPLATE/model-request.yml`

Auf Mobilgeräten wird das Canvas-Pixelverhältnis begrenzt, damit große Modelle
spürbar schneller laden und rendern.

## Nicht Teil der Pages-App

Die frühere Copilot-/Workflow-Steuerung gehört nicht mehr zu `web/`:

- keine Authentifizierung oder Token-Eingabe
- kein Workflow-Dispatch
- keine Prompt-, Skill- oder Job-Steuerung im UI
