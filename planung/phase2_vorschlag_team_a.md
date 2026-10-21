# Phase 2 – Team A: Verknüpfung der 18 Firmen (Neudurchlauf R2)

Stand: 21.10.2026 · Grundlage: `phase1_team_a.md` und `phase1_team_b.md` (beide R2, Firmen unverändert), `NACHRICHTEN.md`,
die verbindliche Entscheidung `phase2_entscheidung.md` / `verknuepfungen.json`, der Phase-2-Vorschlag R2 von Team B
(`phase2_vorschlag_team_b.md`, gelesen und abgeglichen, Abschnitt 1.1), das Skript
`generate_space_trading_data.py` (Seed 42) und eigene Abfragen auf `/home/user/bestand/space_trading_game_bestand.db`
(nur lesend, pandas/sqlite3). Die erste Fassung dieses Vorschlags (20.10.) ist in die Entscheidung eingegangen. Diese
Fassung ersetzt sie.

## 0. Kurzfassung

**Arbeitsweise:** Beide Teams haben in Phase 1 R2 ihre Firmen unverändert gelassen. Die Entscheidung des Schiedsrichters
ist also weiter anwendbar. Deshalb schlägt Team A kein neues Netz vor. Wir haben die Entscheidung **vollständig
nachgerechnet** und schlagen nur dort Änderungen (Δ1–Δ9) vor, wo der Bestand ihr widerspricht oder die Umsetzung sonst
scheitern würde. Damit bleibt alles gültig, was in Phase 2 schon abgestimmt wurde (48 Vereinbarungen, 12 Rivalitäten,
21 Rahmenverträge, 38 Vorgänge).

| Thema | Ergebnis R2 |
|---|---|
| Vereinbarungen | **48 aktiv** (14 Bestand inkl. `helix → corvane` optional, 7 neue Firma → Bestand, 12 Team A, 12 Team B, 3 teamübergreifend). Nachgezählt: alle 18 im Größenbereich, jede mit ≥ 1 ausgehender Kante. **Hub: Helix** (large, 7 Partner, 10 Vereinbarungen). 38/153 Paare direkt, **66 nur über einen Zwischenhändler**, 45 mit Abstand 3, 4 mit Abstand 4, Netz zusammenhängend. Verbraucherprüfung: jede Kante ≥ 52 % Warengewicht mit passendem Käuferstationstyp. |
| Historie | 7 beendete Partnerschaften, Daten gegen `founded_year` und `window_start − 120 T` geprüft |
| Rivalitäten | 12 (4 Bestand, 8 neu). Δ6: Informanten nach der eigenen Leck-Regel bereinigt (+Freddy Dörr 235, +Darren Harris 319) |
| Rahmenverträge | **21** (7 Bestandspaare, 14 neu), **82 Nachträge** (bisher 78, Δ2 teilt 3 Sammelnachträge), 17 offen, 1 abgelehnt. **341 von 475** Bestands-Abrufverträgen reproduziert (2.309 Mio. CR), alle 13 Volumen-Auslöser bestätigt. Δ1 = K1 von Team B: CCI-Exklusivität widerspricht dem Bestand → Vorkaufsrecht. Δ3: Scope KHB-RV-2059-01 ohne Verbraucher. K2, K6, K7, K10 von Team B übernommen |
| Schriftverkehr | Tabelle `correspondence` (20 Briefarten) unverändert. 38 Vorgänge bestätigt (Mitarbeiter am Datum beschäftigt, Strafbeträge stimmen), Mahnfristen-Korrekturen K3–K6 von Team B nachgeprüft und übernommen. Δ7: V14 verletzt Leck-Regel und Reihenfolge. V39 von Team B, neu von uns V40 und V41 |
| Antworten an Team B | R2-1 ja (Ankerobjekte im Bestandsvergleich: 57 Verträge, 9 Bestellungen, 2 Lieferungen, 31 Ereignisse, 49 Mitarbeiter). R2-2 ja, auch für neue Firmen (Δ8). R2-3 Aurelis über Kuppelwerk, Sol bleibt bewusst Importmarkt (Δ9) |

---

## 1. Antworten und offene Punkte aus `NACHRICHTEN.md`

**An Team B, R2-1 (Ankerobjekte in der QA):** Ja, das übernimmt Team A. Der Bestandsvergleich der QA 6/6/6 prüft nicht nur
die Stammdaten der 6 Bestandsfirmen, sondern auch alle Bewegungsobjekte, auf die sich Rahmenverträge, Rivalitäten und
Schreiben stützen. Die Liste steht als `qa_anchor_objects` im JSON und wurde aus beiden Phase-1-Berichten, der
Entscheidung und `verknuepfungen.json` gezogen: 57 Vertragsnummern (darin die 8 Geleitschutzbrüche, HMX-CTR-2059-0242
und die 5 Corvane-Technikverträge aus Δ1), 9 Bestellungen, 2 Lieferungen, 31 Ereignisse (darunter 26, 52, 58, 74) und
49 Mitarbeiter. Verglichen werden je Objekt die Felder, die ein Schreiben nennt (Status, Wert, Frist, Datum, Station,
Name, Einstellungsdatum, Loyalität, Bestechlichkeit, Zugang). Zusätzlich muss die Zuordnung genau **341** Bestandsverträge
ergeben. Alle 57 + 9 + 2 + 31 + 49 Objekte gibt es heute im Bestand (geprüft). `RCS-ORD-2059-00042` in Phase 1 B ist nur
ein Nummernbeispiel.

**R2-2 (Schreiben gegen `hire_date`):** Ja. Alle 44 Mitarbeiter-IDs aus Abschnitt 6.3 der Entscheidung haben wir gegen
`hire_date` und `termination_date` am jeweiligen Datum geprüft. Es gibt **keinen Verstoß**. Neu gefunden haben wir zwei
Regelverstöße anderer Art (V14, siehe Δ7). Erkan Hesse (39) ist ab 2059-06-11 entlassen. Für die **neuen** Firmen gibt
es dieselbe Gefahr in umgekehrter Richtung: `generate_employees` würfelt `hire_date` gleichverteilt bis 2059-12-18. Ein
Graufalk-Vorstand könnte also erst 2059 eingestellt werden und dann den Rahmenvertrag von 2057 nicht unterschreiben.
Lösung: Δ8.

**R2-3 (Rohstofflücken Sol 1/40, Aurelis 1/24):** Rohstoffe entstehen nur an `mining`-Stationen (`choose_supply_stations`
fällt nur dann auf `trade_hub` zurück, wenn eine Firma gar keine Bergbaustation hat). Keine Team-A-Firma hat eine
Bergbau-Pflichtstation in Sol oder Aurelis. Vorschlag (Δ9): **Aurelis** bekommt bei Kuppelwerk eine dritte
Pflichtstation `("mining", "aurelis")` (Regolith und Eis für die Sinteröfen am Hauptsitz). Das passt zur Lore und
schließt die Lücke sicher. **Sol** bleibt bewusst Importmarkt. Der Kernraum ist abgebaut, Rohstoffe kommen aus Brennus,
Aurelis, Myrrhen und Pellora. Für den Spieler ist das die erste verlässliche Einkaufs-Verkaufs-Route (Pellora 174 bzw.
Brennus → Sol). Second Hull muss dafür nicht umgebaut werden.

### 1.1 Abgleich mit `phase2_vorschlag_team_b.md` (R2)

Team B hat parallel dieselbe Nachprüfung gemacht. Netz, Historie, Rivalitäten und die 341 Zuordnungen stimmen bei beiden
überein. Zu den Korrekturen von Team B:

| Team B | Inhalt | Team A |
|---|---|---|
| K1 | CCI-MSA-2057-01 Vorkaufsrecht statt Käuferexklusivität (Corvane → Hande) | **angenommen**, wir hatten denselben Befund (Δ1). Unsere engere Variante (Exklusivität nur `ai_cores`/`quantum_relays`) ziehen wir zugunsten von K1 zurück |
| K2 | Geleitschutzklausel EKM-RV-2057-02 an die echten Geleitschutzbrüche EKM-VTR-2057-0043/-2058-0107, Andockstau-Brüche → Ausweich-Liegeplätze | **angenommen**, im Bestand geprüft (Zwischenfälle „Geleitschutz abgewartet (+118 h/+71 h)“ bzw. „Andockstau (+118 h/+127 h)“) |
| K3–K5 | Mahnfristen V1, V27, V32 | **angenommen**, geprüft: Fälligkeit = Ankunft + 30 T (`PAYMENT_TERMS_DAYS`), z. B. EKM-BST-2057-00352 Ankunft 2057-07-24 → Stufen 08-28/09-13/10-07 |
| K6 | V36 und Eilabrufklausel auf 2059-12-31, Absender Kayla Cannon | **angenommen**, HMX-ORD-2059-01788 ist am 2059-12-29 bestellt |
| K7 | RVF-RV-2058-01: Stickstoffeis erst ab Nachtrag exklusiv | **angenommen** |
| K8 | Sperrfristen für neue Verkäufer | **angenommen und mit unserem Δ4 vereinigt** (Abschnitt 6.4). Neu von uns: Kuppelwerk bei `water_ice` nach Isolde und bei `nav_computers` an Graufalk, sowie die Verkäuferexklusivität `habitat_modules` |
| K9 | HMX-MSA-2057-02 nur mit gezogener `helix → corvane` | **angenommen** |
| K10 | Feldspat-Schulden nach Datum | **angenommen** (Story-Text FSP-RV-2059-01) |
| K11 | Morgengrund zweite Pflichtstation `trade_hub` Isolde | **Zustimmung**. Zusammen mit unserem Δ9 sind das zwei kleine Profiländerungen neuer Firmen, die Bestand und Netz nicht berühren |
| V39 | Chavez-Leck → Rüge Cindervale → Antwort Bauer | **übernommen** statt unseres gleichnamigen Entwurfs. Unsere neuen Vorgänge heißen deshalb V40 und V41 |

Was nur bei uns steht und Team B bitte prüfen möge: Δ2 (Produktaufnahmen einzeln), Δ3 (Scope KHB-RV-2059-01), Δ6/Δ7
(Leck-Regel: Erkan Hesse 68/43 darf nicht der Absender eines Lecks sein, Schuchhardt 85/25 nicht als Leck-Quelle
geführt werden), Δ8 (Einstellungsgrenzen der neuen Firmen) und Δ9 (Kuppelwerk-Bergbau Aurelis). Team B schreibt in 7.3,
Hesse sei „nur im Januar 2059 genutzt“. Das stimmt für `hire_date`, verletzt aber die Leck-Regel aus der Entscheidung (6.1).

**Offene Frage von Team A (Phase 1 R2):** Team B hat bestätigt, dass es bei seinem Phase-1-Stand und bei der
Zuständigkeit bleibt (Eintrag Team B R2). Damit gilt weiter: Team A übernimmt Durchlauf 2, RNG/Faker, den Archetyp-Filter
und die QA 6/6/6 mit Bestandsvergleich. Team B übernimmt Rahmenverträge, Nachträge, Scope, Schriftverkehr und die QA dazu.

---

## 2. Prüfprotokoll R2 (gegen Skript und Bestand)

| # | Prüfung | Ergebnis |
|---|---|---|
| P1 | Zählung je Firma, beide Richtungen (Skript über `verknuepfungen.json`) | wie Tabelle 2.3 der Entscheidung, Summe 96 = 2 × 48 |
| P2 | Netz: Abstände (BFS) | 1: 38, 2: 66, 3: 45, 4: 4 (Kometenpost ↔ Driftwood/Pionierwerk/Outmark/Morgengrund), zusammenhängend |
| P3 | Hub nach QA-Sortierung (Partner, dann Vereinbarungen) | Helix 7/10 vor Graufalk 7/9 und Ravenmoor 7/8. Ohne `helix → corvane` (anderer Seed): Helix 7/9 gleichauf mit Graufalk; welche Zeile `sort_values` dann vorn hat, ist nicht festgelegt, beide sind aber large → die Prüfung „Hub ist groß“ besteht in jedem Fall |
| P4 | Verbraucher je Kante (`CATEGORY_CONSUMERS` und Sonder-Verbraucher je Archetyp) | alle Kanten ≥ 52 %. Knappste: `pionierwerk → morgengrund` 0,52 (nur Agrarstation), `helix → eisenkrone` 0,70, `kuppelwerk → lichtacker` 0,75. Kein `RuntimeError` aus `plan_markets` zu erwarten |
| P5 | Zuordnung Bestandsverträge (eigene Implementierung der Regel) | 54/68/75/65/39/35/5 = **341**, außerhalb genau EKM-VTR-2060-0230 (Energie nach Teilkündigung), FSP-VTR-2059-0001/-0005 (vor Rahmenbeginn) |
| P6 | Volumen-Nachträge (kumuliert > 90 %) | alle 13 Auslöser (davon 4 mit Beginn 2060, daher `proposed`) und Monatsersten stimmen (z. B. HMX-CTR-2058-0161 bei 227,9 von 250; EKM-VTR-2059-0211 bei 141,2 von 150) |
| P7 | Produktaufnahme-Nachträge (Monatserster vor dem ersten Vertrag der Kategorie) | 3 Sammelnachträge weichen ab → **Δ2** |
| P8 | Exklusivitäten gegen Bestandsverträge und -bestellungen | 1 Widerspruch: CCI-MSA-2057-01 → **Δ1** (= K1 Team B). Geprüft und ohne Widerspruch: Energie Helix → Corvane (keine anderen Energielieferanten), Sensorarrays Kharon (EKM-VTR-2058-0097 beginnt 2058-04-02, vor RCS-MSA) |
| P9 | Scope gegen Verbraucher der Käuferstationen | KHB-RV-2059-01 Rohstoffe → **Δ3**. Alle anderen 20 Rahmen haben Verbraucher für jede Scope-Kategorie |
| P10 | Mitarbeiter in 6.3 (44 IDs): Name ↔ ID, Firma, beschäftigt am Datum | ohne Fehler |
| P11 | Leck-Regel (bribe ≥ 50 oder loyalty ≤ 50) für Absender mit `leaked_by` | V14 Erkan Hesse 68/43 verletzt → **Δ7**. Rivalitäts-Informanten 178 (85/25) und 45 (75/23) verletzen → **Δ6** |
| P12 | Reihenfolge in Vorgängen | V14: Gerücht 2059-01-20 über den Strafbescheid vom 2059-01-25 → **Δ7** |
| P13 | Strafbescheide: Datum = letzte Ankunft + 3..14 T | alle 6 geprüften stimmen (z. B. HMX-CTR-2058-0159: Ankunft 2059-01-17, Bescheid 2059-01-25, 6 × 108.860,36 = 653.162,16 CR) |
| P14 | Historie: Ende ≤ `window_start(Käufer)` − 120 T, Beginn ≥ Gründung | alle 7 bestehen (z. B. `outmark → feldspat` Ende 2058-06-30 ≤ 2058-09-03) |
| P15 | Rahmenbeginn ≥ Datenfenster des Verkäufers (`generate_contracts` würfelt ab `window_start(seller)`) | alle 14 neuen Rahmen bestehen (small ab 2059-01-01: SGM 2059-01/-03; medium ab 2058-01-01: KHB, EFF, RVF, OSP) |
| P16 | Referenzierte Bestandsobjekte existieren | 57/57 Verträge, 9/9 Bestellungen, 2/2 Lieferungen, 31/31 Ereignisse, 49/49 Mitarbeiter |

---

## 3. Gerichtete Handelsvereinbarungen (Verkäufer → Käufer)

Regeln eingehalten: Typen nur aus `TRUST_RANGES`. Mit Bestandsfirmen nur in Richtung „neue Firma → Bestandsfirma“, damit
Routen, Verträge und Kunden der Bestandsfirmen (die beim Verkäufer entstehen) unverändert bleiben. Die 13
Blueprint-Kanten und `helix → corvane` bleiben im Bestandsstrom. Neue `trade_partnerships`-Zeilen kommen nach Zeile 15.

### 3.1 Bestand (14, unverändert)

| Kante | Typ | Ware / Käuferstationen | Plausibilität | Spielspaß |
|---|---|---|---|---|
| eisenkrone → helix | supply | Erze, Energie Brennus/Halcyon → Kharon/Sol | Schwerindustrie beliefert den Hub | Geleitschutzbrüche EKM-VTR-2057-0043/-2058-0107, Andockstau-Brüche -2057-0017/-2059-0162, offene dreiseitige Klausel |
| helix → eisenkrone | strategic_alliance | Lebensmittel, Energie, Rohstoffe → Werke, Schächte | gegenseitige Abhängigkeit trotz Rivalität in Sol | Volumensenkung nach KI-Ausfall 19 |
| helix → lichtacker | distribution | Verbundstahl, Luxus → Agrarringe | Hub versorgt Agrarkolonien | 3 Verbundstahl-Brüche → Kuppelwerk springt ein |
| lichtacker → helix | supply | Lebensmittel → Exchanges, Landings | Nahrung für den Hub | Grundlast-Route für Anfänger |
| corvane → helix | licensing | Medizin, Technik | Lizenzware über den Hub | – |
| feldspat → helix | consignment | Rohstoffe Brennus | Kleinförderer verkauft über Hub | – |
| driftwood → helix | consignment | Bergegut, graue Ware → Kharon | einziger legaler Absatzweg | Schmuggel-Graubereich |
| feldspat → eisenkrone | supply | Quantenquarz, Erze | Hauptabnehmer | 25,52 Mio. CR Schulden (13 überfällige Bestellungen) → FSP-RV-2059-01 |
| eisenkrone → feldspat | supply | Ausrüstung, Antimaterie → Becker | Bergbaubedarf | Mahnstufen V1/V27 |
| eisenkrone → lichtacker | supply | Energie, Industriegüter → Seip | Energie für Hydrokultur | 3 Brüche → Teilkündigung → Emberline |
| corvane → eisenkrone | supply | Medizin, **Robotik → Bergbaustation Hande** | Werksmedizin, Technik | Auslöser des CCI-Konflikts (Δ1) |
| eisenkrone → corvane | joint_venture | Rohstoffe, Industriegüter Halcyon | Gemeinschaftswerk | Vorkaufsrecht, Abmahnung LAK-VTR-2058-0033 |
| lichtacker → corvane | supply | Bioproben, Lebensmittel | Medizin-Rohstoff | – |
| helix → corvane | logistics (optional, p = 0,6) | Logistik Halcyon/Aurelis | im Bestand gewürfelt aktiv | Helium-3-Ausfall → Emberline |

### 3.2 Neue Firma → Bestandsfirma (7)

| Kante | Typ | Ware → Käuferstationen | Plausibilität (Anker) | Spielspaß |
|---|---|---|---|---|
| graufalk → helix | supply | Rumpfplatten, Triebwerksteile → Exchanges, Landings, Bastionen | 86 Verspätungen wegen Triebwerksschäden, HMX-CTR-2058-0173 gebrochen | Werft des Spielers, Eilabrufklausel offen |
| cindervale → eisenkrone | supply | KI-Leitsysteme, Robotik → Schächte (Technik nur an `mining`) | KI-Ausfälle Förster 19/36/70 | Firmware-Verdacht, Aussetzung zum Spielstart |
| kuppelwerk → lichtacker | supply | Verbundstahl, Sinterbausteine, Habitatmodule → Agrarringe, Labor | 4 gebrochene Helix-Baustoffverträge | Lücke Myrrhen Industriegüter 0/26 |
| emberline → corvane | supply | Helium-3 → Halcyon Works VI | HMX-CTR-2058-0131/-2057-0014 gebrochen, Sturm 30 | neue Stufe-1-Route Pellora → Halcyon |
| emberline → lichtacker | supply | Energie → Seip | Teilkündigung EKM-RV-2057-03 | Dreikampf Eisenkrone/Helix/Emberline um Energie in Myrrhen |
| raureif → eisenkrone | supply | Eis, Gas → Löchel, Brennus | Konkurrenz zu Feldspat | Preisdruck nach Fund 52 |
| ravenmoor → helix | logistics | Drohnen, Sensoren, Feldbedarf → Kharon | Razzia 26, 8 Geleitschutzbrüche | Gegner wird Schutzpartner |

### 3.3 Innerhalb Team A (12)

| Kante | Typ | Ware | Begründung (Plausibilität / Spielspaß) |
|---|---|---|---|
| cindervale → graufalk | supply | Navigationscomputer, Sensoren | Werften brauchen Avionik / Upgrade-Kette für Spielerschiffe |
| graufalk → cindervale | strategic_alliance | Triebwerksteile, Gehäuse | gemeinsame Navigationsplattform / Allianz mit Geheimhaltungskonflikt |
| emberline → graufalk | supply | Fusionspellets, Helium-3 | Probefahrten, Werftenergie |
| graufalk → emberline | supply | Schöpfschiff-Teile | Pellora-Schöpfer verschleißen in Stürmen |
| kuppelwerk → graufalk | supply | Glaskeramik, Sinterbausteine (an Handelsstation Orrin) | Dockausbau in Orrin. `industrial` verbraucht keine Industriegüter, deshalb läuft die Route über `trade_hub` bzw. die Zusatzverbraucher von `habitat_modules`/`sinter_blocks` |
| emberline → kuppelwerk | supply | Energie für Sinteröfen | Grundlast |
| emberline → cindervale | supply | Energie für Rechenzentren | Rechenwerke verbrauchen viel Energie |
| cindervale → kometenpost | consignment | KI-Kerne, Quantenrelais | teure, eilige `restricted`-Ware in Kommission / Genehmigungs-Mechanik |
| kometenpost → cindervale | logistics | Medizin, Technik express | Pünktlichkeit statt Kharon-Umweg |
| cindervale → lanternfish | supply | Elektronik für Immersionskapseln | Vorprodukt |
| lanternfish → graufalk | supply | Komfortgüter | Werftarbeiter in Orrin / Luxus-Spekulation |
| lanternfish → kometenpost | consignment | Komfortgüter | Kurier verkauft unterwegs mit |

### 3.4 Innerhalb Team B (12) und teamübergreifend (3)

Unverändert aus `phase1_team_b.md` 5.1 und der Entscheidung: `raureif → pionierwerk`, `pionierwerk → morgengrund`,
`morgengrund → pionierwerk`, `ravenmoor → pionierwerk` (logistics), `pionierwerk → ravenmoor`, `outmark → pionierwerk`
(licensing), `second_hull → pionierwerk`, `second_hull → ravenmoor` (consignment), `raureif → ravenmoor`,
`ravenmoor → outmark` (logistics), `morgengrund → ravenmoor`, `outmark → raureif`. Teamübergreifend:
`kuppelwerk → pionierwerk` (Habitatmodule für Isolde/Serravel), `second_hull → graufalk` (Recyclingmetall, aufbereitete
Rumpfplatten), `graufalk → ravenmoor` (Geleitschiff-Teile). Begründungen dort. Für den Spielspaß zählt: Kuppelwerk
beliefert beide Rivalen auf Isolde nur indirekt (Lichtacker direkt, Pionierwerk direkt, die beiden Rivalen sind aber nur
über Kuppelwerk verbunden). Wer bei Kuppelwerk Kontakte hat, hört beide Seiten.

### 3.5 Zählung (nachgerechnet)

| Firma | Größe | Vereinb. | aus | ein | Partner | Bereich | frei |
|---|---|---:|---:|---:|---:|---|---:|
| Feldspat | small | 3 | 2 | 1 | 2 | 1–3 | 0 |
| Driftwood | small | 1 | 1 | 0 | 1 | 1–3 | 2 |
| Lichtacker | medium | 6 | 2 | 4 | 5 | 3–6 | 0 |
| Corvane | medium | 6 | 2 | 4 | 4 | 3–6 | 0 |
| Eisenkrone | large | 9 | 4 | 5 | 6 | 6–10 | 1 |
| **Helix (Hub)** | large | **10** | 3 | 7 | **7** | 6–10 | 0 |
| Graufalk | large | 9 | 4 | 5 | 7 | 6–10 | 1 |
| Cindervale | large | 7 | 4 | 3 | 5 | 6–10 | 3 |
| Kuppelwerk | medium | 4 | 3 | 1 | 4 | 3–6 | 2 |
| Emberline | medium | 6 | 5 | 1 | 5 | 3–6 | 0 |
| Kometenpost | small | 3 | 1 | 2 | 2 | 1–3 | 0 |
| Lanternfish | small | 3 | 2 | 1 | 3 | 1–3 | 0 |
| Pionierwerk | large | 8 | 2 | 6 | 6 | 6–10 | 2 |
| Ravenmoor | large | 8 | 3 | 5 | 7 | 6–10 | 2 |
| Raureif | medium | 4 | 3 | 1 | 4 | 3–6 | 2 |
| Outmark | medium | 3 | 2 | 1 | 3 | 3–6 | 3 |
| Morgengrund | small | 3 | 2 | 1 | 2 | 1–3 | 0 |
| Second Hull | small | 3 | 3 | 0 | 3 | 1–3 | 0 |

**Nur über Zwischenhändler verbunden (Auswahl der 66):** Feldspat ↔ Raureif (über Eisenkrone), Driftwood ↔ Ravenmoor
(über Helix), Lichtacker ↔ Pionierwerk (über Kuppelwerk), Helix ↔ Morgengrund (über Ravenmoor), Graufalk ↔ Kometenpost
(über Cindervale oder Lanternfish), Corvane ↔ Cindervale (über Eisenkrone oder Emberline). **Spielwert:** Die Reserve
(Cindervale 3, Outmark 3, Driftwood 2, Kuppelwerk 2 …) erlaubt es, später neue Vereinbarungen als Spielereignis zu
stiften („der Spieler vermittelt Cindervale ↔ Corvane“), ohne die Größenregel zu brechen.

---

## 4. Historische (beendete) Partnerschaften

| Verkäufer → Käufer | Typ | Zeitraum | Story-Hook (Plausibilität / Spielspaß) |
|---|---|---|---|
| corvane → driftwood | supply | Bestand 2057-04-27 – 2058-07-17 | unverändert, Ursache der Spionage-Rivalität |
| eisenkrone → graufalk | supply | 2039-01-01 – 2049-06-30 | Ausgliederung der Werftsparte, Patentstreit Reaktorkomponenten → Rivalität ab 2049-07-01. Alte Werkspläne als Spionageziel |
| cindervale → helix | licensing | 2041-04-01 – 2054-03-31 | Helix verliert die Lizenz und holt Technik seither aus Kharon (deshalb brechen die Supraleiter-Verträge) → Rivalität ab 2054-04-01 |
| lichtacker → pionierwerk | supply | 2045-03-01 – 2053-06-30 | Versorgung der Isolde-Bautrupps bis zum Pachtstreit |
| emberline → eisenkrone | supply | 2047-02-01 – 2056-06-30 | Helium-3 für Hande, beendet durch eigene Deuteriumförderung. Emberline kennt die Schwächen von Hande |
| outmark → feldspat | licensing | 2055-02-01 – 2058-06-30 | Vermessungsdaten Brennus, ein Jahr später Fund 52 bei Becker: wer hat die Daten weitergegeben? |
| driftwood → second_hull | consignment | 2057-05-01 – 2058-07-01 | endet zwei Tage nach Razzia 26 |

Daten fest (kein Würfel). `trust_level` 3–15 und `contract_volume` würfelt der Erweiterungsstrom wie
`generate_partnerships`. Kein Paar ist mit demselben Typ zugleich aktiv und historisch.

---

## 5. Rivalitäten (12) und Spionage-Potenzial

| Firma → Rivale | Typ | System | seit | Int./Spion. | Anker (Bestand) | Lecks (eigene Firma, Regel erfüllt) | Zeugen/Ziele |
|---|---|---|---|---|---|---|---|
| eisenkrone → helix | market_dominance | sol | Bestand | Bestand | – | Bestandsstrom | – |
| driftwood → corvane | industrial_espionage | halcyon | Bestand | Bestand | – | – | – |
| feldspat → driftwood | territorial_claims | kharon | Bestand | Bestand | – | – | – |
| lichtacker → eisenkrone | resource_competition | myrrhen | Bestand | Bestand | – | – | – |
| graufalk → eisenkrone | market_dominance | halcyon | 2049-07-01 | 70/55 | Ereignisse 19/36/70, EKM-VTR-2057-0064 | Esther Bauer 170 (53/76), **Freddy Dörr 235** (Sicherheit Förster, 45/88, Zugang 1) | Ziel: Annekatrin Schuchhardt 178 (85/25, kaum bestechlich) |
| cindervale → helix | market_dominance | sol | 2054-04-01 | 65/50 | Ereignisse 3/24, HMX-CTR-2057-0050/-2058-0121 | **Darren Harris 319** (Marktaufklärung seit 2056-02-19, 35/69, Zugang 3), Desiree Schwartz 299 (ab 2059-11-24) | Zeuge: Richard Chavez 120 (Corvane) |
| emberline → eisenkrone | resource_competition + Override | myrrhen | 2058-08-15 | 55/40 | EKM-VTR-2058-0099/-0105/-2059-0167 | Esther Bauer 170 | Zeugen: Polina Zahn 83, Hans-Werner Eberhardt 45 (Lichtacker) |
| lichtacker → pionierwerk | territorial_claims + Override | isolde | 2053-07-01 | 60/55 | Ende der historischen Lieferung | Kaspar Täsche 43 (55/61) | – |
| ravenmoor → driftwood | armed_conflict (neu) | nyx | 2058-06-30 | 85/70 | Razzien 26/58, Piraten 45/54/57/67 | Carlos Osborne 29 (3/100), Nathan Hines 33 (36/81) | – |
| outmark → feldspat | territorial_claims | brennus | 2059-07-14 | 65/80 | Fund 52 Becker | Slavko Geisel 16 (55/96) | – |
| ravenmoor → helix | market_dominance | kharon | 2057-11-17 | 55/45 | Piraten 16, Razzia 26 | Wayne Jacobson 302, Tyler Garcia 395, Brandon Jones 445 | – |
| second_hull → driftwood | territorial_claims | nyx | 2058-07-01 | 50/40 | Piraten 54, Ende der Kommission | Douglas Lawson 27 (57/61) | – |

**Δ6 (Informanten nach Leck-Regel):** Die Entscheidung verlangt für jeden Leck-Absender bribe ≥ 50 oder loyalty ≤ 50.
Schuchhardt (85/25) und Eberhardt (75/23) erfüllen das nicht. Wir trennen deshalb **Lecks** (Mitarbeiter der betroffenen
Firma, Regel gilt) von **Zeugen/Zielen** (Dritte oder schwer bestechliche Personen, Regel gilt nicht). Neu sind Freddy
Dörr (Ausfallprotokolle Förster, nur `business`, weil Zugang 1) und Darren Harris. Ohne Harris hätte Cindervale vor
Ende 2059 keine Quelle bei Helix, obwohl die Rivalität seit 2054 läuft. **Spielspaß:** Die harte Zielperson Schuchhardt
bleibt ein Beziehungsziel (Ansehen statt Bestechung). Dörr ist der billige, aber unzuverlässige Weg zu denselben Daten.

**Partner und Rivale zugleich** (bewusst, für Intrigen): Eisenkrone ↔ Helix, Ravenmoor ↔ Helix. Ehemalige Partner als
Rivalen: Graufalk ↔ Eisenkrone, Cindervale ↔ Helix, Emberline ↔ Eisenkrone, Lichtacker ↔ Pionierwerk, Outmark ↔
Feldspat, Second Hull ↔ Driftwood. Jede neue Rivalität hat damit eine Vorgeschichte in den Daten.

---

## 6. Rahmenverträge

### 6.1 Modell (wie entschieden, Kurzfassung)

- `framework_agreements` (Verkäufer `company_id`, Käufer `partner_company_id`, `partnership_id`, Laufzeit mit
  `original_end_date`/`current_end_date`, `status` negotiating/active/suspended/expired/terminated, `base_volume`,
  `current_volume_cap`, `price_formula` fixed/index_linked/cost_plus/market_minus, `indexation`
  none/category_price_index/fuel_index/risk_index, Rabatt/Aufschlag/Deckel in %, `exclusivity`
  none/right_of_first_refusal/buyer_exclusive/seller_exclusive/mutual/regional_exclusive, `exclusivity_system_id`,
  `notice_period_days`, `auto_renewal`, `penalty_rate_pct`, `escort_company_id`, Unterzeichner beider Seiten).
- `framework_agreement_scope`: Kategorie, optional Archetyp und System, `valid_from`/`valid_to`, `is_exclusive`,
  hinzugefügt bzw. entfernt durch Nachtrag. Damit sind Teilkündigung und Produktaufnahme Datensätze, keine Textfelder.
- `framework_amendments`: 17 Typen (volume_increase/-reduction, product_addition/-removal, price_adjustment,
  term_extension, exclusivity_clause/-waiver, penalty_, service_level_, escort_, force_majeure_, competition_,
  confidentiality_clause, scope_extension, partial_termination, suspension). Status proposed/signed/rejected/withdrawn,
  Auslöser `trigger_contract_id`/`trigger_order_id`/`trigger_event_id`. Nummer `{Rahmen}/N{k}` (de) bzw. `/A{k}` (en).
- **Einzelverträge:** neue Spalte `contracts.framework_agreement_id`. Zugeordnet wird deterministisch: gleiches Paar,
  Typ `framework`/`recurring_supply`/`exclusive_supply`, Beginn im gültigen Zeitraum, Kategorie bzw. Archetyp am Beginn
  im Scope. Bestellungen (Abrufe) hängen über `orders.contract_id` daran, Lieferungen über `shipments.order_id`. Der Weg
  Rahmen → Vertrag → Abruf → Lieferung → Schreiben ist so in jeder Richtung abfragbar. Bei Bestandsverträgen ändert sich
  nur die neue Spalte.
- **Neue Paare:** vor Rahmenbeginn nur spot/emergency_supply/consignment, danach die bisherigen Gewichte,
  Rahmen-Vertragstypen nur für Waren im Scope. `penalty_per_day` neuer Rahmenverträge = `penalty_rate_pct` des Rahmens.
- **Lebenszyklus der Erweiterung** (Plausibilität: so wachsen echte Lieferbeziehungen; Spielspaß: jeder Nachtrag ist ein
  sichtbares Ereignis mit Schreiben): Produktaufnahme vor dem ersten Vertrag einer neuen Kategorie → Volumenerhöhung,
  sobald kumuliert 90 % des Deckels erreicht sind → Strafklausel nach dem ersten Bruch → Preisanpassung nach Ereignissen →
  Exklusivklausel oder Vorkaufsrecht, wenn eine Seite Druck aufbaut → Verlängerung 60 Tage vor Ablauf → Teilkündigung,
  Aussetzung oder Kündigung, wenn die Brüche sich häufen. Nachträge mit Auslöser in 2060 stehen am Stichtag als
  `proposed` da. Sie sind die **offenen Verhandlungen, in die der Spieler zum Start eingreifen kann** (17 Stück).

### 6.2 Die 21 Rahmenverträge (mit R2-Korrekturen)

| Nr. | Paar | Beginn, Laufzeit | Volumen Basis → Stichtag (Mio. CR) | Preis / Index | Exklusivität | Kündigung | Nachträge | Bestandsverträge |
|---|---|---|---|---|---|---|---|---:|
| HMX-MSA-2057-01 | helix → lichtacker | 2057-01-01, 36 M | 250 → 550 | index_linked / category | Vorkaufsrecht Industriegüter, Wegfall 2059-03-15 | 180 T | 7 | 54 |
| HMX-MSA-2057-02 | helix → corvane | 2057-01-01, 36 M | 300 → 600 (750 angeboten) | market_minus 4 % / category | Energie käuferexklusiv 2057-05 bis 2059-03-15 | 120 T | 10 (1 offen) | 68 |
| HMX-MSA-2057-03 | helix → eisenkrone | 2057-01-01, 48 M | 300 → 250 → 450 (550 angeboten) | cost_plus 9 % / category | – | 360 T | **7** (1 offen) | 75 |
| EKM-RV-2057-01 | eisenkrone → corvane | 2057-01-01, 60 M | 350 → 450 (550 angeboten) | cost_plus 12 % / category | Vorkaufsrecht Rohstoffe | 360 T | **6** (2 offen) | 65 |
| EKM-RV-2057-02 | eisenkrone → helix | 2057-01-01, 42 M | 200 → 300 (400 angeboten) | index_linked raw, Deckel 10 % | – (Geleit- und Liegeplatzklausel offen, K2) | 180 T | **9** (3 offen) | 39 |
| EKM-RV-2057-03 | eisenkrone → lichtacker | 2057-01-01, 36 M | 150 → 200 | index_linked energy, Deckel 6 % | – | 90 T | 7 (Teilkündigung Energie wirksam 2060-01-18, Rettungsangebot abgelehnt) | 35 |
| FSP-RV-2059-01 | feldspat → eisenkrone | 2059-08-01, 24 M | 12 (20 angeboten) | market_minus 5 % | Vorkaufsrecht Quantenquarz | 90 T | 2 (1 offen) | 5 |
| GFW-RV-2057-01 | graufalk → helix | 2057-01-01, 48 M | 180 → 240 | index_linked industrial | – | 180 T | 3 (Eilabruf offen, angeboten 2059-12-31, K6) | neu |
| GFW-RV-2057-02 | graufalk → cindervale | 2057-01-01, 60 M | 220 → 300 | cost_plus 8 % | gegenseitig drive_parts/nav_computers ab 2058-03-15 | 365 T | 3 (Geheimhaltung offen) | neu |
| GFW-RV-2058-01 | graufalk → ravenmoor | 2058-07-15, 36 M | 90 → 130 | index_linked | Vorkaufsrecht hull_plating Kharon | 180 T | 2 | neu |
| CCI-MSA-2057-01 | cindervale → eisenkrone | 2057-01-01, 48 M | 120 | fixed, −8 % ab 2058-12-15 | **Δ1/K1: Vorkaufsrecht Technik Halcyon** (statt käuferexklusiv) | 180 T | 3, Status `suspended` seit 2059-12-15 | neu |
| KHB-RV-2058-01 | kuppelwerk → pionierwerk | 2058-06-01, 36 M | 70 → 105 | cost_plus 10 % / fuel | verkäuferexklusiv habitat_modules Isolde | 180 T | 2 (Serravel) | neu |
| KHB-RV-2059-01 | kuppelwerk → lichtacker | 2059-04-01, 24 M | 30 (+Regel) | cost_plus 10 % / fuel | – (Myrrhen-Exklusivität offen) | 90 T | 3 (1 offen), **Δ3: Rohstoffe nur regolith/water_ice** | neu |
| EFF-MSA-2059-01 | emberline → corvane | 2059-04-01, 24 M | 40 (+Regel) | index_linked / fuel | – (Helium-3 Halcyon offen) | 90 T | 3 (1 offen) | neu |
| EFF-MSA-2059-02 | emberline → lichtacker | 2059-11-15, 24 M | 18 | index_linked / fuel | Vorkaufsrecht Energie Myrrhen ab 2060-01-18 | 90 T | 1 | neu |
| RCS-MSA-2058-01 | ravenmoor → helix | 2058-08-01, 36 M | 90 → 130 | cost_plus 15 % / risk | regional: escort_drones/sensor_arrays Kharon | 90 T | 3 (2 offen, dreiseitig) | neu |
| RVF-RV-2058-01 | raureif → pionierwerk | 2058-01-01, 36 M | 80 → 110 | index_linked / fuel | regional: water_ice Isolde, nitrogen_ice ab Nachtrag 2058-09-01 (K7) | 180 T | 3 (1 offen) | neu |
| RVF-RV-2058-02 | raureif → eisenkrone | 2058-03-01, 24 M | 45 | index_linked raw, Mindestpreis | – | 90 T | 2 (Verlängerung offen) | neu |
| OSP-MSA-2058-01 | outmark → pionierwerk | 2058-02-01, 36 M | 25 | fixed | regional: survey_charts Serravel ab 2059-08-15 | 180 T | 2 | neu |
| SGM-RV-2059-01 | morgengrund → pionierwerk | 2059-01-01, 12 M + Auto-Verl. | 5 → 7 | fixed + Ernteklausel | – | 60 T | 2 | neu |
| SGM-RV-2059-02 | morgengrund → ravenmoor | 2059-03-01, 12 M | 6 | fixed + Ernteausfallklausel | – | 60 T | 2 (1 offen) | neu |

Summe: 21 Rahmen, **82 Nachträge** (64 signed, 17 proposed, 1 rejected), 341 Bestandsverträge (2.309 Mio. CR) zugeordnet.
Ohne Rahmen bleiben Kommissionen, die übrigen Lizenzen und die kleinen Lieferanten (Driftwood, Lanternfish, Kometenpost,
Second Hull). Dort macht der Spieler Spot-Geschäfte. Das ist auch Spielspaß: Rahmenpaare sind stabil, Spotpaare volatil.

### 6.3 Korrekturen R2

**Δ1 (= K1 von Team B) – CCI-MSA-2057-01: Käuferexklusivität widerspricht dem Bestand.** Eisenkrone soll Technik in
Halcyon nur bei Cindervale kaufen. Im Bestand liefert Corvane aber Technik an die Bergbaustation Hande (Halcyon):
CVB-CTR-2058-0003 (Elektronik), -2058-0013 und -2058-0038 (Navigationscomputer), -2059-0044 (Robotik) und
**CVB-CTR-2059-0066 (Robotik, `exclusive_supply`, 2059-08-24 bis 2060-08-05, aktiv)**, dazu 25 Bestellungen (13 als
Abrufe, 12 ohne Vertrag). Diese Zeilen sind Bestand und dürfen sich nicht ändern. Lösung wie K1: **Vorkaufsrecht** auf
Technik in Halcyon. **Spielspaß:** Der Exklusivvertrag mit Corvane übergeht das Vorkaufsrecht und wird zum Auslöser:
Chavez verrät ihn, Cindervale rügt Eisenkrone (V39), Eisenkrone antwortet mit den Förster-Ausfällen, und drei Monate
später folgt die Aussetzung (V31). Das ist eine Kette über drei Firmen, an der der Spieler ansetzen kann: Er kann das
Leck kaufen, Corvane-Robotik nach Hande liefern oder zwischen beiden vermitteln.

**Δ2 – Produktaufnahmen einzeln nach Regel.** Die Regel heißt „Monatserster vor dem ersten Abrufvertrag **der
Kategorie**“. Drei Sammelnachträge nehmen mehrere Kategorien zum Datum der frühesten auf:

| Rahmen | bisher | neu (erster Vertrag) |
|---|---|---|
| HMX-MSA-2057-03 | medical + technology + industrial_goods 2057-07-01 | medical 2057-07-01 (07-31), technology **2057-09-01** (09-23), industrial_goods **2057-11-01** (11-04) |
| EKM-RV-2057-01 | luxury + technology 2057-05-01 | luxury 2057-05-01 (05-25), technology **2057-06-01** (06-06) |
| EKM-RV-2057-02 | food + technology 2057-06-01 | food 2057-06-01 (06-25), technology **2057-10-01** (10-03) |

Die Zuordnung bleibt bei 341, weil kein Vertrag zwischen altem und neuem Datum beginnt. Die Daten sind dann aber exakt
reproduzierbar, und jede Produktaufnahme hat ein eigenes `amendment_offer`-Schreiben. +4 Nachträge.

**Δ3 – KHB-RV-2059-01: Rohstoff-Scope ohne Verbraucher.** Lichtacker hat nur Agrar- und Forschungsstationen. Rohstoffe
verbrauchen dort laut Archetyp nur `water_ice`, `regolith`, `ammonia_ice` (Agrar) bzw. `rare_earths`, `quantum_quartz`,
`platinum` (Forschung). Kuppelwerk fördert in Myrrhen Regolith und Eis. Scope deshalb auf Kategorie `raw_materials` mit
Archetypen `regolith` und `water_ice` begrenzen (`scope_archetypes` im JSON). Sonst erzeugt der Rahmen Scope-Zeilen, zu
denen es nie einen Vertrag geben kann.

### 6.4 Exklusivitätsfilter für neue Paare (Δ4)

Bestandsverträge sind fest, deshalb gibt es dort nur Vorkaufsrechte. Für neue Paare würfelt Durchlauf 2 die Verträge
selbst. Ohne Filter würde er Exklusivitäten der eigenen Rahmen brechen, zum Beispiel Graufalk-Sensorarrays an Helix in
Kharon trotz RCS-Exklusivität. Regel: Produkte unter fremder Exklusivität (Käufer, Archetyp, System, ab Datum) werden für
Verträge und Partnerbestellungen der anderen Verkäufer ausgeschlossen. Ausnahme sind absichtlich gesetzte Verstöße, die
ein `breach_warning` erzeugen.

| Verkäufer → Käufer | gesperrt | System, Zeitraum | Grund | Herkunft |
|---|---|---|---|---|
| emberline → corvane | Kategorie `energy` | bis 2059-03-14 | HMX-MSA-2057-02 Energie käuferexklusiv | K8 |
| kuppelwerk → lichtacker | Kategorie `industrial_goods` | bis 2059-03-14 | Vorkaufsrecht Helix, Absage V14 | K8 |
| graufalk → helix | `escort_drones`, `sensor_arrays` | Kharon, ab 2058-08-01 | RCS-MSA-2058-01 regional exklusiv | K8 + Δ4 |
| emberline, kometenpost → cindervale | `drive_parts` | ab 2058-03-15 | GFW ↔ CCI gegenseitig | K8 |
| emberline, lanternfish, second_hull, **kuppelwerk** → graufalk | `nav_computers` | ab 2058-03-15 | GFW ↔ CCI gegenseitig | K8 + Δ4 |
| second_hull, outmark, morgengrund, **kuppelwerk** → pionierwerk | `water_ice` (ab 2058-01-01), `nitrogen_ice` (ab 2058-09-01) | Isolde | RVF-RV-2058-01 | K8/K7 + Δ4 (Kuppelwerk fördert Eis in Myrrhen) |
| **kuppelwerk → andere Käufer** | `habitat_modules` | Isolde, ab 2058-06-01 | KHB-RV-2058-01 verkäuferexklusiv (heute ohne weiteren Käufer in Isolde, wirkt bei späteren Spielereignissen) | Δ4 |

Vorkaufsrechte bleiben ohne Filter. Verstöße dagegen sind erlaubt und werden als Schreiben erzählt (V39).

---

## 7. Schriftverkehr (`correspondence`)

### 7.1 Tabelle und Verknüpfungen (wie entschieden)

Pflichtfelder: `reference_number` (`{SKU}-KOR-{Jahr}-{nnnnn}` de / `-COR-` en), `letter_type`, `thread_id`,
`in_reply_to_id`, `refers_to_correspondence_id` (Quelle eines Lecks), `sent_at`, `read_at` (NULL = ungelesen am
Stichtag), Absender (`sender_company_id`, `sender_employee_id`, `sender_station_id`), Empfänger (`recipient_company_id`,
`recipient_employee_id` oder `recipient_customer_id`), `language` (= Absenderfirma), `subject`, `body`, `confidentiality`
public/business/confidential/secret (= nötiger `intel_access_level` 0–3), `tone` cordial/neutral/firm/hostile, `amount`,
`due_date`, `response_required`, `status` sent/read/answered/rejected/escalated/closed, `trust_effect` (−20..10),
`is_accurate` (nur Tipp/Gerücht, NULL = offen), `leak_status`, `leaked_by_employee_id`, `leaked_to_company_id`.
**Fachbezug** über genau die vorhandenen Schlüssel: `framework_agreement_id`, `amendment_id`, `contract_id`,
`order_id`, `shipment_id`, `event_id`, `rivalry_id`, `partnership_id`. Prüfung: Die Parteien des Bezugsobjekts sind
Absender- und Empfängerfirma (außer bei Tipp, Gerücht, Memo und Protest).

### 7.2 Briefarten (20) – Auslöser, Rolle, Bezug

| Art | Auslöser | Absender → Empfänger (Rolle) | Bezug | Spielwert |
|---|---|---|---|---|
| inquiry | 30–60 T vor Rahmenbeginn, Nachtragswunsch, Lücke | relations → relations | partnership | zeigt Bedarf vor dem Vertrag |
| offer / counter_offer / offer_rejection | Antwort auf inquiry, Kaltangebot; 0–2 Runden (2 bei trust < 60); Absage | relations/executive | framework, contract (draft) | Verhandlung beobachten und unterbieten |
| contract_confirmation | Unterschrift Rahmen; `exclusive_supply` | executive (Rahmen), relations | framework, contract | – |
| amendment_offer / _confirmation / _rejection | jeder Nachtrag am `proposed_date` bzw. Unterschrift/Absage | Initiator → Gegenseite | amendment | 17 offene Nachträge zum Start |
| delivery_notice | Abrufsendung ≥ 1 Mio. CR, offene Bestellung zum Stichtag | logistics / station_manager Herkunft | order, shipment | Frachtinformationen (Raubziel) |
| delay_notice | Sendung mit `risk_incident` | logistics Herkunft | shipment | – |
| delay_complaint | Abruf > 48 h verspätet, Vertrag breached, Bestellung delayed | station_manager Ziel | shipment, contract | Notlieferung durch den Spieler |
| penalty_notice | Vertrag breached, `late_days × penalty_per_day` (= `generate_financials`), letzte Ankunft + 3..14 T | finance (≤ 250.000 CR) bzw. executive | contract | Summe = `contract_penalties` |
| payment_reminder | `payment_status = overdue`, Stufen +3..7 / +21 / +45 T | finance → finance | order | Schuldenhebel (Feldspat) |
| breach_warning | Verstoß gegen Exklusivität/Vorkaufsrecht/Gewährleistung | relations/executive | framework, contract | – |
| termination_notice / suspension_notice | Teilkündigung, Aussetzung, Androhung, Ende der Historie | executive | framework, partnership | Marktumbruch zum Spielstart |
| protest | Rivalitätsvorfall | executive → executive | rivalry, event | – |
| confidential_tip / rumor | Leck nach Formel `espionage_risk/100 × bribe/100 × (1 − loyalty/150)`; 30 % wahr, 50 % offen, 20 % falsch | Leck-Mitarbeiter (Regel bribe ≥ 50 oder loyalty ≤ 50) | rivalry, Quelle über `refers_to` | Kern der Spionage: kaufbar, prüfbar, fälschbar |
| internal_memo | interne Bewertung | innerhalb der Firma | beliebig | Beute bei Einbruch/Bestechung |

### 7.3 Verankerte Vorgänge

**V1–V38 aus der Entscheidung bleiben verbindlich und sind geprüft** (P10–P13), mit den Datumskorrekturen K3–K6 von
Team B (V1 2057-08-28/09-13/10-07, V27 2059-10-14, V32 2059-03-29, V36 2059-12-31 durch Kayla Cannon). Weitere
Änderungen und Ergänzungen R2:

| # | Datum | Art | Absender → Empfänger | Bezug | Begründung |
|---|---|---|---|---|---|
| V14 (korr.) | **2059-01-27** / 01-28 / 02-05 | rumor (wahr) / offer / offer_rejection | **Kaspar Täsche 43** (leaked_by) → Kuppelwerk; Kuppelwerk → Hülya Matthäi 41; Matthäi → Kuppelwerk | Strafbescheid V13 (2059-01-25), HMX-MSA-2057-01 | Erkan Hesse (68/43) erfüllt die Leck-Regel nicht. Das Gerücht stand vor dem Bescheid, über den es berichtet |
| V39 (Team B) | 2059-08-28 / 09-02 / 09-12 | rumor (wahr, Leck) / breach_warning / Antwort | Richard Chavez 120 (Corvane, 53/76) → Cindervale Marktaufklärung; Cindervale-Vorstand → Roswitha van der Dussen 168 (cc Bauer 170); Esther Bauer 170 → Cindervale | CVB-CTR-2059-0066, CCI-MSA-2057-01, Ereignisse 19/36 | Δ1/K1. Brücke zwischen Preisnachlass (2058-12) und Aussetzung (2059-12) |
| V40 (neu) | 2059-06-04 | internal_memo (confidential) | Reimar Rörricht 38 → Lena Heß 40 | refers_to V14 | Lichtacker verdächtigt Erkan Hesse, der am 2059-06-11 tatsächlich entlassen wird (Bestand). Das wahre Leck ist Täsche, das zeigt `leaked_by` in V14 → Spionage-Rätsel für den Spieler |
| V41 (neu) | 2058-11-20 | confidential_tip (business, wahr) | Freddy Dörr 235 (leaked_by) → Graufalk Marktaufklärung | Ereignis 36, Rivalität graufalk → eisenkrone | Δ6, Grundlage für Graufalks Angebote zu Triebwerksteilen nach Förster-Ausfällen |

### 7.4 Mitarbeiter der neuen Firmen (Δ8, Antwort auf R2-2)

Durchlauf 2 setzt für Vorstand, erste Partnerbetreuung und erste Marktaufklärung jeder neuen Firma
`hire_date ≤ min(frühestes verankertes Schreiben, Rahmenbeginn − 30 T) − 30 T`. Das gilt nur im Erweiterungsstrom, der
Bestand ändert sich nicht. Berechnete Grenzen: Graufalk und Cindervale 2056-11-02, Pionierwerk und Raureif 2057-11-02,
Outmark 2057-12-03, Second Hull 2058-03-02, Kuppelwerk 2058-04-02, Ravenmoor 2058-05-16, Morgengrund 2058-11-02,
Emberline 2059-01-31, Kometenpost 2059-04-12, Lanternfish ohne Grenze. Alle liegen nach den Gründungsspannen aus Phase 1.
Für Bestandsfirmen ohne Vorstand gilt die Ersatzregel aus der Entscheidung (Eisenkrone vor 2059-07-07: Esther Bauer 170;
Feldspat vor 2057-11-22: Mikhail Gotthard 2), auch als Unterzeichner der Rahmen EKM-RV-2057-0x und HMX-MSA-2057-03.

**Mengen** unverändert: ca. 850 Schreiben zu Bestandsobjekten, ca. 2.200–2.800 für alle 18 Firmen (V39–V41: +5 Schreiben).

---

## 8. QA-Ergänzungen (Zuständigkeit Team A, mit Team B abgestimmt)

1. 18 Firmen 6/6/6, je Größe ≥ 1 de_DE und ≥ 1 en_US (statt 6 Firmen 2/2/2).
2. Zählung nach Tabelle 3.5, jede Firma ≥ 1 ausgehende Vereinbarung, Hub large, ≥ 2 Paare nur indirekt (Soll: 66).
3. **Bestandsvergleich**: Stammdaten der 6 Firmen (Firmen, Stationen inkl. Koordinaten, Produkte, Mitarbeiter) und
   **alle `qa_anchor_objects`** feldweise gegen `space_trading_game_bestand.db` (R2-1).
4. Zuordnung = 341 Bestandsverträge. Außerhalb liegen genau EKM-VTR-2060-0230, FSP-VTR-2059-0001 und -0005.
5. Exklusivitätsfilter 6.4: keine unbeabsichtigten Verstöße bei neuen Paaren. Jeder Verstoß hat ein `breach_warning`.
6. Jeder Rahmen-Scope hat am Käufer mindestens einen Stationstyp, der die Ware verbraucht (Δ3).
7. Absender und Empfänger sind am `sent_at` beschäftigt, auch die Unterzeichner der Rahmen (Δ8). Jeder `leaked_by`
   erfüllt die Leck-Regel (Δ6/Δ7). Antworten kommen nach dem Bezugsschreiben, kein Schreiben vor seinem Bezugsobjekt,
   Mahnungen frühestens Fälligkeit + 3 T (K3–K6).
8. Strafbescheide je Firma und Monat = `contract_penalties`.

## 9. Umsetzung (Reihenfolge, unverändert bis auf R2)

1. Durchlauf 1 = heutige Pipeline (Bestand identisch).
2. Durchlauf 2 (Team A): Systeme anhängen, neue Firmen mit eigenem RNG/Faker, Archetyp-Filter, **Kuppelwerk mit
   Pflichtstation `("mining", "aurelis")` (Δ9)**, Mitarbeiter mit Einstellungsgrenzen (Δ8), Vereinbarungen, Historie
   und Rivalitäten aus dem JSON, Verträge mit Rahmen-Regel und **Exklusivitätsfilter (Δ4)**.
3. Team B: Rahmen, Scope, Nachträge (82, mit Δ1–Δ3 und K1/K2/K6/K7), Schriftverkehr (V1–V41 mit K3–K6), eigene QA.
4. QA (Abschnitt 8).

**Δ-Übersicht:** Δ1 CCI-Exklusivität (= K1) · Δ2 Produktaufnahmen einzeln · Δ3 Scope KHB-RV-2059-01 · Δ4 Exklusivitätsfilter (mit K8 vereinigt) ·
Δ5 Ankerobjekte in der QA (R2-1) · Δ6 Informanten nach Leck-Regel · Δ7 V14 (Absender, Datum) · Δ8 Einstellungsgrenzen
neuer Firmen (R2-2) · Δ9 Kuppelwerk-Bergbau Aurelis (R2-3, optional, braucht Zustimmung von Team B/Schiedsrichter, weil
es ein Phase-1-Profil ändert).

## 10. Maschinenlesbarer Vorschlag

Pflichtschlüssel `partnerships`, `historic`, `rivalries`, `framework_agreements`. Zusätzlich: `optional_partnerships`
(`helix → corvane`, zählt als 48. aktive Kante), Details, Filter, Einstellungsgrenzen, Ankerobjekte und
Schreib-Änderungen. Die Rahmen sind `verknuepfungen.json` mit Δ1–Δ3 und K1/K2/K6/K7/K10 eingearbeitet (Feld `r2_change`).

```json
{
 "meta": {"stand": "2026-10-21", "phase": 2, "team": "A", "revision": "R2 (Neudurchlauf)", "basis": "verknuepfungen.json (Schiedsrichter, verbindlich) + Prüfung gegen Bestand Seed 42", "active_agreements_total": 48, "note": "partnerships = 47 feste Kanten; helix->corvane bleibt in optional_partnerships (Bestandsstrom, Seed 42 aktiv)"},
 "partnerships": [
  ["eisenkrone", "helix", "supply_agreement"],
  ["helix", "eisenkrone", "strategic_alliance"],
  ["helix", "lichtacker", "distribution_agreement"],
  ["lichtacker", "helix", "supply_agreement"],
  ["corvane", "helix", "licensing"],
  ["feldspat", "helix", "consignment"],
  ["driftwood", "helix", "consignment"],
  ["feldspat", "eisenkrone", "supply_agreement"],
  ["eisenkrone", "feldspat", "supply_agreement"],
  ["eisenkrone", "lichtacker", "supply_agreement"],
  ["corvane", "eisenkrone", "supply_agreement"],
  ["eisenkrone", "corvane", "joint_venture"],
  ["lichtacker", "corvane", "supply_agreement"],
  ["graufalk", "helix", "supply_agreement"],
  ["cindervale", "eisenkrone", "supply_agreement"],
  ["kuppelwerk", "lichtacker", "supply_agreement"],
  ["emberline", "corvane", "supply_agreement"],
  ["emberline", "lichtacker", "supply_agreement"],
  ["raureif", "eisenkrone", "supply_agreement"],
  ["ravenmoor", "helix", "logistics_partnership"],
  ["cindervale", "graufalk", "supply_agreement"],
  ["graufalk", "cindervale", "strategic_alliance"],
  ["emberline", "graufalk", "supply_agreement"],
  ["graufalk", "emberline", "supply_agreement"],
  ["kuppelwerk", "graufalk", "supply_agreement"],
  ["emberline", "kuppelwerk", "supply_agreement"],
  ["emberline", "cindervale", "supply_agreement"],
  ["cindervale", "kometenpost", "consignment"],
  ["kometenpost", "cindervale", "logistics_partnership"],
  ["cindervale", "lanternfish", "supply_agreement"],
  ["lanternfish", "graufalk", "supply_agreement"],
  ["lanternfish", "kometenpost", "consignment"],
  ["raureif", "pionierwerk", "supply_agreement"],
  ["pionierwerk", "morgengrund", "supply_agreement"],
  ["morgengrund", "pionierwerk", "supply_agreement"],
  ["ravenmoor", "pionierwerk", "logistics_partnership"],
  ["pionierwerk", "ravenmoor", "supply_agreement"],
  ["outmark", "pionierwerk", "licensing"],
  ["second_hull", "pionierwerk", "supply_agreement"],
  ["second_hull", "ravenmoor", "consignment"],
  ["raureif", "ravenmoor", "supply_agreement"],
  ["ravenmoor", "outmark", "logistics_partnership"],
  ["morgengrund", "ravenmoor", "supply_agreement"],
  ["outmark", "raureif", "supply_agreement"],
  ["kuppelwerk", "pionierwerk", "supply_agreement"],
  ["second_hull", "graufalk", "supply_agreement"],
  ["graufalk", "ravenmoor", "supply_agreement"]
 ],
 "optional_partnerships": [
  ["helix", "corvane", "logistics_partnership", 0.6]
 ],
 "historic": [
  ["corvane", "driftwood", "supply_agreement"],
  ["eisenkrone", "graufalk", "supply_agreement"],
  ["cindervale", "helix", "licensing"],
  ["lichtacker", "pionierwerk", "supply_agreement"],
  ["emberline", "eisenkrone", "supply_agreement"],
  ["outmark", "feldspat", "licensing"],
  ["driftwood", "second_hull", "consignment"]
 ],
 "historic_details": [
  {"seller_key": "corvane", "buyer_key": "driftwood", "type": "supply_agreement", "source": "bestand", "dates": "Bestand 2057-04-27 bis 2058-07-17, unverändert (Bestandsstrom)"},
  {"seller_key": "eisenkrone", "buyer_key": "graufalk", "type": "supply_agreement", "start_date": "2039-01-01", "end_date": "2049-06-30", "hook": "Ausgliederung der Werftsparte Orrin; Patentstreit Reaktorkomponenten"},
  {"seller_key": "cindervale", "buyer_key": "helix", "type": "licensing", "start_date": "2041-04-01", "end_date": "2054-03-31", "hook": "Helix verliert die Cindervale-Lizenz und bezieht Hochtechnologie seither über Kharon"},
  {"seller_key": "lichtacker", "buyer_key": "pionierwerk", "type": "supply_agreement", "start_date": "2045-03-01", "end_date": "2053-06-30", "hook": "Versorgung der Isolde-Bautrupps bis zum Pachtstreit"},
  {"seller_key": "emberline", "buyer_key": "eisenkrone", "type": "supply_agreement", "start_date": "2047-02-01", "end_date": "2056-06-30", "hook": "Helium-3 für Bergbaustation Hande; endete mit eigener Deuteriumförderung von Eisenkrone"},
  {"seller_key": "outmark", "buyer_key": "feldspat", "type": "licensing", "start_date": "2055-02-01", "end_date": "2058-06-30", "hook": "Vermessungsdaten Brennus; ein Jahr später Fund 52 bei Becker"},
  {"seller_key": "driftwood", "buyer_key": "second_hull", "type": "consignment", "start_date": "2057-05-01", "end_date": "2058-07-01", "hook": "Bergegut aus Nyx; Bruch zwei Tage nach Razzia 26"}
 ],
 "rivalries": [
  ["eisenkrone", "helix", "market_dominance", "sol"],
  ["driftwood", "corvane", "industrial_espionage", "halcyon"],
  ["feldspat", "driftwood", "territorial_claims", "kharon"],
  ["lichtacker", "eisenkrone", "resource_competition", "myrrhen"],
  ["graufalk", "eisenkrone", "market_dominance", "halcyon"],
  ["cindervale", "helix", "market_dominance", "sol"],
  ["emberline", "eisenkrone", "resource_competition", "myrrhen"],
  ["lichtacker", "pionierwerk", "territorial_claims", "isolde"],
  ["ravenmoor", "driftwood", "armed_conflict", "nyx"],
  ["outmark", "feldspat", "territorial_claims", "brennus"],
  ["ravenmoor", "helix", "market_dominance", "kharon"],
  ["second_hull", "driftwood", "territorial_claims", "nyx"]
 ],
 "rivalry_details": [
  {"company_key": "eisenkrone", "rival_key": "helix", "type": "market_dominance", "system": "sol", "source": "bestand"},
  {"company_key": "driftwood", "rival_key": "corvane", "type": "industrial_espionage", "system": "halcyon", "source": "bestand"},
  {"company_key": "feldspat", "rival_key": "driftwood", "type": "territorial_claims", "system": "kharon", "source": "bestand"},
  {"company_key": "lichtacker", "rival_key": "eisenkrone", "type": "resource_competition", "system": "myrrhen", "source": "bestand"},
  {"company_key": "graufalk", "rival_key": "eisenkrone", "type": "market_dominance", "system": "halcyon", "since_date": "2049-07-01", "intensity": 70, "espionage_risk": 55, "anchor_events": [19, 36, 70], "anchor_contracts": ["EKM-VTR-2057-0064"], "informants": [170, 235], "targets_hard_to_buy": [178], "r2_change": "Freddy Dörr (235, Sicherheit Förster, Loyalität 45, Bestechlichkeit 88) ergänzt; Schuchhardt (178, 85/25) erfüllt die Leck-Regel nicht und ist nur Zielperson"},
  {"company_key": "cindervale", "rival_key": "helix", "type": "market_dominance", "system": "sol", "since_date": "2054-04-01", "intensity": 65, "espionage_risk": 50, "anchor_events": [3, 24], "anchor_contracts": ["HMX-CTR-2057-0050", "HMX-CTR-2058-0121"], "informants": [319, 299], "witnesses": [120], "r2_change": "Darren Harris (319, Helix-Marktaufklärung seit 2056-02-19, 35/69) ergänzt, damit es vor 2059-11-24 einen Helix-internen Informanten gibt; Chavez ist Corvane (Dritter)"},
  {"company_key": "emberline", "rival_key": "eisenkrone", "type": "resource_competition", "system": "myrrhen", "since_date": "2058-08-15", "intensity": 55, "espionage_risk": 40, "text_override": true, "anchor_contracts": ["EKM-VTR-2058-0099", "EKM-VTR-2058-0105", "EKM-VTR-2059-0167"], "informants": [170], "witnesses": [83, 45], "r2_change": "Eberhardt (45, 75/23) und Zahn (83) sind Lichtacker, also Zeugen, keine Lecks bei Eisenkrone; Leck-Quelle bei Eisenkrone ist Esther Bauer (170)"},
  {"company_key": "lichtacker", "rival_key": "pionierwerk", "type": "territorial_claims", "system": "isolde", "since_date": "2053-07-01", "intensity": 60, "espionage_risk": 55, "text_override": true, "informants": [43]},
  {"company_key": "ravenmoor", "rival_key": "driftwood", "type": "armed_conflict", "system": "nyx", "since_date": "2058-06-30", "intensity": 85, "espionage_risk": 70, "anchor_events": [26, 58, 45, 54, 57, 67], "informants": [29, 33]},
  {"company_key": "outmark", "rival_key": "feldspat", "type": "territorial_claims", "system": "brennus", "since_date": "2059-07-14", "intensity": 65, "espionage_risk": 80, "anchor_events": [52], "informants": [16]},
  {"company_key": "ravenmoor", "rival_key": "helix", "type": "market_dominance", "system": "kharon", "since_date": "2057-11-17", "intensity": 55, "espionage_risk": 45, "anchor_events": [16, 26], "informants": [302, 395, 445]},
  {"company_key": "second_hull", "rival_key": "driftwood", "type": "territorial_claims", "system": "nyx", "since_date": "2058-07-01", "intensity": 50, "espionage_risk": 40, "anchor_events": [54], "informants": [27]}
 ],
 "new_rivalry_types": {"armed_conflict": {"intensity": [60, 90], "texts": "wie phase1_team_b.md"}},
 "rivalry_text_overrides": {"emberline-eisenkrone": {"de_DE": "{company} und {rival} liefern beide Energie ins {system}-System und unterbieten sich bei jedem Liefervertrag.", "en_US": "{company} and {rival} both supply energy to the {system} system and undercut each other on every supply contract."}, "lichtacker-pionierwerk": {"de_DE": "Streit um Pachtrechte im {system}-System: {company} hält {rival} vor, alte Pachtverträge für Makulatur erklärt zu haben.", "en_US": "A dispute over lease rights in the {system} system: {company} accuses {rival} of tearing up old lease contracts."}},
 "framework_agreements": [
  {"number": "HMX-MSA-2057-01", "seller_key": "helix", "buyer_key": "lichtacker", "title": "Distribution Framework Agreement Agricultural Rings Tauvel, Aurelis & Myrrhen", "start_date": "2057-01-01", "start_year": 2057, "term_months": 36, "base_volume_mcr": 250, "price_formula": "index_linked", "indexation": "category_price_index", "exclusivity": "right_of_first_refusal", "notice_days": 180, "scope": ["luxury", "food", "industrial_goods"], "existing_pair": true, "adjustment_cap_pct": 8, "exclusive_categories": ["industrial_goods"], "expected_assigned_contracts": 54, "amendments": [{"type": "product_addition", "effective_date": "2057-04-01", "status": "signed", "categories": ["energy", "technology"], "rule": "first_contract_of_category"}, {"type": "product_addition", "effective_date": "2057-09-01", "status": "signed", "categories": ["medical"], "rule": "first_contract_of_category"}, {"type": "penalty_clause", "effective_date": "2058-03-14", "status": "signed", "proposed_date": "2058-02-20", "initiated_by": "lichtacker", "anchor_contracts": ["HMX-CTR-2057-0043"]}, {"type": "volume_increase", "effective_date": "2058-09-01", "status": "signed", "volume_after_mcr": 400, "anchor_contracts": ["HMX-CTR-2058-0161"], "rule": "cumulative_over_90pct"}, {"type": "exclusivity_waiver", "effective_date": "2059-03-15", "status": "signed", "proposed_date": "2059-03-10", "initiated_by": "lichtacker", "categories": ["industrial_goods"], "anchor_contracts": ["HMX-CTR-2057-0043", "HMX-CTR-2058-0139", "HMX-CTR-2058-0159"]}, {"type": "volume_increase", "effective_date": "2059-10-01", "status": "signed", "volume_after_mcr": 550, "anchor_contracts": ["HMX-CTR-2059-0259"], "rule": "cumulative_over_90pct"}, {"type": "term_extension", "effective_date": "2059-11-01", "status": "signed", "new_end_date": "2060-12-31", "initiated_by": "lichtacker", "rule": "calloff_after_end"}]},
  {"number": "HMX-MSA-2057-02", "seller_key": "helix", "buyer_key": "corvane", "title": "Logistics & Supply Master Agreement Halcyon/Aurelis", "start_date": "2057-01-01", "start_year": 2057, "term_months": 36, "base_volume_mcr": 300, "price_formula": "market_minus", "indexation": "category_price_index", "exclusivity": "none", "notice_days": 120, "scope": ["luxury", "raw_materials"], "existing_pair": true, "base_discount_pct": 4, "expected_assigned_contracts": 68, "amendments": [{"type": "product_addition", "effective_date": "2057-03-01", "status": "signed", "categories": ["technology"], "rule": "first_contract_of_category"}, {"type": "product_addition", "effective_date": "2057-05-01", "status": "signed", "categories": ["energy"], "rule": "first_contract_of_category"}, {"type": "exclusivity_clause", "effective_date": "2057-05-01", "status": "signed", "initiated_by": "helix", "exclusivity": "buyer_exclusive", "categories": ["energy"]}, {"type": "product_addition", "effective_date": "2058-01-01", "status": "signed", "categories": ["industrial_goods"], "rule": "first_contract_of_category"}, {"type": "volume_increase", "effective_date": "2058-08-01", "status": "signed", "volume_after_mcr": 450, "anchor_contracts": ["HMX-CTR-2058-0152"], "rule": "cumulative_over_90pct"}, {"type": "product_removal", "effective_date": "2059-03-15", "status": "signed", "proposed_date": "2059-03-13", "initiated_by": "corvane", "archetypes": ["helium3"], "anchor_contracts": ["HMX-CTR-2058-0131", "HMX-CTR-2057-0014"], "anchor_events": [30]}, {"type": "exclusivity_waiver", "effective_date": "2059-03-15", "status": "signed", "proposed_date": "2059-03-13", "initiated_by": "corvane", "categories": ["energy"], "anchor_contracts": ["HMX-CTR-2058-0131"]}, {"type": "volume_increase", "effective_date": "2059-04-01", "status": "signed", "volume_after_mcr": 600, "anchor_contracts": ["HMX-CTR-2059-0213"], "rule": "cumulative_over_90pct"}, {"type": "term_extension", "effective_date": "2059-11-01", "status": "signed", "new_end_date": "2060-12-31", "initiated_by": "corvane", "rule": "calloff_after_end"}, {"type": "volume_increase", "effective_date": "2060-02-01", "status": "proposed", "proposed_date": "2059-12-15", "volume_after_mcr": 750, "anchor_contracts": ["HMX-CTR-2060-0281"], "rule": "cumulative_over_90pct"}]},
  {"number": "HMX-MSA-2057-03", "seller_key": "helix", "buyer_key": "eisenkrone", "title": "Strategic Supply Framework Sol/Halcyon/Brennus", "start_date": "2057-01-01", "start_year": 2057, "term_months": 48, "base_volume_mcr": 300, "price_formula": "cost_plus", "indexation": "category_price_index", "exclusivity": "none", "notice_days": 360, "scope": ["food", "raw_materials", "energy"], "existing_pair": true, "cost_plus_pct": 9, "expected_assigned_contracts": 75, "amendments": [{"type": "product_addition", "effective_date": "2057-07-01", "status": "signed", "categories": ["medical"], "rule": "first_contract_of_category", "r2_change": "einzeln nach Regel first_contract_of_category"}, {"type": "product_addition", "effective_date": "2057-09-01", "status": "signed", "categories": ["technology"], "rule": "first_contract_of_category", "r2_change": "einzeln nach Regel first_contract_of_category"}, {"type": "product_addition", "effective_date": "2057-11-01", "status": "signed", "categories": ["industrial_goods"], "rule": "first_contract_of_category", "r2_change": "einzeln nach Regel first_contract_of_category"}, {"type": "volume_reduction", "effective_date": "2058-03-01", "status": "signed", "proposed_date": "2058-02-15", "initiated_by": "eisenkrone", "volume_after_mcr": 250, "anchor_events": [19]}, {"type": "volume_increase", "effective_date": "2059-01-01", "status": "signed", "volume_after_mcr": 350, "anchor_contracts": ["HMX-CTR-2059-0192"], "rule": "cumulative_over_90pct"}, {"type": "volume_increase", "effective_date": "2059-06-01", "status": "signed", "volume_after_mcr": 450, "anchor_contracts": ["HMX-CTR-2059-0236"], "rule": "cumulative_over_90pct"}, {"type": "volume_increase", "effective_date": "2060-01-01", "status": "proposed", "proposed_date": "2059-12-10", "volume_after_mcr": 550, "anchor_contracts": ["HMX-CTR-2060-0275"], "rule": "cumulative_over_90pct"}]},
  {"number": "EKM-RV-2057-01", "seller_key": "eisenkrone", "buyer_key": "corvane", "title": "Joint-Venture-Liefervertrag Halcyon", "start_date": "2057-01-01", "start_year": 2057, "term_months": 60, "base_volume_mcr": 350, "price_formula": "cost_plus", "indexation": "category_price_index", "exclusivity": "right_of_first_refusal", "notice_days": 360, "scope": ["raw_materials", "industrial_goods"], "existing_pair": true, "cost_plus_pct": 12, "exclusive_categories": ["raw_materials"], "expected_assigned_contracts": 65, "amendments": [{"type": "product_addition", "effective_date": "2057-05-01", "status": "signed", "categories": ["luxury"], "rule": "first_contract_of_category", "r2_change": "einzeln nach Regel first_contract_of_category"}, {"type": "product_addition", "effective_date": "2057-06-01", "status": "signed", "categories": ["technology"], "rule": "first_contract_of_category", "r2_change": "einzeln nach Regel first_contract_of_category"}, {"type": "penalty_clause", "effective_date": "2058-05-01", "status": "signed", "proposed_date": "2058-04-28", "initiated_by": "corvane", "anchor_contracts": ["EKM-VTR-2057-0064"]}, {"type": "volume_increase", "effective_date": "2059-03-01", "status": "signed", "volume_after_mcr": 450, "anchor_contracts": ["EKM-VTR-2059-0160"], "rule": "cumulative_over_90pct"}, {"type": "service_level_clause", "effective_date": "2060-02-01", "status": "proposed", "proposed_date": "2059-12-23", "initiated_by": "corvane", "anchor_contracts": ["EKM-VTR-2059-0160"]}, {"type": "volume_increase", "effective_date": "2060-01-01", "status": "proposed", "proposed_date": "2059-12-10", "volume_after_mcr": 550, "anchor_contracts": ["EKM-VTR-2060-0219"], "rule": "cumulative_over_90pct"}]},
  {"number": "EKM-RV-2057-02", "seller_key": "eisenkrone", "buyer_key": "helix", "title": "Rahmenvertrag Erze und Energie Brennus/Halcyon – Kharon/Sol", "start_date": "2057-01-01", "start_year": 2057, "term_months": 42, "base_volume_mcr": 200, "price_formula": "index_linked", "indexation": "category_price_index", "exclusivity": "none", "notice_days": 180, "scope": ["energy", "raw_materials"], "existing_pair": true, "price_index_category": "raw_materials", "adjustment_cap_pct": 10, "expected_assigned_contracts": 39, "amendments": [{"type": "product_addition", "effective_date": "2057-06-01", "status": "signed", "categories": ["food"], "rule": "first_contract_of_category", "r2_change": "einzeln nach Regel first_contract_of_category"}, {"type": "product_addition", "effective_date": "2057-10-01", "status": "signed", "categories": ["technology"], "rule": "first_contract_of_category", "r2_change": "einzeln nach Regel first_contract_of_category"}, {"type": "product_addition", "effective_date": "2058-01-01", "status": "signed", "categories": ["industrial_goods"], "rule": "first_contract_of_category"}, {"type": "penalty_clause", "effective_date": "2058-01-09", "status": "signed", "proposed_date": "2057-12-20", "initiated_by": "helix", "anchor_contracts": ["EKM-VTR-2057-0017"]}, {"type": "product_addition", "effective_date": "2058-08-01", "status": "signed", "categories": ["luxury"], "rule": "first_contract_of_category"}, {"type": "volume_increase", "effective_date": "2059-02-01", "status": "signed", "volume_after_mcr": 300, "anchor_contracts": ["EKM-VTR-2059-0151"], "rule": "cumulative_over_90pct"}, {"type": "escort_clause", "effective_date": "2060-02-01", "status": "proposed", "proposed_date": "2059-12-22", "initiated_by": "helix", "escort_key": "ravenmoor", "anchor_contracts": ["EKM-VTR-2057-0043", "EKM-VTR-2058-0107"], "anchor_orders": ["EKM-BST-2059-02343"], "anchor_events": [74], "linked_amendment": "RCS-MSA-2058-01#escort_clause", "berth_anchor_contracts": ["EKM-VTR-2057-0017", "EKM-VTR-2059-0162"], "r2_change": "K2 (Team B): Geleitschutz-Anker sind die echten Geleitschutzbrüche; die Andockstau-Brüche begründen Ausweich-Liegeplätze an Ravenmoors Handelsstation Kharon"}, {"type": "volume_increase", "effective_date": "2060-02-01", "status": "proposed", "proposed_date": "2059-12-22", "volume_after_mcr": 400, "anchor_contracts": ["EKM-VTR-2060-0234"], "rule": "cumulative_over_90pct"}, {"type": "term_extension", "effective_date": "2060-07-01", "status": "proposed", "proposed_date": "2059-12-22", "new_end_date": "2061-06-30", "initiated_by": "helix"}]},
  {"number": "EKM-RV-2057-03", "seller_key": "eisenkrone", "buyer_key": "lichtacker", "title": "Liefervertrag Industriegüter und Energie Myrrhen/Tauvel", "start_date": "2057-01-01", "start_year": 2057, "term_months": 36, "base_volume_mcr": 150, "price_formula": "index_linked", "indexation": "category_price_index", "exclusivity": "none", "notice_days": 90, "scope": ["industrial_goods", "luxury", "raw_materials"], "existing_pair": true, "price_index_category": "energy", "adjustment_cap_pct": 6, "expected_assigned_contracts": 35, "expected_outside": ["EKM-VTR-2060-0230"], "amendments": [{"type": "product_addition", "effective_date": "2057-08-01", "status": "signed", "categories": ["energy"], "rule": "first_contract_of_category"}, {"type": "product_addition", "effective_date": "2058-02-01", "status": "signed", "categories": ["technology"], "rule": "first_contract_of_category"}, {"type": "penalty_clause", "effective_date": "2058-09-14", "status": "signed", "proposed_date": "2058-08-28", "initiated_by": "lichtacker", "anchor_contracts": ["EKM-VTR-2058-0099"]}, {"type": "partial_termination", "effective_date": "2060-01-18", "status": "signed", "proposed_date": "2059-10-20", "initiated_by": "lichtacker", "categories": ["energy"], "anchor_contracts": ["EKM-VTR-2059-0167", "EKM-VTR-2058-0105", "EKM-VTR-2058-0099"], "note": "laufende Energieabrufe (EKM-VTR-2059-0197) werden bis zur Frist erfüllt; EKM-VTR-2060-0230 (Entwurf) liegt außerhalb des Rahmens"}, {"type": "price_adjustment", "effective_date": "2060-01-18", "status": "rejected", "proposed_date": "2059-10-28", "initiated_by": "eisenkrone", "pct": -5, "categories": ["energy"], "note": "Rettungsangebot Eisenkrone, von Lichtacker am 2059-11-10 abgelehnt"}, {"type": "volume_increase", "effective_date": "2059-11-01", "status": "signed", "volume_after_mcr": 200, "anchor_contracts": ["EKM-VTR-2059-0211"], "rule": "cumulative_over_90pct"}, {"type": "term_extension", "effective_date": "2059-11-01", "status": "signed", "new_end_date": "2060-12-31", "initiated_by": "lichtacker", "rule": "calloff_after_end", "note": "nur Restumfang ohne Energie"}]},
  {"number": "FSP-RV-2059-01", "seller_key": "feldspat", "buyer_key": "eisenkrone", "title": "Abnahmerahmen Quantenquarz Becker", "start_date": "2059-08-01", "start_year": 2059, "term_months": 24, "base_volume_mcr": 12, "price_formula": "market_minus", "indexation": "category_price_index", "exclusivity": "right_of_first_refusal", "notice_days": 90, "scope": ["raw_materials"], "existing_pair": true, "base_discount_pct": 5, "exclusive_archetypes": ["quantum_quartz"], "expected_assigned_contracts": 5, "story": "Feldspat schuldet Eisenkrone nach Datum 22,94 Mio. CR (2059-07-20, 11 Bestellungen), 24,22 Mio. (2059-08-01, 12) und ab 2059-09-23 25,52 Mio. (13); das Vorkaufsrecht auf Quantenquarz ist das Pfand (K10 Team B)", "amendments": [{"type": "price_adjustment", "effective_date": "2059-11-20", "status": "signed", "proposed_date": "2059-11-05", "initiated_by": "feldspat", "pct": 12, "anchor_events": [65, 66], "anchor_contracts": ["FSP-VTR-2059-0019"], "note": "nach Stornierung des Abrufvertrags FSP-VTR-2059-0019 im Preisstreit"}, {"type": "volume_increase", "effective_date": "2060-01-15", "status": "proposed", "proposed_date": "2059-12-15", "volume_after_mcr": 20, "initiated_by": "feldspat"}]},
  {"number": "GFW-RV-2057-01", "seller_key": "graufalk", "buyer_key": "helix", "title": "Flottenrahmenvertrag Rumpf- und Triebwerksteile", "start_date": "2057-01-01", "start_year": 2057, "term_months": 48, "base_volume_mcr": 180, "price_formula": "index_linked", "indexation": "category_price_index", "exclusivity": "none", "notice_days": 180, "scope": ["industrial_goods"], "price_index_category": "industrial_goods", "amendments": [{"type": "product_addition", "effective_date": "rule", "status": "signed", "categories": ["technology"], "rule": "first_contract_of_category"}, {"type": "volume_increase", "effective_date": "2058-12-20", "status": "signed", "proposed_date": "2058-12-16", "initiated_by": "helix", "delta_mcr": 60, "anchor_contracts": ["HMX-CTR-2058-0173"]}, {"type": "service_level_clause", "effective_date": "2060-01-15", "status": "proposed", "proposed_date": "2059-12-31", "initiated_by": "helix", "anchor_orders": ["HMX-ORD-2059-01763", "HMX-ORD-2059-01788"], "note": "Eilabrufklausel Triebwerksteile", "r2_change": "K6 (Team B): HMX-ORD-2059-01788 entsteht erst 2059-12-29"}]},
  {"number": "GFW-RV-2057-02", "seller_key": "graufalk", "buyer_key": "cindervale", "title": "Allianzvertrag Navigationsplattform", "start_date": "2057-01-01", "start_year": 2057, "term_months": 60, "base_volume_mcr": 220, "price_formula": "cost_plus", "indexation": "category_price_index", "exclusivity": "none", "notice_days": 365, "scope": ["industrial_goods", "technology"], "cost_plus_pct": 8, "amendments": [{"type": "exclusivity_clause", "effective_date": "2058-03-15", "status": "signed", "proposed_date": "2058-02-20", "initiated_by": "graufalk", "exclusivity": "mutual", "archetypes": ["drive_parts"], "anchor_events": [19], "note": "Cindervale bezieht Triebwerksteile nur von Graufalk; Graufalk bezieht neue Navigationscomputer nur von Cindervale"}, {"type": "volume_increase", "effective_date": "rule", "status": "signed", "delta_mcr": 80, "rule": "cumulative_over_90pct"}, {"type": "confidentiality_clause", "effective_date": "2060-01-15", "status": "proposed", "proposed_date": "2059-12-29", "initiated_by": "cindervale", "note": "nach der Aussetzung CCI-MSA-2057-01 und dem Gerücht vom 2059-12-27"}], "protected_by_generator_filter": true},
  {"number": "GFW-RV-2058-01", "seller_key": "graufalk", "buyer_key": "ravenmoor", "title": "Geleitschiff-Rahmenvertrag Kharon/Brennus", "start_date": "2058-07-15", "start_year": 2058, "term_months": 36, "base_volume_mcr": 90, "price_formula": "index_linked", "indexation": "category_price_index", "exclusivity": "right_of_first_refusal", "notice_days": 180, "scope": ["industrial_goods"], "exclusive_archetypes": ["hull_plating"], "exclusivity_system": "kharon", "story": "Ravenmoor hat Vorkaufsrecht auf Graufalk-Rumpfplatten für Kharon; Helix bekommt nur, was Ravenmoor ablehnt", "amendments": [{"type": "product_addition", "effective_date": "rule", "status": "signed", "categories": ["technology"], "rule": "first_contract_of_category"}, {"type": "volume_increase", "effective_date": "2059-09-01", "status": "signed", "proposed_date": "2059-08-25", "initiated_by": "ravenmoor", "delta_mcr": 40, "anchor_events": [45, 57, 58]}]},
  {"number": "CCI-MSA-2057-01", "seller_key": "cindervale", "buyer_key": "eisenkrone", "title": "AI Control & Robotics Framework Agreement", "start_date": "2057-01-01", "start_year": 2057, "term_months": 48, "base_volume_mcr": 120, "price_formula": "fixed", "indexation": "none", "exclusivity": "right_of_first_refusal", "notice_days": 180, "scope": ["technology", "industrial_goods"], "exclusivity_system": "halcyon", "status_at_reference": "suspended", "amendments": [{"type": "service_level_clause", "effective_date": "2058-03-01", "status": "signed", "proposed_date": "2058-02-10", "initiated_by": "eisenkrone", "anchor_events": [19], "note": "Gewährleistungsklausel"}, {"type": "price_adjustment", "effective_date": "2058-12-15", "status": "signed", "proposed_date": "2058-11-20", "initiated_by": "cindervale", "pct": -8, "anchor_events": [36]}, {"type": "suspension", "effective_date": "2059-12-15", "status": "signed", "proposed_date": "2059-12-05", "initiated_by": "eisenkrone", "anchor_events": [70], "note": "Aussetzung bis zum Firmware-Audit; Kündigungsandrohung zum 2060-06-03 im Schreiben vom 2059-12-05"}], "r2_change": "K1 (Team B) = Δ1 (Team A): Vorkaufsrecht statt Käuferexklusivität, weil Corvane im Bestand Technik an Bergbaustation Hande liefert (CVB-CTR-2058-0003/-0013/-0038, -2059-0044, -2059-0066 exclusive_supply bis 2060-08-05, 25 Bestellungen); Folge-Vorgang V39", "exclusive_categories": ["technology"]},
  {"number": "KHB-RV-2058-01", "seller_key": "kuppelwerk", "buyer_key": "pionierwerk", "title": "Rahmenvertrag Habitatmodule Isolde", "start_date": "2058-06-01", "start_year": 2058, "term_months": 36, "base_volume_mcr": 70, "price_formula": "cost_plus", "indexation": "fuel_index", "exclusivity": "seller_exclusive", "notice_days": 180, "scope": ["industrial_goods"], "exclusive_archetypes": ["habitat_modules"], "exclusivity_system": "isolde", "cost_plus_pct": 10, "amendments": [{"type": "volume_increase", "effective_date": "2059-05-01", "status": "signed", "proposed_date": "2059-04-15", "initiated_by": "pionierwerk", "delta_mcr": 35, "note": "zweite Ausbaustufe Serravel"}, {"type": "scope_extension", "effective_date": "2059-10-01", "status": "signed", "proposed_date": "2059-09-10", "initiated_by": "pionierwerk", "system_code": "serravel", "archetypes": ["sinter_blocks"]}]},
  {"number": "KHB-RV-2059-01", "seller_key": "kuppelwerk", "buyer_key": "lichtacker", "title": "Baustoffrahmen Verbundstahl und Habitatbaustoffe Tauvel/Myrrhen", "start_date": "2059-04-01", "start_year": 2059, "term_months": 24, "base_volume_mcr": 30, "price_formula": "cost_plus", "indexation": "fuel_index", "exclusivity": "none", "notice_days": 90, "scope": ["industrial_goods", "raw_materials"], "cost_plus_pct": 10, "story": "folgt auf den Wegfall des Helix-Vorkaufsrechts (HMX-MSA-2057-01, 2059-03-15) und den Strafbescheid 653.162,16 CR", "amendments": [{"type": "product_addition", "effective_date": "2059-08-01", "status": "signed", "proposed_date": "2059-07-20", "initiated_by": "kuppelwerk", "archetypes": ["habitat_modules"], "anchor_events": [53]}, {"type": "volume_increase", "effective_date": "rule", "status": "signed", "rule": "cumulative_over_90pct"}, {"type": "exclusivity_clause", "effective_date": "2060-02-01", "status": "proposed", "proposed_date": "2059-12-10", "initiated_by": "kuppelwerk", "exclusivity": "regional_exclusive", "system_code": "myrrhen", "archetypes": ["sinter_blocks", "habitat_modules"]}], "scope_archetypes": {"raw_materials": ["regolith", "water_ice"]}, "r2_change": "Rohstoff-Scope auf regolith/water_ice begrenzt: Lichtacker hat nur agricultural/research-Stationen, andere Rohstoffe haben dort keinen Verbraucher"},
  {"number": "EFF-MSA-2059-01", "seller_key": "emberline", "buyer_key": "corvane", "title": "Helium-3 Supply Framework Halcyon Works VI", "start_date": "2059-04-01", "start_year": 2059, "term_months": 24, "base_volume_mcr": 40, "price_formula": "index_linked", "indexation": "fuel_index", "exclusivity": "none", "notice_days": 90, "scope": ["energy"], "story": "direkt nach der Herausnahme von Helium-3 aus HMX-MSA-2057-02 (2059-03-15); Sturmzuschlag Pellora", "amendments": [{"type": "force_majeure_clause", "effective_date": "2059-09-15", "status": "signed", "proposed_date": "2059-09-05", "initiated_by": "emberline", "anchor_events": [59]}, {"type": "volume_increase", "effective_date": "rule", "status": "signed", "rule": "cumulative_over_90pct"}, {"type": "exclusivity_clause", "effective_date": "2060-01-01", "status": "proposed", "proposed_date": "2059-12-05", "initiated_by": "emberline", "exclusivity": "buyer_exclusive", "archetypes": ["helium3"], "system_code": "halcyon"}]},
  {"number": "EFF-MSA-2059-02", "seller_key": "emberline", "buyer_key": "lichtacker", "title": "Energy Framework Agreement Agrarstation Seip", "start_date": "2059-11-15", "start_year": 2059, "term_months": 24, "base_volume_mcr": 18, "price_formula": "index_linked", "indexation": "fuel_index", "exclusivity": "none", "notice_days": 90, "scope": ["energy"], "story": "Kette: EKM-VTR-2058-0099/-0105/-2059-0167 gebrochen -> Teilkündigung EKM-RV-2057-03 -> Emberline", "amendments": [{"type": "exclusivity_clause", "effective_date": "2060-01-18", "status": "signed", "proposed_date": "2059-11-15", "initiated_by": "lichtacker", "exclusivity": "right_of_first_refusal", "categories": ["energy"], "system_code": "myrrhen", "note": "kein Käuferexklusiv, weil HMX-CTR-2059-0257 (Helix, Plasmagas an Seip) bis 2060-03-30 läuft"}]},
  {"number": "RCS-MSA-2058-01", "seller_key": "ravenmoor", "buyer_key": "helix", "title": "Escort & Frontier Supply Framework Kharon Corridor", "start_date": "2058-08-01", "start_year": 2058, "term_months": 36, "base_volume_mcr": 90, "price_formula": "cost_plus", "indexation": "risk_index", "exclusivity": "regional_exclusive", "notice_days": 90, "scope": ["industrial_goods", "technology", "medical", "food"], "cost_plus_pct": 15, "escort_key": "ravenmoor", "exclusive_archetypes": ["escort_drones", "sensor_arrays"], "exclusivity_system": "kharon", "story": "vom Gegner (Razzia 26, 2058-06-30) zum Schutzpartner", "amendments": [{"type": "volume_increase", "effective_date": "2059-06-15", "status": "signed", "proposed_date": "2059-06-05", "initiated_by": "helix", "delta_mcr": 40, "anchor_events": [51]}, {"type": "escort_clause", "effective_date": "2060-02-01", "status": "proposed", "proposed_date": "2059-12-22", "initiated_by": "ravenmoor", "escort_key": "ravenmoor", "anchor_events": [74], "linked_amendment": "EKM-RV-2057-02#escort_clause", "note": "dreiseitig: Geleit auch für Eisenkrone-Konvois nach Kharon"}, {"type": "scope_extension", "effective_date": "2060-01-15", "status": "proposed", "proposed_date": "2059-12-23", "initiated_by": "helix", "station": "Kharon Landing IV", "anchor_events": [74]}], "protected_by_generator_filter": true},
  {"number": "RVF-RV-2058-01", "seller_key": "raureif", "buyer_key": "pionierwerk", "title": "Versorgungsrahmen Isolde – Volatile", "start_date": "2058-01-01", "start_year": 2058, "term_months": 36, "base_volume_mcr": 80, "price_formula": "index_linked", "indexation": "fuel_index", "exclusivity": "regional_exclusive", "notice_days": 180, "scope": ["raw_materials", "energy"], "exclusive_archetypes": ["water_ice"], "exclusivity_system": "isolde", "amendments": [{"type": "exclusivity_clause", "effective_date": "2058-09-01", "status": "signed", "proposed_date": "2058-08-15", "initiated_by": "pionierwerk", "archetypes": ["nitrogen_ice"], "note": "Terraforming beginnt; Stickstoffeis fällt ab hier unter die Exklusivität", "exclusivity": "regional_exclusive", "system_code": "isolde", "r2_change": "K7 (Team B): Stickstoffeis erst ab diesem Nachtrag exklusiv"}, {"type": "volume_increase", "effective_date": "2059-06-01", "status": "signed", "proposed_date": "2059-05-15", "initiated_by": "pionierwerk", "delta_mcr": 30}, {"type": "price_adjustment", "effective_date": "2060-01-01", "status": "proposed", "proposed_date": "2059-11-20", "initiated_by": "raureif", "pct": 10, "note": "lange Wege, Piraterie"}], "protected_by_generator_filter": true, "r2_change": "K7 (Team B) übernommen"},
  {"number": "RVF-RV-2058-02", "seller_key": "raureif", "buyer_key": "eisenkrone", "title": "Volatile-Liefervertrag Myrrhen/Brennus", "start_date": "2058-03-01", "start_year": 2058, "term_months": 24, "base_volume_mcr": 45, "price_formula": "index_linked", "indexation": "category_price_index", "exclusivity": "none", "notice_days": 90, "scope": ["raw_materials", "energy"], "price_index_category": "raw_materials", "price_floor": true, "amendments": [{"type": "price_adjustment", "effective_date": "2059-08-01", "status": "signed", "proposed_date": "2059-07-25", "initiated_by": "eisenkrone", "pct": -6, "anchor_events": [52], "note": "Eisenkrone verweist auf den Fund 52 bei Feldspat"}, {"type": "term_extension", "effective_date": "2060-02-29", "status": "proposed", "proposed_date": "2059-12-15", "new_end_date": "2061-02-28", "initiated_by": "eisenkrone"}]},
  {"number": "OSP-MSA-2058-01", "seller_key": "outmark", "buyer_key": "pionierwerk", "title": "Survey Data License Framework Serravel/Isolde", "start_date": "2058-02-01", "start_year": 2058, "term_months": 36, "base_volume_mcr": 25, "price_formula": "fixed", "indexation": "none", "exclusivity": "none", "notice_days": 180, "scope": ["technology", "raw_materials"], "amendments": [{"type": "exclusivity_clause", "effective_date": "2059-08-15", "status": "signed", "proposed_date": "2059-07-30", "initiated_by": "pionierwerk", "exclusivity": "regional_exclusive", "system_code": "serravel", "archetypes": ["survey_charts"], "anchor_events": [52]}, {"type": "product_addition", "effective_date": "2059-11-01", "status": "signed", "archetypes": ["terraforming_cultures"], "condition": "nur wenn der Archetyp im Outmark-Produktpool liegt"}]},
  {"number": "SGM-RV-2059-01", "seller_key": "morgengrund", "buyer_key": "pionierwerk", "title": "Versorgungsrahmen Isolde – Lebensmittel für Bautrupps", "start_date": "2059-01-01", "start_year": 2059, "term_months": 12, "base_volume_mcr": 5, "price_formula": "fixed", "indexation": "none", "exclusivity": "none", "notice_days": 60, "scope": ["food"], "auto_renewal": true, "renewal_months": 12, "harvest_clause": true, "amendments": [{"type": "volume_increase", "effective_date": "2059-07-01", "status": "signed", "proposed_date": "2059-06-15", "initiated_by": "pionierwerk", "delta_mcr": 2}, {"type": "term_extension", "effective_date": "2060-01-01", "status": "signed", "new_end_date": "2060-12-31", "note": "automatische Verlängerung um 12 Monate"}]},
  {"number": "SGM-RV-2059-02", "seller_key": "morgengrund", "buyer_key": "ravenmoor", "title": "Garnisonsrationen Kharon und Brennus", "start_date": "2059-03-01", "start_year": 2059, "term_months": 12, "base_volume_mcr": 6, "price_formula": "fixed", "indexation": "none", "exclusivity": "none", "notice_days": 60, "scope": ["food"], "story": "schließt die Nahrungslücke Kharon (0 Angebote bei 20 Nachfragen)", "amendments": [{"type": "force_majeure_clause", "effective_date": "2059-03-01", "status": "signed", "proposed_date": "2059-02-15", "initiated_by": "morgengrund", "note": "Ernteausfallklausel; Vorbild sind die Ernteausfälle bei Lichtacker (Ereignisse 61, 71)"}, {"type": "term_extension", "effective_date": "2060-02-29", "status": "proposed", "proposed_date": "2059-12-20", "new_end_date": "2061-02-28", "initiated_by": "ravenmoor"}]}
 ],
 "exclusivity_filter_new_pairs": [
  {"seller_keys": ["emberline"], "buyer_key": "corvane", "categories": ["energy"], "until": "2059-03-14", "reason": "HMX-MSA-2057-02 Energie käuferexklusiv (K8)"},
  {"seller_keys": ["kuppelwerk"], "buyer_key": "lichtacker", "categories": ["industrial_goods"], "until": "2059-03-14", "reason": "Vorkaufsrecht Helix, Absage V14 (K8)"},
  {"seller_keys": ["graufalk"], "buyer_key": "helix", "archetypes": ["escort_drones", "sensor_arrays"], "system": "kharon", "from": "2058-08-01", "reason": "RCS-MSA-2058-01 regional exklusiv"},
  {"seller_keys": ["emberline", "kometenpost"], "buyer_key": "cindervale", "archetypes": ["drive_parts"], "from": "2058-03-15", "reason": "GFW-RV-2057-02 gegenseitig"},
  {"seller_keys": ["emberline", "lanternfish", "second_hull", "kuppelwerk"], "buyer_key": "graufalk", "archetypes": ["nav_computers"], "from": "2058-03-15", "reason": "GFW-RV-2057-02 gegenseitig"},
  {"seller_keys": ["second_hull", "outmark", "morgengrund", "kuppelwerk"], "buyer_key": "pionierwerk", "archetypes": ["water_ice"], "system": "isolde", "from": "2058-01-01", "reason": "RVF-RV-2058-01 regional exklusiv"},
  {"seller_keys": ["second_hull", "outmark", "morgengrund", "kuppelwerk"], "buyer_key": "pionierwerk", "archetypes": ["nitrogen_ice"], "system": "isolde", "from": "2058-09-01", "reason": "RVF-RV-2058-01 Nachtrag (K7)"},
  {"seller_key": "kuppelwerk", "archetypes": ["habitat_modules"], "system": "isolde", "from": "2058-06-01", "allowed_buyer": "pionierwerk", "reason": "KHB-RV-2058-01 verkäuferexklusiv"}
 ],
 "hire_date_caps_new_firms": {"rule": "Durchlauf 2: executive, erste relations und erste intelligence jeder neuen Firma bekommen hire_date <= min(frühestes verankertes Schreiben, Rahmenbeginn - 30 T) - 30 T; signed_date eines Rahmens = start_date - 30 T; gilt nur im Erweiterungsstrom", "caps": {"graufalk": "2056-11-02", "cindervale": "2056-11-02", "kuppelwerk": "2058-04-02", "emberline": "2059-01-31", "kometenpost": "2059-04-12", "lanternfish": null, "pionierwerk": "2057-11-02", "ravenmoor": "2058-05-16", "raureif": "2057-11-02", "outmark": "2057-12-03", "morgengrund": "2058-11-02", "second_hull": "2058-03-02"}},
 "qa_anchor_objects": {"contracts": ["CVB-CTR-2058-0003", "CVB-CTR-2058-0013", "CVB-CTR-2058-0038", "CVB-CTR-2059-0044", "CVB-CTR-2059-0066", "EKM-VTR-2057-0002", "EKM-VTR-2057-0012", "EKM-VTR-2057-0017", "EKM-VTR-2057-0043", "EKM-VTR-2057-0064", "EKM-VTR-2058-0099", "EKM-VTR-2058-0105", "EKM-VTR-2058-0107", "EKM-VTR-2058-0132", "EKM-VTR-2059-0151", "EKM-VTR-2059-0156", "EKM-VTR-2059-0160", "EKM-VTR-2059-0162", "EKM-VTR-2059-0167", "EKM-VTR-2059-0197", "EKM-VTR-2059-0211", "EKM-VTR-2060-0219", "EKM-VTR-2060-0230", "EKM-VTR-2060-0234", "FSP-VTR-2059-0001", "FSP-VTR-2059-0019", "HMX-CTR-2057-0010", "HMX-CTR-2057-0012", "HMX-CTR-2057-0014", "HMX-CTR-2057-0019", "HMX-CTR-2057-0043", "HMX-CTR-2057-0050", "HMX-CTR-2057-0077", "HMX-CTR-2057-0098", "HMX-CTR-2058-0121", "HMX-CTR-2058-0131", "HMX-CTR-2058-0139", "HMX-CTR-2058-0152", "HMX-CTR-2058-0159", "HMX-CTR-2058-0161", "HMX-CTR-2058-0173", "HMX-CTR-2058-0183", "HMX-CTR-2059-0192", "HMX-CTR-2059-0197", "HMX-CTR-2059-0213", "HMX-CTR-2059-0235", "HMX-CTR-2059-0236", "HMX-CTR-2059-0242", "HMX-CTR-2059-0246", "HMX-CTR-2059-0257", "HMX-CTR-2059-0259", "HMX-CTR-2060-0275", "HMX-CTR-2060-0281", "LAK-VTR-2058-0008", "LAK-VTR-2058-0033", "LAK-VTR-2058-0039", "PKB-VTR-2058-0001"], "orders": ["DWS-ORD-2059-00107", "EKM-BST-2057-00352", "EKM-BST-2059-01408", "EKM-BST-2059-01903", "EKM-BST-2059-02343", "FSP-BST-2059-00111", "HMX-ORD-2059-01645", "HMX-ORD-2059-01763", "HMX-ORD-2059-01788"], "shipments": ["HMX-SHP-2059-01012", "HMX-SHP-2059-01094"], "events": [3, 8, 10, 16, 18, 19, 24, 26, 27, 29, 30, 34, 36, 37, 45, 51, 52, 53, 54, 57, 58, 59, 61, 65, 66, 67, 69, 70, 71, 72, 74], "employees": [1, 2, 4, 9, 16, 23, 26, 27, 29, 33, 38, 39, 40, 41, 42, 43, 45, 47, 49, 83, 115, 118, 119, 120, 123, 168, 169, 170, 171, 172, 174, 175, 178, 179, 235, 254, 293, 294, 299, 301, 302, 304, 307, 308, 319, 332, 370, 395, 445], "compare": {"contracts": ["company_id", "partner_company_id", "contract_type", "start_date", "deadline", "status", "total_value", "penalty_per_day"], "orders": ["order_date", "status", "payment_status", "total_amount"], "shipments": ["arrival_date", "actual_arrival_date", "risk_incident"], "events": ["event_date", "event_type", "station_id", "severity"], "employees": ["full_name", "company_id", "role_code", "hire_date", "termination_date", "loyalty", "bribe_susceptibility", "intel_access_level"]}, "expected_assigned_contracts_total": 341},
 "correspondence_changes_r2": [
  {"id": "V14", "change": "rumor-Absender Kaspar Täsche (43, intelligence, 55/61) statt Erkan Hesse (39, 68/43, erfüllt Leck-Regel nicht); Datum 2059-01-27 statt 2059-01-20 (nach dem Strafbescheid V13 vom 2059-01-25)", "refers_to": "V13"},
  {"id": "V39", "source": "Team B (phase2_vorschlag_team_b.md 7.5), übernommen", "steps": [{"date": "2059-08-28", "type": "rumor", "sender": "Richard Chavez 120 (leaked_by, Corvane)", "recipient": "Cindervale Marktaufklärung", "is_accurate": 1, "confidentiality": "confidential", "refs": {"contract": "CVB-CTR-2059-0066"}}, {"date": "2059-09-02", "type": "breach_warning", "sender": "Cindervale-Vorstand", "recipient": "Roswitha van der Dussen 168 (cc Esther Bauer 170)", "refs": {"framework": "CCI-MSA-2057-01"}}, {"date": "2059-09-12", "type": "breach_warning (Antwort)", "sender": "Esther Bauer 170", "recipient": "Cindervale", "refs": {"events": [19, 36]}}]},
  {"id": "V40", "date": "2059-06-04", "types": ["internal_memo"], "sender": "Reimar Rörricht 38 -> Lena Heß 40", "content": "Verdacht gegen Erkan Hesse (39) wegen der Weitergabe des Strafbescheids; Hesse wird am 2059-06-11 entlassen (Bestand). Der wahre Leck ist Täsche (V14, leaked_by 43) – Spionage-Rätsel", "confidentiality": "confidential", "refs": {"correspondence": "V14"}},
  {"id": "V41", "date": "2058-11-20", "types": ["confidential_tip"], "sender": "Freddy Dörr 235 (leaked_by) -> Graufalk Marktaufklärung", "content": "Ausfallprotokoll Förster nach Ereignis 36", "confidentiality": "business", "is_accurate": 1, "refs": {"event": 36, "rivalry": "graufalk-eisenkrone"}},
  {"id": "K3-K6", "source": "Team B, von Team A gegen den Bestand nachgeprüft und übernommen", "changes": {"V1": "2057-08-28 / 2057-09-13 / 2057-10-07", "V27": "2059-10-14, 13 Bestellungen, 25.522.655,14 CR", "V32": "2059-03-29", "V36": "2059-12-31, Absender Kayla Cannon 332"}}
 ]
}
```
