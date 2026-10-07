# Recherche: OrcaSlicer MCP und Skills

Stand: 2026-10-07.

## Ausgewählte Integration

`ShreddyKrueger75/claude-orcaslicer-mcp`, Commit
`b1a7cd13c853a733e09367f18d3c183f04c349d9`, MIT-Lizenz.

Gründe:

- funktioniert mit einer normalen OrcaSlicer-Installation über deren CLI;
- unterstützt STL, 3MF und STEP, Preset-Auflösung und G-Code-Analyse;
- Windows-Pfade werden automatisch erkannt;
- Installation ist über `tools/orcaslicer-mcp-requirements.txt` reproduzierbar;
- Druckersteuerung ist vorhanden, wird durch den Repository-Skill aber nicht
  ohne einen separaten, ausdrücklichen Benutzerauftrag verwendet.

Installation:

```powershell
.\scripts\setup_orcaslicer_mcp.ps1
```

Die Client-Konfiguration liegt in `.vscode/mcp.json`. Sie enthält keine
Zugangsdaten und setzt nur OrcaSlicer-Pfad sowie Druckbett-Typ.

Der Importtest des Servers und die Erkennung von
`C:\Program Files\OrcaSlicer\orca-slicer.exe` waren erfolgreich. Ein
Headless-Test-Slice war noch nicht möglich, weil die laufende Installation nur
ein unbenanntes Maschinenprofil, aber kein gespeichertes Prozess- und
Filamentprofil enthält. Nach dem einmaligen OrcaSlicer-Einrichtungsassistenten
und dem Speichern dieser drei Presets liefert `list_profiles` die Namen für
`slice_model`.

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
