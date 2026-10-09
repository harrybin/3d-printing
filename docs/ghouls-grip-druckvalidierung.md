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
  `normal(auto)`/`snug` für die fünf einzeln gedruckten Mechanikteile
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
| Hand, Unterarm und Sehnenführung | Knochenbeige | `#D8C6A5` |
| Mechanik | Naturweiß | `#F1EBDD` |
| Finger | warmes Beige | `#C9B48E` |
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
| `ghouls-grip-print-black-pla.3mf`, Platte 1 | Erleichterte, außen geschlossene Schatulle | 490 | 282,25 g | 10 h 19 min 37 s | Baum, nur kritische Bereiche | [PNG](images/ghouls-grip-slices/ghouls-grip-print-black-pla-plate_1.png) |
| `ghouls-grip-print-black-pla.3mf`, Platte 2 | Gerippter Deckel mit kollisionsfreier U-Führung | 137 | 175,91 g | 8 h 49 min 44 s | Baum, nur kritische Bereiche | [PNG](images/ghouls-grip-slices/ghouls-grip-print-black-pla-plate_2.png) |
| `ghouls-grip-print-bone-pla.3mf` | Geneigter Unterarm, nach oben gerollte Handfläche, Sehnenführung | 284 | 52,30 g | 3 h 29 min 54 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-bone-pla.png) |
| `ghouls-grip-print-mechanism-pla.3mf` | 4 Scherenarme, Schlitten, 8 kleine und 4 große Pins | 170 | 50,04 g | 2 h 30 min 33 s | nein | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-pla.png) |
| `ghouls-grip-print-mechanism-supported-platform-pla.3mf` | Hubjoch | 344 | 46,11 g | 1 h 58 min 31 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-platform-pla.png) |
| `ghouls-grip-print-mechanism-supported-latch-slider-pla.3mf` | Interner Rastschieber | 344 | 8,89 g | 32 min 23 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-latch-slider-pla.png) |
| `ghouls-grip-print-mechanism-supported-latch-bracket-pla.3mf` | Interne Rastschieberführung mit Montagepads | 170 | 18,93 g | 35 min 22 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-latch-bracket-pla.png) |
| `ghouls-grip-print-mechanism-supported-crank-pla.3mf` | Interne Spule und abnehmbarer Schlüssel | 165 | 5,71 g | 22 min 28 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-crank-pla.png) |
| `ghouls-grip-print-mechanism-supported-band-anchor-pla.3mf` | Bandanker | 143 | 12,22 g | 39 min 51 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-band-anchor-pla.png) |
| `ghouls-grip-print-accent-pla.3mf` | Flacher Totenkopf-Auslöser mit kurzem Stößel | 107 | 14,21 g | 50 min 49 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-accent-pla.png) |
| `ghouls-grip-print-fingers-pla.3mf` | Daumen und vier Finger | 57 | 11,78 g | 1 h 21 min 30 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-fingers-pla.png) |
| **Gesamt** | 34 physische Druckobjekte | - | **678,35 g** | **31 h 30 min 42 s** | - | - |

Gegenüber den vom Benutzer gemessenen Ausgangswerten für Schatulle und Deckel
(400,39 g + 229,27 g = 629,66 g) benötigt das schwarze Projekt jetzt
**458,16 g**. Das spart **171,50 g beziehungsweise 27,2 %**. Die kombinierte
Druckzeit fällt von 27 h 58 min auf 19 h 09 min.

Nach der Deckelkorrektur wurden Deckel, Knochenplatte und Fingerplatte in
dieser Reihenfolge erneut mit demselben Profil gesliced. Die globalen
3MF-Transformationen ergeben zwischen allen drei Knochenobjekten sowie allen
fünf Fingerobjekten jeweils **0,000 mm³** Überlappung. Das STL/3MF-Canvas
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
3. Die gestützten Mechanikteile erzeugten auf einer gemeinsamen Platte
   überlappende Stütz-/G-Code-Pfade. Sie wurden auf fünf Einzelprojekte
   aufgeteilt. Spule und abnehmbarer Schlüssel teilen sich eine Platte mit
   30 mm Objektabstand und 20 mm Bettrand; danach bestanden alle
   Kollisions- und Druckbettprüfungen.
4. Die supportfreie Mechanik bleibt zusammen auf einer Platte, damit Arme,
   Schlitten und vollständige Pin-Stückzahlen gemeinsam geprüft werden.

## Dateibelege

Alle Dateien wurden am 2026-10-09 gegen den hier beschriebenen Slice-Stand
regeneriert. SHA-256:

| Datei | SHA-256 |
| --- | --- |
| `ghouls-grip-master.3mf` | `DA1F707EF99F492CE77239966BF8ADB025F1C216D728E49EEFA5E18065EF4B8C` |
| `ghouls-grip-master-retracted.3mf` | `3708D3A1732AEAB102000DD7BE1AB16E5C9E12F962C73583EAA081AB0A98B418` |
| `ghouls-grip-print-black-pla.3mf` | `9B72F5B8E45EB7133086313EBCFF2521357193D794B49982CF31A70AADB7A804` |
| `ghouls-grip-print-bone-pla.3mf` | `1EF0AD0C85554B60B05D9DECE5C063C9A39FD0C8469BF01E35F0F81866C4D318` |
| `ghouls-grip-print-mechanism-pla.3mf` | `B2DC8339731FE2ADEC21DE571B7339266F22B141052C802FAA4CC5163AACB8ED` |
| `ghouls-grip-print-mechanism-supported-platform-pla.3mf` | `D9C1459963C71730A2CB1AA2A494CAF6EB2F6270A83E1EEA7D72EAB3AD547EFC` |
| `ghouls-grip-print-mechanism-supported-latch-slider-pla.3mf` | `CC08F514D25021E0D2B0297A93488A1DF09B393D358DB254B6AA677D8E456C99` |
| `ghouls-grip-print-mechanism-supported-latch-bracket-pla.3mf` | `33D61C09E187F3587D262CB2534B3CCAD2E79B251DF0FF2837CBA64D721CC4F0` |
| `ghouls-grip-print-mechanism-supported-crank-pla.3mf` | `8FC5BF327B9D8F5C16D25B701D8DE5A9E678031585E424D86824494D01C66F88` |
| `ghouls-grip-print-mechanism-supported-band-anchor-pla.3mf` | `F8FA051699893098C64DE25EF855109D0792BBB5F5EBAD1A6B984526A5280F64` |
| `ghouls-grip-print-accent-pla.3mf` | `8D7A1CEE7341121A0E870F09C265A60C45B481FE153B6A2F2D4D35114560D288` |
| `ghouls-grip-print-fingers-pla.3mf` | `655BB1AA9837B869F08CF917B16190731A77646374354223E3DC159E0A736094` |

## Verbleibende physische Risiken

- Ein erfolgreicher Slice beweist keine reale Lebensdauer der 0,8-mm-PLA-
  Filmscharniere.
- Gummibandvorspannung, Seilspiel und Rastkraft müssen mit einem niedrigen
  Vorspannungs-Testaufbau abgestimmt werden.
- Gedruckte Pivot-Pins bleiben Verschleißteile; M3-Schrauben sind für die vier
  hoch belasteten Scherengelenke vorzuziehen.
- Vor dem Komplettdruck bleiben Arm-/Pin-/Passungscoupon und ein einzelner
  Finger-Testdruck verpflichtend.
