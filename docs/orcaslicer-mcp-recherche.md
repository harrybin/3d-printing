# Recherche: OrcaSlicer MCP und Skills

Stand: 2026-10-07.

## Aktuelle Entscheidung

Für die verbindliche Druckvalidierung wird OrcaSlicers **offizielle CLI**
verwendet. Sie sliced die exakten 3MF-Projekte, exportiert G-Code und liefert
Zeit-, Material-, Schicht- und Warnungsdaten ohne zusätzlichen MCP-Server.

`ShreddyKrueger75/claude-orcaslicer-mcp`, Commit
`b1a7cd13c853a733e09367f18d3c183f04c349d9`, wurde früher als MIT-lizenzierte
lokale Integration geprüft. Es bleibt eine Drittanbieteroption und ist nicht
mehr die voreingestellte oder automatisch aktivierte Projektlösung.

Die `.vscode/mcp.json` enthält daher nur ein deaktiviertes, umgebungsvariablen-
basiertes OrcaSlicer-Template. Absolute Installationspfade, heruntergeladene
Server und persönliche Profile werden nicht eingecheckt. Einrichtung und
Sicherheitsregeln stehen in `docs/mcp-setup.md`.

## Geprüfte Alternative

`MaxEllis/orcaslicer-mcp`, AGPL-3.0, bietet die deutlich engere Live-GUI-
Integration. Sie benötigt jedoch einen speziellen OrcaSlicer-Fork mit lokaler
Remote-API und Token. Da auf dem Zielsystem bereits Standard-OrcaSlicer läuft,
ist sie nicht die voreingestellte Projektlösung.

## Skill-Recherche

Gefunden wurden unter anderem:

- `autonomous-ai/openharness/.../orcaslicer/SKILL.md`: vollständiger
  Mesh-zu-Slicer-Handoff; als fachliche Referenz verwendet.
- `OrcaSlicer/OrcaSlicer/.claude/skills/orca-profiles/SKILL.md`: auf die
  Entwicklung von OrcaSlicer-Profilen im OrcaSlicer-Quellrepository
  zugeschnitten, daher nicht direkt übernommen.

Der projektspezifische, kürzere Skill liegt in
`.github/skills/orcaslicer-project-workflow/SKILL.md` und ergänzt die
bestehenden Anycubic- und Mesh-Validierungsregeln.
