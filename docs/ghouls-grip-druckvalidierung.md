# The Ghoul's Grip – OrcaSlicer-Druckvalidierung

Slice-Ergebnis: **erfolgreich** mit OrcaSlicer CLI 2.4.2; Profilkonformität: **nicht verifiziert**.

Die korrigierte Druckdatei hat fünf Plates und 37 Objekte. Der frische Slice
wurde am 2026-10-12 aus dem aktualisierten `models/ghouls-grip-print.3mf`
erzeugt. Danach wurden nur die neutralen Druckmetadaten aus den Slice-G-Codes
ergänzt. SHA-256 der finalen Druckdatei:
`BF705DC56C1E364254979260E01617842FA7DFE70EF7E3873FC15B4C0D72D5A7`.
Die sieben Knochenobjekte auf Platte 2 wurden ausschließlich in XY neu
angeordnet; Mesh-Payloads, Rotation, Z-Höhe, Einstellungen und übrige
Plattenbelegungen bleiben unverändert.

Weitere finale SHA-256:

| Datei | SHA-256 |
| --- | --- |
| `models/ghouls-grip-view.3mf` | `CB85E2165306EC2D6FD7822CD920C051E1BF797FA82047FFE94D0A2D02DB0D05` |
| `models/ghouls-grip-preview.stl` | `9E9BE5D9588FD4CBFC6F4070ABD03F1C5582CCB854913564BF42C2616860992F` |

Schatulle: 76.418 Facetten, 209 × 130,5 × 98 mm, 198.615,666 mm³,
ein geschlossener Einzelkörper, konsistente Normalen, keine degenerierten
Dreiecke. Das komplette ASCII-STL ist bewusst eine montierte
35-Körper-Vorschau, kein Drucklayout; 37 Druckobjekte inklusive Reservepins
sind im fünfplattigen Print-Projekt.
In dieser Session ist kein STL-Canvas deklariert; die exakte Datei wurde
stattdessen gelesen, validiert und als Farb-3MF-Bild gerendert, ohne UI-Workaround.

Diese Bodenlagerreparatur ersetzt ausschließlich die Schatullen-Geometrie;
die übrigen **36 Mesh-Payloads bleiben byteidentisch** zur übernommenen
Nutzerdatei (`HEAD`). Alle 37 Build-Transforms, Objekt-Overrides, fünf
Plattengruppen, Farben, Materialien und `project_settings.config` bleiben
erhalten. Die beiden Transferzahnräder der vorherigen Wandkorrektur sind
weiterhin Bestandteil der vollständigen Stückliste.
Die exakte finale Druckdatei wurde unabhängig geladen: 37 geschlossene,
orientierungskonsistente Einzelkörper, null degenerierte Dreiecke, alle innerhalb
ihres 250-mm-Betts, Z-Bettkontakt mit 0,01-mm-Rundtoleranz; größtes Bauteil-/Bauteil-Schnittvolumen
auf einer Druckplatte 0,000 mm³. Auch die Arm-/Bodenlagerpaare der montierten
Mechanik bestehen jetzt den 61-Zustands-Nachweis; das ist keine Lastfreigabe.
Prüfartefakt: `build/ghoul-floor-bearing-delivery.json`.

![Aktuelle Fünf-Platten-Übersicht](images/ghouls-grip-print-preview.png)

## Sichtbare Stützstrukturen

**Orange zeigt tatsächlich extrudierte Support- und Support-Interface-Bahnen**
aus den fünf frischen G-Codes; transparentes Grau zeigt die zugehörigen
Bauteile. Es ist ein G-Code-Bahnrender, kein OrcaSlicer-UI-Screenshot.

![Alle fünf Plates mit tatsächlichen Stützbahnen](images/ghouls-grip-print-support-overview.png)

Einzelansichten: [Platte 1 – Schwarz](images/ghouls-grip-print-plate-1-supports.png),
[Platte 2 – Knochenbeige](images/ghouls-grip-print-plate-2-supports.png),
[Platte 3 – Naturweiß](images/ghouls-grip-print-plate-3-supports.png),
[Platte 4 – Naturweiß](images/ghouls-grip-print-plate-4-supports.png),
[Platte 5 – Grau](images/ghouls-grip-print-plate-5-supports.png).

Die Screenshots basieren exakt auf der aktuellen Nutzerdatei und den am
2026-10-12 neu erzeugten G-Codes in `build/ghoul-final-slices/print/`.
Reproduktion:
`.\.venv\Scripts\python.exe scripts\render_ghouls_grip_print_projects.py build\ghoul-final-slices\print --project models\ghouls-grip-print.3mf`
und
`.\.venv\Scripts\python.exe scripts\render_ghouls_grip_supports.py build\ghoul-final-slices\print --project models\ghouls-grip-print.3mf`.
Die Supportpfade bleiben eine separate Bildvorschau und werden nicht in die
3D-Modellgeometrie eingeblendet. Canvas und Web-UI bieten jetzt zusätzlich
direkte Buttons für die einzelnen Plattenbilder; ein Klick öffnet das Bild groß.
## Profilvertrag und tatsächliche Nutzereinstellungen

Das Druckprojekt wurde vom Nutzer in OrcaSlicer geändert. Die aktuellen
Einstellungen werden hier dokumentiert und nicht stillschweigend auf frühere
Vorgaben zurückgesetzt:

- Drucker: `Anycubic Kobra S1 0.4 nozzle`; Düse/Schichthöhe: 0,4 mm / 0,20 mm
- Ein separat benannter Prozessprofilname ist in der 3MF nicht gespeichert;
  die Prozesswerte sind in `Metadata/project_settings.config` eingebettet.
- Filamentprofil: `Anycubic PLA @Anycubic Kobra S1 0.4 nozzle` für vier PLA-Slots
- Im gespeicherten Projekt: Bett `High Temp Plate`, Naht `aligned`, Bügeln
  `no ironing`, global `enable_support=0`, globale Basiswerte 2 Wandlinien und
  15 % Infill.
- Bauteil-Overrides aktivieren Support (`enable_support=1`) für die betreffenden
  Objekte; alle fünf frischen G-Codes enthalten echte Supportbahnen, auch
  0,55 g auf Platte 4 für die vorhandenen Transferzahnräder.
- Support nur auf Druckplatte, globaler Typ `tree(auto)`; Objekt-Overrides
  verwenden teils `normal(auto)`.

Diese Datei weicht damit vom Projektstandard `Textured PEI Plate`, `seam=random`,
`ironing=top` und global aktiviertem Support ab. Der Slice war erfolgreich, aber
Profilkonformität und Druckbereitschaft sind **nicht verifiziert**. OrcaSlicer
CLI gab wiederholt die Diagnose `Not precalculated Placeable areas requested`
aus, erzeugte aber Exit-Code 0 und alle fünf G-Codes. Diese Meldung wurde nicht
im OrcaSlicer-GUI nachbewertet.

## Bodenlagerkorrektur, Reproduktion und Freigabegrenze

Die zentralen kollidierenden Bodenpfosten sind als kurze Doppelwangen um
die unveränderten Armhüllen neu aufgebaut. Der 12-mm-Kanal gibt 1 mm
Axialabstand; die 4-mm-Wangen haben 3 mm radiale Bohrungsstege und direkt
angebundene 9,2 × 4 mm Bodenwurzeln. Alle neuen Maße sind
Konstruktionsschätzungen/Default-Freiräume und brauchen einen PLA-Passungs-
und Lasttest, keine neu behaupteten Messwerte.
Die bestehenden 26-mm-Pins werden von der Kistenmitte eingeführt;
der Kopf des positiven Bodenpins ist im Ansichtsprojekt entsprechend
gespiegelt. Der Print-Pin und die komplette Stückliste bleiben unverändert.

Der ursprüngliche Wandcutter (14 × 12 × 24 mm bei X=-27, Y=58, Z=75)
ist entfernt. Der Folgejoch-Rack liegt 14,854 mm weiter innen; zwei gleiche
Transferzahnräder erhalten 1:1-Übersetzung, 7-mm-Hub und 108° Deckelbewegung.
Die neue Journalhalterung und die asymmetrische Haube schneiden weder Wand
noch mittleren Scharnierbock. Die Dach-/Wandproben zeigen durchgängiges Material.

Beim Print-Refresh verursachte reine Bounds-Zentrierung der höheren neuen Kurbel
einen Boden unter Z=0; OrcaSlicer 2.4.2 brach dabei mit Access Violation ab.
Der Export erhält jetzt die originale transformierte Bettkontakt-Ebene.
Historischer Befund der Wandkorrektur: Die 31 damals unbetroffenen Payloads
wurden nicht neu gerundet. Sowohl fünf einzelne
Platten-Slices als auch der abschließende `--slice=0`-Kontrolllauf waren danach
erfolgreich. Der **aktuelle finale** Kontrolllauf am 2026-10-12 mit
`scripts/slice_ghouls_grip.ps1` hat ebenfalls Exit-Code 0, fünf echte G-Codes
und keine Layout-/Profiländerung. Die Kopfzeile jedes frischen G-Codes
bestätigt OrcaSlicer 2.4.2. Die tatsächliche Installation wurde unter
`C:\Program Files\OrcaSlicer\orca-slicer.exe` gefunden;
`--help` endete mit Exit 0 ohne Konsolentext, daher wurden die bereits
funktionierenden Optionen des vorhandenen Slice-Skripts verwendet.
Die externen Mesh-Relationships sind ohne XML-Namenspräfix serialisiert, wie
Orcas Importer es erwartet.

| Befehl / Nachweis | Ergebnis |
| --- | --- |
| `.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_ghouls_grip*.py'` | 36 Tests bestanden; zusätzlich 244 individuelle Arm-/Kistenpaare, beidseitige Pin-Eingriffslängen, 24-mm-Pinmontage auch an allen drei exakten 3MF-Ansichtszuständen, Arm-Einsetzen, 0,4-mm-Reserve, Bodenwurzeln und 3-mm-Bohrungsstege, exakter Quell-/Printvergleich und byteidentische unbetroffene Payloads |
| `.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_ghouls_grip_print_refresh.py -v` | nach finaler Bettkontakt-Korrektur erneut bestanden; Originaltransforms, Overrides, Plate-Zuordnung, unveränderte Payloads und Idempotenz |
| `.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_slice_support_usage.py -v` | 3 Tests bestanden; M82/M83/G92 und Rückstellungen |
| `.\.venv\Scripts\python.exe scripts\verify_ghouls_grip_mechanics.py` | Gesamt-Nachweis PASS; 61 Scherenstellungen von 18° bis 78° inkl. 48°, alle vier individuellen Arm-/Kistenpaare jetzt hartes Fail-Gate bei >0,001 mm³; übrige geprüfte Paare 0 mm³; JSON in `build/ghoul-floor-bearing-verification.json` |
| `python scripts\arrange_ghouls_grip_bone_plate.py` | PASS: sieben Teile auf Platte 2 mit mindestens 6 mm Footprint-Abstand und mindestens 69 mm Bettrandabstand; nur XY-Translationen geändert |
| `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\slice_ghouls_grip.ps1` | Exit 0, fünf G-Codes mit OrcaSlicer 2.4.2; aktueller Bone-Plate-Preview unter `docs/images/ghouls-grip-slice-plate-2.png` |
| `python scripts\update_ghouls_grip_slice_metadata.py build\ghoul-final-slices\print --project models\ghouls-grip-print.3mf` | frische Slice-Kennzahlen gespeichert; Status weiter `not-verified`, da die dokumentierten Profilabweichungen bestehen |
| `python scripts\render_ghouls_grip_print_projects.py build\ghoul-final-slices\print --project models\ghouls-grip-print.3mf` | PASS: finales 5-Platten-Projektpreview regeneriert |
| `python scripts\render_ghouls_grip_supports.py build\ghoul-final-slices\print --project models\ghouls-grip-print.3mf` | PASS: Supportbilder aus den fünf tatsächlichen G-Codes gerendert |
| `.\.venv\Scripts\python.exe scripts\render_3mf_previews.py models\ghouls-grip-view.3mf models\ghouls-grip-print.3mf` | beide finalen Standard-Sidecars aus den exakten 3MFs regeneriert |
| Renderbefehle oben, `scripts\render_ghouls_grip_wall.py`, `scripts\render_ghouls_grip_floor_bearings.py` | fünf G-Code-Support-Sidecars, Supportübersicht, Wanddetail und exaktes Bodenlagerdetail (Kiste transparent zur Sichtbarkeit) |
| `.\.venv\Scripts\python.exe scripts\mesh_tool.py validate models\ghouls-grip-preview.stl --allow-multibody` | PASS: 254.492 Facetten, 35 absichtlich getrennte montierte Körper, geschlossen/orientiert, null degenerierte Dreiecke; Zentrierwarnung der nicht druckbaren Assembly-Vorschau, nicht verschoben |

**Die dokumentierte Arm-/Bodenlagerkollision ist beseitigt:** Baseline
496,131 / 519,274 / 554,635 mm³ bei 18° / 48° / 78°; aktuell
0,000 mm³ bei drei Nachkommastellen in allen 61 Zuständen.
Maximaler numerischer Rest je Einzelarm: 0,000020464 mm³ an der
tangentialen Bodenberührung, unter 0,001 mm³ Boolean-Toleranz.
Das ist ausdrücklich kein mathematisch exakt nuller Floating-Point-Wert.
Alle anderen im Vollnachweis geprüften Paare sind 0 mm³ und die
Wandfüllung bleibt 100 %. Einzelpaarvolumina stehen in der
[Mechanik-Verifikation](ghouls-grip-mechanik-verifikation.md).
Weiterhin keine physische Druck-/Lastfreigabe: PLA-Passung,
Supportentfernung aus kleinen Querbohrungen, Axialwanderung der bisherigen
unverriegelten Bodenpins, Journalspiel, Zahnprofile, Bodeneinleitung und
Dauerfestigkeit müssen getestet werden. Der Slice enthält echte Supports,
deren Entfernbarkeit im kleinen Lagerbereich noch physisch zu prüfen ist.

![Exakter Endstand, durchgehende Wand und innenliegender Deckelantrieb](images/ghouls-grip-continuous-wall.png)

![Exakte Doppelwangen und unveränderte Arme, Kiste transparent](images/ghouls-grip-floor-bearings.png)

## Ergebnisse des aktuellen Slices

| Plate | Inhalt | Schichten | Filament | davon Stützen | Zeit | Ansicht |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 – Schwarz | Schatulle und Deckel (2) | 649 | 338,28 g | 7,16 g (2,1 %) | 12 h 10 min 43 s | [Supportbild](images/ghouls-grip-print-plate-1-supports.png) |
| 2 – Knochenbeige | Unterarm, Handfläche und Finger (7) | 482 | 43,85 g | 6,25 g (14,3 %) | 3 h 04 min 39 s | [Supportbild](images/ghouls-grip-print-plate-2-supports.png) |
| 3 – Naturweiß | Mechanik-Hauptteile (11) | 492 | 112,23 g | 12,78 g (11,4 %) | 4 h 17 min 14 s | [Supportbild](images/ghouls-grip-print-plate-3-supports.png) |
| 4 – Naturweiß | Zahnräder und Verbinder (16) | 424 | 10,68 g | 0,55 g (5,1 %) | 1 h 01 min 28 s | [Supportbild](images/ghouls-grip-print-plate-4-supports.png) |
| 5 – Grau | Totenkopf-Auslöser (1) | 135 | 24,05 g | 3,40 g (14,1 %) | 1 h 11 min 05 s | [Supportbild](images/ghouls-grip-print-plate-5-supports.png) |
| **Gesamt** | **37 Druckobjekte / 5 Plates** | – | **529,09 g** | **30,15 g (5,7 %)** | **21 h 45 min 09 s** | [Übersicht](images/ghouls-grip-print-support-overview.png) |

| Farbgruppe | Zeit | Masse | Stützmaterial | Länge | Volumen | Plates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Schwarz | 43.843 s | 338,28 g | 7,16 g | 113.419,56 mm | 272.810 mm³ | 1 |
| Knochenbeige | 11.079 s | 43,85 g | 6,25 g | 14.702,67 mm | 35.360 mm³ | 1 |
| Naturweiß | 19.122 s | 122,91 g | 13,33 g | 41.208,25 mm | 99.110 mm³ | 2 |
| Grau | 4.265 s | 24,05 g | 3,40 g | 8.063,84 mm | 19.400 mm³ | 1 |
| **Gesamt** | **78.309 s** | **529,09 g** | **30,15 g** | **177.394,22 mm** | **426.680 mm³** | **5** |

Die Supportanteile werden aus positiven Extrusionen der Support-/Interface-
Bewegungen berechnet; `M82`, `M83` und `G92` werden berücksichtigt,
Extruder-only-Rückstellungen nicht als gedruckter Support gezählt.
Die vorherige absolute-E-Auswertung der relativen Orca-Extrusion war falsch.
Masse und Volumen werden mit dem jeweiligen Slice-Verhältnis umgerechnet:

| Plate | Supportlänge | Supportvolumen |
| --- | ---: | ---: |
| 1 | 2.400,96 mm | 5.775 mm³ |
| 2 | 2.096,62 mm | 5.042 mm³ |
| 3 | 4.285,33 mm | 10.307 mm³ |
| 4 | 184,55 mm | 444 mm³ |
| 5 | 1.141,08 mm | 2.745 mm³ |
| **Gesamt** | **10.108,44 mm** | **24.313 mm³** |

Die Summen und fünf Einzelergebnisse sind in `models/ghouls-grip-print.3mf`
als slicer-neutrale Metadaten gespeichert. Der Metadatenstatus bleibt
`not-verified`, bis Profilabweichungen und CLI-Diagnose geprüft sind.
G-Code-, Mesh- und Modellhashes sowie ausgeführte Befehle stehen zusammen
in `build/ghoul-floor-bearing-quality.json`; Vollsweep und Print-Prüfung in
`build/ghoul-floor-bearing-verification.json` und
`build/ghoul-floor-bearing-delivery.json`.
### Historische Orientierungsoptimierung (A/B-gemessen, nicht aktueller Slice)

Alle Druckorientierungen sind durch echte A/B-Slices belegt. Die Audit-Skripte
klonen dieselbe Projektvorlage und tauschen nur das Build-Item aus, sodass
ausschließlich die Orientierung variiert:

| Teil | Orientierung | Stütz-Extrusion | Alternativen |
| --- | --- | ---: | --- |
| Deckel | auf der Hinterkante stehend | **4.598,9 E** | aufrecht 20.336,1 · kopfüber 20.553,3 · Vorderkante 14.840,6 |
| Handfläche | auf dem Handgelenkschnitt stehend | **290,0 E** | wie gebaut 2.958,9 · gespiegelt 1.970,5 · seitlich 2.084,5–3.102,7 |
| Totenkopfknopf | Gesicht nach oben auf dem Wellenbund | **968,7 E** | wie gebaut 3.266,5 · seitlich 655,8–793,9 (verworfen: Stützen im Gesicht) |
| Unterarm | wie gebaut | **0,0 E** | alle gekippten Varianten 318,2–414,1 |

Skripte: `scripts/audit_lid_orientation.py`, `scripts/audit_part_orientation.py`,
`scripts/audit_chest_support.py`.

Historischer Vergleich vor dieser Wandkorrektur: Gegenüber dem damals
verifizierten Stand (528,22 g / 138,60 g Support) sank der
Stützbedarf um **83,21 g / 60,0 %** und die Gesamtmasse um 11,38 g. Die
gemessenen Orientierungswechsel tragen den Hauptteil der Einsparung; die
zusätzliche geschlossene Deckelhaube erhöht das schwarze Projekt nur um 1,59 g.
Gegenüber dem ursprünglichen 629,66-g-Entwurf beträgt die Materialeinsparung
**112,82 g / 17,9 %**, gegenüber der Vor-Leichtbau-Schatulle (455,96 g schwarz)
**125,00 g / 27,4 %**.

Die vorher dokumentierten Endwerte lagen bei 78.276 s, 528,75 g Filament und
29,79 g Support. Der nach der XY-Neuanordnung ausgeführte frische Slice liefert
die oben angegebenen aktuellen Werte. Geometrie und Orientierungen blieben
unverändert; die aktuellen Werte ersetzen die vorherigen Slicergebnisse.

## Stützen und Objekt-Overrides

- Schatulle/Deckel: 3 Wände, 10 % Gyroid, Baumstützen `tree(auto)` bettgebunden;
  analytischer maximaler Deckel-Brückenspalt 10,0 mm, Schatulle 6,0 mm.
- Mechanik: 5–6 Wände, modellierte Öffnungen, Rahmen, Rippen und Speichen;
  20–50 % Infill in den verbleibenden Hohlräumen. Arme und Pins bleiben durch
  Wandlinien praktisch massiv.
- Hand/Knochen: 4 Wände, 25 %; die Handfläche steht auf dem Handgelenkschnitt,
  wodurch Fingertaschen und Daumenballen senkrecht statt überhängend drucken.
- Finger: 2 Wände, 15 %, 30 mm/s Außenwand und reduzierte Beschleunigung für die 0,8-mm-PLA-Flexuren.
- Totenkopfknopf: 5 Wände, 40 %, Gesicht nach oben, damit keine Stützstruktur
  die skulptierte Fläche berührt.

## Beibehaltene Support-/Materialoptimierung und Wandkorrektur

- Der Deckel besitzt eine 2,4-mm-Deckhaut, offene Unterseiten-Träger,
  fünf gerippte Längstraversen und fünf kurze hintere Anschlagpads statt eines
  massiven, 193 mm breiten Querriegels. Er steht auf seiner Hinterkante: in
  dieser Lage ist weder die hohle Innendecke noch das skulptierte Kartuschen-
  relief ein großer Überhang (4.598,9 statt 20.336,1 Stütz-E).
- Der frühere durchgehende Servicekanal für Yoke und Deckelkurbel ist nach außen
  vollständig geschlossen. Eine lokale schwarze Haube besitzt eine 2,0-mm-
  Dachhaut, eine ausschließlich nach innen offene Montagekavität und eine
  gemessene Labyrinth-Freistellung am Scharnier. Im geschlossenen Zustand liegt
  jedes interne Mechanikteil unter dieser Deckelgeometrie; der vollständige
  18°–78°-Sweep ergibt für `lid_crank_lid`, `lid_yoke_lid`, `lid_chest` und
  die jeweiligen Brustkontakte jeweils **0,000 mm³**.
- In der aktuellen Nutzerdatei teilen sich Schatulle und stehender Deckel
  dieselbe schwarze Platte; beide passen nebeneinander innerhalb des 250-mm-Betts.
  Die vorherige Sechs-Platten-Aufteilung hatte dafür zwei separate Schwarz-Platten.
- Der Sockel und der obere Kranz der Schatulle wurden von horizontalen Stufen
  auf zwei geneigte, selbsttragende Kurse umgebaut. Die Pilasterkapitelle und
  die Unterseiten der Scharnierlager sind ebenfalls geneigt.
- Die dekorative Schatullenwand und der Boden sind 2,0 mm stark; die
  3,0-mm-Funktionsdatums an Schienen, Lagern und Führungen bleiben erhalten.
  Gerundete Außenkanten sowie vertiefte statt aufgesetzte Reliefs wirken
  organischer und vermeiden zusätzliche massive Zierkörper.
- Historischer Leichtbauschritt: Das Schatullen-Volumen sank von 295.062 auf 184.056 mm³
  (**−37,6 %**), das Deckelvolumen von 252.068 auf 124.903 mm³
  (**−50,5 %**). Zusammen sind das **−43,5 % Modellvolumen**.
- Acht überarbeitete Mechanikteile sanken durch offene Rahmen, Fenster und
  Speichen von 118.567 auf 82.649 mm³ (**−30,3 %**).
- Der Deckel bleibt ein einzelner watertight/manifold Körper:
  27.868 Facetten, 206 × 129,786 × 28,2 mm. Die aktuelle Schatulle hat
  199.297,757 mm³, der Deckel 134.466,876 mm³. Die lokale Schutzhaube ist nur
  2,6 mm höher als das skulptierte Kartuschenrelief und enthält keine
  getrennten oder eingeschlossenen Körper.
- Die Schienen- und Lagerbooleans werden zuerst in der bewährten Kernschale
  erzeugt; die geneigten Zierkurse werden danach kontrolliert angefügt. Dadurch
  bleiben die mechanischen Führungen geschlossen und manifold.
- Die aktualisierten farbigen Plattenvorschauen wurden aus den neuen 3MF-Szenen
  regeneriert. Sie zeigen die Material-/Farbgruppierung, nicht geslicte
  Supportvolumina.

## Anzeige in Canvas und Web-Viewer

Die ausgelieferten 3MF-Dateien enthalten die verifizierten Projektwerte direkt
in `Metadata/ghouls_grip_print_metadata.xml`. Der gemeinsame Web-/Canvas-
Renderer zeigt daraus:

- eine kompakte Zeile mit Druckzeit, Gesamtmaterial, Supportmaterial,
  Filamentlänge und Validierungsstatus für **alle Plates**, unabhängig von
  der ausgewählten Ansicht;
- ein einklappbares Detail-Overlay rechts unten mit Maschine, Düse, Prozess,
  Filamentprofil, Material, Farbe, Bett, Wandzahl, Infill, Support und
  Plattenzahl;
- im Detail-Overlay eine separat aufklappbare Tabelle **Print data by plate**
  mit Druckzeit, Material, Supportmaterial, Filamentlänge, Supportlänge, Status und einem
  Supportbild-Button pro gesliceter Plate. Die Bilder zeigen die tatsächlich
  extrudierten Supportbahnen und sind in Canvas sowie Webview per Dialog
  anzusehen. Fehlende oder fehlerhafte Plate-Metadaten werden ausdrücklich angezeigt;
- ein Projektvorschau-Button für das vollständige farbcodierte
  Fünf-Platten-Druckprojekt;
- die korrekte einzelne Platte oder alle Platten unter Berücksichtigung von
  3MF-Komponenten-Transformationen und OrcaSlicer-`plater_id`;
- ein einklappbares Werkzeugmenü für Reload, Auto-Reload, Zoom, Wireframe,
  Shading, Ansichten, Rotation, Hilfsanzeigen und Messung.

Mehrplattige Dateien starten in Canvas und Web-Viewer mit **All plates**.
Mehr als zwei Platten stehen nur in der Gesamtansicht in einem Grid mit
50 mm Zwischenraum; zwei Platten stehen nebeneinander. Die Einzelplatten-
Transformationen bleiben unverändert. Materialfarben folgen OrcaSlicers
Filamentpalette mit Objekt- und Teilzuweisungen; bei Standard-3MF-Dateien
werden weiterhin die 3MF-Materialressourcen verwendet.
Die Druckübersicht zeigt die eingebetteten
Projekt-Gesamtwerte (Zeit, Material, Support und Filamentlänge) sowie die
Plattenzahl. Einzelplatten bleiben über **Plate** auswählbar. Reload derselben
Datei behält die Auswahl; beim Öffnen einer anderen Datei wird wieder
**All plates** gewählt. Einzelplatten-3MF und STL bleiben unverändert.

Viewer-Prüfung (2026-10-12): `npm test --prefix web` bestanden
(22 Tests); `npm run build --prefix web` bestanden. Browser-Screenshots des lokalen
Canvas und der gebauten Web-SPA bestätigen beide schwarzen Druckplatten in
der Übersicht und die Projekt-Gesamtwerte. Einzelplattenwahl, Reload,
Dateiwechsel zur View-3MF und Auto-Reload einer anderen Mehrplatten-Datei
wurden ebenfalls geprüft.

In der lokalen Copilot-Canvas-Erweiterung öffnet **Open in OrcaSlicer** die
exakt ausgewählte Workspace-3MF über einen lokalen POST-Endpunkt mit
Nonce-Prüfung und Pfadvalidierung. Der Button wird für STL, unsichere Pfade und
die öffentliche Web-SPA nicht als Desktop-Startweg angeboten.

## Behobene Probleme

1. 3MF-Build- und Komponenten-Transformationen sowie Orcas `plater_id` werden vom Canvas berücksichtigt; Objekte liegen nicht mehr übereinander.
2. Die interne Führung besitzt eine 1,8-mm-Außenabdeckung; außen bleibt die Kiste geschlossen.
3. Die naturweiße Mechanik ist kompakt auf zwei vollständige 250-mm-Platten
   verteilt; alle 25 Mechanikobjekte sind genau einmal zugeordnet.
4. Der frühere Hebel, Rastschieber, die Spule, Schlüssel, Bandanker, Seile, Gummibänder und Federn sind entfernt. Der graue Totenkopf dreht direkt die Ritzelwelle.
5. `scripts/render_ghouls_grip_print_projects.py` rendert alle fünf
   farbcodierten Plattenvorschauen direkt aus der aktuellen 3MF-Datei.
   Der Export platziert die Platten entsprechend dem OrcaSlicer-3-Spaltenraster;
   der Renderer löst dessen 300-mm-X- und -Y-Abstände für Einzelplattenbilder
   aus den tatsächlichen Plattenzuordnungen auf.

## Dateibelege

| Datei | SHA-256 |
| --- | --- |
| `ghouls-grip-view.3mf` | `687FE6888E0508B58957DA3004B6B71AE6FCFE25A05929F34A0A118B3231A28F` |
| `ghouls-grip-print.3mf` | `BF705DC56C1E364254979260E01617842FA7DFE70EF7E3873FC15B4C0D72D5A7` |

## Physische Restrisiken

- Der direkte Totenkopf hat weniger mechanische Hebelwirkung als der verworfene lange Hebel. Passungen und Zahnflanken vor der Endmontage entgraten.
- Erfolgreiches Slicen und die kollisionsfreie Simulation ersetzen keinen realen Dauerlauf.
- Gedruckte Pins sowie PLA-Flexuren verschleißen. Hoch belastete Scherengelenke vorzugsweise mit M3×16-Schrauben sichern.
- Vor dem Komplettdruck bleiben Arm-/Pin-/Zahnrad-Passungscoupon und ein einzelner Finger-Testdruck empfohlen.
