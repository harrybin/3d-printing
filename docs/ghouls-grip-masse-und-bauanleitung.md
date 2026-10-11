# The Ghoul's Grip – Maße und Bauanleitung

![Ausgefahren](images/ghouls-grip-deployed.png)
![Eingefahren](images/ghouls-grip-retracted.png)

## Status

Parametrischer, vollständig manueller Funktionsprototyp für den Anycubic Kobra S1. Die Kraftkette verwendet ausschließlich starre Druckteile: **drehbarer Totenkopf → Ritzel/Zahnstangen → Doppelschere, Deckelgetriebe und Unterarmgetriebe**. Es gibt keine Seile, Gummibänder, Federn, Rastklinke oder Wickelspule.

Die Finger sind vorgekrümmte PLA-Flexuren. Sie werden nicht aktiv bewegt; beim Ausfahren präsentiert die Mechanik die offene, gekrümmte Handfläche.

## Quellen der Geometrie

| Baugruppe | Quelle |
| --- | --- |
| Schatulle/Deckel | `scripts/gothic_chest.py` |
| Starre Mechanik | `scripts/mechanism.py` |
| Totenkopf-Drehknopf | `scripts/skull.py` |
| Anatomische Hand | `scripts/skeleton_hand.py` |
| Projekte/Mastermodelle | `scripts/ghouls_grip.py` |
| Orca-Projekte | `scripts/export_ghouls_grip_orca_projects.py` |
| Kollisionsnachweis | `scripts/verify_ghouls_grip_mechanics.py` |

## Maßvertrag

| Merkmal | Wert |
| --- | ---: |
| Geschlossene Zielgröße | 200 × 120 × 110 mm |
| Gehäuse inklusive Dekor | 209,0 × 130,5 × 98,0 mm |
| Deckel inklusive lokaler Schutzhaube | 206,0 × 129,8 × 28,2 mm |
| Dekorative Außenwand/Boden | 2,0 mm |
| Funktionsdatum an Schienen, Lagern und Führungen | 3,0 mm |
| Innenraum | 194 × 114 × 80 mm |
| Scherenarm | 72 mm Pivotabstand, 12 × 4 mm |
| Scherenbohrung | 3,2 mm |
| Scherenwinkel | 18° bis 78° |
| Schlittenweg | 53,506 mm |
| Hub des Jochs | 48,177 mm |
| Deckelöffnung | 108° |
| Totenkopf-Drehweg | 113,544° |
| Totenkopfknopf | 48,5 × 55,1 × 27,0 mm |
| Totenkopf-Schaft | Ø8 mm Presssitz, 0,2 mm Untermaß im Knopf |
| Handfläche | 67,9 × 96,5 × 25,2 mm |
| Fingerspitzen ausgefahren | 246,7 mm über Aufstellfläche |

Die Hand ist mit `HAND_SCALE = 0.72` aus einem anatomischen CT-Datensatz abgeleitet. Die größere Handfläche gegenüber der ursprünglichen 50 × 45-mm-Idee ist erforderlich, um Handwurzel- und Mittelhandknochen erkennbar zu erhalten.

## Verbindliche Konstruktionsentscheidungen

- Die Box ist in geschlossener Stellung vollständig geschlossen. Schlitten,
  Schere, Deckelgestänge und Unterarm ragen nicht aus dem Gehäuse.
- Der graue Totenkopf bleibt der absichtlich außenliegende Handantrieb. Er ist
  kein Druckknopf, sondern wird über etwa 114° gedreht.
- Es gibt keine Feder, kein Gummiband, keine Sehne, keine Rastklinke und keinen
  Rückholmechanismus. Zurückgestellt wird durch Rückwärtsdrehen des Totenkopfs.
- Fitkritische Geometrie, Lager, Zahnräder, Schienen, Steckrichtungen und
  Kollisionsfreiräume bleiben parametrisch in Python.
- Organische Zierflächen dürfen in Blender entstehen, verändern aber keine
  Funktionsdatums. Der Generator verwendet reproduzierbare, gecachte
  Höhenfelder aus `assets/gothic-chest-reliefs/`.
- Dicke Bauteile werden nicht unnötig massiv gefüllt: Schatulle und Deckel
  verwenden dünne Schalen, Rippen und offene Träger; Mechanikteile verwenden
  Rahmen, Fenster, Speichen und lokale massive Funktionszonen.
- „Supportfrei“ darf nur nach einem Slice mit eingeschalteter
  Support-Erzeugung behauptet werden. Für die aktuelle Ausgabe wird kein
  vollständiges Supportfrei-Versprechen abgegeben.

## Ornamentik und organische Modellierung

Die finale Schatulle kombiniert abgerundete, selbsttragende Basreliefs:

- Vorderseite: zwei Totenköpfe, Schlangen, Ranken und Voluten
- Rückseite: Brustkorb und zwei Wyvern mit Hörnern, Zähnen, Klauen und Flughaut
- Seiten: Totenkopf mit durchlaufender Schlange
- Deckel: geflügelte Totenkopf-Kartusche mit Schlangen und Voluten
- Pilaster: 1,2 mm vertiefte, kuppelförmig endende Kanneluren

Die erhabenen Reliefs werden als geglättete Höhenfelder aufgebaut und um 45°
geschert. Dadurch wachsen sie ohne scharfe Unterseiten aus der Wand und erhöhen
im gemessenen Kontrollslice die Supportpfade nicht. Die nur 2,0 mm starken
Wandfelder werden nicht tief graviert; vertiefte Details liegen ausschließlich
in ausreichend starkem Material.

## Funktionsprinzip

1. Der graue Totenkopf sitzt direkt auf der Ø8-mm-Welle des Hauptritzels.
2. Eine Drehung um etwa 114° verschiebt die Schlittenzahnstange um 53,5 mm.
3. Der Schlitten spreizt zwei parallele Scherenpaare von 18° auf 78° und hebt das offene Hubjoch um 48,2 mm.
4. Gleichzeitig bewegt das Hauptgetriebe eine starre Deckelzahnstange. Ein gefangener Lost-Motion-Schlitz nimmt zunächst Leerweg auf; anschließend bewegt ein kurzer Folgejochweg von 7 mm das Deckelsegment schnell auf 108°.
5. Ein mitfahrendes Fünf-Zahnrad-Getriebe mit drei Zwischenrädern überträgt die Drehung eines Scherenarms kontinuierlich und mit dem richtigen Drehsinn auf den Unterarm. Der Unterarm schwenkt von -105° auf -45°.
6. Beim Zurückdrehen läuft die gesamte Kraftkette positiv rückwärts: Unterarm faltet ein, Schere sinkt, Deckel schließt. Es wird keine Rückstellfeder benötigt.

Der Deckel erreicht 108° bereits bei etwa 32° Scherenwinkel und bleibt während des restlichen Hubs formschlüssig offen. Dadurch kreuzt die Hand den Deckel nicht.

## Stückliste

Vier Orca-Projekte enthalten **22 Teiltypen / 35 physische Druckobjekte**.

| Teil | Anzahl | Maße ungefähr | Farbe |
| --- | ---: | --- | --- |
| Schatulle | 1 | 209,0 × 130,5 × 98,0 mm | Schwarz |
| Deckel | 1 | 206,0 × 129,8 × 28,2 mm | Schwarz |
| Scherenarm | 4 | 84 × 12 × 4 mm | Naturweiß |
| Schlitten mit Zahnstange | 1 | 94 × 119,2 × 26 mm | Naturweiß |
| Hubjoch | 1 | 82 × 92 × 51 mm | Naturweiß |
| Hauptantriebsritzel | 1 | 57,4 × 57,4 × 24 mm | Naturweiß |
| Deckel-Hauptzahnstange | 1 | 73 × 22 × 8,7 mm | Naturweiß |
| Deckel-Folgejoch/Zahnstange | 1 | 32 × 103 × 14 mm | Naturweiß |
| Deckelsegment | 1 | 22 × 11,5 × 8 mm | Naturweiß |
| Scheren-Eingangszahnrad | 1 | 27,4 × 27,5 × 10 mm | Naturweiß |
| Zwischenrad | 3 | ca. 17 × 17 × 6 mm | Naturweiß |
| Unterarm-Ausgangszahnrad mit D-Welle | 1 | 27,4 × 65 × 27,5 mm | Naturweiß |
| Pivot-Pin Ø3 | 10 | Ø6,2 × 26 mm | Naturweiß |
| Unterarm mit D-Nabe | 1 | 25,8 × 18 × 50 mm | Knochenbeige |
| Handfläche | 1 | 67,9 × 96,5 × 25,2 mm | Knochenbeige |
| Fünf Finger | je 1 | 9–66 mm | Knochenbeige |
| Totenkopf-Drehknopf | 1 | 48,5 × 55,1 × 27,0 mm | Grau |

Die frühere separate Sehnenführung ist entfernt. Sie gehörte zum verworfenen
Seilzugkonzept und hatte in der starren Mechanik keine tragende oder führende
Funktion. Die kleinen Gelenkkragen und Flexurstege innerhalb der Finger bleiben
erhalten, weil sie die einzelnen Knochen druckbar verbinden.

## Verbinder und formschlüssige Schnittstellen

| Verbindung | Verbinder | Montageprinzip |
| --- | --- | --- |
| Scherenarme, Schlitten und Hubjoch | 10 gedruckte Ø3-Pins; optional M3-Schrauben an hoch belasteten Gelenken | Pin durch die fluchtenden 3,2-mm-Bohrungen stecken; Kopf bleibt außen |
| Unterarm im Hubjoch | lange D-Welle des naturweißen Ausgangszahnrads + 1,75-mm-Filament-Querstift | Unterarm zuerst zwischen die Lagerohren setzen, D-Welle danach axial einschieben und außen sichern |
| Handfläche am Unterarm | 11,6-mm-Unterarmzapfen in sichtbarer Ø12-mm-Handgelenkaufnahme + 1,75-mm-Filament-Querstift | Zapfen durch die 2-mm-Einführsenkung bis zum Anschlag einschieben, Querbohrungen fluchten lassen, Filamentstift einsetzen |
| Finger an Handfläche | beschriftete, geneigte MCP-Steckzapfen und passende Sockel | jeden Finger seinem Sockel zuordnen und in Druckrichtung aufstecken |
| Deckel am Gehäuse | 1,75-mm-Filament als Scharnierachse | durch die fluchtenden Scharnierbohrungen schieben |
| Totenkopf am Hauptritzel | blinde Ø8-mm-Pressaufnahme mit 0,2 mm Untermaß am Knopf | geschlossene Stellung ausrichten, anschließend axial aufpressen |

Die Handfläche besitzt ausdrücklich eine offene, verlängerte
Handgelenkaufnahme; sie ist kein massiver Block. Die Einführsenkung macht die
Öffnung im Knochen-3MF sichtbar und nimmt Elephant-Foot- oder Supportspuren auf.

## Montage

1. Je zwei Scherenarme zu einem X verbinden und zwei parallele Paare bauen. Zuerst gedruckte Pins trocken testen; für Dauerbetrieb M3-Schrauben verwenden.
2. Untere Festpunkte auf die Bodenlager stecken. Die gegenüberliegenden unteren Enden mit dem Schlitten verbinden. Der Schlitten muss frei zwischen den beiden Endlagen laufen.
3. Das offene Hubjoch montieren: pro Scherenpaar ein oberes Ende ins feste Auge, das andere in die Kulisse. Der mittlere Handraum bleibt frei.
4. Hauptantriebsritzel von innen in das Frontlager einsetzen. Die integrierte Welle muss außen frei herausstehen und das Ritzel vollständig in die Schlittenzahnstange greifen.
5. Totenkopfknopf außen mit der Blindbohrung auf die Ø8-mm-Welle pressen. Vor endgültigem Einpressen die geschlossene Stellung so ausrichten, dass das Gesicht senkrecht und gut greifbar steht.
6. Deckel-Hauptzahnstange am Antrieb einsetzen. Den Zapfen des Folgejochs vollständig im Lost-Motion-Schlitz fangen. Das hintere Zahnsegment muss ohne Klemmen mit dem Deckelsegment kämmen.
7. Das Scheren-Eingangszahnrad auf den formschlüssigen Zapfen eines Scherenarms setzen. Die drei Zwischenräder bleiben bis nach der Unterarmmontage noch ausgebaut.
8. Den knochenfarbenen Unterarm **ohne Zahnrad** senkrecht von oben
   zwischen die beiden Lagerohren des Jochs setzen. Die runden Lagerbohrungen
   und die D-Nabe müssen fluchten. Anschließend das naturweiße
   Unterarm-Ausgangszahnrad von der offenen Zahnradseite einschieben: Seine
   lange D-Welle läuft durch das äußere Rundlager, die D-Nabe und das innere
   Rundlager. Am gegenüberliegenden Wellenende einen 1,75-mm-Filamentstift
   durch das Querloch stecken. Erst danach die drei Zwischenräder in ihrer
   linearen Reihenfolge auf die zugänglichen Jochpfosten setzen. Alle fünf
   Zahnräder müssen über den gesamten Hub im Eingriff bleiben. Das
   Ausgangszahnrad hält die Welle auf einer Seite,
   der Filamentstift auf der anderen; Klebstoff ist nicht erforderlich.
   In geschlossener Stellung liegt der Unterarm bei -105°, ausgefahren bei
   -45°.
9. Die sichtbare Ø12-mm-Handgelenkaufnahme der Handfläche auf den
   11,6-mm-Unterarmzapfen schieben, die Handfläche dabei um -75° rollen und die
   Querbohrungen ausrichten. Mit 1,75-mm-Filament sichern. Danach die fünf
   vorgekrümmten Finger auf ihre beschrifteten Sockel setzen.
10. Deckel mit 1,75-mm-Filament als Scharnierachse einsetzen und das Deckelsegment formschlüssig am Scharnier koppeln.
11. Ohne Süßigkeiten langsam testen: Totenkopf drehen → Deckel öffnet früh → Schere hebt → Unterarm entfaltet. Danach exakt rückwärts drehen. Nichts darf von selbst zurückschnappen.

## Druckprojekte

- `models/ghouls-grip-master.3mf` – ausgefahrene Montageansicht.
- `models/ghouls-grip-master-retracted.3mf` – geschlossene Einbaukontrolle.
- `models/ghouls-grip-preview.stl` – Canvas-Vorschau.
- `models/ghouls-grip-print-black-pla.3mf` – Platte 1 „Schatulle“ stehend, Platte 2 „Deckel auf Hinterkante stehend“; Baumstützen bleiben aktiviert und sind im Druckbericht quantifiziert.
- `models/ghouls-grip-print-bone-pla.3mf` – Unterarm, Hand und Finger, eine Platte.
- `models/ghouls-grip-print-mechanism-pla.3mf` – starre Mechanik, zwei Platten.
- `models/ghouls-grip-print-accent-pla.3mf` – Totenkopf-Drehknopf, eine Platte.

Im geschlossenen Zustand liegt die vollständige interne Deckelmechanik unter
einer mit dem Deckel vereinigten schwarzen Schutzhaube. Der Montagekanal ist
nur zur Boxinnenseite offen; von oben besteht eine durchgehende 2,0-mm-Dachhaut.
Deckelkurbel und Yoke wurden zusätzlich als eigene Kollisionspaare über den
gesamten Hub geprüft und schneiden weder Deckel noch Schatulle.

Alle Projekte verwenden PLA, Anycubic Kobra S1 0.4, Textured PEI, 0,20 mm Schichthöhe und eingebettete Farben. Die exakten Slice-Ergebnisse stehen in [`ghouls-grip-druckvalidierung.md`](ghouls-grip-druckvalidierung.md).

### Gespeicherte OrcaSlicer-Defaults

Diese Optionen werden beim Generieren aller vier Materialprojekte gesetzt und
durch `tests/test_ghouls_grip_orca_settings.py` abgesichert:

| Option | Gespeicherter Wert |
| --- | --- |
| Nahtposition | Random (`seam_position=random`) |
| Bügeln | Alle oberen Oberflächen (`ironing_type=top`) |
| Support erzeugen | Ein (`enable_support=1`) |
| Standard-Support | automatisch, bettgebunden |
| Schicht / Düse | 0,20 mm / 0,4 mm |
| Platte | Textured PEI Plate |
| XY-Lochkompensation | +0,10 mm |
| XY-Konturkompensation | 0,00 mm |
| Elephant-Foot-Kompensation | 0,15 mm |
| Prime Tower | aus, da jedes Projekt genau eine Farbe/Spule enthält |

Schwarz, Knochen und Grau verwenden automatische Baumstützen. Das
Mechanikprojekt verwendet `normal(auto)` mit `snug`, weil Zahnstangen,
Rahmenöffnungen und Verbinder damit reproduzierbarer abgestützt werden.
Objekt-Overrides steuern Wände, Infill, Geschwindigkeit und Beschleunigung;
kein Override deaktiviert Support.

## Sicherheit und verbleibende Risiken

- Die Bewegung ist direkt handgeführt und nicht federgetrieben. Trotzdem Hände aus Schere, Zahnrädern und Deckelscharnier halten.
- Der größere Totenkopf liefert weniger Hebelübersetzung als der verworfene lange Hebel. Den Mechanismus zuerst ohne Hand und Deckel trocken einlaufen lassen; Grate entfernen, nicht mit Gewalt drehen.
- Vor dem Gesamtdruck einen Arm, einen kleinen/großen Pin und ein Zahnrad als Passungsmuster drucken.
- Gedruckte Pins und 0,8-mm-PLA-Flexuren sind Verschleißteile.
- Die Konstruktion ist kein geprüftes Kinderspielzeug.

## Lizenz der Handgeometrie

Die Hand basiert auf **“Wrist Bones Full Hand – Human Skeleton”**, NIH 3D Print Exchange, Modell `3DPX-016815`, hochgeladen von My Segmenter, **CC BY 4.0**. Im Repository liegt nur der abgeleitete Datensatz `model-sources/ghouls-grip/reference/hand_bones.npz`. Fitkritische Anschlüsse, Flexuren, Lager, Zahnräder und Gehäuse sind eigenständige parametrische Konstruktionen.
