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
| Gesamtdicke | 12.5 | Nutzermessung | gemessen (ohne Fuhrungsschienen) |
| Breite Montagearm | 20 | Nutzermessung | gemessen |
| Lange Montagearm | 43 | Nutzermessung | gemessen |
| Durchmesser Montagebohrungen | 4 | Nutzermessung | gemessen |
| Senkung Montagebohrungen | ⌀8.5 x 5 tief | Nutzermessung | gemessen |
| Mittelpunkte Montagebohrungen | 12.4 / 31.7 von der Aussenkante des Montagearms Richtung Lagerkopf | Nutzermessung | gemessen |
| Grauer Einsatz, Breite | 33.9 | Nutzermessung | gemessen |
| Grauer Einsatz, Lange | 38,3 | Nutzermessung | gemessen |
| Grauer Einsatz, Dicke | 7.85 | Nutzermessung | gemessen |
| Sitzspiel fur Einsatz | 0.20 | FDM-Sliding-Fit | bewusst vorgegeben |
| Boden Lagertasche und Arm | 2.0 | Nutzermessung | gemessen; durchgehend in Kopf und Arm |
| Kreuzstege und Gusspads, Oberkante ab Aussenflache | 2.4 | Nutzermessung | liegen auf dem 2.0er Boden, also 2.4 erhaben |
| Wandstarke Schale und Arm | 2.0 | Nutzermessung | gemessen |
| Einsatzfuhrung, Ausladung / Lange / Breite | 2.0 / 20.0 / 8.1 | Seitenansicht mit Schieblehre | abgeleitet; ragt oben heraus |
| Fuhrungsschienen im Arm, Uberstand / Ausladung / Lange | 5.3 / 2.0 / 20.0 | Nutzermessung + Fotos 202910/201653 (Draufsicht) und 202902 (Seitenansicht) | Paar Langsschienen an beiden inneren Armwanden; sie starten am Kammerboden und ragen 5.3 mm uber den Wandrand hinaus (Oberkante z = 17.8) |
| Fuhrungsschlitz zwischen den Schienen | 12.0 | Draufsicht 201653/202910, skaliert auf Armbreite 20 | abgeleitet |
| Fuhrungsschienen, Lage in Y | 9.5 .. 29.5 | Seitenansicht 202902, skaliert auf Armlange 43 | gemessen 8.1 .. 30.5, auf Lange 20.0 gerundet |
| Tropfen-Kopfradius / Spitzenradius | 19.0 / 10.85 | abgeleitet aus Breite 38 und Lange 43 | gesetzt |
| Tropfen-Flankenradius | 34.0 | Konturabgleich auf Foto 201713 | ersetzt die geraden Tangenten des fruheren Hull |
| Zentraloffnung im Einsatz | 17.9 | Nutzermessung | nicht Teil des Ersatzkorpers |

## Verstarkung

Der Originalbruch liegt in der schmalen Verbindung zwischen Arm und Lagerkopf.
Der Ersatz bildet die Gusskonstruktion aus dem Referenzvideo nach: kreisrunder
Lagerkopf mit tropfenformiger Einsatztasche (Kopfradius und Spitzenradius durch
tangentiale Flankenbogen verbunden, also ohne gerade Abschnitte),
Kreuzstege und vier Gusspads im Schalenboden (nur 0.4 mm erhaben, Oberkante bei
2.4 mm ab der Aussenflache), Kammerarm mit durchgehender
Mittelwand, verschmolzene Schraubdome mit kegeligen Senkungen (ohne Absatz in
die 4-mm-Bohrung ubergehend) und zwei Fuhrungsschienen an den inneren Armwanden,
die vom Kammerboden bis 5.3 mm uber den Wandrand reichen. Der Bruchbereich ist
durch die massiven Schienen und die
durchgehende Bodenplatte deutlich steifer als der dunne Originalsteg.

## Druckvorgabe

1. Zuerst in PLA als Passprobe drucken und den grauen Einsatz einlegen.
2. Fur die Montage ASA verwenden: mindestens 5 Perimeter, 50-60 % Gyroid-Infill,
   0.2 mm Schichthohe und mit der Lageraussparung nach oben drucken.
3. Die Turerst nach erfolgreicher statischer Handprufung einhangen. Ein FDM-Teil
   ersetzt kein sicherheitszertifiziertes Beschlagteil; bei Rissen oder Spiel
   nicht weiter verwenden.