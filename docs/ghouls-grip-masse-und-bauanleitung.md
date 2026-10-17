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
| Ansichts-/Druckprojekte | `scripts/ghouls_grip.py` |
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
| Bodenlager-Doppelwangen (neue Konstruktionsschätzung) | Y=±40±8 mm; 4 mm dick; Außenradius 4,6 mm |
| Offener Armkanal / Arm-Axialspiel | 12 mm / 1,0 mm je Außenseite |
| Bodenlager-Bohrungssteg / Wurzel | 3,0 mm radial / 9,2 × 4,0 mm je Wange |
| Scherenwinkel | 18° bis 78° |
| Schlittenweg | 53,506 mm |
| Hub des Jochs | 48,177 mm |
| Deckelöffnung | 108° |
| Deckel-Zahnstange, neue Y-Pitch-Linie | 42,432 mm (vorher 57,286 mm) |
| Deckel-Transferachsen Y / Z | 46,146 und 53,573 mm / 93,000 mm |
| Transferzahnräder | 2 zusätzliche Teile, 6 Zähne, 4 mm Zahnbreite |
| Transferjournal / Lagerbohrung | Ø2,8 / Ø3,2 mm; 0,4 mm Durchmesserspiel |
| Totenkopf-Drehweg | 113,544° |
| Totenkopfknopf | 48,5 × 55,1 × 27,0 mm |
| Totenkopf-Schaft | Ø8 mm Presssitz, 0,2 mm Untermaß im Knopf |
| Handfläche | 67,9 × 96,5 × 25,2 mm |
| Fingerspitzen ausgefahren | 246,7 mm über Aufstellfläche |

Die Hand ist mit `HAND_SCALE = 0.72` aus einem anatomischen CT-Datensatz abgeleitet. Die größere Handfläche gegenüber der ursprünglichen 50 × 45-mm-Idee ist erforderlich, um Handwurzel- und Mittelhandknochen erkennbar zu erhalten.

### Reparatur der Bodenlager

Der alte 6–6,8 mm breite zentrale Pfosten passte nicht in den nur 2 mm
breiten Zwischenraum der unveränderten 4-mm-Arme bei Y=±40±3 mm.
Er ist durch zwei kurze, direkt mit dem Boden verschmolzene Lagerwangen
je Scherenpaar ersetzt, nicht durch beschnittene Arme.
X=0 mm, Pivot-Z=8 mm, Scherenabstand, alle Armbohrungen, Schlittenweg,
Hub, Deckelantrieb und die geschlossene Wandkorrektur bleiben unverändert.
Diese Änderung allein fügt keine Teile hinzu; den aktuellen Stand zeigt die Stückliste unten.

**Neue Werte sind Konstruktionsschätzungen/Default-Freiräume, keine Messwerte:**
Wangenmitten ±8 mm relativ zur Scherenebene, Dicke 4 mm, Kopf-Radius 4,6 mm.
Das ergibt einen offenen 12-mm-Kanal, 1 mm Abstand zur äußeren Armfläche,
3 mm radialen Reststeg um Ø3,2 mm und 36,8 mm² Fußquerschnitt je Wange.
Die Füße überlappen den 2-mm-Boden um 0,6 mm; die Kopfoberkante Z=12,6 mm
bleibt 0,4 mm unter der Zahnstangen-Unterseite Z=13 mm.
Lastpfad: Arm → unveränderter Pin → beide kurzen Wangen → Boden.
Die beidseitige Lagerung vermeidet einen einseitigen dünnen Kragzapfen.
Das belegt tragfähige **Geometrie**, nicht eine zulässige Nutzlast oder PLA-Dauerfestigkeit.

Die tatsächlich gedruckten Pins haben Ø2,7 mm Schaft (bisheriger Generator),
26 mm Länge und 1,6 mm Kopf; nicht Ø3,0 mm Schaft trotz der Teilebezeichnung.
Sie greifen über die vollen 4 mm beider Wangen, mit 0,5 mm nominalem
Durchmesserspiel. Der Prüfkörper belegt mindestens 0,2 mm radialen Freiraum.
Beide Bodenpins werden **von der Kistenmitte nach außen** eingesetzt;
der Kopf des positiven Y-Scherenpaars wurde in der exakten Ansicht nach innen
gespiegelt. Ein Einführen durch die geschlossene Außenwand ist unmöglich.
24 mm axialer Einführweg, senkrechtes Einsetzen der Arme und 0,4 mm
zusätzlich aufgeweitete Armhüllen wurden per Mesh-Boolean geprüft.
Zuerst die Bodenpins einsetzen, solange der mittlere Mechanikraum frei ist.
Die bisherigen gedruckten Pins besitzen keine neue Verriegelung:
Axialwanderung prüfen; optional vorhandene M3-Verbindung für Dauerbetrieb
mit passenden Muttern verwenden, nicht unbeaufsichtigt belasten.

Alle vier **einzelnen** Arme gegen die dekorierte Kiste in sämtlichen
61 Winkeln 18–78° einschließlich 48°: 0,000 mm³ bei drei Nachkommastellen;
maximal 0,000020464 mm³ numerischer Mesh-Rest je Arm an der tangentialen
Bodenberührung, deutlich unter der dokumentierten 0,001-mm³-Boolean-Toleranz.
Die Baseline bis 554,635 mm³ ist damit beseitigt. Wandfüllung weiterhin 100 %.
PLA-Passung, Loch-/Supportnacharbeit, Axialsicherung, belasteter Hub und
Verschleiß erfordern einen physischen Trocken-/Lasttest.

### Korrektur der hinteren Mechanikaussparung

Die bisherige 14 × 12 × 24-mm-Aussparung bei X=-27, Y=58, Z=75 mm ist
ersatzlos entfernt. Ursache waren der tiefe hintere Querträger der
Deckelzahnstange und der nach unten gerichtete Deckelkurbel-Schlüssel.
Die Zahnstange liegt jetzt um 14,854 mm weiter innen. Zwei zusätzliche
gleich große Zahnräder übertragen mit zwei Drehsinnwechseln 1:1 auf das
Deckelsegment an der unveränderten Scharnierachse. Der Kurbel-Schlüssel
zeigt nach innen, oberhalb des Kistenrands, und greift in eine passende
Unterseiten-Stecktasche im Deckel. Die Lagerzapfen bleiben innerhalb der
verbreiterten, geschlossenen Deckelhaube; die Kiste wurde nicht vergrößert.

Die Positionen sind aus dem bestehenden Radius
`LID_SECTOR_R = 7 mm / radians(108°)` abgeleitet: zwei Achsabstände von jeweils
`2 * LID_SECTOR_R`. Quelle/Vertrauen: bestehender parametrisierter
Bewegungsvertrag, rechnerisch exakt; keine aus Screenshots geschätzten Maße.
Die Ø2,8-/Ø3,2-mm-Journale übernehmen das vorhandene 0,4-mm-Laufspiel;
Zahnbreite 4 mm, Zahnstangen-Zahnbreite 1,6 mm, Zahnphase 15° und
2-mm-Haubendach und X-Seitenwände sind neue Konstruktionswerte, durch Mesh-/Bewegungsproben
geprüft, aber noch nicht durch einen PLA-Passungstest bestätigt.
Die Lager stehen auf kurzen, 4 mm dicken, von innen an die unveränderte
Hinterwand angeschlossenen Kragträgern bei Z=80–84 mm; die Lagerköpfe reichen
von Z=82 bis 96 mm. Das vermeidet zusätzliche hohe Bodenpfosten und erhält
die bestehende Leichtbaugrenze von 200.000 mm³ Schatullenvolumen.
Die asymmetrische Haube ist in X 29 mm breit und bei X=-30,5 mm zentriert:
Sie wächst ausschließlich nach links/innen, nicht in den mittleren Scharnierbock.
Die innere Servicekavität ist 25 mm breit; ihr Cutter bleibt innerhalb der
Haubenfläche. Die vollständige Dachhaut wurde mit einer Volumenprobe geprüft.
Diese Werte sind Konstruktionsentscheidungen, keine neuen gemessenen Gehäusedatums.

Der vollständige konservative Translations-Hüllkörper der Folge-Zahnstange
schneidet die Kiste nicht. 109 aktive Deckelstellungen prüfen zusätzlich
Zahnrad-/Zahnstangenfreiheit und Montage; der gekoppelte Gesamtvergleich
enthält 61 Scherenstellungen einschließlich 18°, 48° und 78°.
Siehe [Mechanik-Verifikation](ghouls-grip-mechanik-verifikation.md), einschließlich
des jetzt bestandenen Einzelarm-/Bodenlager-Nachweises und des historischen
Baseline-Vergleichs.

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

1. Der graue Totenkopf sitzt auf der D-Welle des Hauptritzels und ist mit einem
   1,75-mm-Filament-Querstift gesichert.
2. Eine Drehung um 113,5° verschiebt die Schlittenzahnstange um 53,5 mm.
3. Der Schlitten spreizt zwei parallele Scherenpaare von 18° auf 78° und hebt
   die Plattform (Hubjoch) um 48,2 mm.
4. Eine Kurvenbahn im Schlitten hebt den Deckel-Folger über die ersten 6 mm
   Schlittenweg um 7 mm und hält ihn danach auf einer Rast. Die Folger-
   Zahnstange dreht über zwei Übertragungsräder die Deckelkurbel am Scharnier;
   der Deckel steht bei 30° Scherenwinkel auf 108° und bleibt dann formschlüssig
   offen. Die Hand kreuzt den Deckel nicht.
5. Ein mitfahrendes Fünf-Zahnrad-Getriebe mit drei Zwischenrädern überträgt die
   Drehung eines Scherenarms auf den Unterarm (-105° → -45°).
6. Beim Zurückdrehen läuft die Kraftkette positiv rückwärts: Unterarm faltet
   ein, Schere sinkt, Deckel schließt. Es wird keine Rückstellfeder benötigt.

## Stückliste

Das Orca-Druckprojekt enthält **28 Teiltypen / 41 Druckobjekte** auf vier
Platten. Dazu kommen **sechs nicht gedruckte Filamentstifte** (1,75-mm-PLA vom
Spulenrest), die in Kollisions- und Eingriffsprüfung als Ø1,75-Zylinder
mitgeführt werden.

| Teil | Anzahl | Maße ungefähr | Farbe |
| --- | ---: | --- | --- |
| Schatulle | 1 | 209,0 × 130,5 × 98,0 mm | Schwarz |
| Deckel | 1 | 206,0 × 129,8 × 28,2 mm | Schwarz |
| Scherenarm | 4 | 84 × 12 × 4 mm | Naturweiß |
| Schlitten mit Zahnstange, Kurvenbahn und Schnappfingern | 1 | 120,3 × 118,8 × 20,8 mm | Naturweiß |
| Plattform (Hubjoch) | 1 | 83,5 × 92,6 × 48,5 mm | Naturweiß |
| Hauptantriebsritzel mit D-Welle | 1 | 55,8 × 55,7 × 28 mm | Naturweiß |
| Deckel-Folger mit Zahnstange | 1 | 91 × 12,6 × 6 mm | Naturweiß |
| Deckelkurbel (Segment mit Mitnehmer) | 1 | 9,2 × 20,6 × 11 mm | Naturweiß |
| Kurbel-Distanzhülse (axiale Sicherung auf der Scharnierachse) | 1 | Ø5 × 15,8 mm, Bohrung Ø2,0 | Naturweiß |
| Deckel-Übertragungsrad mit Zapfen und Bund | 2 | Ø9,2 × 18 mm | Naturweiß |
| Scheren-Eingangszahnrad | 1 | 25,8 × 25,8 × 11,5 mm | Naturweiß |
| Zwischenrad | 3 | Ø16,5 × 6 mm | Naturweiß |
| Unterarm-Abtriebsrad mit D-Welle | 1 | 25,8 × 75 × 25,8 mm | Naturweiß |
| Schnappstift Ø4 Boden (Klemmlänge 18,4) | 2 | Ø7,5 × 21,6 mm | Naturweiß |
| Schnappstift Ø4 Schlitten (11,2) | 2 | Ø7,5 × 14,4 mm | Naturweiß |
| Schnappstift Ø4 Mitte (8,4) | 2 | Ø7,5 × 11,6 mm | Naturweiß |
| Schnappstift Ø4 Zahnrad (16,4) | 1 | Ø7,5 × 19,6 mm | Naturweiß |
| Schnappstift Ø4 kurz (6,8) | 3 | Ø7,5 × 10,0 mm | Naturweiß |
| Schnappstift Ø4 Zwischenrad (11,4) | 3 | Ø7,5 × 14,6 mm | Naturweiß |
| Pressstift Ø4 Folger (Quetschrippen) | 1 | Ø7,5 × 11,8 mm | Naturweiß |
| Unterarm mit D-Nabe | 1 | 25,8 × 18 × 50 mm | Knochenbeige |
| Handfläche | 1 | 67,9 × 96,5 × 25,2 mm | Knochenbeige |
| Fünf Finger | je 1 | 36–66 mm | Knochenbeige |
| Totenkopf-Drehknopf | 1 | 48,5 × 55,1 × 27,0 mm | Grau |

**Nicht gedruckte Teile (Filament Ø1,75 mm, abgelängt):**

| Stift | Länge | Bohrung | Ort |
| --- | ---: | --- | --- |
| Deckelscharnier | 198 mm | Ø1,9 Truhe / Ø1,98 Deckel | Scharnierachse, durch alle Knöchel |
| Knauf-Querstift | 14 mm | Ø1,9 | Knauf und Ritzel-D-Welle |
| Übertragungsrad-Sicherung | 2 × 5 mm | Ø1,9 | Zapfen außen am Lagerbock |
| Abtriebswellen-Sicherung | 10 mm | Ø1,9 | D-Welle am Plattformlager |
| Handgelenk | 16 mm | Ø1,9 | Unterarmzapfen und Handfläche |

Die frühere separate Sehnenführung, die starre Deckel-Hauptzahnstange und die
Ø3-Pins sind entfallen.

## Verbinder und formschlüssige Schnittstellen

| Verbindung | Verbinder | Montageprinzip |
| --- | --- | --- |
| Scherenarme, Schlitten, Plattform, Zahnräder | 14 gedruckte Ø4-Schnappstifte in 7 Klemmlängen in Ø4,6-Bohrungen | geschlitzter Schaft mit Rastnase; von der Kopfseite einschieben, bis die Nase hinter der Gegenfläche einrastet (0,25 mm Hinterschnitt) |
| Folger im Kurvenschlitz | massiver Ø4-Pressstift mit Quetschrippen | von innen durch den Folger in den Schlitz drücken |
| Schlitten in der Schiene | zwei integrierte Schnappfinger | senkrecht aufdrücken, Finger rasten in die Nut |
| Unterarm in Plattform | D-Welle des Abtriebsrads + Filamentstift 10 mm | Unterarm zwischen die Ohren, Welle axial einschieben, außen sichern |
| Handfläche am Unterarm | 11,6-mm-Zapfen in Ø12-Aufnahme + Filamentstift 16 mm | Querbohrungen fluchten lassen, Stift quer einsetzen |
| Finger an Handfläche | beschriftete MCP-Steckzapfen | in Druckrichtung aufstecken |
| Deckel am Gehäuse | Filament 198 mm als Scharnierachse | von der Stirnseite durch alle Knöchel, Kurbel und Distanzhülse schieben |
| Totenkopf am Hauptritzel | D-Welle + Filamentstift 14 mm | Knauf aufstecken, Querstift einsetzen |
| Übertragungsräder | Zapfen Ø2,8 in Ø3,2-Lagerbock, Bund innen, Filamentstift 5 mm außen | axial in -X einschieben, Stift außen quer |

Alle Steckspiele, Rastnasen-Dehnungen, Einführwege und Zahnflankenspiele sind
in [`ghouls-grip-montage-audit.md`](ghouls-grip-montage-audit.md) gegen die
Druckungenauigkeit (±0,1–0,2 mm) nachgewiesen.

## Montage

1. Truhe auf den Tisch, Öffnung oben.
2. Schlitten senkrecht auf die Schiene drücken, bis beide Schnappfinger in die
   Nut einrasten. Er muss frei zwischen beiden Endlagen laufen.
3. Antriebsritzel von innen axial durch die Vorderwand-Bohrung schieben; es
   kämmt mit der Schlittenzahnstange.
4. Totenkopfknauf in geschlossener Stellung (Gesicht senkrecht) auf die D-Welle
   stecken und mit Filamentstift 14 mm quer sichern.
5. Deckel-Folger in den Führungskanal absenken; den Folger-Pressstift von innen
   durch den Folger in den Kurvenschlitz drücken.
6. Beide Deckel-Übertragungsräder axial in -X in die Lagerböcke schieben, bis
   der Bund innen anliegt; außen je Filamentstift 5 mm quer durch den Zapfen.
7. Scherenarme je Ebene einsetzen; Boden-, Schlitten- und Mittelstifte mit dem
   Kopf innen einschnappen.
8. Scheren-Eingangszahnrad **vor** der Plattform setzen: von +Y auf das obere
   Armauge schieben, Passstift ins Armloch drücken, dann nach oben in Lage.
9. Plattform-Baugruppe außerhalb vormontieren: Unterarm zwischen die Ohren,
   Abtriebsrad-D-Welle durchschieben, Filament-Sicherungsstift 10 mm, drei
   Zwischenräder mit Zwischenradstiften. Baugruppe senkrecht absenken, dabei
   3 mm vom Scheren-Eingangszahnrad weg (Richtung Zwischenrad 0) versetzt;
   dann entlang der Achsverbindung in den Eingriff schieben. Die Achsverbindung
   liegt 64° zur Senkrechten, ein gerades Absenken würde Zahn auf Zahn treffen.
   Zahnrad-, Fest- und Langlochstifte oben einschnappen.
10. Handfläche auf den Unterarmzapfen schieben (um -75° gerollt), Filamentstift
    16 mm quer. Finger auf ihre beschrifteten Sockel setzen.
11. Deckel-Baugruppe außerhalb vormontieren: Deckel umgedreht, Deckelkurbel von
    unten einlegen und 5,6 mm in +X in die Mitnehmertasche schieben; die
    Kurbel-Distanzhülse von unten in den Servicekanal zwischen Kurbel und
    Deckelauge legen. (Bei aufgesetztem Deckel ist der Kanal geschlossen und die
    Kurbel nicht mehr einsetzbar.)
12. Deckel-Baugruppe etwa 108° geöffnet halten, 3 mm nach hinten (+Y) versetzt
    senkrecht absenken, dann nach vorn in den Eingriff mit dem Zwischenrad
    schieben, bis die Gelenkaugen fluchten. Das 198-mm-Scharnierfilament von
    der Stirnseite durch Truhe, Deckel, Kurbel und Hülse schieben. Die Hülse
    hält die Kurbel axial im Eingriff (Spiel +0,2/−0,1 mm).
13. Ohne Süßigkeiten langsam testen: Totenkopf drehen → Deckel öffnet früh →
    Schere hebt → Unterarm entfaltet. Danach exakt rückwärts drehen.

Zum Zerlegen in umgekehrter Reihenfolge: Schnappstifte durch Zusammendrücken
der Schlitzhälften von der Nasenseite lösen; Filamentstifte herausziehen.
## Druckprojekte

- `models/ghouls-grip-view.3mf` – zusammengesetzte Ansichten auf drei Platten:
  vollständig ausgefahren (78°), Zwischenzustand (48°) und eingefahren (18°).
- `models/ghouls-grip-print.3mf` – ein Orca-Projekt für alle 41 Druckobjekte
  mit vier Filament-/Farbzuordnungen auf vier nach Farbe und Baugruppe
  gruppierten Druckplatten.
- `models/ghouls-grip-preview.stl` – Canvas-Vorschau.

Im geschlossenen Zustand liegt die vollständige interne Deckelmechanik unter
einer mit dem Deckel vereinigten schwarzen Schutzhaube. Der Montagekanal ist
nur zur Boxinnenseite offen; von oben besteht eine durchgehende 2,0-mm-Dachhaut.
Deckelkurbel und Yoke wurden zusätzlich als eigene Kollisionspaare über den
gesamten Hub geprüft und schneiden weder Deckel noch Schatulle.

Das erhaltene Nutzerprojekt verwendet PLA, Anycubic Kobra S1 0.4,
0,20 mm Schichthöhe und vier eingebettete Farben. Seine tatsächlichen
Werte sind High Temp Plate, aligned seam, kein Bügeln und global Support aus
(Objekt-Overrides aktivieren Support). Sie wurden nicht zurückgesetzt;
Profilkonformität bleibt `not-verified`. Die exakten Slice-Ergebnisse stehen in
[`ghouls-grip-druckvalidierung.md`](ghouls-grip-druckvalidierung.md).

### Generator-Defaults (nicht die erhaltenen Nutzereinstellungen)

Diese Optionen gelten für neu angelegte Mehrfarben-Projekte und werden durch
`tests/test_ghouls_grip_orca_settings.py` abgesichert:

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
| Prime Tower | aus, da jede Druckplatte nur einer Farbe/Spule zugeordnet ist |

Schwarz, Knochen und Grau verwenden automatische Baumstützen. Die
naturweißen Mechanikplatten verwenden `normal(auto)` mit `snug`, weil Zahnstangen,
Rahmenöffnungen und Verbinder damit reproduzierbarer abgestützt werden.
Objekt-Overrides steuern Wände, Infill, Geschwindigkeit und Beschleunigung;
kein Override deaktiviert Support.

## Sicherheit und verbleibende Risiken

- Die Bewegung ist direkt handgeführt und nicht federgetrieben. Trotzdem Hände aus Schere, Zahnrädern und Deckelscharnier halten.
- Der größere Totenkopf liefert weniger Hebelübersetzung als der verworfene lange Hebel. Den Mechanismus zuerst ohne Hand und Deckel trocken einlaufen lassen; Grate entfernen, nicht mit Gewalt drehen.
- Vor dem Gesamtdruck einen Arm, einen kleinen/großen Pin und ein Zahnrad als Passungsmuster drucken.
- Gedruckte Pins und 0,8-mm-PLA-Flexuren sind Verschleißteile.
- Die Konstruktion ist kein geprüftes Kinderspielzeug.
- Die separate Bestandskollision `scissors_chest` an den ursprünglichen
  Bodenlagern ist unverändert vorhanden. Die Wandkorrektur ist deshalb keine
  Freigabe der vollständigen Mechanik für einen Funktionsdruck.

## Lizenz der Handgeometrie

Die Hand basiert auf **“Wrist Bones Full Hand – Human Skeleton”**, NIH 3D Print Exchange, Modell `3DPX-016815`, hochgeladen von My Segmenter, **CC BY 4.0**. Im Repository liegt nur der abgeleitete Datensatz `model-sources/ghouls-grip/reference/hand_bones.npz`. Fitkritische Anschlüsse, Flexuren, Lager, Zahnräder und Gehäuse sind eigenständige parametrische Konstruktionen.
