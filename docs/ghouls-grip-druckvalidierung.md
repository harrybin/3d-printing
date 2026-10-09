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
| `ghouls-grip-print-black-pla.3mf`, Platte 1 | Erleichterte, außen geschlossene Schatulle | 490 | 282,25 g | 10 h 19 min 36 s | Baum, nur kritische Bereiche | [PNG](images/ghouls-grip-slices/ghouls-grip-print-black-pla-plate_1.png) |
| `ghouls-grip-print-black-pla.3mf`, Platte 2 | Gerippter Deckel mit kollisionsfreier U-Führung | 137 | 175,91 g | 8 h 49 min 47 s | Baum, nur kritische Bereiche | [PNG](images/ghouls-grip-slices/ghouls-grip-print-black-pla-plate_2.png) |
| `ghouls-grip-print-bone-pla.3mf` | Geneigter Unterarm, nach oben gerollte Handfläche, Sehnenführung | 284 | 52,30 g | 3 h 29 min 54 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-bone-pla.png) |
| `ghouls-grip-print-mechanism-pla.3mf` | 4 Scherenarme, Schlitten, 8 kleine und 4 große Pins | 170 | 50,10 g | 2 h 30 min 41 s | nein | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-pla.png) |
| `ghouls-grip-print-mechanism-supported-platform-pla.3mf` | Hubjoch | 344 | 46,21 g | 1 h 58 min 44 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-platform-pla.png) |
| `ghouls-grip-print-mechanism-supported-latch-slider-pla.3mf` | Interner Rastschieber | 344 | 8,94 g | 32 min 29 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-latch-slider-pla.png) |
| `ghouls-grip-print-mechanism-supported-latch-bracket-pla.3mf` | Interne Rastschieberführung mit Montagepads | 170 | 18,93 g | 35 min 22 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-latch-bracket-pla.png) |
| `ghouls-grip-print-mechanism-supported-crank-pla.3mf` | Interne Spule und abnehmbarer Schlüssel | 165 | 5,73 g | 22 min 31 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-crank-pla.png) |
| `ghouls-grip-print-mechanism-supported-band-anchor-pla.3mf` | Bandanker | 143 | 12,25 g | 39 min 56 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-band-anchor-pla.png) |
| `ghouls-grip-print-accent-pla.3mf` | Flacher Totenkopf-Auslöser mit kurzem Stößel | 107 | 14,32 g | 51 min 09 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-accent-pla.png) |
| `ghouls-grip-print-fingers-pla.3mf` | Daumen und vier Finger | 57 | 11,78 g | 1 h 21 min 30 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-fingers-pla.png) |
| **Gesamt** | 34 physische Druckobjekte | - | **678,72 g** | **31 h 31 min 39 s** | - | - |

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
| `ghouls-grip-master.3mf` | `5FE6DB2EB5B712ADEC53770A1BF4AF0F4C789D7E03E5C75B3E7E6CDED3E113B0` |
| `ghouls-grip-master-retracted.3mf` | `E7C7E98EE6351FD808D967C29DCF07B7813FD4BC2C25233C6A84D313AE553FA6` |
| `ghouls-grip-print-black-pla.3mf` | `BE2E273F3520B34C0D2247DD308E1CE53F3BE5966EB0632FC3D04189B3592221` |
| `ghouls-grip-print-bone-pla.3mf` | `C7268FE6F72E2A549A9FDD444EA8DCEBC249B015D768621F31F1C57E76D16E95` |
| `ghouls-grip-print-mechanism-pla.3mf` | `50EBBF38A4470F9F9CA583DD29826F9E43E1CA0915D2B5A03A0C414B8757C5A5` |
| `ghouls-grip-print-mechanism-supported-platform-pla.3mf` | `D54A7CA767240FF3290792242B192142D7ADA387D086B7950F1CA0BE0DAD21AA` |
| `ghouls-grip-print-mechanism-supported-latch-slider-pla.3mf` | `7150F8D2DDE6C49FDAA50E7A9F2C5D41FDFA6C19871BE5F87773814C792424EA` |
| `ghouls-grip-print-mechanism-supported-latch-bracket-pla.3mf` | `C4308D4AAED3120D6D142AFB6F5C01BCD50EC7FEAF8F0B542C8CC3F62C68BAE9` |
| `ghouls-grip-print-mechanism-supported-crank-pla.3mf` | `71171E55333DC5C096A4E3C4E834372C12B0B38B970FB47923789E8805017085` |
| `ghouls-grip-print-mechanism-supported-band-anchor-pla.3mf` | `91497F5144204B0831D239AB6CC7CFAB00C2E456C645E2A8C68A54211F2B6014` |
| `ghouls-grip-print-accent-pla.3mf` | `1DD9C6D8E5ED42EFC078B446B5B6F2A6EBCC22CB7363BA30E2B22AE1D7548CA3` |
| `ghouls-grip-print-fingers-pla.3mf` | `71EE5AF3CC9B853D077FDCABFD01C30DFE9A50D8E98274B671EB970CE794F6F1` |

## Verbleibende physische Risiken

- Ein erfolgreicher Slice beweist keine reale Lebensdauer der 0,8-mm-PLA-
  Filmscharniere.
- Gummibandvorspannung, Seilspiel und Rastkraft müssen mit einem niedrigen
  Vorspannungs-Testaufbau abgestimmt werden.
- Gedruckte Pivot-Pins bleiben Verschleißteile; M3-Schrauben sind für die vier
  hoch belasteten Scherengelenke vorzuziehen.
- Vor dem Komplettdruck bleiben Arm-/Pin-/Passungscoupon und ein einzelner
  Finger-Testdruck verpflichtend.
