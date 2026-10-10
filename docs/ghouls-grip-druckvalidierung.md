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
- Eine reale Spule/Farbe je Projekt, kein Prime Tower
- Farben: Schwarz `#202124`, Knochenbeige `#D8C6A5`, Naturweiß `#F1EBDD`, Grau `#777777`

Alle fünf Druckplatten wurden nach der Geometrie- und Orientierungsoptimierung
neu gesliced. Die Werte stammen aus den finalen G-Codes; die vier ausgelieferten
Material-3MFs enthalten dieselben Summen mit `status=verified`.

Orca meldet ausschließlich den nicht blockierenden Profilhinweis, dass
`precise wall` bei der gespeicherten Wandreihenfolge ignoriert wird.

## Ergebnisse

| Projekt / Platte | Inhalt | Schichten | Filament | Zeit | Vorschau |
| --- | --- | ---: | ---: | ---: | --- |
| Schwarz | Schatulle stehend, Deckel hochkant dahinter; keine Stützpfade | 645 | 385,08 g | 12 h 44 min 30 s | [PNG](images/ghouls-grip-slice-black-plate-1.png) |
| Knochenbeige | Unterarm, Handfläche, fünf Finger | 250 | 46,63 g | 3 h 31 min 26 s | [PNG](images/ghouls-grip-slice-bone.png) |
| Mechanik, Platte 1 | 4 Arme, Schlitten, Folgejoch, Hubjoch, Ritzel, Deckeltrieb, Scherenrad | 454 | 130,30 g | 6 h 21 min 27 s | [PNG](images/ghouls-grip-slice-mechanism-plate-1.png) |
| Mechanik, Platte 2 | 3 Zwischenräder, Ausgangszahnrad/D-Welle, 10 kleine und 4 große Pins | 214 | 13,65 g | 59 min 34 s | [PNG](images/ghouls-grip-slice-mechanism-plate-2.png) |
| Grau | Anatomischer Totenkopf-Drehknopf | 135 | 23,36 g | 1 h 22 min 53 s | [PNG](images/ghouls-grip-slice-accent.png) |
| **Gesamt** | **39 Druckobjekte / 5 Platten** | – | **599,02 g** | **24 h 59 min 50 s** | – |

Projektmetadaten:

| Projekt | Zeit | Masse | Länge | Volumen | Platten |
| --- | ---: | ---: | ---: | ---: | ---: |
| Schwarz | 45.870 s | 385,08 g | 129.110,25 mm | 310.550 mm³ | 1 |
| Knochenbeige | 12.686 s | 46,63 g | 15.633,52 mm | 37.600 mm³ | 1 |
| Mechanik | 26.461 s | 143,95 g | 48.264,95 mm | 116.090 mm³ | 2 |
| Grau | 4.973 s | 23,36 g | 7.832,36 mm | 18.840 mm³ | 1 |

Das schwarze Projekt benötigt nun 385,08 g statt 455,96 g vor dieser
Optimierungsrunde: **70,88 g / 15,5 % weniger**. Gegenüber dem ursprünglichen
629,66-g-Entwurf beträgt die Einsparung **244,58 g / 38,8 %**. Die Gesamt-BOM
sinkt von 668,50 g auf 599,02 g und von 31 h 00 min 05 s auf 24 h 59 min 50 s.
Die vom Benutzer gezeigte GUI-Vorschau enthielt allein für Schatulle und Deckel
rund 133,7 g Support/Support-Interface. Der finale schwarze G-Code enthält
unter dem eingebetteten Profil **0 Support-Werkzeugpfade**; wegen der zugleich
geänderten Geometrie und Projekteinstellungen ist dies kein 1:1-Profilvergleich.

## Stützen und Objekt-Overrides

- Schatulle/Deckel: 3 Wände, 10 % Gyroid, objektbezogen vollständig
  stützfrei. Der finale schwarze G-Code enthält weder `Support`- noch
  `Support interface`-Werkzeugpfade.
- Mechanik: 5–6 Wände, 40–100 % Infill; Arme, Zahnräder und Pins verstärkt. Normale Stützen sind nur für Plattform, Schlitten, beide Deckelzahnstangen und das lange Ausgangszahnrad/D-Wellen-Teil aktiviert.
- Hand/Knochen: 4 Wände, 25 %; organische Überhänge mit bettgebundenen Baumstützen.
- Finger: 2 Wände, 15 %, 30 mm/s Außenwand und reduzierte Beschleunigung für die 0,8-mm-PLA-Flexuren.
- Totenkopfknopf: 5 Wände, 40 %, supportfrei in der gespeicherten Druckorientierung.

## Aktuelle Support-/Materialoptimierung

- Der Deckel besitzt selbsttragende, etwa 45° geneigte Dächer über den
  unteren Innenaussparungen und steht beim Druck auf seiner geraden Vorderkante.
  Die große Dachfläche liegt damit vertikal statt als Stützdecke über dem Bett.
- Schatulle und Deckel passen mit 20 mm Abstand gemeinsam auf eine Platte.
- Der Sockel und der obere Kranz der Schatulle wurden von horizontalen Stufen
  auf zwei geneigte, selbsttragende Kurse umgebaut. Die Pilasterkapitelle und
  die Unterseiten der Scharnierlager sind ebenfalls geneigt.
- Die inneren nichttragenden Wandfelder behalten nur noch eine 1,2-mm-
  Dreilinien-Außenhaut. Das Schatullen-Volumen sank von 315.001 mm³ auf
  295.062 mm³.
- Der Deckel bleibt watertight/manifold: 23.816 Facetten, 206 × 129 × 27,5 mm.
- Die Schienen- und Lagerbooleans werden zuerst in der bewährten Kernschale
  erzeugt; die geneigten Zierkurse werden danach kontrolliert angefügt. Dadurch
  bleiben die mechanischen Führungen geschlossen und manifold.
- Die aktualisierten farbigen Plattenvorschauen wurden aus den neuen 3MF-Szenen
  regeneriert. Sie zeigen die Material-/Farbgruppierung, nicht geslicte
  Supportvolumina.

## Behobene Probleme

1. 3MF-Build- und Komponenten-Transformationen sowie Orcas `plater_id` werden vom Canvas berücksichtigt; Objekte liegen nicht mehr übereinander.
2. Die interne Führung besitzt eine 1,8-mm-Außenabdeckung; außen bleibt die Kiste geschlossen.
3. Die Mechanikplatte wurde kompakt in zwei vollständige 250-mm-Platten gepackt. Alle 29 naturweißen Mechanikobjekte sind genau einmal zugeordnet.
4. Der frühere Hebel, Rastschieber, die Spule, Schlüssel, Bandanker, Seile, Gummibänder und Federn sind entfernt. Der graue Totenkopf dreht direkt die Ritzelwelle.
5. `scripts/render_ghouls_grip_print_projects.py` rendert die sechs
   farbcodierten Plattenvorschauen direkt aus den ausgelieferten 3MF-Szenen.
   Der im Export verwendete Plattenabstand von 300 mm wird dabei wieder in
   einzelne Druckplatten aufgelöst.

## Dateibelege

| Datei | SHA-256 |
| --- | --- |
| `ghouls-grip-master.3mf` | `4E3EAF7D37C5166D0AE2E59DDCF4AE58B03DB5E789A52356B879D3F1C88EA1E4` |
| `ghouls-grip-master-retracted.3mf` | `B1655EF1455E499D4E05596501FE5939E38045BF58E61F4B50C56855FD9FA073` |
| `ghouls-grip-print-black-pla.3mf` | `1F125B35A8159DEBA431B817C3BC7A3B2FE468AAB61248F9753C56B3D77BACAC` |
| `ghouls-grip-print-bone-pla.3mf` | `2030CBFE7B10C5730D167E84BC916F95C8F05AD1BFAD848F6DDA4077CAEBC8E8` |
| `ghouls-grip-print-mechanism-pla.3mf` | `75F236E91EA1124ECFC19373932F137AA57F8BE94A1712641695C1975875944E` |
| `ghouls-grip-print-accent-pla.3mf` | `B14E3645E8E6C52287FECE87954670670E0BAC706F7328F8F304B16A99F9F784` |

## Physische Restrisiken

- Der direkte Totenkopf hat weniger mechanische Hebelwirkung als der verworfene lange Hebel. Passungen und Zahnflanken vor der Endmontage entgraten.
- Erfolgreiches Slicen und die kollisionsfreie Simulation ersetzen keinen realen Dauerlauf.
- Gedruckte Pins sowie PLA-Flexuren verschleißen. Hoch belastete Scherengelenke vorzugsweise mit M3×16-Schrauben sichern.
- Vor dem Komplettdruck bleiben Arm-/Pin-/Zahnrad-Passungscoupon und ein einzelner Finger-Testdruck empfohlen.
