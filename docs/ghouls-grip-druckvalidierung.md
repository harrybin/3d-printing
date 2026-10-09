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
| `ghouls-grip-print-black-pla.3mf`, Platte 1 | Erleichterte Schatulle ohne offene Klinkenfenster | 490 | 281,28 g | 10 h 18 min 29 s | Baum, nur kritische Bereiche | [PNG](images/ghouls-grip-slices/ghouls-grip-print-black-pla-plate_1.png) |
| `ghouls-grip-print-black-pla.3mf`, Platte 2 | Gerippter Deckel mit kollisionsfreier U-Führung | 137 | 175,91 g | 8 h 49 min 44 s | Baum, nur kritische Bereiche | [PNG](images/ghouls-grip-slices/ghouls-grip-print-black-pla-plate_2.png) |
| `ghouls-grip-print-bone-pla.3mf` | Geneigter Unterarm, nach oben gerollte Handfläche, Sehnenführung | 284 | 52,30 g | 3 h 29 min 54 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-bone-pla.png) |
| `ghouls-grip-print-mechanism-pla.3mf` | 4 Scherenarme, Schlitten, 8 kleine und 4 große Pins | 170 | 50,10 g | 2 h 30 min 41 s | nein | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-pla.png) |
| `ghouls-grip-print-mechanism-supported-platform-pla.3mf` | Hubjoch | 344 | 46,21 g | 1 h 58 min 44 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-platform-pla.png) |
| `ghouls-grip-print-mechanism-supported-latch-slider-pla.3mf` | Interner Rastschieber | 344 | 8,94 g | 32 min 29 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-latch-slider-pla.png) |
| `ghouls-grip-print-mechanism-supported-latch-bracket-pla.3mf` | Interne Rastschieberführung mit Montagepads | 170 | 18,93 g | 35 min 22 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-latch-bracket-pla.png) |
| `ghouls-grip-print-mechanism-supported-crank-pla.3mf` | Interne Spule und abnehmbarer Schlüssel | 165 | 5,73 g | 22 min 31 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-crank-pla.png) |
| `ghouls-grip-print-mechanism-supported-band-anchor-pla.3mf` | Bandanker | 143 | 12,25 g | 39 min 56 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-band-anchor-pla.png) |
| `ghouls-grip-print-accent-pla.3mf` | Flacher Totenkopf-Auslöser mit kurzem Stößel | 107 | 14,32 g | 51 min 09 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-accent-pla.png) |
| `ghouls-grip-print-fingers-pla.3mf` | Daumen und vier Finger | 57 | 11,78 g | 1 h 21 min 30 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-fingers-pla.png) |
| **Gesamt** | 34 physische Druckobjekte | - | **677,75 g** | **31 h 30 min 29 s** | - | - |

Gegenüber den vom Benutzer gemessenen Ausgangswerten für Schatulle und Deckel
(400,39 g + 229,27 g = 629,66 g) benötigt das schwarze Projekt jetzt
**457,19 g**. Das spart **172,47 g beziehungsweise 27,4 %**. Die kombinierte
Druckzeit fällt von 27 h 58 min auf 19 h 08 min.

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
2. Die gestützten Mechanikteile erzeugten auf einer gemeinsamen Platte
   überlappende Stütz-/G-Code-Pfade. Sie wurden auf fünf Einzelprojekte
   aufgeteilt. Spule und abnehmbarer Schlüssel teilen sich eine Platte mit
   30 mm Objektabstand und 20 mm Bettrand; danach bestanden alle
   Kollisions- und Druckbettprüfungen.
3. Die supportfreie Mechanik bleibt zusammen auf einer Platte, damit Arme,
   Schlitten und vollständige Pin-Stückzahlen gemeinsam geprüft werden.

## Dateibelege

Alle Dateien wurden am 2026-10-09 gegen den hier beschriebenen Slice-Stand
regeneriert. SHA-256:

| Datei | SHA-256 |
| --- | --- |
| `ghouls-grip-master.3mf` | `BB966E17772DC53911AAE3403FF04A8C43A69DFD1F58351BB53AB47E1058586C` |
| `ghouls-grip-master-retracted.3mf` | `03AC0DF982DC8CC92844EF659E924CF806EDD46E317506232785CA9DB6CDD15F` |
| `ghouls-grip-print-black-pla.3mf` | `24EE4A9E6501ACB4240925E4C90B7F2E4FE52FDAF98ECA4597FC70929B79E717` |
| `ghouls-grip-print-bone-pla.3mf` | `49C20C184918226AC14F26C3D20855D48476408A3E140911DC6D7178BD5AAD13` |
| `ghouls-grip-print-mechanism-pla.3mf` | `50D9677DC39F7BB159ECE995BCA409D39BA913649D2CAA16091CCC5379A0BA12` |
| `ghouls-grip-print-mechanism-supported-platform-pla.3mf` | `65E4C1B15E56C299C4A7DE01B392C1318EDE6CD33F7CDC8F8D729F3A4A6A94A1` |
| `ghouls-grip-print-mechanism-supported-latch-slider-pla.3mf` | `30B76BFCDC7F39980AE6E3E05DE1122C46EB175973C37AB2E4714DA94D028C89` |
| `ghouls-grip-print-mechanism-supported-latch-bracket-pla.3mf` | `C7A53884E4836CF7C2285BFD805E02E2C9897767EA9CC4926EE8CDBE6CFD5225` |
| `ghouls-grip-print-mechanism-supported-crank-pla.3mf` | `2F1FC89DFD0EA9DB1B2572C37C5BEB60E5F1F5B675A98B9106A5C0638E35FAEB` |
| `ghouls-grip-print-mechanism-supported-band-anchor-pla.3mf` | `8DD25270ADF81341B9E4FDC001AF247DAE1E226FEB8BA662C2292D8B89D46350` |
| `ghouls-grip-print-accent-pla.3mf` | `DB6D378287E1D885742E0BF6CF835D92DBA689283F746F62FB85C098B8F81CB6` |
| `ghouls-grip-print-fingers-pla.3mf` | `5DEA03B2B4B2FA6A568EE787A4D457BB75FFDC183640A9DCBDEE2D250D1F8560` |

## Verbleibende physische Risiken

- Ein erfolgreicher Slice beweist keine reale Lebensdauer der 0,8-mm-PLA-
  Filmscharniere.
- Gummibandvorspannung, Seilspiel und Rastkraft müssen mit einem niedrigen
  Vorspannungs-Testaufbau abgestimmt werden.
- Gedruckte Pivot-Pins bleiben Verschleißteile; M3-Schrauben sind für die vier
  hoch belasteten Scherengelenke vorzuziehen.
- Vor dem Komplettdruck bleiben Arm-/Pin-/Passungscoupon und ein einzelner
  Finger-Testdruck verpflichtend.
