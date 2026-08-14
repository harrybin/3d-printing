# Duschscharnier-Ersatz - Massdokumentation

Diese erste Version ist eine verstarkte Passprobe fur den vorhandenen grauen
Lager-Einsatz. Die Werte stammen aus den Fotos mit Schieblehre bzw. dem
5-mm-Raster und sind fur die finale ASA-Version als Parameter im Generator
`scripts/duschscharnier_ersatz.py` hinterlegt.

| Merkmal | Mass (mm) | Quelle | Status |
| --- | ---: | --- | --- |
| Gesamtlange | 80.33 | Nutzermessung | gemessen |
| Breite Lagerkopf | 38 | Nutzermessung | gemessen |
| Lange Lagerkopf | 43 | Nutzermessung| gemessen |
| Gesamtdicke | 12.5 | Nutzermessung | gemessen |
| Breite Montagearm | 20 | Nutzermessung | gemessen |
| Lange Montagearm | 43 | Nutzermessung | gemessen |
| Durchmesser Montagebohrungen | 4 | Nutzermessung | gemessen |
| Senkung Montagebohrungen | ⌀8.5 x 5 tief | Nutzermessung | gemessen |
| Mittelpunkte Montagebohrungen | 12.4 / 31.7 von der Aussenkante des Montagearms Richtung Lagerkopf | Nutzermessung | gemessen |
| Grauer Einsatz, Breite | 33.9 | Nutzermessung | gemessen |
| Grauer Einsatz, Lange | 38,3 | Nutzermessung | gemessen |
| Grauer Einsatz, Dicke | 7.85 | Nutzermessung | gemessen |
| Sitzspiel fur Einsatz | 0.20 | FDM-Sliding-Fit | bewusst vorgegeben |
| Lagertasche, Boden | 2.4 | Nutzermessung | gemessen |
| Wandstarke Schale und Arm | 2.0 | Nutzermessung | gemessen |
| Einsatzfuhrung, Ausladung / Lange / Breite | 2.0 / 20.0 / 8.1 | Seitenansicht mit Schieblehre | abgeleitet; ragt oben heraus |
| Zentraloffnung im Einsatz | 17.9 | Nutzermessung | nicht Teil des Ersatzkorpers |

## Verstarkung

Der Originalbruch liegt in der schmalen Verbindung zwischen Arm und Lagerkopf.
Der Ersatz bildet die Gusskonstruktion aus dem Referenzvideo nach: kreisrunder
Lagerkopf mit tropfenformiger Einsatztasche (zwei sich schneidende Kreise),
Kreuzstege und vier Gusspads im Schalenboden, Kammerarm mit durchgehender
Mittelwand, verschmolzene Schraubdome mit kegeligen Senkungen (ohne Absatz in
die 4-mm-Bohrung ubergehend) und voll hoher Fuhrungsblock am Taschenauslauf
mit 2.5 mm Uberstand. Der Bruchbereich ist durch den massiven Block und die
durchgehende Bodenplatte deutlich steifer als der dunne Originalsteg.

## Druckvorgabe

1. Zuerst in PLA als Passprobe drucken und den grauen Einsatz einlegen.
2. Fur die Montage ASA verwenden: mindestens 5 Perimeter, 50-60 % Gyroid-Infill,
   0.2 mm Schichthohe und mit der Lageraussparung nach oben drucken.
3. Die Turerst nach erfolgreicher statischer Handprufung einhangen. Ein FDM-Teil
   ersetzt kein sicherheitszertifiziertes Beschlagteil; bei Rissen oder Spiel
   nicht weiter verwenden.