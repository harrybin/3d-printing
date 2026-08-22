# Skills Library

Diese Sammlung ist die wiederverwendbare Wissensbasis für STL-Aufgaben in diesem Repo.
Wenn eine Vorgehensweise mehr als einmal gebraucht wurde, gehört sie in eine Skill-Datei.

## Ziel

- Wiederholbare Abläufe zentral dokumentieren statt nur in einzelnen PRs zu lassen.
- Konsistente Entscheidungen über Geometrie, Druckbarkeit, Validierung und Quellen erzwingen.
- Neue Sessions ohne Kontextverlust schnell auf einen belastbaren Standard bringen.

## Bibliotheksstruktur

| Bereich | Skill | Inhalt |
| --- | --- | --- |
| Drucker-Profil | `anycubic-kobra-s1-ace-pro-profile` | Baselines zu Wandstärken, Toleranzen, Overhang/Bridge und Nozzle-Scaling |
| Neumodellierung | `create-ascii-stl` | Parametrische Modellierung, CSG/Repair-Workflow, Exportregeln |
| STL-Änderungen | `edit-stl-transform` | Transform/Boolean-Regeln, Datei-/Orientierungs-Policy |
| Bild→Modell | `stl-from-image-measurements` | Kontaktblatt-Workflow, Recherche-Branch, Render-Compare-Loop |
| Quellrecherche | `research-part-specs` | Herkunftspflicht für fit-kritische Maße, Messdoku in `docs/` |
| Vorab-Interview | `stl-create-edit-interview` | Erforderliche Fragen zu Zweck, Fit, Material-Semantik, Outputformat |
| Mesh-Qualität | `validate-stl-mesh` | Integritätschecks, Feature-Probes, Dateiverwechslungs-Prüfung |
| Druck-Optimierung | `optimize-stl-for-print` | Orientierungs- und Kompensationsentscheidungen nach korrekter Geometrie |

## Was in die Bibliothek gehört

Übernimm in Skills nur Inhalte, die dauerhaft und wiederverwendbar sind:

- feste Entscheidungsregeln (z. B. STL vs 3MF, Auto-Detection der Koordinatenkonvention)
- reproduzierbare Checklisten (Validierung, Druck-Optimierung, Foto-Workflow)
- wiederkehrende Fehlerbilder und Gegenmaßnahmen (z. B. tangentiale Knife-Edges, stale worktree file)
- belastbare Tooling-Pfade mit Repo-Befehlen (`scripts/mesh_tool.py`, `scripts/make_contact_sheet.py`)

Nicht als ausformulierte Bibliotheksregel übernehmen:

- einmalige Task-Details ohne Wiederverwendung
- volatile Einzelwerte ohne Bezug zur Repo-Policy
- PR-spezifische Diskussionen oder temporäre Workarounds

## Pflege-Regeln

1. **Single source of truth:** Wiederverwendbare Vorgehensweisen in der jeweils zuständigen Skill-Datei pflegen.
2. **Konflikte auflösen:** Bei widersprüchlichen Regeln gilt die spezifischere Skill-Datei (z. B. `stl-from-image-measurements` vor generischen Hinweisen).
3. **Quellen sichtbar halten:** Externe Grundlagen im jeweiligen Skill unter `Sources` pflegen.
4. **Repo-Abgleich:** Wenn sich Script- oder Policy-Verhalten ändert, Skill-Inhalte im selben Change mitziehen.
5. **Kurz aber vollständig:** Regeln handlungsfähig formulieren, ohne unnötige Theory-Blöcke.

## Erweiterungs-Template für neue Erkenntnisse

Wenn neue, wiederverwendbare Vorgehensweisen aus Recherche oder Bugfix-Runden entstehen, ergänze in der passenden Skill-Datei:

1. **Regelname** (kurz, eindeutig)
2. **Wann anwenden**
3. **Verbindliche Schritte**
4. **Abbruch-/Warnkriterien**
5. **Ausgabe/Nachweis** (welche Kennzahlen/Artefakte berichtet werden)

So wächst die Bibliothek kontrolliert und bleibt für Folgesessions nutzbar.
