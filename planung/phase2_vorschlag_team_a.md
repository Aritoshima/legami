# Phase 2 – Team A: Verknüpfung der 18 Firmen

Stand: 20.10.2026 · Grundlage: `phase1_team_a.md`, `phase1_team_b.md`, `NACHRICHTEN.md`, `generate_space_trading_data.py`
(Seed 42) und der Bestand `/home/user/bestand/space_trading_game_bestand.db`. Alle Zahlen zu Verträgen, Lieferungen,
Ereignissen und Mitarbeitern stammen aus eigenen Abfragen auf diesen Bestand (nur lesend).

## 0. Kurzfassung

| Kennzahl | Wert |
|---|---|
| Aktive gerichtete Vereinbarungen | **48** (14 Bestand inkl. `helix → corvane` aus `OPTIONAL_PARTNERSHIPS`, 7 neue Firmen → Bestand, 12 in Team A, 12 in Team B, 3 teamübergreifend) |
| Direkt verbundene Firmenpaare | 38 von 153 (25 %), Netz zusammenhängend, Durchmesser 4 |
| Paare nur über Zwischenhändler | 66 (z. B. Kometenpost ↔ Graufalk über Cindervale/Lanternfish, Feldspat ↔ Raureif über Eisenkrone, Morgengrund ↔ Second Hull über Pionierwerk/Ravenmoor) |
| Zentraler Hub | **Helix** (large): 7 direkte Partner, 10 Vereinbarungen. Regionale Hubs: Graufalk (Kernraum-Werft, 7/9) und Ravenmoor (Grenzraum, 7/8) |
| Historische Partnerschaften | 7 (1 Bestand + 6 neu, alle mit festen Daten; die Daten der Team-B-Firmen stammen von Team B) |
| Rivalitäten | 12 (4 Bestand + 3 Team A + 5 Team B), neuer Typ nur `armed_conflict`, sonst Text-Overrides (Vorschlag Team B übernommen) |
| Rahmenverträge | **20** (8 für Bestandspaare, an die 374 von 475 bestehenden Rahmen-, Dauer- und Exklusivverträgen gehängt werden, 12 für neue Paare), 67 Nachträge |
| Schriftverkehr | neue Tabelle `correspondence` (16 Briefarten), ca. 1.500 Schreiben aus dem Bestand ableitbar, ca. 3.300 insgesamt |

Leitlinien für alle Punkte:

1. **Bestandsschutz**: Vereinbarungen mit Bestandsfirmen nur in Richtung „neue Firma → Bestandsfirma“ (wie in Phase 1
   mit Team B vereinbart). Neue Tabellen und die neue Spalte `contracts.framework_agreement_id` werden **ohne** Zugriff
   auf `world.rng` und ohne neue Zufallszüge für Bestandsfirmen befüllt. Für die Bestandspaare entstehen sie
   deterministisch aus den vorhandenen Verträgen, sonst aus einem eigenen Strom (`random.Random(f"{seed}:links")`).
2. **Keine optionalen Kanten für neue Firmen**. Die Zählung je Firma steht damit vorab fest. `helix → corvane` bleibt in
   `OPTIONAL_PARTNERSHIPS`. Ein Verschieben in den festen Blueprint würde einen `rng.random()`-Aufruf einsparen und den
   Zufallsstrom der Bestandsfirmen verschieben.
3. **Reserve**: Eisenkrone (9/10) und Driftwood (1/3) behalten freie Plätze. Spielidee: Der Spieler kann später selbst
   Vereinbarungen vermitteln, z. B. Driftwood als Abnehmer von Bergegut.

---

## 1. Antworten auf die Fragen von Team B und Abgleich mit `phase2_vorschlag_team_b.md`

Team B hat seinen Phase-2-Vorschlag parallel veröffentlicht. Wir haben ihn gelesen und übernehmen die Punkte, bei
denen Team B für die eigenen Firmen entscheidet.

| Frage (Phase 1 und 2) | Antwort Team A |
|---|---|
| `kuppelwerk → pionierwerk` und `second_hull → graufalk` | **Angenommen**, beide im Vorschlag. |
| Ist `fusion_pellets` aus Deuterium/Helium-3? `raureif → emberline`? | Ja, Fusionspellets werden aus Deuterium und Helium-3 gepresst. Team B streicht `raureif → emberline` in Phase 2 selbst (Vaskar–Pellora ≈ 822 Einheiten, Emberline fördert Helium-3 selbst). Wir **stimmen zu** und behalten `graufalk → emberline` (Schöpfschiff-Teile). |
| `graufalk → ravenmoor` | **Angenommen** (beide Teams schlagen die Kante vor). Graufalk hat damit 9, Ravenmoor 8. |
| `lanternfish → kometenpost` fest statt optional | **Ja**, fest. |
| `RIVALRY_TEXT_OVERRIDES` statt eines neuen Typs | **Ja**. Wir ziehen unseren Typ `price_war` zurück. Emberline ↔ Eisenkrone wird `resource_competition` mit eigenem Text (Abschnitt 4). |
| Schema Rahmenverträge/Schriftverkehr | Beide Entwürfe passen zusammen (Nummern `{SKU}-RV/MSA-{Jahr}-{nn}`, `contracts.framework_agreement_id`, Zuordnung ohne Zufall, Nachträge aus Vertragssummen). Unterschiede und Empfehlung: Abschnitt 1.1. |
| Myrrhen wird voll | In Ordnung. Wir streichen `myrrhen` aus dem Territorium von Graufalk (0,5) und Emberline (0,5). Dann bauen dort nur Kuppelwerk (Pflicht-Bergbau), Raureif und Pionierwerk neu. |
| Orrin: medium-Sicherheit, keine neue Freischaltlogik? | Ja, Orrin bleibt unverändert (Stufe 2, medium). |
| Aufteilung der Infrastruktur | **Einverstanden mit dem Vorschlag von Team B**: Team A übernimmt den zweiten Durchlauf (RNG/Faker, Archetyp-Filter, QA 6/6/6 mit Bestandsvergleich). Team B übernimmt `framework_agreements`, `framework_amendments`, Scope, `correspondence` und die QA dazu. Unsere Abschnitte 5 und 6 sind als Zulieferung für Team B gedacht. |

### 1.1 Unterschiede zu Team B und Empfehlung für die Zusammenführung

| Thema | Team A | Team B | Empfehlung |
|---|---|---|---|
| `emberline → lichtacker` | echte Vereinbarung (letzter freier Platz bei Lichtacker) und Rahmenvertrag EFF-MSA-2059-02 | nur Kaltangebot K12; der Spieler kann vermitteln | **Team A**: Die Kette Bruch → Teilkündigung → neuer Lieferant wird in Routen und Verträgen sichtbar. Die Spielidee „vermitteln“ bleibt für Driftwood und Eisenkrone (freie Plätze). Falls die Koordination Team B folgt, entfallen Kante und Rahmenvertrag, und Lichtacker hat 5. |
| Eisenkrone → Lichtacker, Energie | Teilkündigung, wirksam 2060-01-18. Laufende Abrufe (`EKM-VTR-2059-0197`) laufen aus, der Entwurf `EKM-VTR-2060-0230` fällt aus dem Rahmen | Kündigungsandrohung, danach −5 % | Beide sind widerspruchsfrei. Die Teilkündigung erzeugt einen sichtbaren „Vertrag außerhalb des Rahmens“. Die Androhung ist sanfter. Entscheidung je nach gewünschter Spannung. |
| Rahmenverträge Bestandspaare | 8 (zusätzlich `eisenkrone → feldspat` und `feldspat → eisenkrone`) | 6 (Feldspat bewusst ohne Rahmen, Schulden als Geschichte) | Team B als Basis. Zusätzlich `feldspat → eisenkrone` (FSP-RV-2059-01, klein, nach Fund 52): Er erzählt die Verschuldung (25,5 Mio. CR überfällig) als Verrechnung über Exklusivität und berührt keine Bestandszeile. |
| Rahmenverträge neue Paare | 12 | 10 (darunter `outmark → pionierwerk`, `morgengrund → pionierwerk`) | Vereinigungsmenge ohne Dopplungen: Team B plus `graufalk → cindervale` (Antwort auf eure Frage 4: ja), `graufalk → ravenmoor`, `emberline → lichtacker`, optional `morgengrund → ravenmoor`. Volumen und Daten für gemeinsame Paare (GFW, CCI, KHB, EFF, RCS, RVF) übernehmen wir von Team B, weil Team B das umsetzt. |
| Briefarten | 16 | 17 (`offer`, `counter_offer`, `breach_warning`, `protest`, `confidential_tip`) | Vereinigung: `quotation` = `offer`, `negotiation` = `counter_offer`; `breach_warning`, `protest` und `confidential_tip` übernehmen; `delay_notice` und `suspension_notice` (Team A) ergänzen. |
| Anker mit falschem Datum bei Team B | – | K10 (2058-08-28) und K13 (2058) mit Roswitha van der Dussen; K24 (2057-08-28) an Theodor Krause | Van der Dussen ist erst seit **2059-07-07** im Unternehmen, Krause seit **2057-11-22**. Vorher zeichnet Esther Bauer (170) für Eisenkrone; K24 geht an Mikhail Gotthard (2, seit 2055-03-21). |

---

## 2. Gerichtete Handelsvereinbarungen (Verkäufer → Käufer)

Prüfregel für jede neue Kante: Die Hauptwaren des Verkäufers (`category_weights`) müssen in `CATEGORY_CONSUMERS`
(bzw. `extra_consumers` des Archetyps) einen Stationstyp haben, den der Käufer **sicher** besitzt (Pflichtstationen
aus `required_stations` bzw. Bestandsstationen). Damit erreicht `plan_markets` die geforderten ≥ 4 Partnerrouten.

### 2.1 Bestand (14, unverändert)

`eisenkrone → helix` supply · `helix → eisenkrone` strategic_alliance · `helix → lichtacker` distribution ·
`lichtacker → helix` supply · `corvane → helix` licensing · `feldspat → helix` consignment · `driftwood → helix`
consignment · `feldspat → eisenkrone` supply · `eisenkrone → feldspat` supply · `eisenkrone → lichtacker` supply ·
`corvane → eisenkrone` supply · `eisenkrone → corvane` joint_venture · `lichtacker → corvane` supply · optional (im
Bestand aktiv) `helix → corvane` logistics_partnership.

### 2.2 Neue Firmen → Bestandsfirmen (7)

| Verkäufer → Käufer | Typ | Waren | Käuferstationen (Verbraucher) | Begründung (Plausibilität / Spielspaß) |
|---|---|---|---|---|
| graufalk → helix | supply_agreement | Rumpfplatten, Triebwerksteile, Navigationstechnik | trade_hub, free_port, military | 86 Verspätungen durch Triebwerksschäden, `HMX-CTR-2058-0173` (Triebwerksteile, gebrochen). Spieler sieht Ersatzteilflüsse nach Kharon. |
| cindervale → eisenkrone | supply_agreement | KI-Kerne, Sensorarrays, Robotik, Bergbaudrohnen | mining (Hande, Löchel, Schacht VII) | Technik an Bergbaustationen; die Firmware-Lizenz für Förster steht im Rahmenvertrag. Verdacht nach den KI-Ausfällen 19/36/70 → Spionage. |
| kuppelwerk → lichtacker | supply_agreement | Verbundstahl, Glaskeramik, Sinterbausteine, Habitatmodule | agricultural, research | Ersatz für gebrochene Verbundstahl-Verträge `HMX-CTR-2058-0159`, `-2057-0043`, `-2058-0139`. Kurze, sichere Einsteigerrouten. |
| emberline → corvane | supply_agreement | Helium-3, Deuterium, Fusionspellets | research, industrial | Ersatz für `HMX-CTR-2058-0131` und `-2057-0014` (Helium-3 an Halcyon Works VI, gebrochen). |
| emberline → lichtacker | supply_agreement | Plasmagas, Brennstoffzellen, Fusionspellets | agricultural, research | **Neu (letzter freier Platz bei Lichtacker)**: Energie für Agrarstation Seip nach `EKM-VTR-2058-0099`, `-2059-0167`, `-2058-0105` (alle gebrochen). Tauvel hat 0 Energieangebote. |
| raureif → eisenkrone | supply_agreement | Wassereis, Ammoniak-Eis, Helium-3 | industrial, mining | Team B. Feldspat liefert nur 6,0 Mio. CR an Eisenkrone → Preiskampf im Grenzraum. |
| ravenmoor → helix | logistics_partnership | Geleitschutzdrohnen, Sensorik, Rationen, Medizin | trade_hub, free_port (Kharon) | Team B. Grundlage sind 8 Verträge, die wegen Geleitschutz gebrochen sind, und die Piratenangriffe 51 und 74 in Kharon. |

### 2.3 Innerhalb Team A (12)

| Verkäufer → Käufer | Typ | Waren → Käuferstationen | Begründung |
|---|---|---|---|
| cindervale → graufalk | supply_agreement | Navigationscomputer, KI-Kerne → trade_hub | Steuerkerne für Schiffe; Hochtechnologie wird nicht mehr aus Kharon geholt. |
| graufalk → cindervale | strategic_alliance | Rumpfmodule, Triebwerksteile → research; Energie → industrial | Gemeinsame Schiffsplattform. Gegenspieler sind Eisenkrone und Helix, daraus entsteht ein Machtblock. |
| emberline → graufalk | supply_agreement | Fusionspellets, Deuterium → industrial | Brennstoff für Probefahrten. |
| graufalk → emberline | supply_agreement | Triebwerksteile, Rumpfplatten → mining (Pellora) | Schöpfschiff-Teile für die Gasriesen-Förderung; Graufalk und Emberline beliefern sich gegenseitig. |
| kuppelwerk → graufalk | supply_agreement | Habitatmodule, Sinterbausteine (extra `industrial`), Glaskeramik → trade_hub | Docks und Wohnmodule für Werftarbeiter in Orrin. |
| emberline → kuppelwerk | supply_agreement | Energie → industrial, mining | Sinteröfen brauchen Energie. Das ist die Kostenbasis der Kuppelwerk-Preisformel (`cost_plus`). |
| emberline → cindervale | supply_agreement | Energie → research, industrial | Rechenzentren in Sol und Halcyon brauchen viel Energie. |
| cindervale → kometenpost | consignment | Quantenrelais, KI-Kerne → trade_hub | Kommissionsware im Expresshandel; der Spieler kann sie in kleinen Mengen kaufen. |
| kometenpost → cindervale | logistics_partnership | Medizin, Elektronik → research | Expressversorgung der Labore. |
| cindervale → lanternfish | supply_agreement | Elektronik → trade_hub | Elektronik für Immersionskapseln. |
| lanternfish → graufalk | supply_agreement | Komfortgüter → trade_hub | Werftarbeiter in Orrin; Luxus-Saisonalität. |
| lanternfish → kometenpost | consignment | Unterhaltungselektronik, Kaffee → trade_hub | **Fest statt optional**. Kometenpost verkauft Komfortgüter weiter. |

### 2.4 Innerhalb Team B (12, unverändert aus `phase1_team_b.md`)

`raureif → pionierwerk` supply · `pionierwerk → morgengrund` supply · `morgengrund → pionierwerk` supply ·
`ravenmoor → pionierwerk` logistics · `pionierwerk → ravenmoor` supply · `outmark → pionierwerk` licensing ·
`second_hull → pionierwerk` supply · `second_hull → ravenmoor` consignment · `raureif → ravenmoor` supply ·
`ravenmoor → outmark` logistics · `morgengrund → ravenmoor` supply · `outmark → raureif` supply.
Stationsprüfung: siehe Team B, 5.1. Wir haben alle Kanten gegen die Pflichtstationen nachgerechnet, es gibt keinen
Konflikt.

### 2.5 Teamübergreifend (3)

| Verkäufer → Käufer | Typ | Waren → Käuferstationen | Begründung |
|---|---|---|---|
| kuppelwerk → pionierwerk | supply_agreement | Habitatmodule → trade_hub, agricultural (Isolde/Serravel) | Kolonien brauchen Wohnraum. Kuppelwerk liefert die Module, Pionierwerk rüstet die Kolonien aus. Damit kommt der Spieler vom Kernraum an den Rand. |
| second_hull → graufalk | supply_agreement | Recyclingmetall → industrial; aufbereitete Rumpfplatten → trade_hub | Billiges Material aus Nyx mit hohem Routenrisiko. Spionage: Stammt das Metall aus Driftwood-Ware? |
| graufalk → ravenmoor | supply_agreement | Rumpfplatten Militärnorm, Triebwerksteile → military, trade_hub | Von beiden Teams vorgeschlagen: Die Geleitflotte wird in Orrin gebaut. Nach der Razzia 26 und den Piratenangriffen 45/57/67 braucht Ravenmoor Schiffe. |

Nicht aufgenommen: `raureif → emberline` (von Team B zurückgezogen, siehe Abschnitt 1).

### 2.6 Zählung (aktive Vereinbarungen, beide Richtungen; geprüft mit Skript)

| Firma | Größe | Vereinb. | ausgehend | direkte Partner | Bereich |
|---|---|---|---|---|---|
| Feldspat | small | 3 | 2 | 2 | 1–3 ✓ |
| Driftwood | small | 1 | 1 | 1 | 1–3 ✓ (Reserve 2) |
| Lichtacker | medium | 6 | 2 | 5 | 3–6 ✓ (voll) |
| Corvane | medium | 6 | 2 | 4 | 3–6 ✓ (voll) |
| Eisenkrone | large | 9 | 4 | 6 | 6–10 ✓ (Reserve 1) |
| Helix | large | 10 | 3 | 7 | 6–10 ✓ (voll) |
| Graufalk | large | 9 | 4 | 7 | 6–10 ✓ |
| Cindervale | large | 7 | 4 | 5 | 6–10 ✓ |
| Kuppelwerk | medium | 4 | 3 | 4 | 3–6 ✓ |
| Emberline | medium | 6 | 5 | 5 | 3–6 ✓ (voll) |
| Kometenpost | small | 3 | 1 | 2 | 1–3 ✓ |
| Lanternfish | small | 3 | 2 | 3 | 1–3 ✓ |
| Pionierwerk | large | 8 | 2 | 6 | 6–10 ✓ |
| Ravenmoor | large | 8 | 3 | 7 | 6–10 ✓ |
| Raureif | medium | 4 | 3 | 4 | 3–6 ✓ |
| Outmark | medium | 3 | 2 | 3 | 3–6 ✓ |
| Morgengrund | small | 3 | 2 | 2 | 1–3 ✓ |
| Second Hull | small | 3 | 3 | 3 | 1–3 ✓ |

- **Hub**: Die QA sortiert nach direkten Partnern und dann nach Vereinbarungen. Helix steht mit 7/10 vor Graufalk
  (7/9) und Ravenmoor (7/8), alle drei sind groß. Die Prüfung „Zentraler Hub ist groß“ hält also auch dann, wenn sich die
  Reihenfolge später ändert. Spielspaß: Helix ist der Marktplatz für alle, Graufalk die Werft des Kernraums, Ravenmoor
  der Quartiermeister des Grenzraums.
- **Jede Firma verkauft**: Alle 18 haben mindestens eine ausgehende Vereinbarung, also auch Verträge.
- **Unvollständig**: 38 von 153 Paaren sind direkt verbunden, 66 weitere nur über einen gemeinsamen Partner. Bei vier Paaren liegen 4 Schritte dazwischen (z. B.
  Kometenpost ↔ Morgengrund, Driftwood ↔ Kometenpost). Daraus entstehen Aufträge für den Spieler als Zwischenhändler.
- **Grenzwerte**: Helix, Lichtacker, Corvane und Emberline sind voll. Jede weitere Kante dorthin verletzt die QA.

---

## 3. Historische (beendete) Partnerschaften

Sie bekommen **feste Daten** (keine Würfel), damit Rivalitäten und Schreiben sie zitieren können. `trust_level` wird mit
dem eigenen Strom in 3–15 gewürfelt, `contract_volume` in 0,8–4 Mio. CR wie im Bestand.

| Verkäufer → Käufer | Typ | Zeitraum | Story-Hook | Spielwert |
|---|---|---|---|---|
| corvane → driftwood | supply | Bestand (2057-04-27 – 2058-07-17) | unverändert | – |
| eisenkrone → graufalk | supply | 2039-01 – 2049-06 | Ausgliederung der Werftsparte Orrin, Bruch im Patentstreit um Reaktorkomponenten | Grund der Rivalität Graufalk ↔ Eisenkrone. Ein altes Kündigungsschreiben liegt im Archiv. |
| cindervale → helix | licensing | 2041-04 – 2054-03 | Helix verlor die Cindervale-Lizenz und bezieht Hochtechnologie seitdem aus Kharon | Erklärt die bruchanfälligen Supraleiter-Verträge (`HMX-CTR-2057-0050`, `-2058-0121`, `-2057-0019`) und die Rivalität in Sol. |
| lichtacker → pionierwerk | supply | 2045-03 – 2053-06-30 (Team B) | Lichtacker versorgte die Bautrupps auf Isolde, bis der Pachtstreit eskalierte | Grund der Rivalität `territorial_claims` (Isolde). |
| emberline → eisenkrone | supply | 2047-02 – 2056-06 | Helium-3 für Bergbaustation Hande; endete, als Eisenkrone selbst Deuterium förderte | Grund des Preiskampfs in Myrrhen (Rivalität 7). |
| outmark → feldspat | licensing | 2055-02 – 2058-06-30 (Team B) | Vermessungslizenz Brennus; ein Jahr nach dem Ende findet Feldspat den Quantenquarz (Ereignis 52) | Claim-Streit: Wurden die Daten nach Lizenzende weiter genutzt (Slavko Geisel)? |
| driftwood → second_hull | consignment | 2057-05 – 2058-07-01 (Team B) | Second Hull kaufte Bergegut von Driftwood, bis die Firma ihre Lizenz bekam (zwei Tage nach Razzia 26) | „Verräter am Handwerk“, Grundlage der Rivalität in Nyx. |

Datenprüfung: Jeder Beginn liegt nach der Gründung beider Firmen (Bestand: Feldspat 2054, Driftwood 2056, Lichtacker
2044, Eisenkrone 2033, Helix 2036; neue Firmen gemäß `founded_range`). Jedes Ende liegt vor dem Datenfenster des
Käufers. Es gibt keine Kollision mit `UNIQUE(company_id, partner_company_id, relationship_type)`.

---

## 4. Rivalitäten

| # | Firma | Rivale | Typ | System | `since_date` | Anker im Bestand | Spionage-Potenzial |
|---|---|---|---|---|---|---|---|
| 1–4 | Bestand | | | | gewürfelt (unverändert) | | |
| 5 | graufalk | eisenkrone | market_dominance | halcyon | 2049-07-01 | KI-Ausfälle Förster (19, 36, 70), `EKM-VTR-2057-0064` (Reaktorkomponenten, gebrochen) | Esther Bauer (EKM 170, Bestechlichkeit 76) verkauft Ausfallprotokolle; Annekatrin Schuchhardt (178, Loyalität 85) ist schwer zu knacken. |
| 6 | cindervale | helix | market_dominance | sol | 2054-04-01 | Supraleiter-Verträge gebrochen, Nachfrageschübe 3/24 bei Sol Exchange II | Desiree Schwartz (HMX 299, gierig, seit 2059-11-24 bei Helix) leakt Strafsummen; Richard Chavez (CVB 120) plaudert über Engpässe. |
| 7 | emberline | eisenkrone | resource_competition (Text-Override) | myrrhen | 2058-08-15 | `EKM-VTR-2058-0099` (Plasmagas, Piraten), `-2059-0167`, `-2058-0105`, Asteroidensturm Hande (10) | Hans-Werner Eberhardt (LAK 45) ist umworbener Kunde; Polina Zahn (LAK 83, Disposition Seip, Bestechlichkeit 88) verrät Bestellmengen. |
| 8 | lichtacker | pionierwerk | territorial_claims (Text-Override Team B) | isolde | 2053-07-01 | Isolde im Lichtacker-Territorium (2,0), aber ohne Station (Team B) | Kaspar Täsche (LAK 43, gierig) beobachtet Isolde. |
| 9 | ravenmoor | driftwood | armed_conflict | nyx | 2058-06-30 | Razzien 26 und 58, Piratenangriffe 45/54/57/67 (Team B) | Carlos Osborne (DWS 29, Loyalität 3, Bestechlichkeit 100) als Informant. |
| 10 | outmark | feldspat | territorial_claims | brennus | 2059-07-14 | Rohstofffund 52 an der Bergbaustation Becker (Team B) | Slavko Geisel (FSP 16, Bestechlichkeit 96). |
| 11 | ravenmoor | helix | market_dominance | kharon | 2057-11-17 | Piratenangriff 16 und Razzia 26 auf Kharon Landing IV (Team B) | Brandon Jones (HMX 445, Finanzen Kharon Exchange V, Loyalität 38, Bestechlichkeit 89), Wayne Jacobson (302, gierig). |
| 12 | second_hull | driftwood | territorial_claims | nyx | 2058-07-01 | Ende der historischen Kommission (Team B); Piratenangriff 54 an Smugglers' Haven Hall | Douglas Lawson (DWS 27, ehrgeizig). Wäscht Second Hull Driftwood-Ware? |

Text-Override für Emberline ↔ Eisenkrone (in `RIVALRY_TEXT_OVERRIDES` nach Vorschlag Team B, kein neuer Typ):

```python
RIVALRY_TEXT_OVERRIDES[("emberline", "eisenkrone")] = {
    "de_DE": "{company} und {rival} liefern beide Energie ins {system}-System und unterbieten sich bei jedem Liefervertrag.",
    "en_US": "{company} and {rival} both supply energy to the {system} system and undercut each other on every supply contract.",
}
```

Begründung: Eisenkrone ist mit 4 Rivalitäten (Helix, Lichtacker, Graufalk, Emberline) der Gegenspieler des
Kernraums, Driftwood mit 4 (Corvane, Feldspat, Ravenmoor, Second Hull) der Gegenspieler des Grenzraums. Für den Spieler
ergibt das zwei klare Lager mit Informanten auf beiden Seiten. Die Ereignisse der Bestandsfirmen bekommen damit eine
Erklärung („wer profitiert vom Ausfall?“). `since_date` steht fest. Für die Team-B-Rivalitäten gelten auch die festen
`intensity`- und `espionage_risk`-Werte aus `phase2_vorschlag_team_b.md`. Für die drei Team-A-Rivalitäten würfelt der
eigene Strom wie bisher.

---

## 5. Rahmenverträge (framework_agreements)

### 5.1 Modell

Ein Rahmenvertrag hängt an genau **einer** gerichteten aktiven Vereinbarung (Verkäufer → Käufer). Er legt Laufzeit,
Volumenobergrenze, Preisformel, Indexierung, Exklusivität, Kündigungsfrist und Warenumfang fest. Einzelverträge
(`contracts`) mit den Typen `framework`, `recurring_supply` und `exclusive_supply` sind Abrufverträge unter diesem
Rahmen. `spot`, `emergency_supply` und `consignment` bleiben Einzelverträge außerhalb.

```sql
CREATE TABLE framework_agreements (
    framework_agreement_id INTEGER PRIMARY KEY,
    agreement_number TEXT NOT NULL UNIQUE,            -- {SKU}-{RV|MSA}-{Jahr}-{nn}, RV = de_DE, MSA = en_US
    partnership_id INTEGER NOT NULL REFERENCES trade_partnerships(partnership_id),
    company_id INTEGER NOT NULL REFERENCES companies(company_id),          -- Verkäufer
    partner_company_id INTEGER NOT NULL REFERENCES companies(company_id),  -- Käufer
    title TEXT NOT NULL,
    language TEXT NOT NULL CHECK(language IN ('de_DE','en_US')),           -- Sprache des Verkäufers
    start_date TEXT NOT NULL,
    initial_end_date TEXT NOT NULL,
    current_end_date TEXT NOT NULL,                   -- nach Verlängerungen
    base_volume REAL NOT NULL CHECK(base_volume > 0), -- CR
    current_volume_cap REAL NOT NULL,                 -- nach Volumenerhöhungen
    price_formula TEXT NOT NULL CHECK(price_formula IN ('fixed','index_linked','cost_plus','market_minus')),
    indexation TEXT NOT NULL CHECK(indexation IN ('none','category_price_index','fuel_index','risk_index')),
    price_band_pct REAL NOT NULL DEFAULT 8,           -- max. Anpassung je Indexstichtag
    exclusivity TEXT NOT NULL CHECK(exclusivity IN ('none','buyer_exclusive','seller_exclusive','mutual',
        'right_of_first_refusal','regional_exclusive')),
    exclusivity_system_id INTEGER REFERENCES star_systems(system_id),
    notice_period_days INTEGER NOT NULL CHECK(notice_period_days > 0),
    escort_company_id INTEGER REFERENCES companies(company_id),            -- Vorschlag Team B
    penalty_rate_pct REAL NOT NULL,                   -- Vorgabe für penalty_per_day neuer Abrufverträge
    status TEXT NOT NULL CHECK(status IN ('draft','active','suspended','expired','terminated')),
    seller_signatory_id INTEGER REFERENCES employees(employee_id),
    buyer_signatory_id INTEGER REFERENCES employees(employee_id),
    description TEXT NOT NULL,
    CHECK(company_id <> partner_company_id), CHECK(current_end_date >= initial_end_date)
);
CREATE TABLE framework_scope (                        -- Warenumfang, wächst mit Nachträgen
    framework_scope_id INTEGER PRIMARY KEY,
    framework_agreement_id INTEGER NOT NULL REFERENCES framework_agreements(framework_agreement_id),
    category_code TEXT NOT NULL,
    archetype_code TEXT,                              -- NULL = ganze Kategorie
    valid_from TEXT NOT NULL, valid_to TEXT,          -- valid_to gesetzt bei Teilkündigung
    is_exclusive INTEGER NOT NULL DEFAULT 0,
    added_by_amendment_id INTEGER REFERENCES framework_amendments(amendment_id)
);
CREATE TABLE framework_amendments (
    amendment_id INTEGER PRIMARY KEY,
    framework_agreement_id INTEGER NOT NULL REFERENCES framework_agreements(framework_agreement_id),
    amendment_number TEXT NOT NULL UNIQUE,            -- {agreement_number}/N{k} (de) bzw. /A{k} (en)
    sequence INTEGER NOT NULL,
    amendment_type TEXT NOT NULL CHECK(amendment_type IN ('volume_increase','product_addition','price_adjustment',
        'term_extension','exclusivity_clause','exclusivity_waiver','penalty_clause','service_level_clause',
        'escort_clause','force_majeure_clause','competition_clause','confidentiality_clause','scope_extension',
        'partial_termination','suspension')),
    status TEXT NOT NULL CHECK(status IN ('agreed','proposed','rejected')),
    proposed_date TEXT NOT NULL, effective_date TEXT NOT NULL,
    initiated_by_company_id INTEGER NOT NULL REFERENCES companies(company_id),
    volume_delta REAL, price_change_pct REAL, new_end_date TEXT,
    anchor_contract_id INTEGER REFERENCES contracts(contract_id),
    anchor_event_id INTEGER REFERENCES events(event_id),
    description TEXT NOT NULL,
    UNIQUE(framework_agreement_id, sequence)
);
-- contracts: neue letzte Spalte
--   framework_agreement_id INTEGER REFERENCES framework_agreements(framework_agreement_id)
```

`INSERT_ORDER`: `trade_partnerships` → `framework_agreements` → `framework_amendments` → `framework_scope` →
`contracts` …. Die Fremdschlüssel zwischen Scope und Nachträgen sind `DEFERRABLE INITIALLY DEFERRED`, wie heute bei
`companies.headquarters_station_id`.

### 5.2 Regeln: Einzelverträge, Nachträge, Bestand

**Zuordnung eines Vertrags (deterministisch, ohne Zufall).** Ein Vertrag bekommt `framework_agreement_id`, wenn alle
Bedingungen gelten:

1. Verkäufer und Käufer stimmen mit dem Rahmenvertrag überein.
2. Der Vertragstyp ist `framework`, `recurring_supply` oder `exclusive_supply`.
3. `start_date` liegt zwischen dem Beginn und dem zu diesem Zeitpunkt gültigen Ende (einschließlich vereinbarter
   Verlängerungen).
4. Die Warenkategorie bzw. der Archetyp ist am `start_date` im Scope (`valid_from ≤ start < valid_to`).

Sonst bleibt das Feld NULL. Das ergibt einen sichtbaren „Vertrag außerhalb des Rahmens“, z. B. den Entwurf
`EKM-VTR-2060-0230` (Helium-3) nach der Teilkündigung Energie.

**Neue Firmen (zweiter Durchlauf)**: Vor dem Rahmenbeginn würfelt `generate_contracts` für das Paar nur `spot`,
`emergency_supply` oder `consignment`, ab Rahmenbeginn die bisherigen Gewichte. `penalty_per_day` richtet sich nach
`penalty_rate_pct` des Rahmens. Ab einem `penalty_clause`-Nachtrag wird der Satz erhöht (×1,5).

**Nachträge entstehen nach Regeln** (die Daten der Nachträge folgen aus den Verträgen, deshalb passen sie zum Bestand):

| Nachtrag | Regel | Wer initiiert |
|---|---|---|
| `product_addition` | erster Abrufvertrag einer Kategorie außerhalb des Scopes → Nachtrag 14 Tage vorher | Verkäufer |
| `volume_increase` | kumuliertes Volumen (ohne storniert) würde 90 % der Obergrenze überschreiten → Nachtrag 14 Tage vor diesem Vertrag, Erhöhung = max(25 % der Basis, Bedarf bis Laufzeitende) | Verkäufer |
| `term_extension` | ein Abrufvertrag endet nach dem Laufzeitende → Verlängerung bis Monatsende nach dessen Frist, beschlossen 60 Tage vor Ablauf; liegt das nach dem Stichtag, Status `proposed` | Käufer |
| `price_adjustment` | Jahrestag bei `index_linked`: Änderung des mittleren `market_price` der Scope-Kategorien an den Käuferstationen, begrenzt auf ±`price_band_pct`, nur wenn mehr als 3 % | automatisch |
| `penalty_clause` | erster gebrochener Abrufvertrag → 30 Tage nach dessen Frist | Käufer |
| story-basiert | `exclusivity_*`, `escort_clause`, `service_level_clause`, `force_majeure_clause`, `competition_clause`, `confidentiality_clause`, `scope_extension`, `partial_termination`, `suspension` stehen fest im Blueprint (JSON) mit Anker-Vertrag bzw. -Ereignis | siehe Tabelle |

Nachträge nach dem Stichtag 2060-01-01 haben den Status `proposed`. Das sind offene Verhandlungen, in die der Spieler
eingreifen kann (Informationen verkaufen, einen Konkurrenten empfehlen).

**Bestandsschutz**: Für die Bestandspaare werden **keine** Verträge, Preise oder Strafen geändert. Hinzu kommen nur die
neue Spalte und die neuen Tabellen. Preisänderungen im Bestand werden nur dokumentiert (Index aus `price_history`) und
nicht in Verträge zurückgeschrieben. Probelauf mit den Regeln oben auf dem Bestand: **374 von 475** Abrufverträgen
werden einem Rahmen zugeordnet. Die übrigen 101 gehören zu Paaren ohne Rahmen (Lieferungen von Feldspat, Driftwood,
Lichtacker und Corvane an Helix bzw. Eisenkrone) oder liegen vor dem Rahmenbeginn (`EKM-VTR-2057-0002`,
`FSP-VTR-2059-0001`, `-0005`) bzw. außerhalb des Scopes (`EKM-VTR-2060-0230`).

### 5.3 Die 20 Rahmenverträge

Die Nummern sind vorläufig. Bei der Generierung werden sie je Verkäufer chronologisch vergeben. Bei
`phase2_vorschlag_team_b.md` ist z. B. `EKM-RV-2057-02` der Rahmen Eisenkrone → Helix. Für Paare, die beide Teams
vorschlagen, gelten bei der Zusammenführung die Werte von Team B (Abschnitt 1.1).

**Bestandspaare (8)**. Volumen in Mio. CR; „Abruf“ = zugeordnete Bestandsverträge (ohne storniert).

| Nr. | Verkäufer → Käufer | Titel | Beginn, Laufzeit | Basis → Obergrenze | Abruf | Preis / Index | Exklusivität | Kernnachträge (Anker) |
|---|---|---|---|---|---|---|---|---|
| HMX-MSA-2057-01 | helix → lichtacker | Distribution Framework Tauvel & Myrrhen | 2057-01-01, 36 → 49 M | 300 → 480 | 423,6 (54 Verträge) | index_linked, Kategorieindex | none | +Energie/Technik, +Medizin; Strafklausel nach `HMX-CTR-2057-0043`; +180 vor `HMX-CTR-2059-0194`; **Wettbewerbsklausel** 2059-03-25 nach `HMX-CTR-2058-0159` und dem Kuppelwerk-Angebot; Verlängerung bis 2061-01-31 |
| HMX-MSA-2057-02 | helix → corvane | Logistics Master Agreement Halcyon & Aurelis | 2057-01-01, 36 → 48 M | 350 → 620 | 549,4 (68) | index_linked, Treibstoffindex | Energie exklusiv ab 2057-04-19 | **Aufhebung der Energie-Exklusivität 2059-03-31** nach `HMX-CTR-2058-0131` (332.508,95 CR Strafe) und `-2057-0014` → macht den Emberline-Rahmen möglich |
| HMX-MSA-2057-03 | helix → eisenkrone | Strategic Alliance Supply Framework Sol–Halcyon | 2057-01-01, 36 → 48 M | 400 → 500 | 438,7 (75) | Kategorieindex | Vorkaufsrecht | Indexanpassung 2058 (Einbruch 2058: 53,5 Mio.), +100 vor `HMX-CTR-2059-0248` |
| EKM-RV-2057-01 | eisenkrone → corvane | Joint-Venture-Liefervertrag Platinmetalle und Reaktortechnik | 2057-01-01, 48 M | 380 → 500 | 440,9 (65) | Kategorieindex | Platinmetalle käuferexklusiv | +Industrie, +Luxus/Technik, +120; Service-Level-Nachtrag `proposed` nach `EKM-VTR-2059-0160` (Robotik, „Navigationsfehler nach Sensorausfall“) |
| EKM-RV-2057-02 | eisenkrone → feldspat | Ausrüstungsrahmen Brennus | 2057-01-01, 36 → 48 M | 200 → 280 | 248,6 (34) | fixed + Jahresindex | none | +80 vor `EKM-VTR-2059-0186`; +Technik nach Rohstofffund 52; Verlängerung |
| EKM-RV-2057-03 | eisenkrone → helix | Rahmenvertrag Brennus–Kharon | 2057-03-01, 36 → 46 M | 220 → 300 | 268,9 (38) | Treibstoffindex | none | Strafklausel nach `EKM-VTR-2057-0017` (303.807,21 CR); **Geleitschutzklausel mit Ravenmoor 2059-09-01** nach `EKM-VTR-2058-0107` (Piraten) und `-2059-0162`; Verlängerung `proposed` |
| EKM-RV-2057-04 | eisenkrone → lichtacker | Lieferrahmen Agrartechnik und Energie Myrrhen/Tauvel | 2057-01-01, 36 → 48 M | 180 → 220 | 178,0 (35) | Kategorieindex | none | Strafklausel nach `EKM-VTR-2058-0099` (219.444,96 CR); **Teilkündigung Energie** (Zugang 2059-10-20, wirksam 2060-01-18, 90 Tage) nach `EKM-VTR-2059-0167`; Restumfang verlängert; +40 `proposed` |
| FSP-RV-2059-01 | feldspat → eisenkrone | Abnahmerahmen Quantenquarz Becker | 2059-08-01, 24 M | 12 → 12 (+8 `proposed`) | 2,6 (5) | market_minus (Davids-Kontor −5 %) | Quantenquarz verkäuferexklusiv | +12 % nach den Nachfrageschüben 65/66; Hintergrund: Feldspat schuldet Eisenkrone **25,5 Mio. CR** aus 13 überfälligen Bestellungen. Die Exklusivität dient als Verrechnung. |

**Neue Paare (12)**. Die Daten der Regel-Nachträge entstehen bei der Generierung.

| Nr. | Verkäufer → Käufer | Titel | Beginn, Laufzeit | Basis | Preis / Index | Exklusivität | Nachträge (Anker) | Plausibilität / Spielspaß |
|---|---|---|---|---|---|---|---|---|
| GFW-RV-2057-01 | graufalk → helix | Flottenrahmenvertrag Rumpf und Antrieb | 2057-01, 36 → 60 M | 180 | Kategorieindex | none | +Technik (Regel); +60 am 2058-12-20 nach `HMX-CTR-2058-0173`; Verlängerung bis 2061 | Helix-Flotte fällt mit Triebwerksschäden aus; der Spieler sieht, wie Ersatzteile Kharon-Verspätungen senken. |
| CCI-MSA-2057-01 | cindervale → eisenkrone | AI Control & Robotics Framework | 2057-02, 48 M | 140 | Kategorieindex, Deckel 3 %/Jahr | KI-Kerne käuferexklusiv | Service-Level 2058-03-01 (Ereignis 19); −8 % Kulanz 2058-12-15 (Ereignis 36); **Aussetzung 2059-12-15** (Ereignis 70) → Status `suspended` | Kern der Firmware-Spionage: Ein Rahmen ist ausgesetzt, Eisenkrone ermittelt, Cindervale schweigt. |
| KHB-RV-2059-01 | kuppelwerk → lichtacker | Baustoffrahmen Tauvel und Myrrhen | 2059-02-15, 24 M | 30 | cost_plus (Energiezuschlag) | none → regional (Myrrhen) `proposed` | +Habitatmodule 2059-08-01 (Quarantäne Lindner, 53); +15 | Vorher (2058) nur Notlieferungen. Der Rahmen folgt auf `HMX-CTR-2058-0159` und den Strafbescheid über 653.162,16 CR. |
| EFF-MSA-2059-01 | emberline → corvane | Helium-3 Supply Framework Halcyon Works VI | 2059-04-15, 24 M | 40 | Treibstoffindex + Sturmzuschlag | none | Höhere Gewalt 2059-09-15 (Quarantäne 59); +15 `proposed` | Direkt nach der Aufhebung der Helix-Exklusivität. Pellora-Stürme bewegen den Preis. |
| EFF-MSA-2059-02 | emberline → lichtacker | Energy Framework Agrarstation Seip | 2059-11-15, 24 M | 18 | Treibstoffindex | Energie käuferexklusiv ab 2060-01-18 | Exklusivklausel, wirksam mit der Eisenkrone-Teilkündigung | Handlungskette: Bruch → Kündigung → neuer Lieferant. Der Price War Emberline ↔ Eisenkrone wird sichtbar. |
| GFW-RV-2057-02 | graufalk → cindervale | Allianzvertrag Navigationsplattform | 2057-01, 60 M | 220 | cost_plus | none → mutual 2058-03-15 | Exklusivität Steuerkerne (nach Ereignis 19); +80 (Regel); Geheimhaltungsklausel 2059-12-20 | Machtblock gegen Eisenkrone/Helix; die Geheimhaltung macht Allianzdaten wertvoll. |
| GFW-RV-2058-01 | graufalk → ravenmoor | Geleitschiff-Rahmenvertrag Kharon/Brennus | 2058-07-15, 36 M | 90 | Kategorieindex | Rumpfplatten verkäuferexklusiv in Kharon | +Technik (Regel); +40 am 2059-09-01 (Ereignisse 45, 57, 58) | Driftwood bekommt keine Panzerplatten → Grund für Spionage und Schmuggel. |
| KHB-RV-2058-01 | kuppelwerk → pionierwerk | Habitatmodule Isolde | 2058-04, 36 M | 45 | cost_plus | Habitatmodule verkäuferexklusiv in Isolde | +20 (Regel); Gebietserweiterung Serravel + Sinterbausteine 2059-10-01 | Morgengrund bekommt Module nur über Pionierwerk → Abhängigkeit und Beziehungsgeschichte. |
| RCS-MSA-2059-01 | ravenmoor → helix | Escort & Frontier Supply Framework Kharon Corridor | 2059-07-01, 24 M | 60 | risk_index (Aufschlag je Routenrisiko) | Geleitschutz käuferexklusiv in Kharon | Geleitschutzklausel 2059-09-01 (verknüpft mit EKM-RV-2057-03); Ausweitung auf Kharon Landing IV `proposed` (Ereignis 74) | Feinde (Razzia 26), die Geschäftspartner werden; `escort_company_id` zeigt in beiden Rahmen auf Ravenmoor. |
| RVF-RV-2058-01 | raureif → pionierwerk | Versorgungsrahmen Isolde (Volatile) | 2058-01, 36 M | 35 | Treibstoffindex | Wasser- und Stickstoffeis käuferexklusiv in Isolde | +Energie, +15 (Regel) | Ohne Eis keine Kolonie; die Exklusivität ärgert Lichtacker (Isolde-Streit). |
| RVF-RV-2058-02 | raureif → eisenkrone | Volatile-Lieferrahmen Myrrhen und Brennus | 2058-06, 24 → 36 M | 20 | market_minus (Brennus −4 %) | none | −5 % am 2059-02-01 (Feldspat unterbietet); +8 `proposed` (Piraten Löchel, 69); Verlängerung (Regel) | Preiskampf mit Feldspat um Eisenkrone als Kunden. |
| SGM-RV-2059-01 | morgengrund → ravenmoor | Garnisonsrationen Kharon und Brennus | 2059-03, 12 M | 6 | fixed | none | Ernteausfallklausel ab Beginn; Verlängerung `proposed` | Die Nahrungslücke in Kharon (0 Angebote bei 20 Nachfragen) schließt sich. Kleiner, verlässlicher Partner für Einsteiger. |

Bewusst **ohne** Rahmen bleiben Kommissions- und Lizenzbeziehungen (`*_consignment`, `corvane → helix` licensing),
die kleinen Lieferanten (Feldspat → Helix, Driftwood, Lanternfish, Kometenpost, Second Hull) und Morgengrund →
Pionierwerk (Erntespitzen). Begründung: Kleine Firmen handeln spontan, der Spieler findet dort Spot-Geschäfte.
Offene Anfragen nach einem Rahmen („inquiry“ ohne Abschluss) sind Aufhänger für spätere Spielereignisse.

### 5.4 QA-Ergänzungen für Rahmenverträge

1. Jeder Rahmen gehört zu einer aktiven Partnerschaft. Verkäufer und Käufer stimmen überein, der Beginn liegt nach dem
   Partnerschaftsbeginn.
2. Jeder zugeordnete Vertrag erfüllt die Zuordnungsregel (Paar, Typ, Datum, Scope).
3. Nachträge sind fortlaufend nummeriert. `effective_date` liegt im Rahmen, `current_end_date` und
   `current_volume_cap` entsprechen der Summe der vereinbarten Nachträge.
4. Auslastung: Die Summe der zugeordneten, nicht stornierten Verträge ist ≤ `current_volume_cap` (Bestand: 81–89 %,
   B8 22 %).
5. Status `suspended` nur, wenn ein Nachtrag `suspension` mit Status `agreed` existiert.

---

## 6. Schriftverkehr (correspondence)

### 6.1 Tabelle

```sql
CREATE TABLE correspondence (
    correspondence_id INTEGER PRIMARY KEY,
    reference_number TEXT NOT NULL UNIQUE,      -- {SKU Absender}-{BRF|LTR}-{Jahr}-{nnnnn}
    letter_type TEXT NOT NULL CHECK(letter_type IN ('inquiry','quotation','negotiation','contract_confirmation',
        'amendment_offer','amendment_acceptance','amendment_rejection','delivery_notice','delay_notice',
        'delay_complaint','penalty_notice','payment_reminder','termination_notice','suspension_notice',
        'internal_memo','rumor')),
    thread_id INTEGER REFERENCES correspondence(correspondence_id),       -- erstes Schreiben des Vorgangs
    in_reply_to_id INTEGER REFERENCES correspondence(correspondence_id),
    source_correspondence_id INTEGER REFERENCES correspondence(correspondence_id), -- Gerücht → geleakte Mitteilung
    sent_at TEXT NOT NULL,                      -- ≤ 2060-01-01
    language TEXT NOT NULL CHECK(language IN ('de_DE','en_US')),          -- Sprache der Absenderfirma
    sender_company_id INTEGER NOT NULL REFERENCES companies(company_id),
    sender_employee_id INTEGER NOT NULL REFERENCES employees(employee_id),
    recipient_company_id INTEGER NOT NULL REFERENCES companies(company_id),
    recipient_employee_id INTEGER REFERENCES employees(employee_id),
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    confidentiality TEXT NOT NULL CHECK(confidentiality IN ('public','business','confidential','secret')),
    partnership_id INTEGER REFERENCES trade_partnerships(partnership_id),
    framework_agreement_id INTEGER REFERENCES framework_agreements(framework_agreement_id),
    amendment_id INTEGER REFERENCES framework_amendments(amendment_id),
    contract_id INTEGER REFERENCES contracts(contract_id),
    order_id INTEGER REFERENCES orders(order_id),
    shipment_id INTEGER REFERENCES shipments(shipment_id),
    event_id INTEGER REFERENCES events(event_id),
    rivalry_id INTEGER REFERENCES company_rivalries(rivalry_id),
    amount REAL CHECK(amount IS NULL OR amount >= 0),                    -- Strafe, Mahnbetrag, Angebotswert (CR)
    due_date TEXT,                              -- Zahlungs- oder Antwortfrist
    status TEXT NOT NULL CHECK(status IN ('sent','acknowledged','answered','rejected','escalated','closed')),
    intel_value INTEGER NOT NULL DEFAULT 0 CHECK(intel_value BETWEEN 0 AND 100),
    min_intel_access INTEGER NOT NULL DEFAULT 0 CHECK(min_intel_access BETWEEN 0 AND 3),
    leak_status TEXT NOT NULL DEFAULT 'none' CHECK(leak_status IN ('none','rumored','leaked')),
    leaked_by_employee_id INTEGER REFERENCES employees(employee_id),
    leaked_to_company_id INTEGER REFERENCES companies(company_id),
    rumor_reliability TEXT CHECK(rumor_reliability IN ('confirmed','plausible','false')),
    CHECK(sender_company_id <> recipient_company_id OR letter_type = 'internal_memo'),
    CHECK((letter_type = 'rumor') = (rumor_reliability IS NOT NULL))
);
```

Verknüpfung: Der Vorgang hängt über `thread_id` und `in_reply_to_id` zusammen. Der Fachbezug läuft über genau die
Schlüssel, die schon existieren. Ein Lieferavis kennt `shipment_id`, `order_id` und `contract_id`, ein
Nachtragsangebot `amendment_id` und `framework_agreement_id`, ein Gerücht `source_correspondence_id` und
`rivalry_id`. Mitarbeiter sind immer echte Zeilen aus `employees` (Bestands-IDs bleiben stabil).

### 6.2 Briefarten, Auslöser, Rollen

Absender werden nach Rolle gewählt. Der Mitarbeiter muss **am Versanddatum aktiv** sein
(`hire_date ≤ sent_at < termination_date`) und, wenn möglich, an der betroffenen Station arbeiten. Gibt es keinen
passenden Mitarbeiter, folgt die nächste Rolle: executive → relations → station_manager.

| letter_type | Auslöser (Daten) | Absender → Empfänger (Rollen) | Bezüge | Zeitpunkt | Vertraulichkeit |
|---|---|---|---|---|---|
| inquiry (Anfrage) | Rahmen-Anbahnung; Nachtragswunsch des Käufers; Paare ohne Rahmen (offene Anfrage) | Käufer relations → Verkäufer relations | partnership, framework | Beginn −60…−30 T | business |
| quotation (Angebot) | auf eine Anfrage; Werbeangebot an einen Kunden der Konkurrenz | Verkäufer relations → Käufer relations | framework (Angebotswert in `amount`) | +3…10 T | business |
| negotiation | 0–2 Runden, 2 bei `trust_level` < 60 | abwechselnd relations | framework | +5…15 T | confidential |
| contract_confirmation | Rahmenbeginn (Unterschrift executive) und **jeder Partnervertrag** (relations) | Verkäufer → Käufer | framework bzw. contract | `start_date` | business |
| amendment_offer | jeder Nachtrag | Initiator (s. 5.2) → Gegenpartei | amendment, framework, Anker-Vertrag/-Ereignis | wirksam −30…−14 T | confidential |
| amendment_acceptance / _rejection | Status `agreed` / `rejected`; `proposed` bleibt unbeantwortet | Gegenpartei executive | amendment | wirksam −7…0 T | business |
| delivery_notice (Lieferavis) | Abrufsendung mit Wert ≥ 1 Mio. CR und letzter Abruf jedes Vertrags | Verkäufer logistics (Ursprung) → Käufer station_manager (Ziel) | shipment, order, contract | Abflug | business |
| delay_notice (Verzugsanzeige) | Partnersendung mit `risk_incident` | Verkäufer logistics → Käufer station_manager | shipment, order | geplante Ankunft | business |
| delay_complaint (Verzugsbeschwerde) | Abruf mehr als 24 h zu spät oder Vertrag `breached` | Käufer station_manager (Ziel) → Verkäufer relations | shipment, order, contract | tatsächliche Ankunft +0…3 T | business |
| penalty_notice (Vertragsstrafenbescheid) | Vertrag `breached` | Käufer finance → Verkäufer finance | contract (+ letzte Sendung) | letzte Ankunft +5…14 T | business |
| payment_reminder (Mahnung) | Bestellung `overdue` | Verkäufer finance → Käufer finance | order | fällig +7 / +21 / +45 T (bis zum Stichtag) | business |
| termination_notice (Kündigung) | Vertrag `cancelled`; Nachtrag `partial_termination`; Ende einer historischen Partnerschaft | kündigende Partei executive | contract, amendment, partnership | Storno- bzw. Zugangsdatum | business |
| suspension_notice | Nachtrag `suspension` | Käufer executive → Verkäufer executive | amendment, event | wirksam | confidential |
| internal_memo (vertrauliche Mitteilung) | Ereignis an eigener Station mit Bezug zu Partner/Rivale (machine_failure, black_market_raid, pirate_attack, quarantine, resource_discovery); Strafbescheid > 250.000 CR | intelligence oder station_manager → executive derselben Firma | event, contract, rivalry | Ereignis +1…10 T | secret/confidential |
| rumor (Gerücht) | Leck aus einem internal_memo oder vertraulichen Schreiben | Leck-Mitarbeiter (Firma A) → intelligence/relations der Rivalin oder eines Partners | source, rivalry, event | +3…30 T | confidential |

**Strafbetrag** im Bescheid = `late_days × penalty_per_day`, mit derselben Formel wie in `generate_financials`
(Datumsdifferenz letzte Ankunft – Frist, Restlauf bis 2059-12-31). Die Summe der Bescheide je Firma und Monat muss
`company_financials.contract_penalties` entsprechen (zusätzlicher QA-Check).

**Spionage-Mechanik**: Ein Leck entsteht mit Wahrscheinlichkeit
`p = espionage_risk/100 × bribe_susceptibility/100 × (1 − loyalty/150)`. Der Leck-Mitarbeiter wird nach diesem Gewicht
unter den aktiven Mitarbeitern der Absenderfirma gezogen, die mindestens `min_intel_access` haben. 20 % der Gerüchte
sind `false` (verfälschter Betrag, falscher Vertrag), 50 % `plausible`. Spielspaß: Der Spieler kauft Gerüchte, prüft
sie gegen Lieferungen und Verträge und kann Fälschungen erkennen. `intel_value` steuert den Preis.

**Mengen** (aus dem Bestand abgeleitet): 743 Vertragsbestätigungen, 215 Verzugsanzeigen, 91 Verzugsbeschwerden plus
Beschwerden zu gebrochenen Verträgen, 80 Strafbescheide, etwa 140 Mahnungen (93 überfällige Bestellungen),
49 Kündigungen (stornierte Verträge), etwa 110 Schreiben zu den 8 Bestandsrahmen, etwa 60 Mitteilungen und Gerüchte.
Das ergibt etwa 1.500 Schreiben, mit den neuen Firmen etwa 3.300 (unter 3 MB).

### 6.3 Pflichtschreiben, verankert an echten Bestandsobjekten

Neue Firmen erscheinen mit Rolle, weil ihre Mitarbeiter erst im zweiten Durchlauf entstehen. IDs = `employee_id`.

| Datum | Art | Absender → Empfänger | Bezug | Inhalt |
|---|---|---|---|---|
| 2059-01-18 | delay_complaint | Toralf Gerlach (47, Tauvel Labor II) → Kayla Cannon (332, Helix) | `HMX-CTR-2058-0159`, `HMX-SHP-2059-01012` („Bright Margin“, Andockstau +147 h) | Baustelle Tauvel steht still. |
| 2059-01-20 | rumor (confirmed) | Erkan Hesse (39, LAK Finanzen, ausgeschieden 2059-06-11) → Partnerbetreuung Kuppelwerk | Strafbescheid unten | „Lichtacker hat genug von Helix.“ Hesse wird im Juni entlassen (Bestandsdatum). |
| 2059-01-25 | penalty_notice | Lena Heß (40) → Donald Morris (294) | `HMX-CTR-2058-0159` | 6 Tage × 108.860,36 = **653.162,16 CR** |
| 2059-01-28 | quotation | Partnerbetreuung Kuppelwerk → Hülya Matthäi (41) | Bezug auf `HMX-CTR-2058-0159`, `-2057-0043`, `-2058-0139` | Angebot Baustoffrahmen → KHB-RV-2059-01 |
| 2059-03-10 / 03-25 | amendment_offer / acceptance | Hülya Matthäi → Kayla Cannon; Annahme Elizabeth Lopez (293) | HMX-MSA-2057-01, Wettbewerbsklausel | Helix muss Kuppelwerk-Preise mitgehen oder den Bezug freigeben. |
| 2059-03-07 | delay_complaint | Matthew Thomas (123, Halcyon Works VI) → Jennifer Smith (298) | `HMX-CTR-2058-0131`, `HMX-SHP-2059-01094` („Open Ledger“, +103 h) | Helium-3 fehlt. |
| 2059-03-14 | penalty_notice | Dawn Turner (118) → Donald Morris (294) | `HMX-CTR-2058-0131` | 5 × 66.501,79 = **332.508,95 CR** |
| 2059-03-20 / 03-31 | amendment_offer / acceptance | Jason Armstrong (115) → Elizabeth Lopez (293) | HMX-MSA-2057-02, Aufhebung Energie-Exklusivität | Voraussetzung für EFF-MSA-2059-01 |
| 2059-04-02 / 04-15 | quotation / contract_confirmation | Partnerbetreuung Emberline → Matthew Thomas; Gegenzeichnung John Aguirre (119) | EFF-MSA-2059-01 | Helium-3 aus Pellora |
| 2059-06-10 | rumor (plausible) | Brandon Jones (445, Helix Finanzen Kharon) → Analyse Ravenmoor | 8 wegen Geleitschutz gebrochene Verträge | Grundlage des Ravenmoor-Angebots an David Hendricks (304, Team B) |
| 2059-07-20 / 08-01 | quotation / contract_confirmation | Aleksandra Koch (4) → Esther Bauer (170); Unterschriften Theodor Krause (1) und Roswitha van der Dussen (168, seit 2059-07-07) | FSP-RV-2059-01 nach Fund 52 | Exklusivität gegen Verrechnung der überfälligen 25,5 Mio. CR |
| 2059-08-05 | penalty_notice | Emily Floyd (368, Kharon Exchange IX) → Pamela Stroh (169) | `EKM-VTR-2059-0162` | 5 × 62.833,32 = **314.166,60 CR** |
| 2059-09-01 | amendment_acceptance | Elizabeth Lopez (293) → Esther Bauer (170) | EKM-RV-2057-03, Geleitschutzklausel Ravenmoor | nach `EKM-VTR-2058-0107` (Piraten) und `EKM-VTR-2059-0162` |
| 2059-09-10 | payment_reminder (2.) | Pamela Stroh (169) → Mikhail Gotthard (2, FSP Finanzen) | `EKM-BST-2059-01903` und 12 weitere | Druckmittel vor der Preisanpassung |
| 2059-10-11 | delay_complaint | Hans-Werner Eberhardt (45, Seip) → Esther Bauer (170) | `EKM-VTR-2059-0167` (Brennstoffzellen, Piraten/Geleitschutz) | dritte Energie-Panne an Seip |
| 2059-10-20 | termination_notice | Reimar Rörricht (38) → Roswitha van der Dussen (168) | EKM-RV-2057-04, Teilkündigung Energie | wirksam 2060-01-18 |
| 2059-10-28 / 11-15 | quotation / contract_confirmation | Partnerbetreuung Emberline → Hans-Werner Eberhardt (45) | EFF-MSA-2059-02 | Energie Seip |
| 2059-11-30 | delay_complaint | Claire Rust (174, Brennus Schacht VII) → Wayne Jacobson (302) | `HMX-CTR-2059-0242`, `HMX-SHP-2059-01602` (Quarantäne +97 h) | Medikamente zu spät |
| 2059-12-01 | internal_memo (secret) | Annekatrin Schuchhardt (178) → Roswitha van der Dussen (168) | Ereignis 70 (Förster) | drittes Ausfallprotokoll, gleiche Firmware-Version |
| 2059-12-05 | payment_reminder (3.) | Pamela Stroh (169) → Dawn Turner (118) | `EKM-BST-2059-01408` (4,39 Mio. CR) | Corvane schuldet Eisenkrone 34,4 Mio. CR und Helix 20,4 Mio. CR |
| 2059-12-12 | rumor (confirmed) | Desiree Schwartz (299, seit 2059-11-24) → Analyse Cindervale | Helix-Vertragsstrafen 2059: 2,08 Mio. CR | Helix ist im Technikmarkt Sol angreifbar. |
| 2059-12-15 | suspension_notice | Roswitha van der Dussen (168) → Vorstand Cindervale | CCI-MSA-2057-01, Ereignis 70 | Aussetzung bis zum Firmware-Audit |
| 2059-12-20 | internal_memo (secret) | Dolores Mühle (171) → Roswitha van der Dussen (168) | Rivalität Graufalk, Ereignisse 19/36/70 | Verdacht auf eine Hintertür; Graufalk hat dieselben Steuerkerne. |
| 2059-12-27 | rumor (plausible) | Esther Bauer (170) → Analyse Graufalk | Quelle: Mitteilung Mühle | Daraufhin die Geheimhaltungsklausel GFW-RV-2057-02 |
| 2059-12-29 | amendment_rejection | Heinz Dieter Schmidtke (42, seit 2059-11-03) → Esther Bauer (170) | Entwurf `EKM-VTR-2060-0230` (Helium-3) | Verweis auf die Teilkündigung |
| 2059-12-30 | delay_notice | Marijan Hörle (254, Brennus Schacht VII) → Eric Adkins (307, Kharon Exchange IX) | `EKM-BST-2059-02343` (offen, `delayed`, 3,63 Mio. CR) | läuft über den Stichtag |
| 2059-12-30 | delay_notice | Dorothee Girschner (9, FSP, gesprächig) → Irmingard Scholl (179, Hande) | `FSP-BST-2059-00111` (offen, `delayed`) | Girschner erzählt dabei zu viel über Becker. |
| 2059-05 | quotation | Kometenpost → Tilman Christoph (49, Hartmann-Gartenring, gesprächig) | `HMX-CTR-2059-0197` (Medizin, Quarantäne +58 h, 101.141,50 CR Strafe) | Werbung für den Expressdienst |
| Team B | – | Driftwood (Tina Gould, 23) → Ravenmoor; Outmark → Theodor Krause (1); Rörricht → Pionierwerk; Morgengrund → Ravenmoor | Razzia 58; Fund 52; Isolde; SGM-RV-2059-01 | wie `phase1_team_b.md` 5.3 |

Alle Datumsangaben sind gegen `hire_date` geprüft. Roswitha van der Dussen ist erst seit 2059-07-07 Vorstand,
Desiree Schwartz seit 2059-11-24, Heinz Dieter Schmidtke seit 2059-11-03 und Eric Adkins seit 2059-07-18. Ältere
Eisenkrone-Schreiben zeichnet deshalb Esther Bauer.

### 6.4 QA-Ergänzungen für Schriftverkehr

1. Absender und Empfänger gehören zur angegebenen Firma und sind am `sent_at` aktiv.
2. Bezüge sind konsistent: Die Partner des Vertrags bzw. Rahmens sind {Absender, Empfänger}. Die Sendung gehört zur
   Bestellung, die Bestellung zum Vertrag.
3. `sent_at` ≤ 2060-01-01. `language` ist die Sprache der Absenderfirma.
4. Strafbescheide entsprechen `company_financials.contract_penalties` (je Firma und Monat).
5. Jedes Gerücht hat eine Quelle mit `leak_status <> 'none'`. Der Leck-Mitarbeiter hat Bestechlichkeit ≥ 50 oder
   Loyalität ≤ 50.

---

## 7. Umsetzung (Reihenfolge im Skript)

Zuständigkeit wie von Team B vorgeschlagen: Schritte 1, 2 und 5 (ohne die neuen Checks 5.4/6.4) übernimmt Team A,
Schritte 3 und 4 sowie die Checks 5.4/6.4 übernimmt Team B.

1. Durchlauf 1 unverändert (6 Bestandsfirmen, identische Stammdaten und Bewegungsdaten).
2. Durchlauf 2 mit `random.Random(f"{seed}:ext")` und eigenen Faker-Instanzen: Firmen, Stationen, Produkte, neue
   Vereinbarungen, historische Partnerschaften und Rivalitäten (feste Daten, wie oben), Rahmenvertrags-Gerüste für
   neue Paare, Märkte und Routen der neuen Verkäufer, Verträge (Typregel 5.2), Bestellungen, Sendungen, Ereignisse und
   Mitarbeiter.
3. Danach mit `random.Random(f"{seed}:links")`: Rahmenverträge der Bestandspaare, Zuordnung `framework_agreement_id`,
   Nachträge nach Regeln, Scope, Schriftverkehr.
4. Finanzen neu summieren (nur Bestandsfirmen mit neuen Zulieferern ändern sich nachvollziehbar, auf der Kaufseite).
5. QA: 18 Firmen 6/6/6, Partnerzahlen (Tabelle 2.6), Hub, Unvollständigkeit, Bestandsvergleich gegen
   `space_trading_game_bestand.db`, Checks 5.4 und 6.4.

---

## 8. Maschinenlesbarer Vorschlag

`partnerships` enthält die 13 Blueprint-Einträge und die 34 neuen Kanten. `helix → corvane` steht getrennt unter
`optional_partnerships_existing`, damit es nicht doppelt angelegt wird. Zusätzliche Schlüssel: `historic_details`
(feste Daten), `rivalry_since_dates`, `new_rivalry_types` (nur `armed_conflict`) und `rivalry_text_overrides`.
Nachträge mit `"effective_date": "rule"` werden bei der Generierung nach Abschnitt 5.2 datiert.

```json
{
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
 "optional_partnerships_existing": [
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
  {"seller_key": "corvane", "buyer_key": "driftwood", "type": "supply_agreement", "dates": "Bestand (2057-04-27 bis 2058-07-17), unverändert"},
  {"seller_key": "eisenkrone", "buyer_key": "graufalk", "type": "supply_agreement", "start_date": "2039-01-01", "end_date": "2049-06-30", "hook": "Ausgliederung der Werftsparte Orrin; Bruch im Streit um Patente für Reaktorkomponenten"},
  {"seller_key": "cindervale", "buyer_key": "helix", "type": "licensing", "start_date": "2041-04-01", "end_date": "2054-03-31", "hook": "Helix verlor die Cindervale-Lizenz und bezieht Hochtechnologie seither aus Kharon (lange, bruchanfällige Routen)"},
  {"seller_key": "lichtacker", "buyer_key": "pionierwerk", "type": "supply_agreement", "start_date": "2045-03-01", "end_date": "2053-06-30", "source": "Team B", "hook": "Lichtacker versorgte die Isolde-Bautrupps, bis der Pachtstreit eskalierte"},
  {"seller_key": "emberline", "buyer_key": "eisenkrone", "type": "supply_agreement", "start_date": "2047-02-01", "end_date": "2056-06-30", "hook": "Helium-3 für Bergbaustation Hande, beendet als Eisenkrone eigenes Deuterium förderte"},
  {"seller_key": "outmark", "buyer_key": "feldspat", "type": "licensing", "start_date": "2055-02-01", "end_date": "2058-06-30", "source": "Team B", "hook": "Vermessungsdaten Brennus; Feldspat fand 2059 den Quantenquarz bei Becker (Ereignis 52)"},
  {"seller_key": "driftwood", "buyer_key": "second_hull", "type": "consignment", "start_date": "2057-05-01", "end_date": "2058-07-01", "source": "Team B", "hook": "Bergegut aus Nyx; Bruch nach der Lizenzierung von Second Hull, zwei Tage nach Razzia 26"}
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
 "rivalry_since_dates": {"graufalk-eisenkrone": "2049-07-01", "cindervale-helix": "2054-04-01", "emberline-eisenkrone": "2058-08-15", "lichtacker-pionierwerk": "2053-07-01", "ravenmoor-driftwood": "2058-06-30", "outmark-feldspat": "2059-07-14", "ravenmoor-helix": "2057-11-17", "second_hull-driftwood": "2058-07-01"},
 "new_rivalry_types": {"armed_conflict": {"intensity": [60, 90], "source": "Team B"}},
 "rivalry_text_overrides": {"emberline-eisenkrone": {"de_DE": "{company} und {rival} liefern beide Energie ins {system}-System und unterbieten sich bei jedem Liefervertrag.", "en_US": "{company} and {rival} both supply energy to the {system} system and undercut each other on every supply contract."}, "lichtacker-pionierwerk": "Text Team B (Pachtrechte Isolde)"},
 "framework_agreements": [
  {"number": "HMX-MSA-2057-01", "seller_key": "helix", "buyer_key": "lichtacker", "title": "Distribution Framework Tauvel & Myrrhen", "start_date": "2057-01-01", "start_year": 2057, "term_months": 36, "base_volume_mcr": 300, "price_formula": "index_linked", "indexation": "category_price_index", "exclusivity": "none", "notice_days": 180, "scope": ["luxury", "food", "industrial_goods"], "existing_pair": true, "amendments": [
    {"type": "product_addition", "effective_date": "2057-03-23", "status": "agreed", "categories": ["energy", "technology"]},
    {"type": "product_addition", "effective_date": "2057-09-05", "status": "agreed", "categories": ["medical"]},
    {"type": "penalty_clause", "effective_date": "2058-03-14", "status": "agreed", "anchor": "HMX-CTR-2057-0043"},
    {"type": "volume_increase", "effective_date": "2058-12-25", "status": "agreed", "delta_mcr": 180, "anchor": "HMX-CTR-2059-0194"},
    {"type": "competition_clause", "effective_date": "2059-03-25", "status": "agreed", "anchor": "HMX-CTR-2058-0159; Angebot Kuppelwerk"},
    {"type": "term_extension", "effective_date": "2059-11-01", "status": "agreed", "new_end_date": "2061-01-31"}
  ]},
  {"number": "HMX-MSA-2057-02", "seller_key": "helix", "buyer_key": "corvane", "title": "Logistics Master Agreement Halcyon & Aurelis", "start_date": "2057-01-01", "start_year": 2057, "term_months": 36, "base_volume_mcr": 350, "price_formula": "index_linked", "indexation": "fuel_index", "exclusivity": "none", "notice_days": 180, "scope": ["luxury", "raw_materials", "technology"], "existing_pair": true, "amendments": [
    {"type": "product_addition", "effective_date": "2057-04-19", "status": "agreed", "categories": ["energy"]},
    {"type": "exclusivity_clause", "effective_date": "2057-04-19", "status": "agreed", "exclusivity": "buyer_exclusive", "categories": ["energy"]},
    {"type": "product_addition", "effective_date": "2057-12-29", "status": "agreed", "categories": ["industrial_goods"]},
    {"type": "volume_increase", "effective_date": "2058-10-18", "status": "agreed", "delta_mcr": 270, "anchor": "HMX-CTR-2058-0171"},
    {"type": "exclusivity_waiver", "effective_date": "2059-03-31", "status": "agreed", "categories": ["energy"], "anchor": "HMX-CTR-2058-0131; HMX-CTR-2057-0014"},
    {"type": "term_extension", "effective_date": "2059-11-01", "status": "agreed", "new_end_date": "2060-12-31"}
  ]},
  {"number": "HMX-MSA-2057-03", "seller_key": "helix", "buyer_key": "eisenkrone", "title": "Strategic Alliance Supply Framework Sol-Halcyon", "start_date": "2057-01-01", "start_year": 2057, "term_months": 36, "base_volume_mcr": 400, "price_formula": "index_linked", "indexation": "category_price_index", "exclusivity": "right_of_first_refusal", "notice_days": 365, "scope": ["food", "raw_materials", "energy"], "existing_pair": true, "amendments": [
    {"type": "product_addition", "effective_date": "2057-07-17", "status": "agreed", "categories": ["medical", "technology"]},
    {"type": "product_addition", "effective_date": "2057-10-21", "status": "agreed", "categories": ["industrial_goods"]},
    {"type": "price_adjustment", "effective_date": "2058-01-01", "status": "agreed", "pct": "aus Preisindex"},
    {"type": "volume_increase", "effective_date": "2059-07-17", "status": "agreed", "delta_mcr": 100, "anchor": "HMX-CTR-2059-0248"},
    {"type": "term_extension", "effective_date": "2059-11-01", "status": "agreed", "new_end_date": "2060-12-31"}
  ]},
  {"number": "EKM-RV-2057-01", "seller_key": "eisenkrone", "buyer_key": "corvane", "title": "Joint-Venture-Liefervertrag Platinmetalle und Reaktortechnik", "start_date": "2057-01-01", "start_year": 2057, "term_months": 48, "base_volume_mcr": 380, "price_formula": "index_linked", "indexation": "category_price_index", "exclusivity": "buyer_exclusive", "exclusive_archetypes": ["platinum"], "notice_days": 365, "scope": ["raw_materials"], "existing_pair": true, "amendments": [
    {"type": "product_addition", "effective_date": "2057-01-24", "status": "agreed", "categories": ["industrial_goods"]},
    {"type": "product_addition", "effective_date": "2057-05-11", "status": "agreed", "categories": ["luxury", "technology"]},
    {"type": "volume_increase", "effective_date": "2059-04-23", "status": "agreed", "delta_mcr": 120, "anchor": "EKM-VTR-2059-0168"},
    {"type": "service_level_clause", "effective_date": "2059-12-23", "status": "proposed", "anchor": "EKM-VTR-2059-0160"}
  ]},
  {"number": "EKM-RV-2057-02", "seller_key": "eisenkrone", "buyer_key": "feldspat", "title": "Ausrüstungsrahmen Brennus", "start_date": "2057-01-01", "start_year": 2057, "term_months": 36, "base_volume_mcr": 200, "price_formula": "fixed", "indexation": "category_price_index", "exclusivity": "none", "notice_days": 90, "scope": ["industrial_goods", "energy"], "existing_pair": true, "amendments": [
    {"type": "product_addition", "effective_date": "2057-08-17", "status": "agreed", "categories": ["luxury"]},
    {"type": "product_addition", "effective_date": "2058-01-06", "status": "agreed", "categories": ["medical", "raw_materials", "food"]},
    {"type": "volume_increase", "effective_date": "2059-06-26", "status": "agreed", "delta_mcr": 80, "anchor": "EKM-VTR-2059-0186"},
    {"type": "product_addition", "effective_date": "2059-09-20", "status": "agreed", "categories": ["technology"], "anchor": "Ereignis 52"},
    {"type": "term_extension", "effective_date": "2059-11-01", "status": "agreed", "new_end_date": "2060-12-31"}
  ]},
  {"number": "EKM-RV-2057-03", "seller_key": "eisenkrone", "buyer_key": "helix", "title": "Rahmenvertrag Brennus-Kharon", "start_date": "2057-03-01", "start_year": 2057, "term_months": 36, "base_volume_mcr": 220, "price_formula": "index_linked", "indexation": "fuel_index", "exclusivity": "none", "notice_days": 180, "scope": ["energy", "raw_materials"], "existing_pair": true, "amendments": [
    {"type": "product_addition", "effective_date": "2057-06-11", "status": "agreed", "categories": ["food", "technology"]},
    {"type": "product_addition", "effective_date": "2057-12-31", "status": "agreed", "categories": ["industrial_goods", "luxury"]},
    {"type": "penalty_clause", "effective_date": "2058-01-09", "status": "agreed", "anchor": "EKM-VTR-2057-0017"},
    {"type": "volume_increase", "effective_date": "2059-03-15", "status": "agreed", "delta_mcr": 80, "anchor": "EKM-VTR-2059-0162"},
    {"type": "escort_clause", "effective_date": "2059-09-01", "status": "agreed", "escort_key": "ravenmoor", "anchor": "EKM-VTR-2058-0107; EKM-VTR-2059-0162"},
    {"type": "term_extension", "effective_date": "2059-12-15", "status": "proposed", "new_end_date": "2060-12-31"}
  ]},
  {"number": "EKM-RV-2057-04", "seller_key": "eisenkrone", "buyer_key": "lichtacker", "title": "Lieferrahmen Agrartechnik und Energie Myrrhen/Tauvel", "start_date": "2057-01-01", "start_year": 2057, "term_months": 36, "base_volume_mcr": 180, "price_formula": "index_linked", "indexation": "category_price_index", "exclusivity": "none", "notice_days": 90, "scope": ["industrial_goods", "luxury", "raw_materials"], "existing_pair": true, "amendments": [
    {"type": "product_addition", "effective_date": "2057-08-13", "status": "agreed", "categories": ["energy", "technology"]},
    {"type": "penalty_clause", "effective_date": "2058-09-14", "status": "agreed", "anchor": "EKM-VTR-2058-0099"},
    {"type": "partial_termination", "effective_date": "2060-01-18", "status": "agreed", "notice_date": "2059-10-20", "categories": ["energy"], "anchor": "EKM-VTR-2059-0167; EKM-VTR-2058-0105"},
    {"type": "term_extension", "effective_date": "2059-11-15", "status": "agreed", "new_end_date": "2060-12-31"},
    {"type": "volume_increase", "effective_date": "2060-01-08", "status": "proposed", "delta_mcr": 40, "anchor": "EKM-VTR-2060-0222"}
  ]},
  {"number": "FSP-RV-2059-01", "seller_key": "feldspat", "buyer_key": "eisenkrone", "title": "Abnahmerahmen Quantenquarz Becker", "start_date": "2059-08-01", "start_year": 2059, "term_months": 24, "base_volume_mcr": 12, "price_formula": "market_minus", "indexation": "category_price_index", "exclusivity": "seller_exclusive", "exclusive_archetypes": ["quantum_quartz"], "notice_days": 90, "scope": ["raw_materials"], "existing_pair": true, "amendments": [
    {"type": "price_adjustment", "effective_date": "2059-11-20", "status": "agreed", "pct": 12, "anchor": "Ereignisse 65, 66"},
    {"type": "volume_increase", "effective_date": "2060-01-15", "status": "proposed", "delta_mcr": 8}
  ]},
  {"number": "GFW-RV-2057-01", "seller_key": "graufalk", "buyer_key": "helix", "title": "Flottenrahmenvertrag Rumpf und Antrieb", "start_date": "2057-01-01", "start_year": 2057, "term_months": 36, "base_volume_mcr": 180, "price_formula": "index_linked", "indexation": "category_price_index", "exclusivity": "none", "notice_days": 180, "scope": ["industrial_goods"], "amendments": [
    {"type": "product_addition", "effective_date": "rule", "status": "agreed", "categories": ["technology"]},
    {"type": "volume_increase", "effective_date": "2058-12-20", "status": "agreed", "delta_mcr": 60, "anchor": "HMX-CTR-2058-0173"},
    {"type": "term_extension", "effective_date": "2059-11-01", "status": "agreed", "new_end_date": "2061-12-31"}
  ]},
  {"number": "CCI-MSA-2057-01", "seller_key": "cindervale", "buyer_key": "eisenkrone", "title": "AI Control & Robotics Framework", "start_date": "2057-02-01", "start_year": 2057, "term_months": 48, "base_volume_mcr": 140, "price_formula": "index_linked", "indexation": "category_price_index", "price_cap_pct_per_year": 3, "exclusivity": "buyer_exclusive", "exclusive_archetypes": ["ai_cores"], "notice_days": 180, "scope": ["technology", "industrial_goods"], "amendments": [
    {"type": "service_level_clause", "effective_date": "2058-03-01", "status": "agreed", "anchor": "Ereignis 19"},
    {"type": "price_adjustment", "effective_date": "2058-12-15", "status": "agreed", "pct": -8, "anchor": "Ereignis 36"},
    {"type": "suspension", "effective_date": "2059-12-15", "status": "agreed", "anchor": "Ereignis 70"}
  ]},
  {"number": "KHB-RV-2059-01", "seller_key": "kuppelwerk", "buyer_key": "lichtacker", "title": "Baustoffrahmen Tauvel und Myrrhen", "start_date": "2059-02-15", "start_year": 2059, "term_months": 24, "base_volume_mcr": 30, "price_formula": "cost_plus", "indexation": "fuel_index", "exclusivity": "none", "notice_days": 90, "scope": ["industrial_goods", "raw_materials"], "amendments": [
    {"type": "product_addition", "effective_date": "2059-08-01", "status": "agreed", "archetypes": ["habitat_modules"], "anchor": "Ereignis 53"},
    {"type": "volume_increase", "effective_date": "2059-11-01", "status": "agreed", "delta_mcr": 15},
    {"type": "exclusivity_clause", "effective_date": "2060-02-01", "status": "proposed", "exclusivity": "regional_exclusive", "system_code": "myrrhen", "archetypes": ["sinter_blocks", "habitat_modules"]}
  ]},
  {"number": "EFF-MSA-2059-01", "seller_key": "emberline", "buyer_key": "corvane", "title": "Helium-3 Supply Framework Halcyon Works VI", "start_date": "2059-04-15", "start_year": 2059, "term_months": 24, "base_volume_mcr": 40, "price_formula": "index_linked", "indexation": "fuel_index", "exclusivity": "none", "notice_days": 90, "scope": ["energy"], "amendments": [
    {"type": "force_majeure_clause", "effective_date": "2059-09-15", "status": "agreed", "anchor": "Ereignis 59"},
    {"type": "volume_increase", "effective_date": "2059-12-15", "status": "proposed", "delta_mcr": 15}
  ]},
  {"number": "EFF-MSA-2059-02", "seller_key": "emberline", "buyer_key": "lichtacker", "title": "Energy Framework Agrarstation Seip", "start_date": "2059-11-15", "start_year": 2059, "term_months": 24, "base_volume_mcr": 18, "price_formula": "index_linked", "indexation": "fuel_index", "exclusivity": "none", "notice_days": 90, "scope": ["energy"], "amendments": [
    {"type": "exclusivity_clause", "effective_date": "2060-01-18", "status": "agreed", "exclusivity": "buyer_exclusive", "categories": ["energy"], "anchor": "Teilkündigung EKM-RV-2057-04"}
  ]},
  {"number": "GFW-RV-2057-02", "seller_key": "graufalk", "buyer_key": "cindervale", "title": "Allianzvertrag Navigationsplattform", "start_date": "2057-01-01", "start_year": 2057, "term_months": 60, "base_volume_mcr": 220, "price_formula": "cost_plus", "indexation": "category_price_index", "exclusivity": "none", "notice_days": 365, "scope": ["industrial_goods", "technology"], "amendments": [
    {"type": "exclusivity_clause", "effective_date": "2058-03-15", "status": "agreed", "exclusivity": "mutual", "archetypes": ["nav_computers", "ai_cores"], "anchor": "Ereignis 19"},
    {"type": "volume_increase", "effective_date": "rule", "status": "agreed", "delta_mcr": 80},
    {"type": "confidentiality_clause", "effective_date": "2059-12-20", "status": "agreed", "anchor": "Suspendierung CCI-MSA-2057-01"}
  ]},
  {"number": "GFW-RV-2058-01", "seller_key": "graufalk", "buyer_key": "ravenmoor", "title": "Geleitschiff-Rahmenvertrag Kharon/Brennus", "start_date": "2058-07-15", "start_year": 2058, "term_months": 36, "base_volume_mcr": 90, "price_formula": "index_linked", "indexation": "category_price_index", "exclusivity": "seller_exclusive", "exclusive_archetypes": ["hull_plating"], "system_code": "kharon", "notice_days": 180, "scope": ["industrial_goods"], "amendments": [
    {"type": "product_addition", "effective_date": "rule", "status": "agreed", "categories": ["technology"]},
    {"type": "volume_increase", "effective_date": "2059-09-01", "status": "agreed", "delta_mcr": 40, "anchor": "Ereignisse 45, 57, 58"}
  ]},
  {"number": "KHB-RV-2058-01", "seller_key": "kuppelwerk", "buyer_key": "pionierwerk", "title": "Habitatmodule Isolde", "start_date": "2058-04-01", "start_year": 2058, "term_months": 36, "base_volume_mcr": 45, "price_formula": "cost_plus", "indexation": "fuel_index", "exclusivity": "seller_exclusive", "exclusive_archetypes": ["habitat_modules"], "system_code": "isolde", "notice_days": 180, "scope": ["industrial_goods"], "amendments": [
    {"type": "volume_increase", "effective_date": "rule", "status": "agreed", "delta_mcr": 20},
    {"type": "scope_extension", "effective_date": "2059-10-01", "status": "agreed", "system_code": "serravel", "archetypes": ["sinter_blocks"]}
  ]},
  {"number": "RCS-MSA-2059-01", "seller_key": "ravenmoor", "buyer_key": "helix", "title": "Escort & Frontier Supply Framework Kharon Corridor", "start_date": "2059-07-01", "start_year": 2059, "term_months": 24, "base_volume_mcr": 60, "price_formula": "index_linked", "indexation": "risk_index", "exclusivity": "buyer_exclusive", "system_code": "kharon", "notice_days": 90, "scope": ["industrial_goods", "technology", "energy", "medical", "food"], "escort_key": "ravenmoor", "amendments": [
    {"type": "escort_clause", "effective_date": "2059-09-01", "status": "agreed", "anchor": "EKM-RV-2057-03 Nachtrag 5"},
    {"type": "scope_extension", "effective_date": "2060-01-15", "status": "proposed", "delta_mcr": 25, "station": "Kharon Landing IV", "anchor": "Ereignis 74"}
  ]},
  {"number": "RVF-RV-2058-01", "seller_key": "raureif", "buyer_key": "pionierwerk", "title": "Versorgungsrahmen Isolde (Volatile)", "start_date": "2058-01-01", "start_year": 2058, "term_months": 36, "base_volume_mcr": 35, "price_formula": "index_linked", "indexation": "fuel_index", "exclusivity": "buyer_exclusive", "exclusive_archetypes": ["water_ice", "nitrogen_ice"], "system_code": "isolde", "notice_days": 180, "scope": ["raw_materials"], "amendments": [
    {"type": "product_addition", "effective_date": "rule", "status": "agreed", "categories": ["energy"]},
    {"type": "volume_increase", "effective_date": "rule", "status": "agreed", "delta_mcr": 15}
  ]},
  {"number": "RVF-RV-2058-02", "seller_key": "raureif", "buyer_key": "eisenkrone", "title": "Volatile-Lieferrahmen Myrrhen und Brennus", "start_date": "2058-06-01", "start_year": 2058, "term_months": 24, "base_volume_mcr": 20, "price_formula": "market_minus", "indexation": "category_price_index", "exclusivity": "none", "notice_days": 90, "scope": ["raw_materials", "energy"], "amendments": [
    {"type": "price_adjustment", "effective_date": "2059-02-01", "status": "agreed", "pct": -5, "anchor": "Konkurrenz Feldspat"},
    {"type": "volume_increase", "effective_date": "2059-12-10", "status": "proposed", "delta_mcr": 8, "anchor": "Ereignis 69"},
    {"type": "term_extension", "effective_date": "rule", "status": "agreed", "new_end_date": "2061-05-31"}
  ]},
  {"number": "SGM-RV-2059-01", "seller_key": "morgengrund", "buyer_key": "ravenmoor", "title": "Garnisonsrationen Kharon und Brennus", "start_date": "2059-03-01", "start_year": 2059, "term_months": 12, "base_volume_mcr": 6, "price_formula": "fixed", "indexation": "none", "exclusivity": "none", "notice_days": 60, "scope": ["food"], "amendments": [
    {"type": "force_majeure_clause", "effective_date": "2059-03-01", "status": "agreed", "anchor": "Ernteausfallklausel"},
    {"type": "term_extension", "effective_date": "2059-12-20", "status": "proposed", "new_end_date": "2061-02-28"}
  ]}
 ]
}
```
