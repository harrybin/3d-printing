# 3d-printing - create and adjust models with GH-Copilot (GitHub Pages)

Diese SPA hostet den STL-Viewer auf GitHub Pages und startet GitHub Copilot als
GitHub-Action im vollständigen Repository.

Die Viewer-Implementierung wird mit `.github/extensions/stl-canvas/viewer-app.mjs`
geteilt, damit Pages-App und Copilot-Extension synchron bleiben.

## Lokal starten

```bash
cd web
npm install
npm run dev
```

`predev`/`prebuild` erzeugen automatisch:

- `web/public/models/` + `models.json` aus dem Repo-Ordner `models/` (`sync-models.mjs`)
- `web/public/skills-manifest.json` aus `.github/skills/**` (`sync-skills.mjs`)
- `web/public/build-info.json` (`write-build-info.mjs`)

## Build

```bash
cd web
npm run build
```

## Deployment

Automatisch via GitHub Actions, wenn sich diese Pfade ändern:

- `.github/extensions/stl-canvas/**`
- `.github/skills/**`
- `.github/workflows/copilot-agent.yml`
- `web/**`
- `scripts/**`
- `models/**`

## Konfiguration

`web/public/app-config.json` steuert Titel, Repository, Workflow-Datei,
Prompt-Limits und den Bildspeicher. Die Skill-Liste im UI ist rein informativ –
Copilot bekommt in der Action immer alle Skills.

## Browser-Speicher

| Daten | Ort | Grund |
| --- | --- | --- |
| PAT | `sessionStorage` | Verschwindet mit dem Tab. |
| Zuletzt verbundener Benutzer, Prompt-Journal | `localStorage` | Kleine Metadaten. |
| Referenzbilder, Modelle, Berichte | **IndexedDB** (`stl-copilot-store`) | Blobs statt Base64; `localStorage` ist auf ~5 MB begrenzt und würde schon beim ersten Foto überlaufen. |

Modelle aus dem alten `localStorage`-Format werden beim ersten Start automatisch
in die IndexedDB übernommen.

## Token

Fine-grained PAT für dieses Repository mit **`Metadata: Read`** und
**`Actions: Read and write`**. Kein `Contents`-Recht: die App schreibt nie in das
Repository. `Actions: Read and write` ist die kleinste Stufe, mit der GitHub
`workflow_dispatch` erlaubt.
