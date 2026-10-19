# Ghoul's Grip – Quellen und Lizenzen

## Totenkopf-Akzent

### Suchumfang

Vor der Überarbeitung wurden am 10. Oktober 2026 folgende Suchbegriffe
verwendet:

- `human skull anatomical scan CC BY STL`
- `NIH 3D Print Exchange human skull CC BY`
- `Smithsonian Open Access human skull 3D scan CC0`
- `human skull CT scan Printables license`

Gesucht wurde zuerst nach einem anatomischen Scan mit einer Lizenz, die
Bearbeitung und Weiterverteilung des abgeleiteten Repository-Inhalts erlaubt.

### Kandidaten

| Kandidat | Urheber / Primärquelle | Lizenz und Rechte | Dateien / Qualität | Bewertung |
| --- | --- | --- | --- | --- |
| **Skull_Human Skeleton**, `3DPX-016801` | My Segmenter, [NIH 3D](https://3d.nih.gov/entries/3DPX-016801/3), Metadaten: [NIH-API](https://3d.nih.gov/api/entries/16801) | **CC BY 4.0**. Bearbeitung, kommerzielle Nutzung und Weiterverteilung sind mit Namensnennung, Lizenzlink und Änderungshinweis erlaubt: [Lizenztext](https://creativecommons.org/licenses/by/4.0/). | CT-Segmentierung; STL, OBJ, GLB, X3D, WRL und BLEND. Das veröffentlichte STL hat 613.916 Dreiecke, 306.736 Punkte, ist laut NIH-Metadaten wasserdicht und hat keine nichtmanifold Kanten. Direkter NIH-API-Download der geprüften STL-Version: `https://3d.nih.gov/api/files/1058705`. | **Sehr gute anatomische Referenz**, aber kein zweckmäßiger Mesh-Baustein für diesen 48,5-mm-Drehknopf. |
| **Human skull CT scan**, Modell `731166` | Andrzejerzy, [Printables](https://www.printables.com/model/731166-human-skull-ct-scan) | Die Modellseite war bei der Prüfung automatisiert nicht abrufbar; die konkrete Modelllizenz und Weiterverteilungspflichten konnten daher nicht aus der Primärquelle verifiziert werden. | STL, etwa 70 MB; laut Suchindex CT-basiert und mit Halswirbeln. Topologie und Maßstab wurden nicht heruntergeladen oder geprüft. | **Abgelehnt**: unbestätigte Lizenz; Halswirbel und vollständige Scan-Geometrie passen außerdem nicht zum Akzent. |
| **Open3DModel – Skull** | Open3DModel / AnatomyTOOL, [Projektseite](https://anatomytool.org/content/open3dmodel-skull-english-labels) | Suchindex nennt CC BY-SA; die konkrete Primärseite war bei der Prüfung nicht abrufbar, daher wurden Version, Urheberkette und Share-Alike-Text nicht ausreichend verifiziert. | Lehrmodell, unter anderem als GLB. Kein geprüfter druckbarer Einzelkörper oder reproduzierbarer Direktdownload ermittelt. | **Abgelehnt**: Provenienz und konkrete Download-Lizenz nicht ausreichend verifiziert. |

### Entscheidung: `reference-only`

Der NIH-Scan ist lizenzkompatibel, wurde aber **nicht in das Repository
übernommen**. Eine lokale Hybridprobe zeigte, warum:

- Das Scan-STL enthält 613.916 Dreiecke und elf zusätzliche winzige
  Acht-Dreieck-Fragmente neben dem Hauptkörper.
- Der vollständige Scan besitzt viele echte anatomische Öffnungen und innere
  Hohlräume (`Euler-Zahl -222`). Nach Skalierung, Reliefschnitt und Verbindung
  mit dem Knopfrücken blieb die Probe zwar ein Körper, hatte aber noch 556.272
  Dreiecke und `Euler-Zahl -246`.
- Bei nur etwa 48,5 × 55,1 mm würden die dünnen Siebbein-, Zahn- und
  Orbitalstrukturen unterhalb sinnvoll druckbarer Detailstärken liegen. Eine
  notwendige starke Voxelreparatur würde die Scanoberfläche so weit verändern,
  dass gegenüber einer kontrollierten parametrischen Rekonstruktion kein
  verlässlicher Vorteil bleibt.

Darum verwendet `scripts/skull.py` den Scan ausschließlich als anatomische
Formreferenz. Die überarbeitete Eigenkonstruktion ergänzt insbesondere
Supraorbitalleisten, Jochbein-Pfeiler, Oberkieferbogen, aufsteigende
Unterkieferäste, ovale Augenhöhlen, eine piriforme Nasenöffnung und feinere
Zahnzwischenräume. Flansch, Rippe, Schaft und die blinde Ø8-mm-Aufnahme bleiben
vollständig parametrisch und unverändert fitkritisch.

Für den NIH-Scan besteht keine Attributionspflicht im ausgelieferten Modell,
weil keine Scan-Geometrie verteilt wird. Falls er später doch als Mesh-Basis
verwendet wird, muss mindestens folgende Angabe erhalten bleiben:

> “Skull_Human Skeleton” (`3DPX-016801`) by My Segmenter, NIH 3D,
> licensed under CC BY 4.0; modified for Ghoul's Grip.

## Gotische Truhenornamente

### Suchumfang und Kandidaten

Vor der Überarbeitung der Reliefs wurden `Gothic tracery public domain vector`,
`Gothic horror ornament CC0`, `bat wing ornament vector` und
`acanthus thorn scroll public domain` gesucht.

| Kandidat | Quelle | Lizenz und Rechte | Bewertung |
| --- | --- | --- | --- |
| **Gothic tracery design elements** | CraftsmanSpace, nach Mabel Sykes, *A Source Book of Problems for Geometry* (1912), [Projektseite](https://www.craftsmanspace.com/free-patterns/gothic-tracery-design-elements.html) | Die angebotenen SVG/EPS/DWG-Dateien stehen laut Projektseite unter **CC BY-SA**; Bearbeitung und Weitergabe sind mit Namensnennung und Share-Alike erlaubt. | **Reference-only**. Die historischen Spitzbogen- und Vierpassproportionen wurden studiert, aber keine Datei oder Kontur übernommen. |
| **Free Gothic vector art** | PublicDomainVectors, [Sammlung](https://publicdomainvectors.org/en/free-gothic-vector-art) | Die Sammlung bezeichnet ihre Inhalte als Public Domain/CC0; einzelne Beiträge müssten vor einer direkten Übernahme nochmals auf ihrer Detailseite geprüft werden. | **Reference-only**. Wegen gemischter Urheber und fehlender Notwendigkeit wurde keine Fremdgeometrie importiert. |
| **Wikimedia Commons 3D resources** | Wikimedia Commons, [3D-Ressourcen](https://commons.wikimedia.org/wiki/Commons:Free_media_resources/3D_models) | Dateispezifische freie Lizenzen; Rechte und Attribution müssen je Objekt geprüft werden. | **Abgelehnt als Baustein**: kein passender, einfacher und eindeutig lizenzierter Truhenrelief-Satz wurde benötigt. |

### Entscheidung: `rebuild`

Die Reliefs in `scripts/gothic_chest.py` sind eine neue parametrische
Eigenkonstruktion. Verwendet werden:

- abgerundete Dornen- und Akanthusranken aus kubisch abgetasteten Kurven;
- Blattfinials und Vierpass-Rosetten;
- trefoilartige Einlagen in den rückwärtigen Spitzbogenfeldern;
- offene Fledermausflügel mit druckbaren Rippen auf dem Deckel;
- eine zusammenhängende Frontkartusche um die drehbare Totenkopfaufnahme.

Es wurde keine fremde Vektor- oder Mesh-Geometrie übernommen. Die historischen
Quellen dienen ausschließlich als Stil- und Proportionsreferenz; daher entsteht
für die ausgelieferten Reliefs keine zusätzliche Attributions- oder
Share-Alike-Pflicht.

## Weitere bereits verwendete Anatomiequelle und Schalenhand-Erweiterung

Die Handgeometrie basiert weiterhin auf **“Wrist Bones Full Hand – Human
Skeleton”**, NIH 3D Print Exchange, Modell `3DPX-016815`, hochgeladen von My
Segmenter, **CC BY 4.0** ([NIH 3D Entry](https://3d.nih.gov/entries/3DPX-016815)).
Vor der Schalenhand-Erweiterung am 19. Oktober 2026 wurde zusätzlich nach
wiederverwendbaren Vorlagen gesucht (`3D printable cupped skeleton hand candy holder bowl removable dish STL license Creative Commons`).
Zwei Printables-Kandidaten (`model/1436550-skeleton-hand-bowl`,
`model/590777-halloween-skeleton-candy-bowl`) lieferten beim Abruf der
Primärseiten HTTP 403; ihre Lizenzen konnten nicht aus der Primärquelle
verifiziert werden und es wurde keine Geometrie heruntergeladen.

Entscheidung: **Hybrid-Weiterverwendung** des bereits lizenzierten NIH-Hand-Scans
(`3DPX-016815`, CC BY 4.0) mit starrer Neu-Posierung (opponierter Daumen,
gekrümmte Finger, massiv geschlossene Knöchel ohne V-Kerben) in
`scripts/skeleton_hand.py` sowie einer technisch neu konstruierten,
abnehmbaren elliptischen Süßigkeitenschale (`candy-dish`) mit drei
asymmetrischen Positionierstiften in `scripts/candy_hand.py`.
