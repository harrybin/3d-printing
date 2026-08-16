# Duschscharnier-Ersatz - Massdokumentation

Diese erste Version ist eine verstarkte Passprobe fur den vorhandenen grauen
Lager-Einsatz. Die Werte stammen aus den Fotos mit Schieblehre bzw. dem
5-mm-Raster und sind fur die finale ASA-Version als Parameter im Generator
`scripts/duschscharnier_ersatz.py` hinterlegt.

| Merkmal | Mass (mm) | Quelle | Status |
| --- | ---: | --- | --- |
| Gesamtlange | 82.53 | konstruiert | 82.33 + 0.2 durch die dickere Tropfen-Aussenwand |
| Breite Lagerkopf | 38.4 | konstruiert | Original 38.0 + 2 x 0.2 Wandzuwachs nach aussen; innen unverandert |
| Lange Lagerkopf | 43 | Nutzermessung | gemessen |
| Gesamtdicke | 12.5 | Nutzermessung | gemessen (ohne Fuhrungsschienen) |
| Breite Montagearm | 20 | Nutzermessung | gemessen |
| Lange Montagearm | 45 | Nutzermessung 16.08. | 43 + 2.0; die 2 mm liegen zwischen Tropfen und erster Bohrung (Original 42.83 vs. Druck 40.87) |
| Durchmesser Montagebohrungen | 4 (Modell 4.4) | Nutzermessung | Sollmass 4.0; im Generator +0.4 Druckkompensation, damit die gedruckte Bohrung 4 mm misst |
| Senkung Montagebohrungen | ⌀8.5 x 5 tief | Nutzermessung | gemessen |
| Mittelpunkte Montagebohrungen | 12.4 / 31.7 von der Aussenkante des Montagearms Richtung Lagerkopf | Nutzermessung | gemessen |
| Grauer Einsatz, Breite | 33.9 | Nutzermessung | gemessen |
| Grauer Einsatz, Lange | 38,3 | Nutzermessung | gemessen |
| Grauer Einsatz, Dicke | 7.85 | Nutzermessung | gemessen |
| Sitzspiel fur Einsatz | 0.20 | FDM-Sliding-Fit | bewusst vorgegeben; Passung bestatigt, Taschenmasse ab 16.08. eingefroren |
| Boden Lagertasche und Arm | 2.0 | Nutzermessung | gemessen; durchgehend in Kopf und Arm |
| Verrundung untere Aussenkanten | 0.8 | Gussvorbild | umlaufender Radius an der geschlossenen Aussenflache |
| Kreuzstege und Gusspads, Hohe uber dem Boden | 2.4 | Nutzermessung | 2.4 erhaben auf dem 2.0er Boden, Oberkante bei 4.4 ab Aussenflache |
| Einbindung Kreuzstege in die Wand | 1.6 | Verstarkung 16.08. | alle vier Stegenden laufen 1.6 mm in die Wand statt davor zu enden |
| Wandstarke Schale (Tropfen) | 2.05 | Verstarkung 16.08. | 1.85 + 0.2, ausschliesslich nach aussen; Taschenkontur unverandert |
| Wandstarke Arm | 2.0 | Nutzermessung | gemessen |
| Aussenverrundung Ubergang Arm zu Tropfen | 8.0 | Verstarkung 16.08. | Hohlkehle statt scharfer Innenecke an der Taille (x = +-10, y = -0.37) |
| Einsatzfuhrung, Ausladung / Lange / Breite | 2.0 / 20.0 / 8.1 | Seitenansicht mit Schieblehre | abgeleitet; ragt oben heraus |
| Fuhrungsschienen im Arm, Uberstand / Ausladung / Lange | 5.3 / 2.0 / 22.5 | Nutzermessung + Fotos 202910/201653 (Draufsicht) und 202902 (Seitenansicht) | Paar Langsschienen an beiden inneren Armwanden; sie starten am Kammerboden und ragen 5.3 mm uber den Wandrand hinaus (Oberkante z = 17.8) |
| Fuhrungsschlitz zwischen den Schienen | 12.0 | Draufsicht 201653/202910, skaliert auf Armbreite 20 | abgeleitet |
| Fuhrungsschienen, Lage in Y | 7.0 .. 29.5 | Vergleichsfoto 104653 (Druck auf Original) | armseitiges Ende unverandert, tropfenseitig um 2.5 verlangert |
| Tropfen-Kopfradius / Spitzenradius, aussen | 19.2 / 11.05 | abgeleitet aus Breite 38 und Lange 43, + 0.2 Wandzuwachs | gesetzt |
| Tropfen-Kopfradius / Spitzenradius, Tasche | 17.15 / 9.0 | Einsatzmass + Sitzspiel | unverandert, Passung bestatigt |
| Tropfen-Flankenradius, aussen / Tasche | 34.2 / 32.15 | Konturabgleich auf Foto 201713 | ersetzt die geraden Tangenten des fruheren Hull; Bogenmittelpunkte fur Aussen und Tasche identisch |
| Zentraloffnung im Einsatz | 17.9 | Nutzermessung | nicht Teil des Ersatzkorpers |

Bildindex: `model-sources/_index.png` (nummeriertes Kontaktblatt aller Referenzfotos).
Die Kachelnummern verweisen auf die Dateien in `model-sources/`; die Quellenangaben
oben nennen den Zeitstempel-Teil des Dateinamens, z. B. `202902` = Kachel 16.
Neu erzeugen mit `python scripts/make_contact_sheet.py model-sources`.

## Verstarkung

Der Originalbruch liegt in der schmalen Verbindung zwischen Arm und Lagerkopf.
Der Ersatz bildet die Gusskonstruktion aus dem Referenzvideo nach: kreisrunder
Lagerkopf mit tropfenformiger Einsatztasche (Kopfradius und Spitzenradius durch
tangentiale Flankenbogen verbunden, also ohne gerade Abschnitte),
Kreuzstege und vier Gusspads im Schalenboden (2.4 mm uber dem Boden erhaben,
Oberkante bei 4.4 mm ab der Aussenflache), Kammerarm mit durchgehender
Mittelwand, verschmolzene Schraubdome mit kegeligen Senkungen (ohne Absatz in
die 4-mm-Bohrung ubergehend) und zwei Fuhrungsschienen an den inneren Armwanden,
die vom Kammerboden bis 5.3 mm uber den Wandrand reichen. Der Bruchbereich ist
durch die massiven Schienen und die
durchgehende Bodenplatte deutlich steifer als der dunne Originalsteg.

Ab 16.08. zusatzlich verstarkt, nachdem die Taille als nachste Schwachstelle
auffiel:

- Die Aussenwand des Tropfens ist 0.2 mm dicker (1.85 -> 2.05). Weil alle drei
  Bogenmittelpunkte mit der Tasche geteilt werden, wachst die Wand
  ausschliesslich nach aussen; die Taschenkontur ist rechnerisch und per
  Volumenprobe identisch geblieben, der graue Einsatz passt also unverandert.
- Am Ubergang Arm zu Tropfen sass eine scharfe einspringende Ecke, dort wo die
  gerade Armflanke den Kopfkreis schneidet. Sie ist durch eine Hohlkehle mit
  R 8 ersetzt: die Kerbwirkung entfallt und der Querschnitt an der Taille waechst
  um rund 9.5 mm2.
- Die Kreuzstege im Schalenboden endeten frei vor der Wand (Langssteg 0.5 mm
  Luft am Armende, Quersteg 0.2 mm je Seite) und konnten so keine Last in die
  Wand einleiten. Jetzt laufen alle vier Stegenden 1.6 mm in die Wand hinein.
  Die Stege stutzen den Einsatz weiterhin nur von unten, die Taschenkontur
  bleibt unverandert.

## Druckvorgabe

1. Zuerst in PLA als Passprobe drucken und den grauen Einsatz einlegen.
2. Fur die Montage ASA verwenden: mindestens 5 Perimeter, 50-60 % Gyroid-Infill,
   0.2 mm Schichthohe und mit der Lageraussparung nach oben drucken.
3. Die Turerst nach erfolgreicher statischer Handprufung einhangen. Ein FDM-Teil
   ersetzt kein sicherheitszertifiziertes Beschlagteil; bei Rissen oder Spiel
   nicht weiter verwenden.