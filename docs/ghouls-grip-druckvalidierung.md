# The Ghoul's Grip – OrcaSlicer-Druckvalidierung

Slice-Ergebnis: **erfolgreich** mit OrcaSlicer CLI 2.4.2; Profilkonformität: **nicht verifiziert**.

**Stand 2026-10-17 (Mechanik-Re-Audit):** Die Druckdatei hat vier Plates und
41 Objekte (28 Teiletypen inklusive Reservepins und neuer
Kurbel-Distanzhülse `crank-spacer`; 31 Naturweißteile auf Platte 3). Der
Montage-Audit `docs/ghouls-grip-montage-audit.md` besteht alle 10 Prüfungen.
Beim ersten Slice nach dem Re-Audit brach Orca das Laden mit
„parsing aborted“ in `Metadata/model_settings.config` ab: Der
`<assemble>`-Abschnitt verwies noch auf gelöschte Objekt-IDs.
`scripts/refresh_ghouls_grip_print_geometry.py` synchronisiert ihn jetzt mit den
vorhandenen Objekten; ein Test sichert das ab. Der anschließende Slice endete mit
Exit 0 und vier G-Codes. Aktuelle SHA-256 der Druckdatei:
`AF3325DB2B8F273C1B41C307B6414481E2F01BBD10602C3743BAC4486E491EA7`.

Historie (2026-10-12): Damals wurden die 16 Objekte der früheren Naturweiß-Platte 4 mit den 11 Hauptteilen
von Platte 3 zusammengepackt. `scripts/consolidate_ghouls_grip_mechanism_plates.py`
erhält Teileorientierungen und Z-Lagen, lässt 6 mm Abstand zwischen den
Bauteil-Begrenzungsrahmen und mindestens 10 mm Bettrand. Anschließend wurden
die sieben Knochenobjekte auf Platte 2 ausschließlich in XY neu angeordnet;
Mesh-Payloads, Rotation und Z-Lagen bleiben erhalten. Ihr Footprint-Abstand
beträgt mindestens 6 mm, der Bettrandabstand mindestens 69 mm. Der aktualisierte
OrcaSlicer-CLI-Slice 2.4.2 lief danach mit Exit-Code 0 und vier G-Codes.
Die damalige Druckdatei-SHA ist durch den Stand vom 2026-10-17 ersetzt.

Aktuelle finale SHA-256 (2026-10-17):

| Datei | SHA-256 |
| --- | --- |
| `models/ghouls-grip-view.3mf` | `82A87333F4648A82BB225C5281FFFE9F12FE87C1608BE0FB9C096001020D7B02` |
| `models/ghouls-grip-preview.stl` | `95DFF18EB160D70EC08AB5952D8F946EAA35BFC1CB723B6E03EDABCA11772FE8` |
| `models/ghouls-grip-print.3mf` | `AF3325DB2B8F273C1B41C307B6414481E2F01BBD10602C3743BAC4486E491EA7` |

Schatulle: 76.838 Facetten, 209 × 130,5 × 98 mm, 200.928,569 mm³,
ein geschlossener Einzelkörper, konsistente Normalen, keine degenerierten
Dreiecke. Das komplette ASCII-STL ist bewusst eine montierte
41-Körper-Vorschau, kein Drucklayout; 41 Druckobjekte inklusive Reservepins
sind im vierplattigen Print-Projekt.
In dieser Session ist kein STL-Canvas deklariert; die exakte Datei wurde
stattdessen gelesen, validiert und als Farb-3MF-Bild gerendert, ohne UI-Workaround.

Historie (2026-10-12, 37-Objekt-Stand): Die damalige Bodenlagerreparatur
ersetzte ausschließlich die Schatullen-Geometrie;
die übrigen **36 Mesh-Payloads bleiben byteidentisch** zur übernommenen
Nutzerdatei (`HEAD`). Alle 37 Mesh-Payloads, Objekt-Overrides, Farben,
Materialien und `project_settings.config` bleiben erhalten. Die 16
Getriebe-/Verbinderteile liegen jetzt gemeinsam mit den 11 Hauptteilen auf
Platte 3; alle 37 Objekte bleiben genau einmal in der vollständigen Stückliste.
Die exakte finale Druckdatei wurde unabhängig geladen: 37 geschlossene,
orientierungskonsistente Einzelkörper, null degenerierte Dreiecke, alle innerhalb
ihres 250-mm-Betts, Z-Bettkontakt mit 0,01-mm-Rundtoleranz; größtes Bauteil-/Bauteil-Schnittvolumen
auf einer Druckplatte 0,000 mm³. Auch die Arm-/Bodenlagerpaare der montierten
Mechanik bestehen jetzt den 61-Zustands-Nachweis; das ist keine Lastfreigabe.
Prüfartefakt: `build/ghoul-floor-bearing-delivery.json`.

![Aktuelle Vier-Platten-Übersicht](images/ghouls-grip-print-preview.png)

## Sichtbare Stützstrukturen

**Orange zeigt tatsächlich extrudierte Support- und Support-Interface-Bahnen**
aus den vier frischen G-Codes; transparentes Grau zeigt die zugehörigen
Bauteile. Es ist ein G-Code-Bahnrender, kein OrcaSlicer-UI-Screenshot.

![Alle vier Plates mit tatsächlichen Stützbahnen](images/ghouls-grip-print-support-overview.png)

Einzelansichten: [Platte 1 – Schwarz](images/ghouls-grip-print-plate-1-supports.png),
[Platte 2 – Knochenbeige](images/ghouls-grip-print-plate-2-supports.png),
[Platte 3 – Naturweiß, 31 Teile](images/ghouls-grip-print-plate-3-supports.png),
[Platte 4 – Grau](images/ghouls-grip-print-plate-4-supports.png).

Die Screenshots basieren exakt auf der aktuellen Druckdatei und den am
2026-10-17 neu erzeugten vier G-Codes in `build/ghoul-final-slices/print/`.
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
  Objekte; alle vier frischen G-Codes enthalten echte Supportbahnen. Platte 3
  enthält jetzt sämtliche Naturweißteile einschließlich der früheren
  Transferzahnräder.
- Support nur auf Druckplatte, globaler Typ `tree(auto)`; Objekt-Overrides
  verwenden teils `normal(auto)`.

Diese Datei weicht damit vom Projektstandard `Textured PEI Plate`, `seam=random`,
`ironing=top` und global aktiviertem Support ab. Der Slice war erfolgreich, aber
Profilkonformität und Druckbereitschaft sind **nicht verifiziert**. OrcaSlicer
meldete für alle vier Plates, dass `precise wall` bei den gewählten
Wandsequenzen ignoriert wird; die G-Code-Erzeugung war erfolgreich. Es wurde
keine automatische Wiederherstellung oder Neuanordnung der Teile zugelassen.

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
`scripts/slice_ghouls_grip.ps1` hat nach der Plattenzusammenlegung Exit-Code 0
und vier echte G-Codes. Die Kopfzeile jedes frischen G-Codes
bestätigt OrcaSlicer 2.4.2. Die tatsächliche Installation wurde unter
`C:\Program Files\OrcaSlicer\orca-slicer.exe` gefunden;
`--help` endete mit Exit 0 ohne Konsolentext, daher wurden die bereits
funktionierenden Optionen des vorhandenen Slice-Skripts verwendet.
Die externen Mesh-Relationships sind ohne XML-Namenspräfix serialisiert, wie
Orcas Importer es erwartet.

| Befehl / Nachweis | Ergebnis |
| --- | --- |
| `.\.venv\Scripts\python.exe -m unittest discover -s tests` | PASS: 63 Tests (Stand 2026-10-17) |
| `.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_ghouls_grip_print_refresh.py -v` | nach finaler Bettkontakt-Korrektur erneut bestanden; Originaltransforms, Overrides, Plate-Zuordnung, unveränderte Payloads und Idempotenz |
| `.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_slice_support_usage.py -v` | 3 Tests bestanden; M82/M83/G92 und Rückstellungen |
| `.\.venv\Scripts\python.exe scripts\verify_ghouls_grip_mechanics.py` | Gesamt-Nachweis PASS; 61 Scherenstellungen von 18° bis 78° inkl. 48°, alle vier individuellen Arm-/Kistenpaare jetzt hartes Fail-Gate bei >0,001 mm³; übrige geprüfte Paare 0 mm³; JSON in `build/ghoul-floor-bearing-verification.json` |
| `python scripts\consolidate_ghouls_grip_mechanism_plates.py` | PASS: alle 31 Naturweißteile auf einer Platte; mindestens 10 mm Bettrand, 6 mm Rahmenabstand, Teileorientierungen und Mesh-Payloads erhalten |
| `python scripts\arrange_ghouls_grip_bone_plate.py` | PASS: sieben Teile auf Platte 2 mit mindestens 6 mm Footprint-Abstand und mindestens 69 mm Bettrandabstand; nur XY-Translationen geändert |
| `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\slice_ghouls_grip.ps1` | Exit 0 und vier frische OrcaSlicer-2.4.2-G-Codes |
| `python scripts\update_ghouls_grip_slice_metadata.py build\ghoul-final-slices\print --project models\ghouls-grip-print.3mf` | neue Slice-Kennzahlen gespeichert; Profilstatus weiter `not-verified` |
| `python scripts\render_3mf_previews.py models\ghouls-grip-print.3mf` | vollständige Projektvorschau aus dem exakten 3MF regeneriert |
| `python scripts\render_ghouls_grip_print_projects.py build\ghoul-final-slices\print --project models\ghouls-grip-print.3mf` und `python scripts\render_ghouls_grip_supports.py build\ghoul-final-slices\print --project models\ghouls-grip-print.3mf` | vier Plattenvorschauen und vier tatsächliche G-Code-Support-Sidecars |
| `.\.venv\Scripts\python.exe scripts\mesh_tool.py validate models\ghouls-grip-preview.stl --allow-multibody` | PASS: 270.134 Facetten, 41 absichtlich getrennte montierte Körper, geschlossen/orientiert, null degenerierte Dreiecke; Zentrierwarnung der nicht druckbaren Assembly-Vorschau, nicht verschoben |

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
| 1 – Schwarz | Schatulle und Deckel (2) | 649 | 334,99 g | 6,71 g (2,0 %) | 12 h 03 min 00 s | [Supportbild](images/ghouls-grip-print-plate-1-supports.png) |
| 2 – Knochenbeige | Unterarm, Handfläche und Finger (7) | 482 | 43,85 g | 6,25 g (14,3 %) | 3 h 04 min 39 s | [Supportbild](images/ghouls-grip-print-plate-2-supports.png) |
| 3 – Naturweiß | Hauptmechanik, Zahnräder, Wellen, Pins und Kurbel-Distanzhülse (31) | 631 | 111,63 g | 11,48 g (10,3 %) | 4 h 35 min 21 s | [Supportbild](images/ghouls-grip-print-plate-3-supports.png) |
| 4 – Grau | Totenkopf-Auslöser (1) | 135 | 23,94 g | 3,39 g (14,2 %) | 1 h 10 min 59 s | [Supportbild](images/ghouls-grip-print-plate-4-supports.png) |
| **Gesamt** | **41 Druckobjekte / 4 Plates** | – | **514,41 g** | **27,83 g (5,4 %)** | **20 h 53 min 59 s** | [Übersicht](images/ghouls-grip-print-support-overview.png) |

| Farbgruppe | Zeit | Masse | Stützmaterial | Länge | Volumen | Plates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Schwarz | 43.380 s | 334,99 g | 6,71 g | 112.316,83 mm | 270.150 mm³ | 1 |
| Knochenbeige | 11.079 s | 43,85 g | 6,25 g | 14.702,67 mm | 35.360 mm³ | 1 |
| Naturweiß | 16.521 s | 111,63 g | 11,48 g | 37.426,25 mm | 90.020 mm³ | 1 |
| Grau | 4.259 s | 23,94 g | 3,39 g | 8.025,39 mm | 19.300 mm³ | 1 |
| **Gesamt** | **75.239 s** | **514,41 g** | **27,83 g** | **172.471,14 mm** | **414.830 mm³** | **4** |

Die Supportanteile werden aus positiven Extrusionen der Support-/Interface-
Bewegungen berechnet; `M82`, `M83` und `G92` werden berücksichtigt,
Extruder-only-Rückstellungen nicht als gedruckter Support gezählt.
Die vorherige absolute-E-Auswertung der relativen Orca-Extrusion war falsch.
Masse und Volumen werden mit dem jeweiligen Slice-Verhältnis umgerechnet:

| Plate | Supportlänge | Supportvolumen |
| --- | ---: | ---: |
| 1 | 2.400,96 mm | 5.775 mm³ |
| 2 | 1.977,14 mm | 4.756 mm³ |
| 3 | 4.469,88 mm | 10.751 mm³ |
| 4 | 1.140,98 mm | 2.745 mm³ |
| **Gesamt** | **10.108,44 mm** | **24.314 mm³** |

Die Summen und vier Einzelergebnisse sind in `models/ghouls-grip-print.3mf`
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

Der Nutzerstand vor der Wandkorrektur lag bei 77.721 s, 527,20 g Filament und
28,42 g Support. Die aktuelle Änderung erhöht das um 279 s, 1,76 g Filament
und 1,36 g Support. Diese Differenz stammt aus echten Slices; die historischen
Werte ersetzen nicht die oben aufgeführten neuen Ergebnisse.

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
  Vier-Platten-Druckprojekt;
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

In der lokalen Copilot-Canvas-Erweiterung öffnet **3mf öffnen** die
exakt ausgewählte Workspace-3MF mit dem registrierten Standardprogramm über einen lokalen POST-Endpunkt mit
Nonce-Prüfung und Pfadvalidierung. Der Button wird für STL, unsichere Pfade und
die öffentliche Web-SPA nicht als Desktop-Startweg angeboten.

## Behobene Probleme

1. 3MF-Build- und Komponenten-Transformationen sowie Orcas `plater_id` werden vom Canvas berücksichtigt; Objekte liegen nicht mehr übereinander.
2. Die interne Führung besitzt eine 1,8-mm-Außenabdeckung; außen bleibt die Kiste geschlossen.
3. Alle 31 naturweißen Mechanikteile sind kollisionsfrei auf einer
   250-mm-Platte gruppiert; jedes der 41 Druckobjekte ist genau einmal
   einer von vier Materialplatten zugeordnet.
4. Der frühere Hebel, Rastschieber, die Spule, Schlüssel, Bandanker, Seile, Gummibänder und Federn sind entfernt. Der graue Totenkopf dreht direkt die Ritzelwelle.
5. `scripts/render_ghouls_grip_print_projects.py` rendert alle vier
   farbcodierten Plattenvorschauen direkt aus der aktuellen 3MF-Datei.
   Das gespeicherte OrcaSlicer-Plattenraster wird abhängig von der Plattenzahl
   aufgelöst (drei Spalten bei fünf, zwei bei vier Plates); 300-mm-X- und
   -Y-Abstände werden für Einzelplattenbilder anhand der tatsächlichen
   Plattenzuordnungen entfernt.

## Dateibelege

| Datei | SHA-256 |
| --- | --- |
| `ghouls-grip-view.3mf` | `82A87333F4648A82BB225C5281FFFE9F12FE87C1608BE0FB9C096001020D7B02` |
| `ghouls-grip-print.3mf` | `AF3325DB2B8F273C1B41C307B6414481E2F01BBD10602C3743BAC4486E491EA7` |

## Physische Restrisiken

- Der direkte Totenkopf hat weniger mechanische Hebelwirkung als der verworfene lange Hebel. Passungen und Zahnflanken vor der Endmontage entgraten.
- Erfolgreiches Slicen und die kollisionsfreie Simulation ersetzen keinen realen Dauerlauf.
- Gedruckte Pins sowie PLA-Flexuren verschleißen. Hoch belastete Scherengelenke vorzugsweise mit M3×16-Schrauben sichern.
- Vor dem Komplettdruck bleiben Arm-/Pin-/Zahnrad-Passungscoupon und ein einzelner Finger-Testdruck empfohlen.
