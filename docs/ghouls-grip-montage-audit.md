# Ghoul's Grip - Montage- und Mechanik-Audit

Automatisch erzeugt von `scripts/audit_ghouls_grip_assembly.py`. Alle Pruefungen laufen auf den exakten Szenen-Meshes (`render_ghouls_grip.build_scene_at`) mit manifold-Booleans.

Toleranzannahmen (Kobra S1, 0.4 mm Duese, 0.2 mm Schicht): radiales Spiel >= 0.2 mm je Seite, axiales Spiel >= 0.1 mm, Flankenspiel >= 0.1 mm je Richtung, Schnapp-Dehnung <= 2 %, Kollision > 0.5 mm3 = FAIL, Einschub-/Montage-Huellen > 0.05 mm3 = FAIL.
## Ergebnis

**Gesamt: PASS** (172 s)

| Pruefung | Status |
| --- | --- |
| Stueckliste vollstaendig, nichts ueberzaehlig | PASS |
| Nicht gedruckte Filamentstifte passen und halten | PASS |
| Keine Kollision im Bewegungsbereich | PASS |
| Schnappstifte: radiales/axiales Spiel | PASS |
| Stifte einsteckbar (Einschub- und Fingerraum) | PASS |
| Montagewege aller Baugruppen frei | PASS |
| Fuehrungs- und Axialspiel der beweglichen Teile | PASS |
| Zahnraeder kaemmen mit Flankenspiel | PASS |
| Rastnasen/Widerhaken/Pressrippen dimensioniert | PASS |
| Deckel-Kurvengetriebe klemmt nicht | PASS |


## 1. Stueckliste (gedruckt)

**PASS** - 42 Druckobjekte im Druckprojekt, 42 Teile in der Baugruppe.

| Teil | im Druckprojekt | in der Baugruppe |
| --- | ---: | ---: |
| candy-dish | 1 | 1 |
| chest | 1 | 1 |
| crank-spacer | 1 | 1 |
| drive-pinion | 1 | 1 |
| drive-skull-knob | 1 | 1 |
| forearm | 1 | 1 |
| forearm-output-gear | 1 | 1 |
| hand-finger-index | 1 | 1 |
| hand-finger-little | 1 | 1 |
| hand-finger-middle | 1 | 1 |
| hand-finger-ring | 1 | 1 |
| hand-finger-thumb | 1 | 1 |
| hand-palm | 1 | 1 |
| idler-gear | 3 | 3 |
| lid | 1 | 1 |
| lid-crank | 1 | 1 |
| lid-follower-rack | 1 | 1 |
| lid-transfer-gear | 2 | 2 |
| pivot-pin-centre | 2 | 2 |
| pivot-pin-floor | 2 | 2 |
| pivot-pin-follower | 1 | 1 |
| pivot-pin-gear | 1 | 1 |
| pivot-pin-idler | 3 | 3 |
| pivot-pin-short | 3 | 3 |
| pivot-pin-slider | 2 | 2 |
| platform | 1 | 1 |
| scissor-arm | 4 | 4 |
| scissor-drive-gear | 1 | 1 |
| slider | 1 | 1 |

Fehlend: keine; ueberzaehlig: keine; Stift-Mengen-Abweichung: keine.

## 2. Nicht gedruckte Teile (1.75 mm PLA-Filament)

**PASS** - Stift-Ersatzkoerper Ø1.75 in den Szenen bei Theta 18/48/78: keine Kollision, und jedes Wirtsteil hat Material um den Stift (Ring +0.6 mm > 1 mm3).

| Stift | Laenge mm | Zweck | Wirte (gehalten) | Kollision | Status |
| --- | ---: | --- | --- | --- | --- |
| hinge | 198 | Deckelscharnier-Achse (Truhe Ø1.9, Deckel/Kurbel/Distanzhuelse Ø2.0) | chest (ja), lid (ja), lid-crank (ja), crank-spacer (ja) | - | PASS |
| knob-cross | 14 | Querstift Schaedelknauf/Ritzelwelle | drive-pinion (ja), drive-skull-knob (ja) | - | PASS |
| transfer-input-journal | 5 | Axialsicherung Deckel-Uebertragungsrad (Eingang) | lid-transfer-input (ja) | - | PASS |
| transfer-idler-journal | 5 | Axialsicherung Deckel-Uebertragungsrad (Zwischenrad) | lid-transfer-idler (ja) | - | PASS |
| forearm-retainer | 10 | Axialsicherung Unterarm-D-Welle | forearm-output-gear (ja) | - | PASS |
| wrist | 16 | Handgelenk-Querstift | forearm (ja), hand-palm (ja) | - | PASS |

## 3. Kollisionen im Bewegungsbereich

| Theta | Kontakte | Soll-Pressungen | Kollisionen | groesste unbeabsichtigte mm3 |
| ---: | ---: | --- | ---: | ---: |
| 18 | 2 | lid-follower-rackxpivot-pin-follower 0.89 | 0 | 0.026 |
| 25 | 2 | lid-follower-rackxpivot-pin-follower 0.89 | 0 | 0.026 |
| 30 | 2 | lid-follower-rackxpivot-pin-follower 0.89 | 0 | 0.026 |
| 36 | 2 | lid-follower-rackxpivot-pin-follower 0.89 | 0 | 0.026 |
| 48 | 2 | lid-follower-rackxpivot-pin-follower 0.89 | 0 | 0.026 |
| 60 | 2 | lid-follower-rackxpivot-pin-follower 0.89 | 0 | 0.026 |
| 78 | 2 | lid-follower-rackxpivot-pin-follower 0.89 | 0 | 0.026 |

**PASS** - groesste unbeabsichtigte Ueberschneidung 0.026 mm3 (Netz-Rauschen/Flaechenkontakt).

## 4. Spiel der Schnappstifte im eingebauten Zustand (Theta 48)

**PASS** - freie Verschiebung bis zum ersten Kontakt.

| Stift | radial min mm (+x,-x,+z,-z) | axial gesamt mm | Nachbarn | Status |
| --- | --- | ---: | --- | --- |
| pivot-pin-floor-0 | 0.30 (0.30, 0.30, 0.30, 0.37) | 0.20 | chest, slider, arm-0-False, arm-0-True | PASS |
| pivot-pin-slider-0 | 0.30 (0.30, 0.30, 0.30, 0.37) | 0.20 | chest, slider, arm-0-False, arm-0-True | PASS |
| pivot-pin-centre-0 | 0.30 (0.30, 0.30, 0.31, 0.38) | 0.20 | chest, arm-0-False, arm-0-True | PASS |
| pivot-pin-fixed-0 | 0.30 (0.30, 0.30, 0.31, 0.37) | 0.20 | chest, arm-0-False, arm-0-True, platform | PASS |
| pivot-pin-slot-0 | 0.31 (0.31, 0.31, 0.32, 0.38) | 0.21 | chest, arm-0-False, platform | PASS |
| pivot-pin-floor-1 | 0.30 (0.30, 0.30, 0.37, 0.30) | 0.20 | chest, slider, arm-1-False, arm-1-True | PASS |
| pivot-pin-slider-1 | 0.30 (0.30, 0.30, 0.37, 0.30) | 0.20 | chest, slider, arm-1-False, arm-1-True | PASS |
| pivot-pin-centre-1 | 0.30 (0.30, 0.30, 0.38, 0.31) | 0.20 | chest, arm-1-False, arm-1-True | PASS |
| pivot-pin-fixed-1 | 0.30 (0.30, 0.30, 0.37, 0.30) | 0.20 | chest, arm-1-False, arm-1-True, platform, scissor-drive-gear | PASS |
| pivot-pin-slot-1 | 0.31 (0.31, 0.31, 0.38, 0.32) | 0.21 | chest, arm-1-False, platform | PASS |
| pivot-pin-idler-0 | 0.21 (0.21, 0.21, 0.21, 0.37) | 0.20 | chest, platform, idler-gear-0 | PASS |
| pivot-pin-idler-1 | 0.21 (0.21, 0.21, 0.21, 0.37) | 0.20 | chest, platform, idler-gear-1 | PASS |
| pivot-pin-idler-2 | 0.21 (0.21, 0.21, 0.21, 0.37) | 0.20 | chest, lid, platform, idler-gear-2 | PASS |
| pivot-pin-follower | 0.31 (1.50, 1.50, 0.70, 0.31) | Pressstift, Rippen 0.89 mm3 | chest, slider, lid-follower-rack | PASS |

## 5. Einsteckbarkeit der Stifte

**PASS** - exakte Einschub-Huelle: geschlossene Widerhaken r 2.2 mm vom Ansatz bis zur Spitze plus Kopf r 3.75 mm mit 8 mm Finger-/Zangenraum, gegen alle zu diesem Montageschritt schon verbauten Teile.

| Stift | Variante | frei bei Theta | Treffer (falls nicht frei) |
| --- | --- | --- | --- |
| pivot-pin-floor-0 | floor | [18.0] | - |
| pivot-pin-slider-0 | slider | [18.0] | - |
| pivot-pin-centre-0 | centre | [18.0] | - |
| pivot-pin-fixed-0 | short | [18.0] | - |
| pivot-pin-slot-0 | short | [18.0] | - |
| pivot-pin-floor-1 | floor | [18.0] | - |
| pivot-pin-slider-1 | slider | [18.0] | - |
| pivot-pin-centre-1 | centre | [18.0] | - |
| pivot-pin-fixed-1 | gear | [18.0] | - |
| pivot-pin-slot-1 | short | [18.0] | - |
| pivot-pin-idler-0 | idler | [18.0] | - |
| pivot-pin-idler-1 | idler | [18.0] | - |
| pivot-pin-idler-2 | idler | [18.0] | - |
| pivot-pin-follower | follower | [18.0] | - |

## 6. Montagewege (schrittweise Bewegungs-Huellen, 1.5 mm)

**PASS**

| Montageschritt | frei bei Theta | Treffer |
| --- | --- | --- |
| Schlitten senkrecht einsetzen (ohne Rastnasen) | [18.0] | - |
| Ritzel axial von innen, dann nach oben heraus | [18.0] | - |
| Schaedelknauf axial auf die D-Welle | [18.0] | - |
| lid-transfer-input: Zapfen axial in Lagerbock, dann nach oben | [18.0] | - |
| lid-transfer-idler: Zapfen axial in Lagerbock, dann nach oben | [18.0] | - |
| Scherenarm-Paar Ebene 0 senkrecht absenken | [18.0] | - |
| Scherenarm-Paar Ebene 1 senkrecht absenken | [18.0] | - |
| Scherenantriebsrad: Passstift aus Armloch, dann nach oben | [48.0] | - |
| Plattform-Baugruppe versetzt absenken, radial in Eingriff | [78.0] | - |
| Hand axial vom Unterarm-Zapfen | [78.0] | - |
| Deckelkurbel am losen Deckel: von unten, dann +X in die Tasche | [48.0] | - |
| Distanzhuelse am losen Deckel von unten in den Kanal | [48.0] | - |
| Deckel-Baugruppe geoeffnet: 3 mm hinten absenken, nach vorn in Eingriff | [48.0] | - |

## 7. Fuehrungs- und Axialspiel (Theta 48)

**PASS** - Summe beider Richtungen 0.1 .. 2.9 mm (3.0 = nicht gefuehrt).

| Teil | +/- mm | gesamt | Status |
| --- | --- | ---: | --- |
| Schlitten in Schiene (quer Y) | 0.60, 0.60 | 1.20 | PASS |
| Schlitten in Schiene (Z) | 0.50, 0.20 | 0.70 | PASS |
| Folger im Kanal (X) | 0.40, 0.40 | 0.80 | PASS |
| Folger im Kanal (Y) | 0.40, 0.40 | 0.80 | PASS |
| Ritzel+Knauf axial (Y) | 0.40, 0.50 | 0.90 | PASS |
| Uebertragungsrad Eingang axial (X) | 0.36, 0.21 | 0.57 | PASS |
| Uebertragungsrad Zwischen axial (X) | 0.36, 0.21 | 0.57 | PASS |
| Abtriebsrad+Welle axial (Y) | 1.65, 0.40 | 2.05 | PASS |
| Deckelkurbel axial (X, Huelse) | 0.20, 0.10 | 0.30 | PASS |
| Distanzhuelse axial (X) | 0.10, 0.10 | 0.20 | PASS |
| Zwischenrad 0 axial (Y) | 0.00, 0.40 | 0.40 | PASS |
| Zwischenrad 1 axial (Y) | 0.00, 0.40 | 0.40 | PASS |
| Zwischenrad 2 axial (Y) | 0.00, 0.40 | 0.40 | PASS |

## 8. Flankenspiel der Zahnraeder

**PASS** - Spiel je Drehrichtung am Teilkreis; 'eingegriffen' = Anschlag vor dem Suchlimit.

| Theta | Paarung | + mm | - mm | eingegriffen | Status |
| ---: | --- | ---: | ---: | --- | --- |
| 18 | pinion-rack | 0.24 | 0.22 | ja | PASS |
| 18 | transfer-idler | 0.69 | 0.50 | ja | PASS |
| 18 | idler-crank | 0.69 | 0.50 | ja | PASS |
| 18 | scissor-drive-gear~idler-gear-0 | 0.51 | 0.51 | ja | PASS |
| 18 | idler-gear-0~idler-gear-1 | 0.63 | 0.62 | ja | PASS |
| 18 | idler-gear-1~idler-gear-2 | 0.53 | 0.53 | ja | PASS |
| 18 | idler-gear-2~forearm-output-gear | 0.59 | 0.59 | ja | PASS |
| 18 | follower-rack~transfer | 0.38 | 0.24 | ja | PASS |
| 48 | pinion-rack | 0.22 | 0.22 | ja | PASS |
| 48 | transfer-idler | 0.47 | 0.44 | ja | PASS |
| 48 | idler-crank | 0.64 | 0.48 | ja | PASS |
| 48 | scissor-drive-gear~idler-gear-0 | 0.71 | 0.49 | ja | PASS |
| 48 | idler-gear-0~idler-gear-1 | 0.57 | 0.49 | ja | PASS |
| 48 | idler-gear-1~idler-gear-2 | 0.70 | 0.56 | ja | PASS |
| 48 | idler-gear-2~forearm-output-gear | 0.51 | 0.43 | ja | PASS |
| 48 | follower-rack~transfer | 0.57 | 0.54 | ja | PASS |
| 78 | pinion-rack | 0.22 | 0.22 | ja | PASS |
| 78 | transfer-idler | 0.47 | 0.44 | ja | PASS |
| 78 | idler-crank | 0.64 | 0.48 | ja | PASS |
| 78 | scissor-drive-gear~idler-gear-0 | 0.45 | 0.62 | ja | PASS |
| 78 | idler-gear-0~idler-gear-1 | 0.51 | 0.75 | ja | PASS |
| 78 | idler-gear-1~idler-gear-2 | 0.47 | 0.63 | ja | PASS |
| 78 | idler-gear-2~forearm-output-gear | 0.47 | 0.74 | ja | PASS |
| 78 | follower-rack~transfer | 0.57 | 0.54 | ja | PASS |

## 9. Rastnasen, Widerhaken, Pressrippen

**PASS**

* Widerhaken geschlossen r 2.20 in Bohrung r 2.30: 0.10 mm Einschubspiel; entspannt r 2.55: 0.25 mm Hinterschnitt; Senkung r 3.0: 0.45 mm frei.
* Pressstift Folger: Rippen r 2.45 in r 2.30 = 0.15 mm Uebermass (kein Widerhaken, Druck-Toleranz wird von den Rippen aufgenommen).
* Schlitten-Schnappfinger: Auslenkung 1.4 mm, Dicke 1.6 mm, Laenge 23.5 mm -> Dehnung 0.61 % (PASS).

| Stift | Klemmlaenge mm | Federlaenge mm | c mm | Dehnung % | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| floor | 18.4 | 7.20 | 0.76 | 1.53 | PASS |
| slider | 11.2 | 7.20 | 0.76 | 1.53 | PASS |
| centre | 8.4 | 7.20 | 0.76 | 1.53 | PASS |
| gear | 16.4 | 7.20 | 0.76 | 1.53 | PASS |
| short | 6.8 | 6.40 | 0.76 | 1.94 | PASS |
| idler | 11.4 | 7.20 | 0.76 | 1.53 | PASS |

## 10. Lastpfad Deckel (Abschaetzung, Risiko statt Beweis)

Deckel 128 cm3 Volumen, Schwerpunkt 63 mm vor der Scharnierachse. Kurvensteigung max 49.4 deg, Reibwinkel 16.7 deg (mu 0.3) -> PASS (Summe < 80 deg).

| Fall | Masse g | Moment Nm | Zahnstange N | Schlitten N | Knauf Nm | Fingerkraft N am Knauf | Zahnfuss-Spannung MPa (Lewis, 4 mm Rad) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| realistisch (60 % Fuellung) | 95 | 0.059 | 21.6 | 48.8 | 1.32 | 67.6 | 24.3 |
| obere Grenze (massiv) | 159 | 0.098 | 36.1 | 81.4 | 2.20 | 112.7 | 40.5 |

Die kleinen 6-Zahn-Raeder (r 3.7 mm) der Deckeluebertragung sind das hoechstbelastete Glied; PLA in Schichtebene ~50 MPa, also Sicherheit ~2-3. Bei Probedruck auf Zahnbruch/Ueberspringen achten; ggf. Deckel leichter (weniger Fuellung) drucken.

## 11. Montagereihenfolge (geprueft in Abschnitt 5/6)

1. Truhe (chest) auf den Tisch, Oeffnung oben.
2. Schlitten (slider) senkrecht auf die Schiene druecken, bis beide Schnappfinger in die Nut einrasten.
3. Antriebsritzel von innen axial durch die Vorderwand-Bohrung schieben (Zahnstange kaemmt).
4. Schaedelknauf auf die D-Welle stecken, Filamentstift Ø1.75 x 14 quer durch Knauf und Welle.
5. Deckel-Folger in den Fuehrungskanal absenken; Folger-Pressstift von innen durch Folger in den Kurvenschlitz druecken.
6. Beide Deckel-Uebertragungsraeder axial (-X) in die Lagerboecke, je Filamentstift Ø1.75 x 5 aussen quer durch den Zapfen.
7. Scherenarme je Ebene einsetzen; Boden-, Schlitten- und Mittelstifte von innen (Kopf innen) einschnappen.
8. Scherenantriebsrad von +Y auf das obere Armauge setzen, Passstift in das Armloch druecken (vor der Plattform!).
9. Plattform-Baugruppe ausserhalb vormontieren: Unterarm zwischen die Ohren, Abtriebsrad-D-Welle durch, Filament-Sicherungsstift Ø1.75 x 10, drei Zwischenraeder mit Idler-Stiften. Senkrecht absenken, dabei 3 mm vom Scherenantriebsrad weg versetzt (Richtung Zwischenrad 0), dann entlang der Achsverbindung in Eingriff schieben; Zahnrad-/Fest-/Langlochstifte oben einschnappen.
10. Hand auf den Unterarm-Zapfen, Filamentstift Ø1.75 x 16 quer.
11. Deckel-Baugruppe ausserhalb vormontieren: Deckel umgedreht, Deckelkurbel von unten einlegen und in +X in die Mitnehmertasche schieben; Distanzhuelse von unten in den Servicekanal zwischen Kurbel und Deckelauge legen.
12. Deckel-Baugruppe ~108 Grad geoeffnet halten, 3 mm nach hinten (+Y) versetzt senkrecht absenken, dann nach vorn in den Eingriff mit dem Zwischenrad schieben, bis die Gelenkaugen fluchten; Scharnier-Filament Ø1.75 x 198 durch Truhe, Deckel, Kurbel und Huelse schieben.

