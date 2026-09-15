# Pfeffermühlen-Mahlwerk: Einsatz (Antriebskupplung)

Generator: `scripts/pfeffermuehle_mahlwerk_einsatz.py`
Output: `models/pfeffermuehle-mahlwerk-einsatz.stl`
Referenzfotos: `model-sources/pfeffermuehle-mahlwerk/` (Index: `_index.png`)

## Funktion

Der Fünfkant-Antriebsschaft des Mahlwerks wird zentrisch durch den Einsatz
gesteckt (volles Durchgangsloch, vom Nutzer explizit bestätigt trotz
resultierender dünnerer Restwand). Der Einsatz ist zylindrisch. Unter dem runden Kragen am oberen Ende sitzen
4 halbrunde Nasen (90° versetzt), die in die
vierfach geschwungene ("Kleeblatt") Vertiefung im Mahlwerk-Gehäuse einrasten
(sichtbar auf Bild-Kachel 02, geprägt "CRUSHGRIND CO"). Damit dreht sich der
Einsatz mit dem Fünfkant mit und überträgt das Drehmoment über die Nasen auf
das Mahlwerk-Gehäuse/den Mahlstein.

## Referenzkachel-Zuordnung (Contact Sheet)

| Kachel | Datei | Zeigt |
| --- | --- | --- |
| 00 | `...165635927.jpg` | Fünfkant-Schaft am Mahlwerk, Messschieber 5,75 mm (Schlüsselweite) |
| 01 | `...170606863.jpg` | Bohrung im alten (beschädigten) Einsatz, Messschieber 7,06 mm |
| 02 | `...170541868.jpg` | Unterseite des alten Einsatzes/Gehäuses, 4-Nasen-Kleeblattmuster, Prägung "CRUSHGRIND CO" |
| 03 | `...165523655.jpg` | Bruchstück-Detail, Messschieber 8,88 mm (Zuordnung unsicher) |
| 04 | `...165440445.jpg` | Gesamthöhe Mahlwerk/altes Teil, Messschieber 17,01 mm |
| 05 | `...170527313.jpg` | Alter Einsatz, Außenmaß, Messschieber 12,59 mm |
| 06 | `...170742712.jpg` | Abgebrochenes Fragment des alten Einsatzes, Wandstärke 2,12 mm |

## Maßtabelle

| Maß | Wert | Quelle | Status |
| --- | --- | --- | --- |
| Gesamthöhe Einsatz | 17,0 mm | Nutzerangabe, bestätigt durch Kachel 04 (17,01 mm) | gemessen/bestätigt |
| Fünfkant Schlüsselweite (Schaft) | 5,75 mm | Kachel 00 | gemessen |
| Fünfkant-Bohrung im Einsatz (Ziel) | 6,00 mm SW (Diagonale 6,31 mm) | 5,75 mm + 0,25 mm Spiel (nahe CrushGrind-Standard ~6 mm, siehe Recherche) | abgeleitet |
| Alter Einsatz Außen-Ø (max.) | 12,59 mm | Kachel 05 | gemessen |
| Bohrung im beschädigten Fragment | 7,06 mm | Kachel 01 | gemessen, aber **kein Konstruktionsmaß** - laut Nutzer hatte der alte, intakte Einsatz überall mind. 1 mm Wandstärke; 7,06 mm ist die durch den Bruch aufgeweitete Öffnung, nicht die ursprüngliche Bohrung |
| Wandstärke Bruchstück | 2,12 mm | Kachel 06 | gemessen (Referenz für Mindestwandstärke) |
| Nasen-Muster | 4 Nasen, 90° versetzt | Kachel 02, vom Nutzer bestätigt | bestätigt |
| Länge Nase inklusive Kragen | 7,08 mm | Nutzerangabe | gemessen/bestätigt |
| Kragenhöhe | 2,0 mm | Nutzerbestätigte Standardannahme | Annahme |

## Konstruktionsentscheidungen (neu, nicht 1:1 vom alten Teil übernommen)

- Schaft: Ø 9,0 mm, bis 9,92 mm Höhe glatt zylindrisch
- Nasenzone: 4 voneinander getrennte Rundnasen, je Radius 1,65 mm mit
  Mittelpunkten auf dem Schaftradius (4,5 mm). Jede Nase überlappt den
  zylindrischen Schaft um 1,65 mm, die Nasen grenzen jedoch nicht
  aneinander. Das entspricht den vier separaten runden Vertiefungen auf
  Kachel 02. Die Nasen sind 5,08 mm hoch; zusammen mit dem Kragen
  entsprechen sie dem gemessenen Maß von 7,08 mm.
  - Spitzenradius (durch eine Nase): 6,15 mm (Ø 12,3 mm Hüllkreis)
  - Zwischen den Nasen bleibt der Schaft bei Radius 4,50 mm sichtbar; die
    runden Nasen berühren sich nicht.
- Kragen: runde Deckscheibe, Ø 12,3 mm x 2,0 mm hoch, bündig über den Nasen
- Fünfkant-Durchgangsloch: 6,0 mm Schlüsselweite, volle Höhe 17 mm durchgehend
- Resultierende Mindestwandstärke um die Fünfkant-Bohrung: 1,35 mm am
  zylindrischen Schaft; an Nasenspitze/Kragen 3,00 mm. Die Mindestwandstärke
  von 1 mm ist damit erfüllt.

Die Höhenaufteilung folgt der bestätigten Nasenlänge inklusive Kragen:
9,92 mm glatter Schaft + 5,08 mm Nasenzone + 2,00 mm Kragen = 17,00 mm.

## Recherche

CrushGrind-Mahlwerke verwenden üblicherweise einen Fünfkant-Schaft mit
~6 mm Schlüsselweite als Kupplungs-Standard (öffentliche Herstellerangaben,
z. B. crushgrind.ca/pages/instructions). Das bestätigt die gewählte
6,0-mm-Zielbohrung als sinnvolles, leicht übermaßiges Spielpassmaß zum
gemessenen 5,75-mm-Schaft.

## Druckbarkeit

- Material: PLA/PETG, 0,4 mm Düse
- Mindestwandstärke überall >= 1,35 mm (deutlich über 0,8 mm Baseline)
- Ausgangsmodell (Schaft unten): 0,2 % unsupported
  (`mesh_tool.py overhang`), praktisch vollständig selbsttragend.
- Druckorientierte Datei `models/pfeffermuehle-mahlwerk-einsatz-druckorientiert.stl`
  (Kragen unten, Schaft oben): 33,9 % unsupported; für diese bewusst
  gewünschte Orientierung sind Stützstrukturen erforderlich.
- Naht/Deckflächen (>=89°) 55,17 mm² - flache Deck-/Bodenflächen, unkritisch
- Mesh: watertight, manifold, euler_number 0 (korrekt für ein durchgehendes
  Loch), keine degenerierten Facetten
