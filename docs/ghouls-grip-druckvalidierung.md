# The Ghoul's Grip – OrcaSlicer-Druckvalidierung

Status: **VERIFIED**  
Validiert: 2026-10-08  
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
| `ghouls-grip-print-black-pla.3mf`, Platte 1 | Deckel | 137 | 229,27 g | 12 h 24 min 01 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-black-pla-plate_1.png) |
| `ghouls-grip-print-black-pla.3mf`, Platte 2 | Schatulle ohne offene Klinkenfenster | 490 | 400,39 g | 15 h 34 min 35 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-black-pla-plate_2.png) |
| `ghouls-grip-print-bone-pla.3mf` | Unterarm, Handfläche, Sehnenführung | 262 | 51,24 g | 3 h 26 min 50 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-bone-pla.png) |
| `ghouls-grip-print-mechanism-pla.3mf` | 4 Scherenarme, Schlitten, 8 kleine und 4 große Pins | 170 | 50,10 g | 2 h 30 min 41 s | nein | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-pla.png) |
| `ghouls-grip-print-mechanism-supported-platform-pla.3mf` | Hubjoch | 344 | 46,21 g | 1 h 58 min 44 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-platform-pla.png) |
| `ghouls-grip-print-mechanism-supported-latch-slider-pla.3mf` | Interner Rastschieber | 344 | 8,94 g | 32 min 29 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-latch-slider-pla.png) |
| `ghouls-grip-print-mechanism-supported-latch-bracket-pla.3mf` | Interne Rastschieberführung mit Montagepads | 170 | 18,93 g | 35 min 22 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-latch-bracket-pla.png) |
| `ghouls-grip-print-mechanism-supported-crank-pla.3mf` | Interne Spule und abnehmbarer Schlüssel | 165 | 5,73 g | 22 min 31 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-crank-pla.png) |
| `ghouls-grip-print-mechanism-supported-band-anchor-pla.3mf` | Bandanker | 143 | 12,25 g | 39 min 56 s | normal/snug | [PNG](images/ghouls-grip-slices/ghouls-grip-print-mechanism-supported-band-anchor-pla.png) |
| `ghouls-grip-print-accent-pla.3mf` | Flacher Totenkopf-Auslöser mit kurzem Stößel | 107 | 14,32 g | 51 min 09 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-accent-pla.png) |
| `ghouls-grip-print-fingers-pla.3mf` | Daumen und vier Finger | 57 | 12,01 g | 1 h 22 min 55 s | Baum | [PNG](images/ghouls-grip-slices/ghouls-grip-print-fingers-pla.png) |
| **Gesamt** | 34 physische Druckobjekte | - | **849,39 g** | **40 h 19 min 13 s** | - | - |

Nach der Fingerketten-Korrektur wurde
`ghouls-grip-print-fingers-pla.3mf` erneut mit demselben Profil gesliced:
57 Layer, 12,01 g, 1 h 22 min 55 s, Tree-Support und keine unaufgelösten
Toolpath-, Druckbett- oder Leerlagenfehler.

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

Alle Dateien wurden am 2026-10-08 gegen den hier beschriebenen Slice-Stand
regeneriert. SHA-256:

| Datei | SHA-256 |
| --- | --- |
| `ghouls-grip-master.3mf` | `5DD2BCCE66AEAE9E5FD8E173FE2AA39F52ED80DE083D2BC6213231DAEAE7F01A` |
| `ghouls-grip-master-retracted.3mf` | `A6804EC2EAFF13375DC02BBD147FE497F29468FD89ACC60348F6284D7A63E2EA` |
| `ghouls-grip-print-black-pla.3mf` | `2A365BC931D8E981497A56E4055E831A74231D5E0E058E32B343B13035D6CA58` |
| `ghouls-grip-print-bone-pla.3mf` | `9A4DAFF54DB048E5FF0A785F35E3DBD2DDB00EF4446D111A6C32B8E54307E495` |
| `ghouls-grip-print-mechanism-pla.3mf` | `C321406596B38EEAF188998B81A0A22731C32D59681EAFF6D25A4A61D0E3D8A4` |
| `ghouls-grip-print-mechanism-supported-platform-pla.3mf` | `7792C24D2C199BBA147B9AC8E877DCC2B2C76F702ACBCCDC19107B9713E16564` |
| `ghouls-grip-print-mechanism-supported-latch-slider-pla.3mf` | `1FAD52C408458E02CAEEF98F16F18BB30D780C3B6CCE9CBF5A913E794735CEC9` |
| `ghouls-grip-print-mechanism-supported-latch-bracket-pla.3mf` | `6C5447EA87630D448D82CCBA30A16B16AA316F7B74E7573377417FB566709AD3` |
| `ghouls-grip-print-mechanism-supported-crank-pla.3mf` | `8611B79C20E0FBDD4D1184DDEBE6A4F165C2961673E277AD8426DD7D46BE6E6E` |
| `ghouls-grip-print-mechanism-supported-band-anchor-pla.3mf` | `15FFBAF26C6F0D69EAE05EA664A851B6B1DE8B9BAE3E9EF00941FD3810654187` |
| `ghouls-grip-print-accent-pla.3mf` | `6AA0462B7B61D67986AEB8D00E44C5257D1847926DCFA8D2002AB7DF3BFE1AC3` |
| `ghouls-grip-print-fingers-pla.3mf` | `DFB7A525F9055D3BB3F75753ACECB6791C7FE4264BAB076F15E3257F75469F67` |

## Verbleibende physische Risiken

- Ein erfolgreicher Slice beweist keine reale Lebensdauer der 0,8-mm-PLA-
  Filmscharniere.
- Gummibandvorspannung, Seilspiel und Rastkraft müssen mit einem niedrigen
  Vorspannungs-Testaufbau abgestimmt werden.
- Gedruckte Pivot-Pins bleiben Verschleißteile; M3-Schrauben sind für die vier
  hoch belasteten Scherengelenke vorzuziehen.
- Vor dem Komplettdruck bleiben Arm-/Pin-/Passungscoupon und ein einzelner
  Finger-Testdruck verpflichtend.
