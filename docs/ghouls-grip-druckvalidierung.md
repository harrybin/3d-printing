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
| Schwarz | Leichtbau-Schatulle stehend, gerippter Deckel hochkant; automatische kritische Baumstützen | 645 | 332,91 g | 13 h 10 min 22 s | [PNG](images/ghouls-grip-slice-black-plate-1.png) |
| Knochenbeige | Unterarm, Handfläche, fünf Finger | 250 | 45,72 g | 3 h 27 min 40 s | [PNG](images/ghouls-grip-slice-bone.png) |
| Mechanik, Platte 1 | 4 gelochte Arme, offener Schlitten/Plattformrahmen, Zahnstangen und Speichenritzel | 464 | 111,11 g | 4 h 44 min 30 s | [PNG](images/ghouls-grip-slice-mechanism-plate-1.png) |
| Mechanik, Platte 2 | 3 Zwischenräder, Ausgangszahnrad/D-Welle, 10 kleine und 4 große Pins | 217 | 13,00 g | 1 h 00 min 26 s | [PNG](images/ghouls-grip-slice-mechanism-plate-2.png) |
| Grau | Anatomischer Totenkopf-Drehknopf | 135 | 23,14 g | 1 h 22 min 13 s | [PNG](images/ghouls-grip-slice-accent.png) |
| **Gesamt** | **39 Druckobjekte / 5 Platten** | – | **525,88 g** | **23 h 45 min 11 s** | – |

Projektmetadaten:

| Projekt | Zeit | Masse | Länge | Volumen | Platten |
| --- | ---: | ---: | ---: | ---: | ---: |
| Schwarz | 47.422 s | 332,91 g | 111.620,36 mm | 268.480 mm³ | 1 |
| Knochenbeige | 12.460 s | 45,72 g | 15.329,80 mm | 36.870 mm³ | 1 |
| Mechanik | 20.696 s | 124,11 g | 41.613,71 mm | 100.090 mm³ | 2 |
| Grau | 4.933 s | 23,14 g | 7.759,25 mm | 18.660 mm³ | 1 |

Das schwarze Projekt benötigt nun 332,91 g statt 455,96 g vor der
Leichtbau-Runde: **123,05 g / 27,0 % weniger**. Gegenüber dem ursprünglichen
629,66-g-Entwurf beträgt die Einsparung **296,75 g / 47,1 %**. Die Gesamt-BOM
sinkt gegenüber dem zuletzt verifizierten Stand von 599,02 g auf 525,88 g
und von 24 h 59 min 50 s auf 23 h 45 min 11 s.

Wichtig: Das schwarze Projekt wird nicht mehr als „supportfrei“ bezeichnet.
OrcaSlicer hatte zuvor nur deshalb keine Stützpfade erzeugt, weil Support
deaktiviert war. Im finalen Projekt sind automatische Baumstützen, 45°-Schwelle
und `critical regions only` aktiv. Der G-Code enthält tatsächlich
**74,49 g Support einschließlich Interface**. Diese Zahl stammt aus den
Support-Extrusionswegen des G-Codes, skaliert mit dessen Gesamtmasse/-länge.

## Stützen und Objekt-Overrides

- Schatulle/Deckel: 3 Wände, 10 % Gyroid, automatische kritische Baumstützen;
  analytischer maximaler Deckel-Brückenspalt 10,0 mm, Schatulle 6,0 mm.
- Mechanik: 5–6 Wände, modellierte Öffnungen, Rahmen, Rippen und Speichen;
  20–50 % Infill in den verbleibenden Hohlräumen. Arme und Pins bleiben durch
  Wandlinien praktisch massiv. Normale Stützen sind nur an den weiterhin
  kritischen Objekten aktiv.
- Hand/Knochen: 4 Wände, 25 %; organische Überhänge mit bettgebundenen Baumstützen.
- Finger: 2 Wände, 15 %, 30 mm/s Außenwand und reduzierte Beschleunigung für die 0,8-mm-PLA-Flexuren.
- Totenkopfknopf: 5 Wände, 40 %, supportfrei in der gespeicherten Druckorientierung.

## Aktuelle Support-/Materialoptimierung

- Der Deckel besitzt eine 2,4-mm-Deckhaut, offene Unterseiten-Träger,
  fünf gerippte Längstraversen und fünf kurze hintere Anschlagpads statt eines
  massiven, 193 mm breiten Querriegels. Er steht auf seiner langen Vorderkante.
- Schatulle und Deckel passen mit 20 mm Abstand gemeinsam auf eine Platte.
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
  22.114 Facetten, 206 × 129 × 24 mm.
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
5. `scripts/render_ghouls_grip_print_projects.py` rendert die fünf
   farbcodierten Plattenvorschauen direkt aus den ausgelieferten 3MF-Szenen.
   Der im Export verwendete Plattenabstand von 300 mm wird dabei wieder in
   einzelne Druckplatten aufgelöst.

## Dateibelege

| Datei | SHA-256 |
| --- | --- |
| `ghouls-grip-master.3mf` | `8BDA068705130408D9A91B6AABF8AF1AE575472CB5A1F3AD9F74C0815C7B76B5` |
| `ghouls-grip-master-retracted.3mf` | `905067CECDFA3E5DDB6CF00E15F4CD3330636D0CF336590BA7260929F32776F1` |
| `ghouls-grip-print-black-pla.3mf` | `5DBD4F49BDE80D10FDCAA41947862FD63827E318532E97D2FD8395489BA2DAF5` |
| `ghouls-grip-print-bone-pla.3mf` | `95E424893539C2F9D2AAD413214473E2F68BB06D82E800A66842C6821ECF8613` |
| `ghouls-grip-print-mechanism-pla.3mf` | `51478FAC1719AB7FB046616012DFEC29D6075A15809737D38AE457578064CDA0` |
| `ghouls-grip-print-accent-pla.3mf` | `03556A2356C72CEAB3E4491530B20DEA5D7E58D42DE23F058FDB7C8B8496FD49` |

## Physische Restrisiken

- Der direkte Totenkopf hat weniger mechanische Hebelwirkung als der verworfene lange Hebel. Passungen und Zahnflanken vor der Endmontage entgraten.
- Erfolgreiches Slicen und die kollisionsfreie Simulation ersetzen keinen realen Dauerlauf.
- Gedruckte Pins sowie PLA-Flexuren verschleißen. Hoch belastete Scherengelenke vorzugsweise mit M3×16-Schrauben sichern.
- Vor dem Komplettdruck bleiben Arm-/Pin-/Zahnrad-Passungscoupon und ein einzelner Finger-Testdruck empfohlen.
