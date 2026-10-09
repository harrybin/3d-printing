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

## Platten und Ergebnisse

| Druckprojekt / Platte | Enthaltene Objekte | Schichten | PLA | Zeit | Stützen | Vorschau |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `ghouls-grip-print-black-pla.3mf`, Platte 1 | Schatulle ohne offene Klinkenfenster | 490 | 399,34 g | 15 h 30 min 42 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-black-pla-plate_1.png) |
| `ghouls-grip-print-black-pla.3mf`, Platte 2 | Deckel mit kollisionsfreier U-Führung | 137 | 212,99 g | 11 h 59 min 40 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-black-pla-plate_2.png) |
| `ghouls-grip-print-bone-pla.3mf` | Geneigter Unterarm, nach oben gerollte Handfläche, Sehnenführung | 284 | 52,30 g | 3 h 29 min 54 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-bone-pla.png) |
| `ghouls-grip-print-mechanism-pla.3mf` | 4 Scherenarme, Schlitten, 8 kleine und 4 große Pins | 170 | 50,10 g | 2 h 30 min 41 s | nein | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-pla.png) |
| `ghouls-grip-print-mechanism-supported-platform-pla.3mf` | Hubjoch | 344 | 46,21 g | 1 h 58 min 44 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-platform-pla.png) |
| `ghouls-grip-print-mechanism-supported-latch-slider-pla.3mf` | Interner Rastschieber | 344 | 8,94 g | 32 min 29 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-latch-slider-pla.png) |
| `ghouls-grip-print-mechanism-supported-latch-bracket-pla.3mf` | Interne Rastschieberführung mit Montagepads | 170 | 18,93 g | 35 min 22 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-latch-bracket-pla.png) |
| `ghouls-grip-print-mechanism-supported-crank-pla.3mf` | Interne Spule und abnehmbarer Schlüssel | 165 | 5,73 g | 22 min 31 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-crank-pla.png) |
| `ghouls-grip-print-mechanism-supported-band-anchor-pla.3mf` | Bandanker | 143 | 12,25 g | 39 min 56 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-band-anchor-pla.png) |
| `ghouls-grip-print-accent-pla.3mf` | Flacher Totenkopf-Auslöser mit kurzem Stößel | 107 | 14,32 g | 51 min 09 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-accent-pla.png) |
| `ghouls-grip-print-fingers-pla.3mf` | Daumen und vier Finger | 57 | 11,78 g | 1 h 21 min 30 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-fingers-pla.png) |
| **Gesamt** | 34 physische Druckobjekte | - | **832,89 g** | **39 h 52 min 38 s** | - | - |

Nach der Deckelkorrektur wurden Deckel, Knochenplatte und Fingerplatte in
dieser Reihenfolge erneut mit demselben Profil gesliced. Die globalen
3MF-Transformationen ergeben zwischen allen drei Knochenobjekten sowie allen
fünf Fingerobjekten jeweils **0,000 mm³** Überlappung. Das einfache STL/3MF-
Canvas ignoriert diese Objekttransformationen und zeigt die Teile deshalb
fälschlich übereinander; maßgeblich sind OrcaSlicer und die G-Code-Vorschauen.

Die G-Code-Pfad-Vorschauen werden von `scripts/render_gcode_preview.py` direkt
aus den erfolgreichen OrcaSlicer-Ausgaben gerendert. Rosa markiert höhere,
blau niedrigere Extrusionspfade; die Bilder sind kein Ersatz für die
interaktive Layeransicht, belegen aber Platte, Bettlage und erzeugte Toolpaths.

## Behobene Slice-Probleme

1. Ohne Stützen meldete OrcaSlicer schwebende Bereiche an Fingern, Handteilen,
   Totenkopf, Deckel und Gehäuse. Bettgebundene Stützen beseitigen diese
   Warnungen.
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
| `ghouls-grip-master.3mf` | `8A50229B2352988EECDF48DE19519EE05F6B60DECAE8E6BE8709FBBC12717A11` |
| `ghouls-grip-master-retracted.3mf` | `68E702CEED7F9F2D4E8A588115EC688EB3803C12946004B486D7940A91C4FFA0` |
| `ghouls-grip-print-black-pla.3mf` | `DF94447E6A3320A0BD59780CAEBEAF8E91CFE611945CF76E44603318D546D29F` |
| `ghouls-grip-print-bone-pla.3mf` | `5FCA18C75F0AD4C6F872998D73D3DF708FDC38DE14B863C34F7241B4B880F7BA` |
| `ghouls-grip-print-mechanism-pla.3mf` | `882EBFED4411A64483F290021836FCB9B80E8A714DE538AA0597F1A2A951013C` |
| `ghouls-grip-print-mechanism-supported-platform-pla.3mf` | `E56B5255A1F6569391CB2709A731B604D4C39041993EB6FDE2DEC97E8271D780` |
| `ghouls-grip-print-mechanism-supported-latch-slider-pla.3mf` | `99B8FA7ED80B5D2D5B83E2060A96007906EA179FC2DE4DEBC895AA23D5CD97B6` |
| `ghouls-grip-print-mechanism-supported-latch-bracket-pla.3mf` | `1DA56AE52BF2F34F9FCE9979A6BA498B45BB4BF9B616E55E3D66CE1CBD5F3096` |
| `ghouls-grip-print-mechanism-supported-crank-pla.3mf` | `C6A37D7B30C35D0E1B4BF63B9BDF1C5AF7BB14336821B551CA4BF399FCB94FB5` |
| `ghouls-grip-print-mechanism-supported-band-anchor-pla.3mf` | `800406A48C83CE7C2BBBF0C7F7A246DA22998F8B10C09D83A22AEDED6AE60576` |
| `ghouls-grip-print-accent-pla.3mf` | `8BB52D6997B9B2ABDA10D7CAA2A233DB7E0F7CF17944B72B93C142AE06050CA6` |
| `ghouls-grip-print-fingers-pla.3mf` | `365359FCBAAE44BA686AF98DD0C06D2C92298FA2E51574FB4DD2C9D274F81AB9` |

## Verbleibende physische Risiken

- Ein erfolgreicher Slice beweist keine reale Lebensdauer der 0,8-mm-PLA-
  Filmscharniere.
- Gummibandvorspannung, Seilspiel und Rastkraft müssen mit einem niedrigen
  Vorspannungs-Testaufbau abgestimmt werden.
- Gedruckte Pivot-Pins bleiben Verschleißteile; M3-Schrauben sind für die vier
  hoch belasteten Scherengelenke vorzuziehen.
- Vor dem Komplettdruck bleiben Arm-/Pin-/Passungscoupon und ein einzelner
  Finger-Testdruck verpflichtend.
