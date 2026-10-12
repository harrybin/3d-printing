# The Ghoul's Grip – OrcaSlicer-Druckvalidierung

Status: **VERIFIED**

Geometrie-Optimierung: 2026-10-10

OrcaSlicer-Basisprofil: **2.4.3 GUI / 2.4.2 CLI**

![Übersicht](images/ghouls-grip-slice-overview.png)

## Profilvertrag

- Drucker: `Anycubic Kobra S1 0.4 nozzle`
- Düse/Schicht: 0,4 mm / 0,20 mm
- Prozess: `0.20mm Standard @Anycubic Kobra S1 0.4 nozzle`
- Filament: `Anycubic PLA @Anycubic Kobra S1 0.4 nozzle`
- Bett: `Textured PEI Plate`
- Starttemperaturen: 55/215 °C
- Vier PLA-Farb-/Spulenzuordnungen in einem Druckprojekt; je Platte nur eine
  Farbe, kein Prime Tower
- Farben: Schwarz `#202124`, Knochenbeige `#D8C6A5`, Naturweiß `#F1EBDD`, Grau `#777777`
- Nahtposition: `random`
- Bügeln: `top` (**Alle oberen Oberflächen**)
- Automatischer Support im Druckprojekt aktiviert (`enable_support=1`)
- Support-Auflage: nur Druckplatte
- XY-Lochkompensation: +0,10 mm
- Elephant-Foot-Kompensation: 0,15 mm

Alle sechs Druckplatten wurden nach der Geometrie- und Orientierungsoptimierung
mit OrcaSlicer CLI 2.4.2 neu gesliced. Die Werte stammen aus den finalen
G-Codes; das eine ausgelieferte Druck-3MF enthält dieselben Summen und
Farbteilsummen mit `status=verified`.
Reproduzierbar: `.\scripts\slice_ghouls_grip.ps1`, danach
`.\.venv\Scripts\python.exe scripts\update_ghouls_grip_slice_metadata.py`.

Orca meldet ausschließlich den nicht blockierenden Profilhinweis, dass
`precise wall` bei der gespeicherten Wandreihenfolge ignoriert wird.

## Ergebnisse

| Projekt / Platte | Inhalt | Schichten | Filament | davon Stützen | Zeit | Vorschau |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Schwarz, Platte 1 | Leichtbau-Schatulle stehend mit organisch skulptierten Kreaturenreliefs | 490 | 197,08 g | 0,33 g (0,2 %) | 8 h 19 min 16 s | [PNG](images/ghouls-grip-slice-black-plate-1.png) |
| Schwarz, Platte 2 | Gerippter, vollständig geschlossener Deckel auf seiner Hinterkante stehend | 649 | 134,60 g | 17,54 g (13,0 %) | 5 h 39 min 44 s | [PNG](images/ghouls-grip-slice-black-plate-2.png) |
| Knochenbeige | Unterarm, Handfläche hochkant, fünf Finger | 482 | 43,35 g | 12,43 g (28,7 %) | 3 h 16 min 29 s | [PNG](images/ghouls-grip-slice-bone.png) |
| Naturweiß, Platte 1 | 4 gelochte Arme, offener Schlitten/Plattformrahmen, Zahnstangen und Speichenritzel | 464 | 111,96 g | 15,57 g (13,9 %) | 4 h 58 min 31 s | [PNG](images/ghouls-grip-slice-mechanism-plate-1.png) |
| Naturweiß, Platte 2 | Zwischenräder, Ausgangszahnrad/D-Welle, Pins und Splinte | 177 | 10,90 g | 1,27 g (11,7 %) | 0 h 50 min 27 s | [PNG](images/ghouls-grip-slice-mechanism-plate-2.png) |
| Grau | Anatomischer Totenkopf-Drehknopf, Gesicht nach oben | 135 | 23,83 g | 7,95 g (33,4 %) | 1 h 31 min 27 s | [PNG](images/ghouls-grip-slice-accent.png) |
| **Gesamt** | **35 Druckobjekte / 6 Platten** | – | **521,72 g** | **55,09 g (10,6 %)** | **24 h 35 min 54 s** | – |

Projektmetadaten (`status=verified` im einzigen Druck-3MF):

| Farbgruppe | Zeit | Masse | Stützmaterial | Länge | Volumen | Platten |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Schwarz | 50.340 s | 331,68 g | 17,87 g | 111.207,58 mm | 267.480 mm³ | 2 |
| Knochenbeige | 11.789 s | 43,35 g | 12,43 g | 14.533,07 mm | 34.960 mm³ | 1 |
| Naturweiß | 20.938 s | 122,86 g | 16,84 g | 41.192,39 mm | 99.080 mm³ | 2 |
| Grau | 5.487 s | 23,83 g | 7,95 g | 7.990,34 mm | 19.220 mm³ | 1 |
| **Gesamt** | **88.554 s** | **521,72 g** | **55,09 g** | **174.923,38 mm** | **420.740 mm³** | **6** |

### Orientierungsoptimierung (gemessen, nicht geschätzt)

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

Gegenüber dem zuvor verifizierten Stand (528,22 g / 138,60 g Support) sinkt der
Stützbedarf um **83,21 g / 60,0 %** und die Gesamtmasse um 11,38 g. Die
gemessenen Orientierungswechsel tragen den Hauptteil der Einsparung; die
zusätzliche geschlossene Deckelhaube erhöht das schwarze Projekt nur um 1,59 g.
Gegenüber dem ursprünglichen 629,66-g-Entwurf beträgt die Materialeinsparung
**112,82 g / 17,9 %**, gegenüber der Vor-Leichtbau-Schatulle (455,96 g schwarz)
**125,00 g / 27,4 %**.

Wichtig: Keine Platte wird als „supportfrei“ bezeichnet. Automatische,
bettgebundene Support-Erzeugung bleibt im gemeinsamen Druckprojekt aktiv.
Schwarz, Knochen und Grau verwenden `tree(auto)`; die Mechanik verwendet
`normal(auto)` mit `snug`. Der Standardwinkel beträgt 30°, beim schwarzen
Material 45°. Die angegebenen Stützmengen stammen aus den `;TYPE:Support`-
und `;TYPE:Support interface`-Extrusionswegen des G-Codes, skaliert mit dessen
filamentslot-spezifischer Masse und Länge.

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

## Aktuelle Support-/Materialoptimierung

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
- Schatulle und Deckel liegen auf zwei getrennten Platten derselben schwarzen
  Farbgruppe im gemeinsamen Druckprojekt, weil der stehende Deckel 129 mm hoch
  baut.
- Der Sockel und der obere Kranz der Schatulle wurden von horizontalen Stufen
  auf zwei geneigte, selbsttragende Kurse umgebaut. Die Pilasterkapitelle und
  die Unterseiten der Scharnierlager sind ebenfalls geneigt.
- Die dekorative Schatullenwand und der Boden sind 2,0 mm stark; die
  3,0-mm-Funktionsdatums an Schienen, Lagern und Führungen bleiben erhalten.
  Gerundete Außenkanten sowie vertiefte statt aufgesetzte Reliefs wirken
  organischer und vermeiden zusätzliche massive Zierkörper.
- Das Schatullen-Volumen sank von 295.062 auf 184.056 mm³
  (**−37,6 %**), das Deckelvolumen von 252.068 auf 124.903 mm³
  (**−50,5 %**). Zusammen sind das **−43,5 % Modellvolumen**.
- Acht überarbeitete Mechanikteile sanken durch offene Rahmen, Fenster und
  Speichen von 118.567 auf 82.649 mm³ (**−30,3 %**).
- Der Deckel bleibt ein einzelner watertight/manifold Körper:
  27.796 Facetten, 206 × 129,786 × 28,2 mm. Die lokale Schutzhaube ist nur
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
  Filamentlänge und Validierungsstatus;
- ein einklappbares Detail-Overlay rechts unten mit Maschine, Düse, Prozess,
  Filamentprofil, Material, Farbe, Bett, Wandzahl, Infill, Support und
  Plattenzahl;
- die korrekte einzelne Platte oder alle Platten unter Berücksichtigung von
  3MF-Komponenten-Transformationen und OrcaSlicer-`plater_id`;
- ein einklappbares Werkzeugmenü für Reload, Auto-Reload, Zoom, Wireframe,
  Shading, Ansichten, Rotation, Hilfsanzeigen und Messung.

Mehrplattige Dateien starten in Canvas und Web-Viewer mit **All plates**.
Die Platten stehen nebeneinander: vorhandene Orca-Grid-Offsets bleiben erhalten;
ohne ausreichenden Abstand werden sie nur für die Übersicht in einer Reihe
mit 50 mm Zwischenraum angeordnet. Die Druckübersicht zeigt die eingebetteten
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
5. `scripts/render_ghouls_grip_print_projects.py` rendert alle sechs
   farbcodierten Plattenvorschauen direkt aus den ausgelieferten 3MF-Szenen.
   Der Export platziert die Platten entsprechend dem OrcaSlicer-3-Spaltenraster;
   der Renderer löst dessen 300-mm-X- und -Y-Abstände für Einzelplattenbilder
   aus den tatsächlichen Plattenzuordnungen auf.

## Dateibelege

| Datei | SHA-256 |
| --- | --- |
| `ghouls-grip-view.3mf` | `D6118D9AEB4C5EF3A2D55BBBD36EE7B69EBAB049599845D8CD11A3AB75BD1592` |
| `ghouls-grip-print.3mf` | `0B9450F36E26B28A5D05286DF7E45F3C5FA7386A0E0E7896990FF5107D26569D` |

## Physische Restrisiken

- Der direkte Totenkopf hat weniger mechanische Hebelwirkung als der verworfene lange Hebel. Passungen und Zahnflanken vor der Endmontage entgraten.
- Erfolgreiches Slicen und die kollisionsfreie Simulation ersetzen keinen realen Dauerlauf.
- Gedruckte Pins sowie PLA-Flexuren verschleißen. Hoch belastete Scherengelenke vorzugsweise mit M3×16-Schrauben sichern.
- Vor dem Komplettdruck bleiben Arm-/Pin-/Zahnrad-Passungscoupon und ein einzelner Finger-Testdruck empfohlen.
