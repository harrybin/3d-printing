# The Ghoul's Grip – OrcaSlicer-Druckvalidierung

Status: **VERIFIED**
Validiert: 2026-10-09
OrcaSlicer: **2.4.2**

![Übersicht der geslicten G-Code-Pfade](images/ghouls-grip-slice-overview.png)

## Fester Profilvertrag

- Drucker: `Anycubic Kobra S1 0.4 nozzle`
- Düse: 0,4 mm
- Prozess: `0.20mm Standard @Anycubic Kobra S1 0.4 nozzle`
- Filament: `Anycubic PLA @Anycubic Kobra S1 0.4 nozzle`
- Druckbett: `Textured PEI Plate`
- Schichthöhe: 0,20 mm
- Starttemperaturen: Bett 55 °C, Düse 215 °C
- Stützen: nur vom Druckbett; Baumstützen für organische/äußere Formen,
  objektbezogene `normal(auto)`/`snug`-Stützen in den Mechanikplatten
- Prime Tower: aus, da jede Druckplatte nur eine PLA-Spule nutzt

## Materialfarben

Jedes Druckprojekt speichert seine Farbe in Orcas
`filament_colour`, `extruder_colour` und `default_filament_colour` sowie in
`Metadata/ghouls_grip_print_metadata.xml`. Der Canvas verwendet denselben Wert
als Darstellungsfarbe, wenn Orcas Komponentenmodell keine Standard-3MF-Palette
enthält.

| Materialgruppe | Farbe | Hex |
| --- | --- | --- |
| Schatulle und Deckel | Anthrazit/Schwarz | `#202124` |
| Hand, Unterarm, Sehnenführung und Finger | Knochenbeige | `#D8C6A5` |
| Mechanik | Naturweiß | `#F1EBDD` |
| Totenkopf-Auslöser | Grau | `#777777` |

Die offizielle OrcaSlicer-CLI wurde mit dem exakten gelieferten 3MF jeder
Platte aufgerufen. Jeder Slice erzeugte eine vollständige G-Code-Datei. Die
Logs enthalten keine verbleibende Floating-region-, Floating-cantilever-,
Toolpath-conflict-, Out-of-bed-, Empty-layer- oder Invalid-toolpath-Warnung.

Jedes Ghoul's-Grip-3MF enthält zusätzlich
`Metadata/ghouls_grip_print_metadata.xml`. Dort stehen Drucker, Düse,
Schichthöhe, Filament, Bett, Wände, Infill, Support und Plattenzahl sowie
standardisierte Felder für Druckzeit und Filamentverbrauch. Für Exporte ohne
erfolgreichen Slice bleiben die Verbrauchswerte bewusst `unknown` und der
Status lautet `not-verified`; die STL-Canvas-App zeigt diese Werte an.

## Platten und Ergebnisse

| Druckprojekt / Platte | Enthaltene Objekte | Schichten | PLA | Zeit | Stützen | Vorschau |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `ghouls-grip-print-black-pla.3mf`, Platte 1 | Erleichterte, außen geschlossene Schatulle | 490 | 282,25 g | 10 h 19 min 36 s | Baum, nur kritische Bereiche | [PNG](images/ghouls-grip-slices/ghouls-grip-print-black-pla-plate_1.png) |
| `ghouls-grip-print-black-pla.3mf`, Platte 2 | Gerippter Deckel mit kollisionsfreier U-Führung | 137 | 175,91 g | 8 h 49 min 44 s | Baum, nur kritische Bereiche | [PNG](images/ghouls-grip-slices/ghouls-grip-print-black-pla-plate_2.png) |
| `ghouls-grip-print-bone-pla.3mf`, Platte 1 | Unterarm, Handfläche, Sehnenführung und fünf Finger | 284 | 64,15 g | 4 h 48 min 13 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-bone-pla.png) |
| `ghouls-grip-print-mechanism-pla.3mf`, Platte 1 | 4 Scherenarme, Schlitten, Hubjoch, Rastschieber und Führung | 467 | 120,44 g | 5 h 04 min 16 s | objektbezogen normal/keine | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-pla-plate_1.png) |
| `ghouls-grip-print-mechanism-pla.3mf`, Platte 2 | Spule, Schlüssel, Bandanker, 8 kleine und 4 große Pins | 206 | 22,25 g | 1 h 24 min 21 s | objektbezogen normal/keine | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-pla-plate_2.png) |
| `ghouls-grip-print-accent-pla.3mf` | Flacher Totenkopf-Auslöser mit kurzem Stößel | 107 | 14,21 g | 50 min 49 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-accent-pla.png) |
| **Gesamt** | 34 physische Druckobjekte | - | **679,21 g** | **31 h 16 min 59 s** | - | - |

Gegenüber den vom Benutzer gemessenen Ausgangswerten für Schatulle und Deckel
(400,39 g + 229,27 g = 629,66 g) benötigt das schwarze Projekt jetzt
**458,16 g**. Das spart **171,50 g beziehungsweise 27,2 %**. Die kombinierte
Druckzeit fällt von 27 h 58 min auf 19 h 09 min.

Knochen und Finger wurden mit derselben Spule auf einer gemeinsamen Platte
angeordnet und als acht vollständige G-Code-Objekte nachgewiesen. Die globalen
3MF-Transformationen ergeben zwischen allen acht Objekten **0,000 mm³**
Überlappung. Das STL/3MF-Canvas
wertet die standardkonformen 3MF-Build- und Komponenten-Transformationen aus
und zeigt deshalb dieselbe getrennte Anordnung wie OrcaSlicer. Bei
Mehrplattenprojekten liest es außerdem Orcas `plater_id`-Zuordnung: Die
Auswahl `Plate 1`/`Plate 2` zeigt jeweils nur die zugehörigen Objekte auf einem
lokalen 250-mm-Druckbett, während `All plates` getrennte, beschriftete
Druckbetten als Übersicht rendert.

Die G-Code-Pfad-Vorschauen werden von `scripts/render_gcode_preview.py` direkt
aus den erfolgreichen OrcaSlicer-Ausgaben gerendert. Rosa markiert höhere,
blau niedrigere Extrusionspfade; die Bilder sind kein Ersatz für die
interaktive Layeransicht, belegen aber Platte, Bettlage und erzeugte Toolpaths.

## Behobene Slice-Probleme

1. Ohne Stützen meldete OrcaSlicer schwebende Bereiche an Fingern, Handteilen,
   Totenkopf, Deckel und Gehäuse. Bettgebundene Stützen beseitigen diese
   Warnungen. Für das erleichterte schwarze Projekt reduziert
   `support_critical_regions_only=1` die Stützen auf tatsächlich kritische
   Bereiche; beide Platten slicen ohne Floating-region-Warnung.
2. Die ursprünglich 3 mm tiefe Führung traf auf eine ebenfalls 3 mm starke
   Seitenwand und erschien dadurch von außen als horizontaler Schlitz. Eine
   1,8-mm-Abdeckung setzt den unteren Sockel über der Führung fort. Der
   Schlitten behält den vollständigen inneren Führungsraum; die Außenwand ist
   geschlossen.
3. Die Mechanik wird nicht mehr nach Stützbedarf auf mehrere Dateien verteilt.
   Eine naturweiße 3MF enthält zwei explizite Orca-Platten. Platte 1 enthält
   die großen Funktionsteile, Platte 2 Spule, Schlüssel, Bandanker und alle
   zwölf Pins. Objekt-Overrides aktivieren Stützen nur dort, wo sie gebraucht
   werden. Beide Platten slicen ohne Pfadkonflikt und enthalten zusammen alle
   23 Mechanikobjekte.

## Dateibelege

Alle Dateien wurden am 2026-10-09 gegen den hier beschriebenen Slice-Stand
regeneriert. SHA-256:

| Datei | SHA-256 |
| --- | --- |
| `ghouls-grip-master.3mf` | `69EE336B8E09F18AB3158BB4BA8EC885F6C6628C20ABF6F33CD6C1537440370C` |
| `ghouls-grip-master-retracted.3mf` | `0937FFC771A9A685C6A12456EA5E36CF94A34997482FB3D4133EA22A37FA8017` |
| `ghouls-grip-print-black-pla.3mf` | `13F80840F46D24C3D4CC30FAEDAC50C01CF7F25F79FC03E169C700AB8BFC26DF` |
| `ghouls-grip-print-bone-pla.3mf` | `505E65712D3EC2A8A431DC9612D4061440D99FC7C47B79FE50CCAD6967F20059` |
| `ghouls-grip-print-mechanism-pla.3mf` | `8ABC4EB13B83A97E69C29A4049FDC891FA2CD897897741CDCCA652E894FD1951` |
| `ghouls-grip-print-accent-pla.3mf` | `475329DBE016BF010B73B0E4A6E8D6A62078C70063D0EBDCE5DE274B8E16E3C0` |

## Verbleibende physische Risiken

- Ein erfolgreicher Slice beweist keine reale Lebensdauer der 0,8-mm-PLA-
  Filmscharniere.
- Gummibandvorspannung, Seilspiel und Rastkraft müssen mit einem niedrigen
  Vorspannungs-Testaufbau abgestimmt werden.
- Gedruckte Pivot-Pins bleiben Verschleißteile; M3-Schrauben sind für die vier
  hoch belasteten Scherengelenke vorzuziehen.
- Vor dem Komplettdruck bleiben Arm-/Pin-/Passungscoupon und ein einzelner
  Finger-Testdruck verpflichtend.
