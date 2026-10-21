# Phase 2 – Vorschlag Team B: Verknüpfungen der 18 Firmen (Revision 2)

Stand: 21.10.2026 · Neudurchlauf Phase 2 mit halbierter Agentenbesetzung · Grundlage: `phase1_team_a.md`,
`phase1_team_b.md` (Revision 2), `NACHRICHTEN.md`, `phase2_entscheidung.md`, `verknuepfungen.json`, das Skript
`generate_space_trading_data.py` (Seed 42, als Modul geladen, nicht ausgeführt) und eigene Abfragen auf
`/home/user/bestand/space_trading_game_bestand.db` (nur lesend, `mode=ro`). Alle Vertrags-, Bestell-, Lieferungs-,
Ereignis- und Mitarbeiternummern stammen aus dieser Datenbank.

**Vorgehen in Revision 2.** Beide Phase-1-Berichte lassen die 12 neuen Firmen unverändert, weil die verbindliche
Phase-2-Entscheidung (`verknuepfungen.json`) darauf aufbaut. Ein neues Netz würde 48 Vereinbarungen, 21 Rahmenverträge und
38 verankerte Vorgänge entwerten, ohne Plausibilität oder Spielwert zu verbessern. Team B übernimmt daher das
verbindliche Netz als Basis. Neu ist die **unabhängige Nachprüfung** aller Teile mit eigenen Skripten (Zählregeln, Netz,
Verbraucherstationen, Zuordnung der Bestandsverträge, Volumen-Auslöser, Strafbeträge, Mahnfristen, Einstellungsdaten,
Exklusivitäten gegen Bestandsflüsse). Dabei haben wir **11 Korrekturen (K1–K11)** gefunden. Sie sind unten markiert und im
JSON-Block eingearbeitet.

## 0. Kurzfassung

| Thema | Ergebnis |
|---|---|
| Aktive Vereinbarungen | **48** gerichtete Vereinbarungen: 13 Blueprint-Kanten + `helix → corvane` (Bestand, bleibt in `OPTIONAL_PARTNERSHIPS`), 7 neue Firma → Bestandsfirma, 12 innerhalb Team A, 12 innerhalb Team B, 3 teamübergreifend. Nachgezählt: alle 18 Firmen im Größenbereich, jede mit ≥ 1 ausgehender Vereinbarung. |
| Hub | **Helix Meridian** (large): 7 direkte Partner, 10 Vereinbarungen. Dahinter Graufalk (7/9) und Ravenmoor (7/8), beide large. |
| Netz | zusammenhängend und unvollständig: 38 von 153 Paaren direkt, **66 nur über einen Zwischenhändler**, 45 mit Abstand 3, 4 mit Abstand 4 (Durchmesser 4). |
| Verbraucherprüfung | Jede Kante hat ≥ 52 % des Warengewichts des Verkäufers mit passendem Verbraucher-Stationstyp beim Käufer (`CATEGORY_CONSUMERS`). Den niedrigsten Wert hat `pionierwerk → morgengrund`, Verbesserung als K11. |
| Historisch | 7 beendete Partnerschaften (1 Bestand, 6 neu), alle mit festen Daten und Story-Hook. |
| Rivalitäten | 12 (4 Bestand, 8 neu). Neu ist nur der Typ `armed_conflict`, dazu 2 Text-Overrides. Feste since/intensity/espionage-Werte. |
| Rahmenverträge | **21** (7 Bestandspaare, 14 neue Paare), **78 Nachträge** (60 unterzeichnet, 17 offen, 1 abgelehnt). Nachgerechnet: **341 von 475** Abrufverträgen des Bestands gehören zu einem Rahmen (2.309,1 Mio. CR). Alle 12 Volumen-Auslöser lassen sich exakt reproduzieren. |
| Schriftverkehr | Tabelle `correspondence` (37 Spalten, 20 Briefarten), verknüpft mit Rahmen, Nachtrag, Vertrag, Bestellung, Lieferung, Ereignis, Rivalität, Partnerschaft und Kunde. 38 verankerte Vorgänge + neu **V39**. Alle 91 Personen-Datums-Paare sind gegen `hire_date` geprüft. |
| Korrekturen R2 | K1 Exklusivität CCI widerspricht dem Bestand · K2 Geleitschutz-Anker · K3–K5 Mahnfristen · K6 Datum vor Bestellung · K7 Exklusivität RVF · K8 Sperrfristen für neue Kanten · K9 optionaler Rahmen · K10 Schuldenstand nach Datum · K11 Morgengrund-Handelsstation (optional) |

---

## 1. Antworten auf NACHRICHTEN.md

**An Team A, Frage aus dem Phase-1-Neudurchlauf („Bleibt ihr bei eurem Phase-1-Stand und bei der Zuständigkeit?“):**
Ja. Team B bleibt bei PKB, RCS, RVF, OSP, SGM, SHR, den Systemen `vaskar`/`serravel` (Stufe 5, Sektor `far_reach`), den
Archetypen `escort_drones`, `nitrogen_ice`, `terraforming_cultures` (optional `survey_charts`) und bei der Zuständigkeit aus
Phase 2. Team A übernimmt Durchlauf 2 (RNG/Faker, Archetyp-Filter, neue Vereinbarungen, Historie, Rivalitäten, QA 6/6/6 mit
Bestandsvergleich). Team B übernimmt Rahmenverträge, Nachträge, Scope, Schriftverkehr und die QA dazu.

**Hinweis an Team A zu Durchlauf 2:** Die Sperrfristen aus K8 betreffen die Vertrags- und Bestellerzeugung der neuen
Verkäufer, also euren Teil. Bitte als Filter einbauen (eine Zeile je Regel, siehe Abschnitt 6.6).

**Unsere offenen Phase-1-Fragen R2-1 bis R2-3** bleiben bestehen. Für R2-1 (Ankerobjekte im Bestandsvergleich) schlagen wir
die konkrete Liste in Abschnitt 8.2 vor.

---

## 2. Was aus dem Bestand genutzt wird (eigene Auswertung)

| Befund (Bestands-DB) | Wert | Nutzung |
|---|---|---|
| Aktive Vereinbarungen der Bestandsfirmen heute | Feldspat 3, Driftwood 1, Lichtacker 4, Corvane 5, Eisenkrone 7, Helix 8 | Nur 10 freie Plätze. 7 davon belegen die neuen Kanten, 3 bleiben Reserve (Driftwood 2, Eisenkrone 1). |
| Abrufverträge (framework/recurring/exclusive) | 475 | 341 unter Rahmenverträge gestellt |
| Gebrochene Verträge mit Geleitschutz-Zwischenfall | 8 (55 Lieferungen mit „Geleitschutz abgewartet“) | Geleitschutzklausel, Ravenmoor |
| Strafen der Brüche (Formel `generate_financials`) | z. B. HMX-CTR-2058-0159 = 6 × 108.860,36 = 653.162,16 CR | Strafbescheide |
| Überfällige Feldspat-Schulden bei Eisenkrone | 13 Bestellungen, 25,52 Mio. CR | FSP-RV-2059-01 (K10) |
| Systeme ohne Station | Orrin, Isolde | Graufalk/Lanternfish bzw. Pionierwerk/Morgengrund |
| Ereignisse als Anker | 3, 10, 16, 19, 24, 26, 27, 30, 36, 45, 51, 52, 53, 54, 57, 58, 59, 61, 65, 66, 67, 69, 70, 71, 72, 74 | Rivalitäten, Nachträge, Schreiben (alle Daten, Typen, Stationen geprüft) |
| Technik an Eisenkrone in Halcyon | 5 Corvane-Verträge + 25 Bestellungen an Bergbaustation Hande (2058–2059) | **K1** |

---

## 3. Gerichtete Handelsvereinbarungen (aktiv, Verkäufer → Käufer)

### 3.1 Liste mit Begründung

Typen nur aus `TRUST_RANGES`. Mit Bestandsfirmen nur in der Richtung **neue Firma → Bestandsfirma**. Routen, Verträge,
Kunden und Bestellungen entstehen im Skript beim Verkäufer, also bleiben die Bewegungsdaten der Bestandsfirmen stabil.
Bestandsstationen sind nur zusätzliche Ziele.

**Bestand (14, unverändert)**

| # | Verkäufer → Käufer | Typ | Plausibilität | Spielspaß |
|---|---|---|---|---|
| 1 | eisenkrone → helix | supply_agreement | Erze und Energie aus Brennus/Halcyon für die Handelsstationen | Grundlast-Routen, Brennus–Kharon mit Andockstau |
| 2 | helix → eisenkrone | strategic_alliance | Handel versorgt die Schwerindustrie mit allem, was sie nicht selbst fördert | Partner und Rivale zugleich (Sol) |
| 3 | helix → lichtacker | distribution_agreement | Verbundstahl, Technik, Medizin für die Agrarringe | Kette der Verbundstahl-Brüche → Kuppelwerk |
| 4 | lichtacker → helix | supply_agreement | Lebensmittel für die Handelsstationen | Einsteiger-Route |
| 5 | corvane → helix | licensing | Medizin und Bioproben in Lizenz | Quarantäne-Ereignisse |
| 6 | feldspat → helix | consignment | Rohstoffe in Kommission | kleiner Händler als Vorbild für den Spieler |
| 7 | driftwood → helix | consignment | Bergegut über die Freihäfen | Schmuggel-Einstieg |
| 8 | feldspat → eisenkrone | supply_agreement | Quantenquarz, Eis | Schulden und Pfand (FSP-RV) |
| 9 | eisenkrone → feldspat | supply_agreement | Maschinen und Energie für den Bergbau | Mahnungen |
| 10 | eisenkrone → lichtacker | supply_agreement | Energie, Industriegüter für Myrrhen/Tauvel | Teilkündigung Energie → Emberline |
| 11 | corvane → eisenkrone | supply_agreement | Medizin, Robotik für Bergbau | Robotik an Hande, Konflikt mit Cindervale (K1, V39) |
| 12 | eisenkrone → corvane | joint_venture | Rohstoffe und Industriegüter für Halcyon | Vorkaufsrecht, Abmahnung |
| 13 | lichtacker → corvane | supply_agreement | Lebensmittel, Bioproben | Exklusivlieferung, Storno |
| 14 | helix → corvane | logistics_partnership | optional (p = 0,6), im Bestand gezogen | bleibt optional (sonst ändert sich ein `rng.random()`-Zug) |

**Neue Firma → Bestandsfirma (7)**

| # | Verkäufer → Käufer | Typ | Plausibilität | Spielspaß |
|---|---|---|---|---|
| 15 | graufalk → helix | supply_agreement | Rumpfplatten und Triebwerksteile für die Helix-Flotte; 40 Helix-Lieferungen mit Triebwerksschaden | Eilabrufe nach Triebwerksschaden (V36) |
| 16 | cindervale → eisenkrone | supply_agreement | KI-Leitsysteme und Robotik; Ausfälle in Förster (19, 36, 70) | Firmware-Gerücht, Aussetzung, Spionage |
| 17 | kuppelwerk → lichtacker | supply_agreement | Ersatz für die gebrochenen Verbundstahl-Lieferungen von Helix | Absage im Januar, Abschluss im April 2059 |
| 18 | emberline → corvane | supply_agreement | Helium-3 für Halcyon Works VI nach HMX-CTR-2058-0131/-2057-0014 | Sturmzuschlag Pellora |
| 19 | emberline → lichtacker | supply_agreement | Energie für Agrarstation Seip nach drei Eisenkrone-Brüchen | Dreikampf um Energie in Myrrhen |
| 20 | raureif → eisenkrone | supply_agreement | Volatile für die Schwerindustrie, Konkurrenz zu Feldspat | Preisdruck nach Fund 52 |
| 21 | ravenmoor → helix | logistics_partnership | Grenzlandversorgung der Kharon-Stationen; Piraten 16, 51, 74 | vom Gegner (Razzia 26) zum Schutzpartner |

**Innerhalb Team A (12)**

| # | Verkäufer → Käufer | Typ | Plausibilität / Spielspaß |
|---|---|---|---|
| 22 | cindervale → graufalk | supply_agreement | Navigation und Sensorik für neue Schiffe / Werft als Upgrade-Ziel |
| 23 | graufalk → cindervale | strategic_alliance | Triebwerksteile für die Robotikfertigung / Allianz mit Geheimhaltungsklausel |
| 24 | emberline → graufalk | supply_agreement | Fusionsbrennstoff für Probefahrten / Grundlast-Route Pellora–Orrin |
| 25 | graufalk → emberline | supply_agreement | Schöpfschiff-Teile / Werftaufträge nach Stürmen |
| 26 | kuppelwerk → graufalk | supply_agreement | Glaskeramik, Bauteile für Docks / Massengut |
| 27 | emberline → kuppelwerk | supply_agreement | Energie für Sinteröfen / kurzer sicherer Weg |
| 28 | emberline → cindervale | supply_agreement | Energie für Rechenzentren / stabile Nachfrage |
| 29 | cindervale → kometenpost | consignment | Technik in Kommission / kleine, teure Fracht |
| 30 | kometenpost → cindervale | logistics_partnership | Expresslieferungen an Forschung / Kurier-Missionen |
| 31 | cindervale → lanternfish | supply_agreement | Elektronik für Immersionskapseln / Luxus-Spekulation |
| 32 | lanternfish → graufalk | supply_agreement | Komfortgüter für Werftarbeiter in Orrin / Grund, Orrin zu besuchen |
| 33 | lanternfish → kometenpost | consignment | Komfortgüter für Kuriere in Sol / gesprächige Pilotinnen und Piloten |

**Innerhalb Team B (12)**

| # | Verkäufer → Käufer | Typ | Plausibilität | Spielspaß |
|---|---|---|---|---|
| 34 | raureif → pionierwerk | supply_agreement | Wasser- und Stickstoffeis, Treibstoff für Isolde | lange Massengut-Routen Vaskar–Isolde (283 Einheiten) |
| 35 | pionierwerk → morgengrund | supply_agreement | Lebenserhaltung, Polymere, Habitatmodule (über Pionierwerk, siehe KHB-Exklusivität) | Notlieferung nach Ernteausfall |
| 36 | morgengrund → pionierwerk | supply_agreement | Lebensmittel für die Bautrupps | kleiner, fairer Partner für Einsteiger |
| 37 | ravenmoor → pionierwerk | logistics_partnership | Drohnen, Sensoren, Feldbedarf für Baustellen | Geleit zu neuen Kolonien |
| 38 | pionierwerk → ravenmoor | supply_agreement | Module und Bauteile für Bastionen | Bastionsausbau |
| 39 | outmark → pionierwerk | licensing | Vermessungsdaten, Sensoren | Daten schalten Serravel frei |
| 40 | second_hull → pionierwerk | supply_agreement | Recyclingmetall | billig, aber aus Nyx (Risiko) |
| 41 | second_hull → ravenmoor | consignment | aufbereitete Rumpfplatten | wäscht Second Hull Driftwood-Ware? |
| 42 | raureif → ravenmoor | supply_agreement | Treibstoff für die Geleitflotte, Freihafen Vaskar | Schwarzmarkt im Freihafen |
| 43 | ravenmoor → outmark | logistics_partnership | Expeditionsversorgung | Begleitung von Expeditionen |
| 44 | morgengrund → ravenmoor | supply_agreement | Rationen für Kharon/Brennus (Nahrung in Kharon heute 0 Angebote bei 20 Nachfragen) | Lücke wird sichtbar geschlossen |
| 45 | outmark → raureif | supply_agreement | Bergbaudrohnen, Sensorarrays | Fundorte als Spionageziel |

**Teamübergreifend (3)**

| # | Verkäufer → Käufer | Typ | Plausibilität / Spielspaß |
|---|---|---|---|
| 46 | kuppelwerk → pionierwerk | supply_agreement | Habitatmodule für Isolde/Serravel / Großfracht als Fortschrittsziel |
| 47 | second_hull → graufalk | supply_agreement | Recyclingmetall für die Werften / Brücke vom Rand in den Kernraum |
| 48 | graufalk → ravenmoor | supply_agreement | Geleitschiff-Teile / Vorkaufsrecht verschärft die Rivalität Ravenmoor ↔ Helix |

### 3.2 Zählung (beide Richtungen, eigenes Skript)

| Firma | Größe | Vereinb. | aus | ein | Partner | erlaubt | frei |
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
| **Summe** | | **96 = 2 × 48** | 48 | 48 | | | 16 |

- **Hub**: Die QA sortiert nach `distinct_partners`, dann `active_agreements`. Helix liegt vorn (7/10). Ohne `helix → corvane`
  (anderer Seed) hätte Helix 7/9 und läge gleichauf mit Graufalk. Bei Gleichstand bleibt die Reihenfolge nach `company_id`
  (Helix 6 vor Graufalk 7). Der Hub ist in jedem Fall eine große Firma, die QA-Prüfung ist also immer erfüllt.
- **Nur über Zwischenhändler verbunden (Auswahl)**: Feldspat ↔ Raureif (über Eisenkrone), Driftwood ↔ Ravenmoor (über
  Helix), Lichtacker ↔ Pionierwerk (über Kuppelwerk), **Morgengrund ↔ Kuppelwerk (über Pionierwerk)**: Die
  Habitatmodule für die Siedler laufen wegen der Exklusivität von Kuppelwerk in Isolde zwingend über Pionierwerk.
  Weitere Beispiele sind Feldspat ↔ Corvane und Helix ↔ Morgengrund (über Ravenmoor). Abstand 4 haben Kometenpost ↔
  Driftwood, Pionierwerk, Outmark und Morgengrund.
- **Reserve** für spätere Spielereignisse (neue Partnerschaft nach einer Mission): Cindervale 3, Outmark 3, Driftwood 2,
  Kuppelwerk 2, Raureif 2, Pionierwerk 2, Ravenmoor 2, Eisenkrone 1, Graufalk 1.

### 3.3 Verbraucherprüfung (Ware ↔ Stationstyp)

Geprüft wurde jede der 48 Kanten. Der Anteil des Warengewichts des Verkäufers (Bestand: Anteil der handelbaren Produkte je
Kategorie, neue Firmen: `category_weights`), für den der Käufer einen Verbraucher-Stationstyp hat. Bei Bestandsfirmen
zählen die echten Stationen, bei neuen nur `required_stations`, also das sichere Minimum.

| Kante | Anteil | Begründung |
|---|---:|---|
| pionierwerk → morgengrund | 0,52 | Morgengrund hat sicher nur eine Agrarstation: Industriegüter, Energie, Medizin passen, Technik/Lebensmittel/Rohstoffe nicht → K11 |
| helix → eisenkrone | 0,67 | Luxus wird an `industrial`/`mining` nicht verbraucht (Bestand, unverändert) |
| eisenkrone → lichtacker | 0,72 | Bestand, unverändert |
| kuppelwerk → lichtacker | 0,75 | Rohstoffe gehen nicht an Agrar/Forschung. Die Industriegüter (55 %) passen. |
| emberline → lichtacker | 0,80 | Energie passt an `agricultural` |
| alle anderen 43 | ≥ 0,88 | |

Jede Kante erreicht damit die ≥ 4 Partnerrouten aus `plan_markets` (`MIN_PARTNER_ROUTES_PER_AGREEMENT`).

---

## 4. Historische (beendete) Partnerschaften

| Verkäufer → Käufer | Typ | Zeitraum | Story-Hook (Plausibilität) | Spielspaß |
|---|---|---|---|---|
| corvane → driftwood | supply_agreement | 2057-04-27 – 2058-07-17 (Bestand) | Bruch → Rivalität Driftwood ↔ Corvane | Rezeptur-Spionage |
| eisenkrone → graufalk | supply_agreement | 2039-01-01 – 2049-06-30 | Ausgliederung der Werftsparte Orrin, Patentstreit Reaktorkomponenten | „offene Rechnung“ → Rivalität seit 2049-07-01 |
| cindervale → helix | licensing | 2041-04-01 – 2054-03-31 | Lizenzverlust erklärt, warum Helix Hochtechnik aus Kharon holt (und warum die Verträge platzen) | Rivalität Sol ab dem Tag danach |
| lichtacker → pionierwerk | supply_agreement | 2045-03-01 – 2053-06-30 | Versorgung der Isolde-Bautrupps bis zum Pachtstreit | Erklärt, warum Lichtacker Isolde im Territorium hat, aber nicht baut |
| emberline → eisenkrone | supply_agreement | 2047-02-01 – 2056-06-30 | Helium-3 für Hande, endet mit Eisenkrones eigener Deuteriumförderung | Rückkehr nach Myrrhen als Rivale |
| outmark → feldspat | licensing | 2055-02-01 – 2058-06-30 | Vermessungsdaten Brennus; ein Jahr später Fund 52 bei Becker | Claim-Streit, Datendiebstahl |
| driftwood → second_hull | consignment | 2057-05-01 – 2058-07-01 | Bergegut aus Nyx; Bruch zwei Tage nach Razzia 26 | Verdacht der Geldwäsche |

Alle Daten liegen nach `founded_year` + 1 beider Firmen und enden vor dem Datenfenster des Käufers bzw. vor dem
Ankerereignis. Es gibt keine Kollision mit `UNIQUE(company_id, partner_company_id, relationship_type)`. `trust_level`
(3–15) und `contract_volume` würfelt der Erweiterungsstrom. Bestandszeile 15 behält `partnership_id` 15. Neue
Partnerschaften (aktiv und historisch) kommen erst danach.

---

## 5. Rivalitäten und Spionage-Potenzial

| Firma → Rivale | Typ | System | seit | Int. / Spion. | Anker (Bestand) | Informanten (ID, Loyalität/Bestechlichkeit) | Spielspaß |
|---|---|---|---|---|---|---|---|
| eisenkrone → helix | market_dominance | sol | Bestand | Bestand | – | – | Partner und Rivale |
| driftwood → corvane | industrial_espionage | halcyon | Bestand | Bestand | – | – | Rezepturen |
| feldspat → driftwood | territorial_claims | kharon | Bestand | Bestand | – | – | Claims |
| lichtacker → eisenkrone | resource_competition | myrrhen | Bestand | Bestand | – | – | Wassereis |
| graufalk → eisenkrone | market_dominance | halcyon | 2049-07-01 | 70 / 55 | Ausfälle Förster 19/36/70, EKM-VTR-2057-0064 | Esther Bauer 170 (53/76), Annekatrin Schuchhardt 178 (85/25) | Bauer ist käuflich, Schuchhardt kennt die Protokolle |
| cindervale → helix | market_dominance | sol | 2054-04-01 | 65 / 50 | Booms 3/24, HMX-CTR-2057-0050, -2058-0121 | Desiree Schwartz 299 (ab 2059-11-24, 58/78), Richard Chavez 120 (53/76) | Lecks über Supraleiter-Engpass |
| emberline → eisenkrone | resource_competition + Override „Energie“ | myrrhen | 2058-08-15 | 55 / 40 | EKM-VTR-2058-0099, -0105, -2059-0167 | Polina Zahn 83 (55/88), Hans-Werner Eberhardt 45 (75/23) | Wechsel des Energielieferanten |
| lichtacker → pionierwerk | territorial_claims + Override „Pacht“ | isolde | 2053-07-01 | 60 / 55 | Ende der historischen Lieferung | Kaspar Täsche 43 (55/61, greedy) | Isolde-Freischaltung mit Konflikt |
| ravenmoor → driftwood | **armed_conflict** (neu, 60–90) | nyx | 2058-06-30 | 85 / 70 | Razzien 26/58, Piraten 45/54/57/67 | Carlos Osborne 29 (3/100), Nathan Hines 33 (36/81) | Wer hat die Razzia verraten? |
| outmark → feldspat | territorial_claims | brennus | 2059-07-14 | 65 / 80 | Fund 52 bei Becker (critical, 240 Tage) | Slavko Geisel 16 (55/96) | Datenkauf, Claim-Beweise |
| ravenmoor → helix | market_dominance | kharon | 2057-11-17 | 55 / 45 | Piraten 16, Razzia 26 | Wayne Jacobson 302 (48/73), Tyler Garcia 395 (ab 2058-01-05), Brandon Jones 445 (38/89) | Schutzpartner mit eigener Agenda |
| second_hull → driftwood | territorial_claims | nyx | 2058-07-01 | 50 / 40 | Piraten 54, Ende der Kommission | Douglas Lawson 27 (57/61) | Wrackrechte in Nyx |

Driftwood hat damit 4 Rivalen und ist der Außenseiter. Das passt zur Schmuggelfirma und bietet dem Spieler die meisten
Gelegenheiten für Spionage. Eisenkrone hat 4 Rivalen (Helix, Graufalk, Emberline, Lichtacker) und ist der Gegenspieler im
Kernraum. `UNIQUE(company_id, rival_company_id)` ist eingehalten. `armed_conflict`-Text wie in `phase1_team_b.md` 4.4.

---

## 6. Rahmenverträge

### 6.1 Wann ein Rahmenvertrag entsteht (Plausibilität und Spielspaß)

1. **Bestandspaare mit vielen Abrufverträgen** (≥ 35): Hier ist der Rahmen die nachträgliche Erklärung für Hunderte
   vorhandener Verträge. Die Bestandszeilen bleiben unverändert, neu ist nur `contracts.framework_agreement_id`.
2. **Neue Paare mit Dauerbedarf** (Energie, Volatile, Module, Geleitschutz, Rationen). Kommission, Lizenzen und kleine
   Lieferanten (Driftwood, Lanternfish, Kometenpost, Second Hull) bleiben ohne Rahmen. Dort macht der Spieler Spot-Geschäfte.
3. Ein Rahmen entsteht nur, wenn er eine **Geschichte mit Datenfolge** trägt. Beispiel: Bruch → Nachtrag →
   neuer Lieferant → neue Routen.

### 6.2 Datenmodell (vereinigt, wie in `verknuepfungen.json`)

- `framework_agreements`: Nummer, `partnership_id`, `company_id` (Verkäufer), `partner_company_id` (Käufer), Titel (Sprache
  des Verkäufers), Unterzeichnung, Beginn, Laufzeit, ursprüngliches und aktuelles Ende, Status
  (`negotiating/active/suspended/expired/terminated`), Basisvolumen und aktuelle Obergrenze, `price_formula`
  (`fixed/index_linked/cost_plus/market_minus`), `indexation` (`none/category_price_index/fuel_index/risk_index`),
  Rabatt/Aufschlag/Anpassungsdeckel, `exclusivity`
  (`none/right_of_first_refusal/buyer_exclusive/seller_exclusive/mutual/regional_exclusive`) mit System,
  Kündigungsfrist, Auto-Verlängerung, Strafsatz, `escort_company_id`, Unterzeichner beider Seiten.
- `framework_agreement_scope`: Kategorie, optional Archetyp und System, gültig von/bis, `is_exclusive`, hinzugefügt bzw.
  entfernt durch Nachtrag. So entstehen „neue Waren“ und „Exklusivklausel“ als Zeilen statt als Freitext.
- `framework_amendments`: 17 Typen (`volume_increase`, `volume_reduction`, `product_addition`, `product_removal`,
  `price_adjustment`, `term_extension`, `exclusivity_clause`, `exclusivity_waiver`, `penalty_clause`,
  `service_level_clause`, `escort_clause`, `force_majeure_clause`, `competition_clause`, `confidentiality_clause`,
  `scope_extension`, `partial_termination`, `suspension`), Status `proposed/signed/rejected/withdrawn`, Auslöser
  (`trigger_contract_id`, `trigger_order_id`, `trigger_event_id`). Nummern `{Rahmen}/N{k}` (de) bzw. `/A{k}` (en).
- `contracts.framework_agreement_id` (NULL = außerhalb).

### 6.3 Wie Einzelverträge am Rahmen hängen (deterministisch, nachgeprüft)

Ein Vertrag gehört zum Rahmen, wenn alle Bedingungen erfüllt sind: gleiches Paar, `contract_type` in `framework`,
`recurring_supply` oder `exclusive_supply`, `start_date` zwischen Rahmenbeginn und dem **zu diesem Datum** gültigen Ende
(Verlängerungen zählen ab Wirksamkeit), Kategorie bzw. Archetyp am `start_date` im Scope (Hinzufügungen, Herausnahmen und
Teilkündigungen ab Wirksamkeit). `spot`, `emergency_supply` und `consignment` bleiben außerhalb. Sie sind die Spot-Geschäfte
neben dem Rahmen.

Regel-Nachträge: (a) Monatserster vor dem ersten Abruf einer neuen Kategorie → `product_addition`. (b) Kumulierte Summe
ohne Stornos > 90 % der Obergrenze → `volume_increase` zum Monatsersten des auslösenden Vertrags, Auslöser 2060 →
`proposed`. (c) Abruf nach Laufzeitende → `term_extension`, wirksam 60 Tage vor Ablauf.

**Nachprüfung am Bestand (eigenes Skript):**

| Rahmen | Paar | erwartet | berechnet | Summe ohne Storno (Mio. CR) | Volumen-Auslöser reproduziert |
|---|---|---:|---:|---:|---|
| HMX-MSA-2057-01 | helix → lichtacker | 54 | 54 | 423,6 | HMX-CTR-2058-0161 (227,9 > 225), HMX-CTR-2059-0259 |
| HMX-MSA-2057-02 | helix → corvane | 68 | 68 | 549,4 | HMX-CTR-2058-0152, -2059-0213, -2060-0281 |
| HMX-MSA-2057-03 | helix → eisenkrone | 75 | 75 | 438,7 | HMX-CTR-2059-0192, -2059-0236, -2060-0275 |
| EKM-RV-2057-01 | eisenkrone → corvane | 65 | 65 | 440,9 | EKM-VTR-2059-0160, -2060-0219 |
| EKM-RV-2057-02 | eisenkrone → helix | 39 | 39 | 275,9 | EKM-VTR-2059-0151, -2060-0234 |
| EKM-RV-2057-03 | eisenkrone → lichtacker | 35 | 35 | 178,0 | EKM-VTR-2059-0211; außerhalb EKM-VTR-2060-0230 (nach Teilkündigung) |
| FSP-RV-2059-01 | feldspat → eisenkrone | 5 | 5 | 2,6 | –; außerhalb FSP-VTR-2059-0001/-0005 (vor Beginn) |
| **Summe** | | **341** | **341** | **2.309,1** | 12 von 12 |

### 6.4 Die 21 Rahmenverträge

| Nr. | Paar | Beginn, Laufzeit | Basis (Mio. CR) | Preis / Index | Exklusivität | Kündigung (T) | Nachträge |
|---|---|---|---:|---|---|---:|---:|
| HMX-MSA-2057-01 | helix → lichtacker | 2057-01-01, 36 M | 250 | index_linked / category | Vorkaufsrecht Industriegüter, entfällt 2059-03-15 | 180 | 7 |
| HMX-MSA-2057-02 | helix → corvane | 2057-01-01, 36 M | 300 | market_minus −4 % / category | Energie käuferexklusiv 2057-05-01 bis 2059-03-15 | 120 | 10 |
| HMX-MSA-2057-03 | helix → eisenkrone | 2057-01-01, 48 M | 300 | cost_plus 9 % / category | – | 360 | 5 |
| EKM-RV-2057-01 | eisenkrone → corvane | 2057-01-01, 60 M | 350 | cost_plus 12 % / category | Vorkaufsrecht Rohstoffe | 360 | 5 |
| EKM-RV-2057-02 | eisenkrone → helix | 2057-01-01, 42 M | 200 | index_linked (raw) ±10 % | – | 180 | 8 |
| EKM-RV-2057-03 | eisenkrone → lichtacker | 2057-01-01, 36 M | 150 | index_linked (energy) ±6 % | – | 90 | 7 |
| FSP-RV-2059-01 | feldspat → eisenkrone | 2059-08-01, 24 M | 12 | market_minus −5 % | Vorkaufsrecht Quantenquarz | 90 | 2 |
| GFW-RV-2057-01 | graufalk → helix | 2057-01-01, 48 M | 180 | index_linked (industrial) | – | 180 | 3 |
| GFW-RV-2057-02 | graufalk → cindervale | 2057-01-01, 60 M | 220 | cost_plus 8 % | ab 2058-03-15 gegenseitig: drive_parts / nav_computers | 365 | 3 |
| GFW-RV-2058-01 | graufalk → ravenmoor | 2058-07-15, 36 M | 90 | index_linked | Vorkaufsrecht hull_plating Kharon | 180 | 2 |
| CCI-MSA-2057-01 | cindervale → eisenkrone | 2057-01-01, 48 M | 120 | fixed | **Vorkaufsrecht** Technik Halcyon (K1) | 180 | 3, Status `suspended` |
| KHB-RV-2058-01 | kuppelwerk → pionierwerk | 2058-06-01, 36 M | 70 | cost_plus 10 % / fuel | verkäuferexklusiv Habitatmodule Isolde | 180 | 2 |
| KHB-RV-2059-01 | kuppelwerk → lichtacker | 2059-04-01, 24 M | 30 | cost_plus 10 % / fuel | Myrrhen-Exklusivität angeboten (offen) | 90 | 3 |
| EFF-MSA-2059-01 | emberline → corvane | 2059-04-01, 24 M | 40 | index_linked / fuel | Helium-3 Halcyon angeboten (offen) | 90 | 3 |
| EFF-MSA-2059-02 | emberline → lichtacker | 2059-11-15, 24 M | 18 | index_linked / fuel | Vorkaufsrecht Energie Myrrhen ab 2060-01-18 | 90 | 1 |
| RCS-MSA-2058-01 | ravenmoor → helix | 2058-08-01, 36 M | 90 | cost_plus 15 % / risk | regional: escort_drones, sensor_arrays Kharon | 90 | 3 |
| RVF-RV-2058-01 | raureif → pionierwerk | 2058-01-01, 36 M | 80 | index_linked / fuel | regional: water_ice ab Beginn, nitrogen_ice ab 2058-09-01 (K7) | 180 | 3 |
| RVF-RV-2058-02 | raureif → eisenkrone | 2058-03-01, 24 M | 45 | index_linked (raw), Mindestpreis | – | 90 | 2 |
| OSP-MSA-2058-01 | outmark → pionierwerk | 2058-02-01, 36 M | 25 | fixed | regional: survey_charts Serravel ab 2059-08-15 | 180 | 2 |
| SGM-RV-2059-01 | morgengrund → pionierwerk | 2059-01-01, 12 M + Auto 12 M | 5 | fixed, Ernteklausel | – | 60 | 2 |
| SGM-RV-2059-02 | morgengrund → ravenmoor | 2059-03-01, 12 M | 6 | fixed, Ernteausfallklausel | – | 60 | 2 |

**Spätere Erweiterung (Beispiele, alle im JSON):** Volumenerhöhung nach > 90 % Auslastung (12 Auslöser im Bestand), neue
Waren per `product_addition` (erste Abrufe je Kategorie), Preisanpassung (CCI −8 % nach Ausfall 36, RVF −6 % nach Fund 52,
FSP +12 % nach Booms 65/66, Rettungsangebot EKM −5 % abgelehnt), Verlängerung (vier Rahmen zum 2060-12-31, drei offen),
Exklusivklausel (HMX → Corvane Energie, GFW ↔ CCI, OSP Serravel, angeboten KHB Myrrhen und EFF Helium-3) und deren Wegfall
(HMX → Lichtacker nach drei Verbundstahl-Brüchen).

**Spielwert zum Spielstart (17 offene Nachträge):** Der Spieler findet laufende Verhandlungen vor, in die er eingreifen
kann. Beispiele: die dreiseitige Geleitschutzklausel Eisenkrone–Helix–Ravenmoor, die Eilabrufklausel Triebwerksteile, die
Geheimhaltungsklausel Graufalk–Cindervale, die Myrrhen-Exklusivität von Kuppelwerk und die Volumenerhöhung für den
Schuldenabbau bei Feldspat (K10).

### 6.5 Korrekturen an den Rahmenverträgen

- **K1 – CCI-MSA-2057-01: Käuferexklusivität widerspricht dem Bestand.** Eisenkrone soll Technik für Halcyon nur bei Cindervale
  beziehen. Im Bestand liefert Corvane aber 5 Technikverträge und 25 Bestellungen an die Bergbaustation Hande (Halcyon):
  CVB-CTR-2058-0003 (Elektronik), -2058-0013 und -2058-0038 (Navigationscomputer), -2059-0044 (Robotik) und
  **CVB-CTR-2059-0066** (Exklusivlieferung Robotik, ab 2059-08-24, 3,22 Mio. CR). → `right_of_first_refusal` auf Technik
  in Halcyon. Spielwert: Der Exklusivvertrag mit Corvane übergeht Cindervales Vorkaufsrecht. Daraus entsteht der neue
  Vorgang V39 (Abschnitt 7.5), der die Aussetzung im Dezember (V31) vorbereitet.
- **K2 – Geleitschutzklausel EKM-RV-2057-02: falsche Anker.** EKM-VTR-2057-0017 und -2059-0162 sind wegen **Andockstau**
  gebrochen, nicht wegen Piraten. Die echten Geleitschutzbrüche des Paares Eisenkrone → Helix sind **EKM-VTR-2057-0043**
  (Hande → Munoz Landing) und **EKM-VTR-2058-0107** (Hande → Kharon Exchange IX). Diese beiden werden Anker der
  Geleitschutzklausel. Die zwei Andockstau-Brüche begründen einen zweiten Teil derselben dreiseitigen Klausel:
  Ausweich-Liegeplätze an Ravenmoors Handelsstation in Kharon. Damit bekommt die Klausel einen echten Nutzen für beide
  Probleme, und Ravenmoors Pflichtstation `trade_hub` in Kharon bekommt eine Aufgabe.
- **K6 – GFW-RV-2057-01, Eilabrufklausel:** Angeboten am 2059-12-28 mit Bezug auf HMX-ORD-2059-01788, das aber erst am
  2059-12-29 bestellt wird und am 12-30 abfliegt. → `proposed_date` 2059-12-31. Der Anlass passt: Beide Lieferungen haben
  einen Triebwerksschaden (HMX-SHP-2059-01721 „Drive malfunction, emergency repair en route (+99 h)“, HMX-SHP-2059-01746
  „(+38 h)“).
- **K7 – RVF-RV-2058-01:** `nitrogen_ice` stand ab Beginn in der Exklusivität, obwohl der Nachtrag vom 2058-09-01 sie erst
  einführt. → Basis-Exklusivität nur `water_ice`. Der Nachtrag ist jetzt `exclusivity_clause` (Stickstoffeis ist über die
  Kategorie schon im Scope).
- **K9 – HMX-MSA-2057-02** nur anlegen, wenn `helix → corvane` im Bestandsstrom gezogen wird (Seed 42: ja). Sonst fehlt
  die Partnerschaft für `partnership_id`.
- **K10 – Schuldenstand Feldspat nach Datum** (Fälligkeit = Ankunft + 30 Tage): 2059-07-20: 11 Bestellungen, 22,94 Mio. CR;
  2059-08-01: 12, 24,22 Mio. CR; ab 2059-09-23: 13, **25,52 Mio. CR**. Das Angebot V22 nennt 22,94 Mio., die Unterschrift
  24,22 Mio. Der offene Nachtrag „Volumen 20 Mio.“ (Auslastung erst 22 %) ist ausdrücklich ein Schuldenabbau-Angebot von
  Feldspat, keine Regel-Erhöhung.

### 6.6 K8 – Sperrfristen für neue Verkäufer (Filter in Durchlauf 2)

Exklusivitäten dürfen nicht schon durch die Erweiterung verletzt werden, sonst erzeugt der Generator unkontrolliert
`breach_warning`-Schreiben. Diese Filter gelten für Verträge **und** Partnerbestellungen der neuen Verkäufer:

| Verkäufer → Käufer | gesperrt | Zeitraum | Grund |
|---|---|---|---|
| emberline → corvane | Kategorie `energy` | bis 2059-03-14 | HMX-MSA-2057-02: Energie käuferexklusiv |
| kuppelwerk → lichtacker | Kategorie `industrial_goods` | bis 2059-03-14 | Vorkaufsrecht Helix, Absage V14 |
| graufalk → helix | `sensor_arrays` an Kharon-Stationen | ab 2058-08-01 | RCS-MSA-2058-01 regional exklusiv |
| emberline, kometenpost → cindervale | `drive_parts` | ab 2058-03-15 | GFW ↔ CCI gegenseitig |
| emberline, lanternfish, second_hull → graufalk | `nav_computers` | ab 2058-03-15 | GFW ↔ CCI gegenseitig |
| second_hull, outmark, morgengrund → pionierwerk | `water_ice` an Isolde | ab 2058-01-01 (`nitrogen_ice` ab 2058-09-01) | RVF-RV-2058-01 regional exklusiv |

Vorkaufsrechte bleiben ohne Filter. Verstöße dagegen sind erlaubt und können als Schreiben erzählt werden (V39).

---

## 7. Schriftverkehr

### 7.1 Briefarten, Auslöser, Absender (20)

| Briefart | Auslöser (Daten) | Absender → Empfänger (Rolle) | Spielspaß |
|---|---|---|---|
| inquiry | 30–60 T vor Rahmenbeginn; Nachtragswunsch; Lücke im Angebot | Partnerbetreuung Käufer → Partnerbetreuung Verkäufer | Vorlauf, den der Spieler abfangen kann |
| offer | Antwort auf inquiry (+3..10 T) oder Kaltangebot | Partnerbetreuung Verkäufer | Preisinformation (intel_value) |
| counter_offer | 0–2 Runden, 2 bei trust < 60 | Partnerbetreuung | Verhandlung sichtbar |
| offer_rejection | Absage auf Angebot oder Entwurf (`draft`) | Partnerbetreuung / Vorstand | Gelegenheit für Konkurrenten |
| contract_confirmation | Unterschrift Rahmen; `exclusive_supply` | Vorstände bzw. Partnerbetreuung | – |
| amendment_offer / _confirmation / _rejection | jeder Nachtrag am `proposed_date` / bei `signed` (−7..0 T) / bei `rejected` | Initiator / Gegenseite | offene Nachträge zum Spielstart |
| delivery_notice | Abruf ≥ 1 Mio. CR; offene Bestellungen zum Stichtag | Logistik der Herkunftsstation | Frachtfenster |
| delay_notice | Lieferung mit `risk_incident` | Logistik / Stationsleitung Herkunft | Gerüchte über Piraten |
| delay_complaint | Abruf > 48 h verspätet, `breached`, Bestellung `delayed` (Ankunft +0..3 T) | Stationsleitung Ziel | Beziehungsschaden |
| penalty_notice | `breached`; Betrag = Verzugstage × `penalty_per_day` (letzte Ankunft +3..14 T) | Finanzen; > 250.000 CR Vorstand | Strafsummen = `contract_penalties` |
| payment_reminder | `overdue`; Fälligkeit = Ankunft + 30 T; Stufen +3..7 / +21 / +45 T | Finanzen → Finanzen | Schuldenstory (Feldspat) |
| breach_warning | Verstoß gegen Exklusivität/Gewährleistung; erzählte Verstöße gegen Vorkaufsrecht | Partnerbetreuung / Vorstand | Eskalationsstufe |
| termination_notice | `partial_termination`, Ende historischer Partnerschaft, Androhung | Vorstand | Wendepunkte |
| suspension_notice | Nachtrag `suspension` | Vorstand | CCI-Aussetzung |
| protest | Razzia, Claim-Streit | Vorstand → Vorstand des Rivalen | Rivalität wird sichtbar |
| confidential_tip | Mitarbeiter mit Bestechlichkeit ≥ 70 oder greedy/talkative verrät Wissen | Leck → Rivale | Spionageziel |
| rumor | wie oben, Wahrheitsgehalt offen | beliebig, Quelle über `refers_to_correspondence_id` | Wahr, offen oder falsch (30/50/20 %) |
| internal_memo | Ereignis an eigener Station mit Partnerbezug; Strafe > 250.000 CR | intern | Einblick per Spionage |

### 7.2 Tabelle `correspondence` (Felder)

`correspondence_id` PK · `reference_number` UNIQUE (`{SKU}-KOR-{Jahr}-{nnnnn}` de, `{SKU}-COR-…` en) · `letter_type` ·
`thread_id` (erstes Schreiben des Vorgangs) · `in_reply_to_id` · `refers_to_correspondence_id` (Quelle eines Lecks) ·
`sent_at` (< 2060-01-01) · `read_at` (NULL = ungelesen zum Stichtag, also Posteingang des Spielstarts) ·
`sender_company_id` NOT NULL · `sender_employee_id` (NULL nur bei anonymem Gerücht) · `sender_station_id` ·
`recipient_company_id` · `recipient_employee_id` · `recipient_customer_id` (Nicht-Firmenkunden) · `language`
(Absenderfirma) · `subject` · `body` · `confidentiality` (`public/business/confidential/secret` =
`intel_access_level` 0–3) · `tone` (`cordial/neutral/firm/hostile`) · `amount` · `due_date` · `response_required` ·
`status` (`sent/read/answered/rejected/escalated/closed`) · `trust_effect` (−20..10) · `is_accurate` (nur Tipp/Gerücht) ·
`intel_value` (0–100, Preis für den Spieler) · `leak_status` (`none/rumored/leaked`) · `leaked_by_employee_id` ·
`leaked_to_company_id` · Fachbezüge: `partnership_id`, `framework_agreement_id`, `amendment_id`, `contract_id`,
`order_id`, `shipment_id`, `event_id`, `rivalry_id`.

**Verknüpfungen:** Vorgang über `thread_id`/`in_reply_to_id`. Fachlich hängt jedes Schreiben an genau den vorhandenen
Schlüsseln: ein Strafbescheid an `contract_id` (und an `framework_agreement_id`, falls zugeordnet), eine Mahnung an
`order_id`, ein Lieferavis an `shipment_id`, ein Nachtragsangebot an `amendment_id`. Die Parteien von Vertrag,
Bestellung oder Rahmen sind genau Absender- und Empfängerfirma. Ausnahmen sind `confidential_tip`, `rumor`,
`internal_memo` und `protest`. Mitarbeiter sind über `sender_employee_id`/`recipient_employee_id` angebunden und müssen am
`sent_at` beschäftigt sein (`hire_date ≤ sent_at < termination_date`). Ersatzreihenfolge: executive → relations →
station_manager. Feldspat hat vor 2057-11-22 und Eisenkrone vor 2059-07-07 keinen Vorstand. Dann zeichnen Mikhail
Gotthard (2) bzw. Esther Bauer (170).

**Spionage:** Leck-Wahrscheinlichkeit = `espionage_risk/100 × bribe/100 × (1 − loyalty/150)`. Der Leck-Pool sind
aktive Mitarbeiter mit `intel_access_level` ≥ Stufe der Vertraulichkeit. Strom: `random.Random(f"{seed}:correspondence")`,
der nach allen anderen Schritten läuft. So bleibt der Bestand unberührt.

### 7.3 Prüfergebnisse

- Alle 7 Strafbeträge der Vorgänge stimmen mit der Formel aus `generate_financials` überein: 303.807,21 · 219.444,96 ·
  653.162,16 · 332.508,95 · 314.166,60 · 58.589,66 · 60.719,68 CR. Alle Beschwerden liegen 0–1 Tage nach der letzten
  Ankunft, alle Strafbescheide 5–9 Tage danach.
- Alle 91 Personen-Datums-Paare in V1–V38 sind gültig, dazu die 14 Informanten-Zuordnungen der Rivalitäten (Firma stimmt,
  am Datum beschäftigt; Erkan Hesse 39 ist bis 2059-06-11 beschäftigt und wird nur im Januar 2059 genutzt).
- **Fehler bei den Mahnfristen (K3–K5)** und **ein Schreiben vor seinem Bezugsobjekt (K6)**, siehe 7.4.

### 7.4 Korrekturen an den verankerten Vorgängen

| # | Vorgang | Problem (Bestand) | Korrektur |
|---|---|---|---|
| K3 | V27 Sammelmahnung 2. Stufe, 2059-09-10, EKM-BST-2059-01903 + 12 weitere, 25,5 Mio. | 01903 kommt am 2059-08-24 an und ist erst am **2059-09-23** fällig. Am 09-10 sind nur 12 Bestellungen (24,22 Mio.) überfällig. | Datum **2059-10-14** (Fälligkeit 01903 + 21 T), 13 Bestellungen, 25.522.655,14 CR |
| K4 | V1 Mahnungen 1–3 zu EKM-BST-2057-00352 am 08-28 / 09-11 / 09-27 | Ankunft 2057-07-24, fällig 2057-08-23. Die Stufen +21/+45 sind nicht eingehalten. | **2057-08-28 / 2057-09-13 / 2057-10-07** |
| K5 | V32 3. Mahnung zu EKM-BST-2059-01408 am 2059-12-05 | Ankunft 2059-01-13, fällig 2059-02-12; Stufe 3 = 2059-03-29 | Datum **2059-03-29** |
| K6 | V36 Anfrage Eilabrufe, 2059-12-28, Kurt Sullivan 301 → Graufalk | HMX-ORD-2059-01788 entsteht erst 2059-12-29. Sullivan leitet Sol Exchange II, die Bestellungen starten in Kharon Landing IV bzw. Aurelis Gardens II. | Datum **2059-12-31**. Absender **Kayla Cannon 332** (Partnerbetreuung, schon in V12 Graufalk-Kontakt). Bezug: Triebwerksschäden HMX-SHP-2059-01721/-01746. |

### 7.5 Neuer Vorgang V39 (aus K1)

| Datum | Art | Absender → Empfänger | Bezug | Daten |
|---|---|---|---|---|
| 2059-08-28 | rumor (`is_accurate` = 1) | Richard Chavez 120 (Corvane, Marktaufklärung, talkative, Bestechlichkeit 76) → Cindervale Marktaufklärung | CVB-CTR-2059-0066 (Robotik exklusiv an Hande, 2059-08-24) | `leak_status` = leaked, `confidentiality` confidential |
| 2059-09-02 | breach_warning | Cindervale-Vorstand → Roswitha van der Dussen 168 (Vorstand seit 2059-07-07), cc Esther Bauer 170 | CCI-MSA-2057-01, Vorkaufsrecht Technik Halcyon | tone firm, `trust_effect` −8 |
| 2059-09-12 | Antwort (breach_warning, in_reply_to) | Esther Bauer 170 → Cindervale | Ausfälle 19/36 als Begründung, Hinweis auf Gewährleistungsklausel 2058-03-01 | tone firm |

Plausibilität: Eisenkrone weicht nach zwei KI-Ausfällen auf Corvane-Robotik aus. Spielspaß: Der Spieler kann Chavez' Leck
kaufen (Spionagekette Corvane → Cindervale), ahnt die Aussetzung im Dezember (V31) voraus und kann zwischen Eisenkrone und
Cindervale vermitteln oder auf einen Bruch spekulieren.

Die übrigen Vorgänge V2–V26, V28–V31, V33–V35, V37 und V38 bleiben wie in `phase2_entscheidung.md` 6.3. In V22 lautet der
Schuldenstand 22,94 Mio. CR (Angebot) bzw. 24,22 Mio. CR (Unterschrift), siehe K10.

### 7.6 Mengengerüst

Etwa 850 Schreiben zu Bestandsobjekten: Bestätigungen für die 96 `exclusive_supply`-Verträge und die 21 Rahmen,
Nachtragsschreiben für die 78 Nachträge, Beschwerden und Strafbescheide für die 80 gebrochenen Verträge, Mahnungen für
überfällige Bestellungen, Avise der offenen Bestellungen, Lecks nach der Formel. Für alle 18 Firmen kommen wir auf etwa
2.200–2.800 Schreiben. Das ist klein gegenüber den 93.648 Preispunkten.

---

## 8. Umsetzung und QA

### 8.1 Reihenfolge im Skript (Bestandsschutz)

1. Durchlauf 1 unverändert (6 Bestandsfirmen inklusive `OPTIONAL_PARTNERSHIPS`/`HISTORIC_PARTNERSHIPS`).
2. Durchlauf 2 (Team A): neue Firmen, Partnerschaften ab `partnership_id` 16, Rivalitäten, Routen, Verträge mit den
   Sperrfristen aus K8.
3. `generate_framework_agreements` (Team B): deterministisch für Bestandspaare (Zuordnungsregel 6.3, Prüfwerte im JSON),
   eigener Strom für die neuen Paare.
4. `generate_correspondence` (Team B): eigener Strom, Bestandsfirmen nur mit vorhandenen Mitarbeitern.

### 8.2 Neue QA-Prüfungen

- Zählung aus 3.2 (18 Firmen im Größenbereich, ≥ 1 ausgehend), Hub large, ≥ 2 Paare nur indirekt.
- 341 zugeordnete Bestandsverträge, 2.309,1 Mio. CR; EKM-VTR-2060-0230 und FSP-VTR-2059-0001/-0005 außerhalb.
- Volumen-Auslöser = die 12 Vertragsnummern aus 6.3.
- Keine Verletzung einer Exklusivität (nicht Vorkaufsrecht) durch neue Verkäufer (K8).
- Strafbescheide: Betrag = Formel, Summe je Firma und Monat = `contract_penalties`.
- Mahnungen frühestens Fälligkeit + 3 T (K3–K5). Kein Schreiben vor seinem Bezugsobjekt (`order_date`, `start_date`,
  `departure_date`, `event_date`) (K6).
- Absender und Empfänger am `sent_at` beschäftigt und in der richtigen Firma.
- **Ankerliste für den Bestandsvergleich (Antwort auf R2-1):** Verträge EKM-VTR-2057-0017, -2057-0043, -2058-0099,
  -2058-0107, -2059-0162, -2059-0167, HMX-CTR-2058-0131, -2058-0159, -2059-0242, CVB-CTR-2059-0066; Bestellungen
  EKM-BST-2057-00352, -2059-01408, -2059-01903, -2059-02343, HMX-ORD-2059-01645, -01763, -01788, FSP-BST-2059-00111;
  Ereignisse 19, 26, 36, 52, 58, 70, 74. Wenn eines davon fehlt oder sich ändert, ist der Bestandsstrom verschoben.

### 8.3 K11 (optional, Profil Morgengrund)

`required_stations=(("agricultural", "isolde"), ("trade_hub", "isolde"))` statt nur der Agrarstation. Damit steigt die
Verbraucherabdeckung von `pionierwerk → morgengrund` von 52 % auf 100 %. Die Station passt zur Beschreibung („kleiner Markt,
auf dem Kolonisten tauschen“) und gibt dem Spieler einen Handelsplatz in Isolde. Small erlaubt 2–3 Stationen, zwei
Pflichtstationen sind zulässig. Die Zahl der Vereinbarungen ändert sich nicht.

---

## 9. Daten (JSON)

`partnerships` enthält alle 48 aktiven Kanten. Die letzte (`helix → corvane`) bleibt im Skript in
`OPTIONAL_PARTNERSHIPS` (p = 0,6). `framework_agreements` enthält die 21 Rahmen mit allen 78 Nachträgen, K1, K2, K6, K7 und
K9 sind eingearbeitet. Weitere Details (Schema, Briefarten, Rivalitätswerte) stehen unverändert in
`verknuepfungen.json`.

```json
{
 "partnerships": [
  [
   "eisenkrone",
   "helix",
   "supply_agreement"
  ],
  [
   "helix",
   "eisenkrone",
   "strategic_alliance"
  ],
  [
   "helix",
   "lichtacker",
   "distribution_agreement"
  ],
  [
   "lichtacker",
   "helix",
   "supply_agreement"
  ],
  [
   "corvane",
   "helix",
   "licensing"
  ],
  [
   "feldspat",
   "helix",
   "consignment"
  ],
  [
   "driftwood",
   "helix",
   "consignment"
  ],
  [
   "feldspat",
   "eisenkrone",
   "supply_agreement"
  ],
  [
   "eisenkrone",
   "feldspat",
   "supply_agreement"
  ],
  [
   "eisenkrone",
   "lichtacker",
   "supply_agreement"
  ],
  [
   "corvane",
   "eisenkrone",
   "supply_agreement"
  ],
  [
   "eisenkrone",
   "corvane",
   "joint_venture"
  ],
  [
   "lichtacker",
   "corvane",
   "supply_agreement"
  ],
  [
   "graufalk",
   "helix",
   "supply_agreement"
  ],
  [
   "cindervale",
   "eisenkrone",
   "supply_agreement"
  ],
  [
   "kuppelwerk",
   "lichtacker",
   "supply_agreement"
  ],
  [
   "emberline",
   "corvane",
   "supply_agreement"
  ],
  [
   "emberline",
   "lichtacker",
   "supply_agreement"
  ],
  [
   "raureif",
   "eisenkrone",
   "supply_agreement"
  ],
  [
   "ravenmoor",
   "helix",
   "logistics_partnership"
  ],
  [
   "cindervale",
   "graufalk",
   "supply_agreement"
  ],
  [
   "graufalk",
   "cindervale",
   "strategic_alliance"
  ],
  [
   "emberline",
   "graufalk",
   "supply_agreement"
  ],
  [
   "graufalk",
   "emberline",
   "supply_agreement"
  ],
  [
   "kuppelwerk",
   "graufalk",
   "supply_agreement"
  ],
  [
   "emberline",
   "kuppelwerk",
   "supply_agreement"
  ],
  [
   "emberline",
   "cindervale",
   "supply_agreement"
  ],
  [
   "cindervale",
   "kometenpost",
   "consignment"
  ],
  [
   "kometenpost",
   "cindervale",
   "logistics_partnership"
  ],
  [
   "cindervale",
   "lanternfish",
   "supply_agreement"
  ],
  [
   "lanternfish",
   "graufalk",
   "supply_agreement"
  ],
  [
   "lanternfish",
   "kometenpost",
   "consignment"
  ],
  [
   "raureif",
   "pionierwerk",
   "supply_agreement"
  ],
  [
   "pionierwerk",
   "morgengrund",
   "supply_agreement"
  ],
  [
   "morgengrund",
   "pionierwerk",
   "supply_agreement"
  ],
  [
   "ravenmoor",
   "pionierwerk",
   "logistics_partnership"
  ],
  [
   "pionierwerk",
   "ravenmoor",
   "supply_agreement"
  ],
  [
   "outmark",
   "pionierwerk",
   "licensing"
  ],
  [
   "second_hull",
   "pionierwerk",
   "supply_agreement"
  ],
  [
   "second_hull",
   "ravenmoor",
   "consignment"
  ],
  [
   "raureif",
   "ravenmoor",
   "supply_agreement"
  ],
  [
   "ravenmoor",
   "outmark",
   "logistics_partnership"
  ],
  [
   "morgengrund",
   "ravenmoor",
   "supply_agreement"
  ],
  [
   "outmark",
   "raureif",
   "supply_agreement"
  ],
  [
   "kuppelwerk",
   "pionierwerk",
   "supply_agreement"
  ],
  [
   "second_hull",
   "graufalk",
   "supply_agreement"
  ],
  [
   "graufalk",
   "ravenmoor",
   "supply_agreement"
  ],
  [
   "helix",
   "corvane",
   "logistics_partnership"
  ]
 ],
 "historic": [
  [
   "corvane",
   "driftwood",
   "supply_agreement"
  ],
  [
   "eisenkrone",
   "graufalk",
   "supply_agreement"
  ],
  [
   "cindervale",
   "helix",
   "licensing"
  ],
  [
   "lichtacker",
   "pionierwerk",
   "supply_agreement"
  ],
  [
   "emberline",
   "eisenkrone",
   "supply_agreement"
  ],
  [
   "outmark",
   "feldspat",
   "licensing"
  ],
  [
   "driftwood",
   "second_hull",
   "consignment"
  ]
 ],
 "rivalries": [
  [
   "eisenkrone",
   "helix",
   "market_dominance",
   "sol"
  ],
  [
   "driftwood",
   "corvane",
   "industrial_espionage",
   "halcyon"
  ],
  [
   "feldspat",
   "driftwood",
   "territorial_claims",
   "kharon"
  ],
  [
   "lichtacker",
   "eisenkrone",
   "resource_competition",
   "myrrhen"
  ],
  [
   "graufalk",
   "eisenkrone",
   "market_dominance",
   "halcyon"
  ],
  [
   "cindervale",
   "helix",
   "market_dominance",
   "sol"
  ],
  [
   "emberline",
   "eisenkrone",
   "resource_competition",
   "myrrhen"
  ],
  [
   "lichtacker",
   "pionierwerk",
   "territorial_claims",
   "isolde"
  ],
  [
   "ravenmoor",
   "driftwood",
   "armed_conflict",
   "nyx"
  ],
  [
   "outmark",
   "feldspat",
   "territorial_claims",
   "brennus"
  ],
  [
   "ravenmoor",
   "helix",
   "market_dominance",
   "kharon"
  ],
  [
   "second_hull",
   "driftwood",
   "territorial_claims",
   "nyx"
  ]
 ],
 "framework_agreements": [
  {
   "number": "HMX-MSA-2057-01",
   "seller_key": "helix",
   "buyer_key": "lichtacker",
   "title": "Distribution Framework Agreement Agricultural Rings Tauvel, Aurelis & Myrrhen",
   "start_date": "2057-01-01",
   "start_year": 2057,
   "term_months": 36,
   "base_volume_mcr": 250,
   "price_formula": "index_linked",
   "indexation": "category_price_index",
   "exclusivity": "right_of_first_refusal",
   "notice_days": 180,
   "scope": [
    "luxury",
    "food",
    "industrial_goods"
   ],
   "adjustment_cap_pct": 8,
   "exclusive_categories": [
    "industrial_goods"
   ],
   "existing_pair": true,
   "expected_assigned_contracts": 54,
   "amendments": [
    {
     "type": "product_addition",
     "effective_date": "2057-04-01",
     "status": "signed",
     "categories": [
      "energy",
      "technology"
     ],
     "rule": "first_contract_of_category"
    },
    {
     "type": "product_addition",
     "effective_date": "2057-09-01",
     "status": "signed",
     "categories": [
      "medical"
     ],
     "rule": "first_contract_of_category"
    },
    {
     "type": "penalty_clause",
     "effective_date": "2058-03-14",
     "status": "signed",
     "proposed_date": "2058-02-20",
     "initiated_by": "lichtacker",
     "anchor_contracts": [
      "HMX-CTR-2057-0043"
     ]
    },
    {
     "type": "volume_increase",
     "effective_date": "2058-09-01",
     "status": "signed",
     "volume_after_mcr": 400,
     "anchor_contracts": [
      "HMX-CTR-2058-0161"
     ],
     "rule": "cumulative_over_90pct"
    },
    {
     "type": "exclusivity_waiver",
     "effective_date": "2059-03-15",
     "status": "signed",
     "proposed_date": "2059-03-10",
     "initiated_by": "lichtacker",
     "categories": [
      "industrial_goods"
     ],
     "anchor_contracts": [
      "HMX-CTR-2057-0043",
      "HMX-CTR-2058-0139",
      "HMX-CTR-2058-0159"
     ]
    },
    {
     "type": "volume_increase",
     "effective_date": "2059-10-01",
     "status": "signed",
     "volume_after_mcr": 550,
     "anchor_contracts": [
      "HMX-CTR-2059-0259"
     ],
     "rule": "cumulative_over_90pct"
    },
    {
     "type": "term_extension",
     "effective_date": "2059-11-01",
     "status": "signed",
     "new_end_date": "2060-12-31",
     "initiated_by": "lichtacker",
     "rule": "calloff_after_end"
    }
   ]
  },
  {
   "number": "HMX-MSA-2057-02",
   "seller_key": "helix",
   "buyer_key": "corvane",
   "title": "Logistics & Supply Master Agreement Halcyon/Aurelis",
   "start_date": "2057-01-01",
   "start_year": 2057,
   "term_months": 36,
   "base_volume_mcr": 300,
   "price_formula": "market_minus",
   "indexation": "category_price_index",
   "exclusivity": "none",
   "notice_days": 120,
   "scope": [
    "luxury",
    "raw_materials"
   ],
   "base_discount_pct": 4,
   "existing_pair": true,
   "expected_assigned_contracts": 68,
   "condition": "K9: nur anlegen, wenn OPTIONAL_PARTNERSHIPS helix -> corvane gezogen wird (Seed 42: ja)",
   "amendments": [
    {
     "type": "product_addition",
     "effective_date": "2057-03-01",
     "status": "signed",
     "categories": [
      "technology"
     ],
     "rule": "first_contract_of_category"
    },
    {
     "type": "product_addition",
     "effective_date": "2057-05-01",
     "status": "signed",
     "categories": [
      "energy"
     ],
     "rule": "first_contract_of_category"
    },
    {
     "type": "exclusivity_clause",
     "effective_date": "2057-05-01",
     "status": "signed",
     "initiated_by": "helix",
     "exclusivity": "buyer_exclusive",
     "categories": [
      "energy"
     ]
    },
    {
     "type": "product_addition",
     "effective_date": "2058-01-01",
     "status": "signed",
     "categories": [
      "industrial_goods"
     ],
     "rule": "first_contract_of_category"
    },
    {
     "type": "volume_increase",
     "effective_date": "2058-08-01",
     "status": "signed",
     "volume_after_mcr": 450,
     "anchor_contracts": [
      "HMX-CTR-2058-0152"
     ],
     "rule": "cumulative_over_90pct"
    },
    {
     "type": "product_removal",
     "effective_date": "2059-03-15",
     "status": "signed",
     "proposed_date": "2059-03-13",
     "initiated_by": "corvane",
     "archetypes": [
      "helium3"
     ],
     "anchor_contracts": [
      "HMX-CTR-2058-0131",
      "HMX-CTR-2057-0014"
     ],
     "anchor_events": [
      30
     ]
    },
    {
     "type": "exclusivity_waiver",
     "effective_date": "2059-03-15",
     "status": "signed",
     "proposed_date": "2059-03-13",
     "initiated_by": "corvane",
     "categories": [
      "energy"
     ],
     "anchor_contracts": [
      "HMX-CTR-2058-0131"
     ]
    },
    {
     "type": "volume_increase",
     "effective_date": "2059-04-01",
     "status": "signed",
     "volume_after_mcr": 600,
     "anchor_contracts": [
      "HMX-CTR-2059-0213"
     ],
     "rule": "cumulative_over_90pct"
    },
    {
     "type": "term_extension",
     "effective_date": "2059-11-01",
     "status": "signed",
     "new_end_date": "2060-12-31",
     "initiated_by": "corvane",
     "rule": "calloff_after_end"
    },
    {
     "type": "volume_increase",
     "effective_date": "2060-02-01",
     "status": "proposed",
     "proposed_date": "2059-12-15",
     "volume_after_mcr": 750,
     "anchor_contracts": [
      "HMX-CTR-2060-0281"
     ],
     "rule": "cumulative_over_90pct"
    }
   ]
  },
  {
   "number": "HMX-MSA-2057-03",
   "seller_key": "helix",
   "buyer_key": "eisenkrone",
   "title": "Strategic Supply Framework Sol/Halcyon/Brennus",
   "start_date": "2057-01-01",
   "start_year": 2057,
   "term_months": 48,
   "base_volume_mcr": 300,
   "price_formula": "cost_plus",
   "indexation": "category_price_index",
   "exclusivity": "none",
   "notice_days": 360,
   "scope": [
    "food",
    "raw_materials",
    "energy"
   ],
   "cost_plus_pct": 9,
   "existing_pair": true,
   "expected_assigned_contracts": 75,
   "amendments": [
    {
     "type": "product_addition",
     "effective_date": "2057-07-01",
     "status": "signed",
     "categories": [
      "medical",
      "technology",
      "industrial_goods"
     ],
     "rule": "first_contract_of_category"
    },
    {
     "type": "volume_reduction",
     "effective_date": "2058-03-01",
     "status": "signed",
     "proposed_date": "2058-02-15",
     "initiated_by": "eisenkrone",
     "volume_after_mcr": 250,
     "anchor_events": [
      19
     ]
    },
    {
     "type": "volume_increase",
     "effective_date": "2059-01-01",
     "status": "signed",
     "volume_after_mcr": 350,
     "anchor_contracts": [
      "HMX-CTR-2059-0192"
     ],
     "rule": "cumulative_over_90pct"
    },
    {
     "type": "volume_increase",
     "effective_date": "2059-06-01",
     "status": "signed",
     "volume_after_mcr": 450,
     "anchor_contracts": [
      "HMX-CTR-2059-0236"
     ],
     "rule": "cumulative_over_90pct"
    },
    {
     "type": "volume_increase",
     "effective_date": "2060-01-01",
     "status": "proposed",
     "proposed_date": "2059-12-10",
     "volume_after_mcr": 550,
     "anchor_contracts": [
      "HMX-CTR-2060-0275"
     ],
     "rule": "cumulative_over_90pct"
    }
   ]
  },
  {
   "number": "EKM-RV-2057-01",
   "seller_key": "eisenkrone",
   "buyer_key": "corvane",
   "title": "Joint-Venture-Liefervertrag Halcyon",
   "start_date": "2057-01-01",
   "start_year": 2057,
   "term_months": 60,
   "base_volume_mcr": 350,
   "price_formula": "cost_plus",
   "indexation": "category_price_index",
   "exclusivity": "right_of_first_refusal",
   "notice_days": 360,
   "scope": [
    "raw_materials",
    "industrial_goods"
   ],
   "cost_plus_pct": 12,
   "exclusive_categories": [
    "raw_materials"
   ],
   "existing_pair": true,
   "expected_assigned_contracts": 65,
   "amendments": [
    {
     "type": "product_addition",
     "effective_date": "2057-05-01",
     "status": "signed",
     "categories": [
      "luxury",
      "technology"
     ],
     "rule": "first_contract_of_category"
    },
    {
     "type": "penalty_clause",
     "effective_date": "2058-05-01",
     "status": "signed",
     "proposed_date": "2058-04-28",
     "initiated_by": "corvane",
     "anchor_contracts": [
      "EKM-VTR-2057-0064"
     ]
    },
    {
     "type": "volume_increase",
     "effective_date": "2059-03-01",
     "status": "signed",
     "volume_after_mcr": 450,
     "anchor_contracts": [
      "EKM-VTR-2059-0160"
     ],
     "rule": "cumulative_over_90pct"
    },
    {
     "type": "service_level_clause",
     "effective_date": "2060-02-01",
     "status": "proposed",
     "proposed_date": "2059-12-23",
     "initiated_by": "corvane",
     "anchor_contracts": [
      "EKM-VTR-2059-0160"
     ]
    },
    {
     "type": "volume_increase",
     "effective_date": "2060-01-01",
     "status": "proposed",
     "proposed_date": "2059-12-10",
     "volume_after_mcr": 550,
     "anchor_contracts": [
      "EKM-VTR-2060-0219"
     ],
     "rule": "cumulative_over_90pct"
    }
   ]
  },
  {
   "number": "EKM-RV-2057-02",
   "seller_key": "eisenkrone",
   "buyer_key": "helix",
   "title": "Rahmenvertrag Erze und Energie Brennus/Halcyon – Kharon/Sol",
   "start_date": "2057-01-01",
   "start_year": 2057,
   "term_months": 42,
   "base_volume_mcr": 200,
   "price_formula": "index_linked",
   "indexation": "category_price_index",
   "exclusivity": "none",
   "notice_days": 180,
   "scope": [
    "energy",
    "raw_materials"
   ],
   "price_index_category": "raw_materials",
   "adjustment_cap_pct": 10,
   "existing_pair": true,
   "expected_assigned_contracts": 39,
   "amendments": [
    {
     "type": "product_addition",
     "effective_date": "2057-06-01",
     "status": "signed",
     "categories": [
      "food",
      "technology"
     ],
     "rule": "first_contract_of_category"
    },
    {
     "type": "product_addition",
     "effective_date": "2058-01-01",
     "status": "signed",
     "categories": [
      "industrial_goods"
     ],
     "rule": "first_contract_of_category"
    },
    {
     "type": "penalty_clause",
     "effective_date": "2058-01-09",
     "status": "signed",
     "proposed_date": "2057-12-20",
     "initiated_by": "helix",
     "anchor_contracts": [
      "EKM-VTR-2057-0017"
     ]
    },
    {
     "type": "product_addition",
     "effective_date": "2058-08-01",
     "status": "signed",
     "categories": [
      "luxury"
     ],
     "rule": "first_contract_of_category"
    },
    {
     "type": "volume_increase",
     "effective_date": "2059-02-01",
     "status": "signed",
     "volume_after_mcr": 300,
     "anchor_contracts": [
      "EKM-VTR-2059-0151"
     ],
     "rule": "cumulative_over_90pct"
    },
    {
     "type": "escort_clause",
     "effective_date": "2060-02-01",
     "status": "proposed",
     "proposed_date": "2059-12-22",
     "initiated_by": "helix",
     "escort_key": "ravenmoor",
     "anchor_contracts": [
      "EKM-VTR-2057-0043",
      "EKM-VTR-2058-0107"
     ],
     "anchor_orders": [
      "EKM-BST-2059-02343"
     ],
     "anchor_events": [
      74
     ],
     "linked_amendment": "RCS-MSA-2058-01#escort_clause",
     "anchor_contracts_docking": [
      "EKM-VTR-2057-0017",
      "EKM-VTR-2059-0162"
     ],
     "note": "K2: Geleitschutz für die zwei echten Geleitschutzbrüche des Paares; die zwei Andockstau-Brüche begründen Ausweich-Liegeplätze an der Ravenmoor-Handelsstation in Kharon"
    },
    {
     "type": "volume_increase",
     "effective_date": "2060-02-01",
     "status": "proposed",
     "proposed_date": "2059-12-22",
     "volume_after_mcr": 400,
     "anchor_contracts": [
      "EKM-VTR-2060-0234"
     ],
     "rule": "cumulative_over_90pct"
    },
    {
     "type": "term_extension",
     "effective_date": "2060-07-01",
     "status": "proposed",
     "proposed_date": "2059-12-22",
     "new_end_date": "2061-06-30",
     "initiated_by": "helix"
    }
   ]
  },
  {
   "number": "EKM-RV-2057-03",
   "seller_key": "eisenkrone",
   "buyer_key": "lichtacker",
   "title": "Liefervertrag Industriegüter und Energie Myrrhen/Tauvel",
   "start_date": "2057-01-01",
   "start_year": 2057,
   "term_months": 36,
   "base_volume_mcr": 150,
   "price_formula": "index_linked",
   "indexation": "category_price_index",
   "exclusivity": "none",
   "notice_days": 90,
   "scope": [
    "industrial_goods",
    "luxury",
    "raw_materials"
   ],
   "price_index_category": "energy",
   "adjustment_cap_pct": 6,
   "existing_pair": true,
   "expected_assigned_contracts": 35,
   "expected_outside": [
    "EKM-VTR-2060-0230"
   ],
   "amendments": [
    {
     "type": "product_addition",
     "effective_date": "2057-08-01",
     "status": "signed",
     "categories": [
      "energy"
     ],
     "rule": "first_contract_of_category"
    },
    {
     "type": "product_addition",
     "effective_date": "2058-02-01",
     "status": "signed",
     "categories": [
      "technology"
     ],
     "rule": "first_contract_of_category"
    },
    {
     "type": "penalty_clause",
     "effective_date": "2058-09-14",
     "status": "signed",
     "proposed_date": "2058-08-28",
     "initiated_by": "lichtacker",
     "anchor_contracts": [
      "EKM-VTR-2058-0099"
     ]
    },
    {
     "type": "partial_termination",
     "effective_date": "2060-01-18",
     "status": "signed",
     "proposed_date": "2059-10-20",
     "initiated_by": "lichtacker",
     "categories": [
      "energy"
     ],
     "anchor_contracts": [
      "EKM-VTR-2059-0167",
      "EKM-VTR-2058-0105",
      "EKM-VTR-2058-0099"
     ],
     "note": "laufende Energieabrufe (EKM-VTR-2059-0197) werden bis zur Frist erfüllt; EKM-VTR-2060-0230 (Entwurf) liegt außerhalb des Rahmens"
    },
    {
     "type": "price_adjustment",
     "effective_date": "2060-01-18",
     "status": "rejected",
     "proposed_date": "2059-10-28",
     "initiated_by": "eisenkrone",
     "pct": -5,
     "categories": [
      "energy"
     ],
     "note": "Rettungsangebot Eisenkrone, von Lichtacker am 2059-11-10 abgelehnt"
    },
    {
     "type": "volume_increase",
     "effective_date": "2059-11-01",
     "status": "signed",
     "volume_after_mcr": 200,
     "anchor_contracts": [
      "EKM-VTR-2059-0211"
     ],
     "rule": "cumulative_over_90pct"
    },
    {
     "type": "term_extension",
     "effective_date": "2059-11-01",
     "status": "signed",
     "new_end_date": "2060-12-31",
     "initiated_by": "lichtacker",
     "rule": "calloff_after_end",
     "note": "nur Restumfang ohne Energie"
    }
   ]
  },
  {
   "number": "FSP-RV-2059-01",
   "seller_key": "feldspat",
   "buyer_key": "eisenkrone",
   "title": "Abnahmerahmen Quantenquarz Becker",
   "start_date": "2059-08-01",
   "start_year": 2059,
   "term_months": 24,
   "base_volume_mcr": 12,
   "price_formula": "market_minus",
   "indexation": "category_price_index",
   "exclusivity": "right_of_first_refusal",
   "notice_days": 90,
   "scope": [
    "raw_materials"
   ],
   "base_discount_pct": 5,
   "exclusive_archetypes": [
    "quantum_quartz"
   ],
   "existing_pair": true,
   "expected_assigned_contracts": 5,
   "story": "Feldspat schuldet Eisenkrone 25,5 Mio. CR (13 überfällige Bestellungen); das Vorkaufsrecht auf Quantenquarz ist das Pfand",
   "amendments": [
    {
     "type": "price_adjustment",
     "effective_date": "2059-11-20",
     "status": "signed",
     "proposed_date": "2059-11-05",
     "initiated_by": "feldspat",
     "pct": 12,
     "anchor_events": [
      65,
      66
     ],
     "anchor_contracts": [
      "FSP-VTR-2059-0019"
     ],
     "note": "nach Stornierung des Abrufvertrags FSP-VTR-2059-0019 im Preisstreit"
    },
    {
     "type": "volume_increase",
     "effective_date": "2060-01-15",
     "status": "proposed",
     "proposed_date": "2059-12-15",
     "volume_after_mcr": 20,
     "initiated_by": "feldspat"
    }
   ]
  },
  {
   "number": "GFW-RV-2057-01",
   "seller_key": "graufalk",
   "buyer_key": "helix",
   "title": "Flottenrahmenvertrag Rumpf- und Triebwerksteile",
   "start_date": "2057-01-01",
   "start_year": 2057,
   "term_months": 48,
   "base_volume_mcr": 180,
   "price_formula": "index_linked",
   "indexation": "category_price_index",
   "exclusivity": "none",
   "notice_days": 180,
   "scope": [
    "industrial_goods"
   ],
   "price_index_category": "industrial_goods",
   "amendments": [
    {
     "type": "product_addition",
     "effective_date": "rule",
     "status": "signed",
     "categories": [
      "technology"
     ],
     "rule": "first_contract_of_category"
    },
    {
     "type": "volume_increase",
     "effective_date": "2058-12-20",
     "status": "signed",
     "proposed_date": "2058-12-16",
     "initiated_by": "helix",
     "delta_mcr": 60,
     "anchor_contracts": [
      "HMX-CTR-2058-0173"
     ]
    },
    {
     "type": "service_level_clause",
     "effective_date": "2060-01-15",
     "status": "proposed",
     "proposed_date": "2059-12-31",
     "initiated_by": "helix",
     "anchor_orders": [
      "HMX-ORD-2059-01763",
      "HMX-ORD-2059-01788"
     ],
     "note": "K6: Eilabrufklausel Triebwerksteile nach zwei Triebwerksschäden (HMX-SHP-2059-01721 +99 h, HMX-SHP-2059-01746 +38 h); HMX-ORD-2059-01788 existiert erst ab 2059-12-29"
    }
   ]
  },
  {
   "number": "GFW-RV-2057-02",
   "seller_key": "graufalk",
   "buyer_key": "cindervale",
   "title": "Allianzvertrag Navigationsplattform",
   "start_date": "2057-01-01",
   "start_year": 2057,
   "term_months": 60,
   "base_volume_mcr": 220,
   "price_formula": "cost_plus",
   "indexation": "category_price_index",
   "exclusivity": "none",
   "notice_days": 365,
   "scope": [
    "industrial_goods",
    "technology"
   ],
   "cost_plus_pct": 8,
   "amendments": [
    {
     "type": "exclusivity_clause",
     "effective_date": "2058-03-15",
     "status": "signed",
     "proposed_date": "2058-02-20",
     "initiated_by": "graufalk",
     "exclusivity": "mutual",
     "archetypes": [
      "drive_parts"
     ],
     "anchor_events": [
      19
     ],
     "note": "Cindervale bezieht Triebwerksteile nur von Graufalk; Graufalk bezieht neue Navigationscomputer nur von Cindervale"
    },
    {
     "type": "volume_increase",
     "effective_date": "rule",
     "status": "signed",
     "delta_mcr": 80,
     "rule": "cumulative_over_90pct"
    },
    {
     "type": "confidentiality_clause",
     "effective_date": "2060-01-15",
     "status": "proposed",
     "proposed_date": "2059-12-29",
     "initiated_by": "cindervale",
     "note": "nach der Aussetzung CCI-MSA-2057-01 und dem Gerücht vom 2059-12-27"
    }
   ]
  },
  {
   "number": "GFW-RV-2058-01",
   "seller_key": "graufalk",
   "buyer_key": "ravenmoor",
   "title": "Geleitschiff-Rahmenvertrag Kharon/Brennus",
   "start_date": "2058-07-15",
   "start_year": 2058,
   "term_months": 36,
   "base_volume_mcr": 90,
   "price_formula": "index_linked",
   "indexation": "category_price_index",
   "exclusivity": "right_of_first_refusal",
   "notice_days": 180,
   "scope": [
    "industrial_goods"
   ],
   "exclusive_archetypes": [
    "hull_plating"
   ],
   "exclusivity_system": "kharon",
   "story": "Ravenmoor hat Vorkaufsrecht auf Graufalk-Rumpfplatten für Kharon; Helix bekommt nur, was Ravenmoor ablehnt",
   "amendments": [
    {
     "type": "product_addition",
     "effective_date": "rule",
     "status": "signed",
     "categories": [
      "technology"
     ],
     "rule": "first_contract_of_category"
    },
    {
     "type": "volume_increase",
     "effective_date": "2059-09-01",
     "status": "signed",
     "proposed_date": "2059-08-25",
     "initiated_by": "ravenmoor",
     "delta_mcr": 40,
     "anchor_events": [
      45,
      57,
      58
     ]
    }
   ]
  },
  {
   "number": "CCI-MSA-2057-01",
   "seller_key": "cindervale",
   "buyer_key": "eisenkrone",
   "title": "AI Control & Robotics Framework Agreement",
   "start_date": "2057-01-01",
   "start_year": 2057,
   "term_months": 48,
   "base_volume_mcr": 120,
   "price_formula": "fixed",
   "indexation": "none",
   "exclusivity": "right_of_first_refusal",
   "notice_days": 180,
   "scope": [
    "technology",
    "industrial_goods"
   ],
   "exclusive_categories": [
    "technology"
   ],
   "exclusivity_system": "halcyon",
   "status_at_reference": "suspended",
   "r2_correction": "K1: buyer_exclusive -> right_of_first_refusal; Corvane liefert im Bestand Technik an Bergbaustation Hande (CVB-CTR-2058-0003, -0013, -0038, CVB-CTR-2059-0044, -0066 und 25 Bestellungen)",
   "amendments": [
    {
     "type": "service_level_clause",
     "effective_date": "2058-03-01",
     "status": "signed",
     "proposed_date": "2058-02-10",
     "initiated_by": "eisenkrone",
     "anchor_events": [
      19
     ],
     "note": "Gewährleistungsklausel"
    },
    {
     "type": "price_adjustment",
     "effective_date": "2058-12-15",
     "status": "signed",
     "proposed_date": "2058-11-20",
     "initiated_by": "cindervale",
     "pct": -8,
     "anchor_events": [
      36
     ]
    },
    {
     "type": "suspension",
     "effective_date": "2059-12-15",
     "status": "signed",
     "proposed_date": "2059-12-05",
     "initiated_by": "eisenkrone",
     "anchor_events": [
      70
     ],
     "note": "Aussetzung bis zum Firmware-Audit; Kündigungsandrohung zum 2060-06-03 im Schreiben vom 2059-12-05"
    }
   ]
  },
  {
   "number": "KHB-RV-2058-01",
   "seller_key": "kuppelwerk",
   "buyer_key": "pionierwerk",
   "title": "Rahmenvertrag Habitatmodule Isolde",
   "start_date": "2058-06-01",
   "start_year": 2058,
   "term_months": 36,
   "base_volume_mcr": 70,
   "price_formula": "cost_plus",
   "indexation": "fuel_index",
   "exclusivity": "seller_exclusive",
   "notice_days": 180,
   "scope": [
    "industrial_goods"
   ],
   "cost_plus_pct": 10,
   "exclusive_archetypes": [
    "habitat_modules"
   ],
   "exclusivity_system": "isolde",
   "amendments": [
    {
     "type": "volume_increase",
     "effective_date": "2059-05-01",
     "status": "signed",
     "proposed_date": "2059-04-15",
     "initiated_by": "pionierwerk",
     "delta_mcr": 35,
     "note": "zweite Ausbaustufe Serravel"
    },
    {
     "type": "scope_extension",
     "effective_date": "2059-10-01",
     "status": "signed",
     "proposed_date": "2059-09-10",
     "initiated_by": "pionierwerk",
     "system_code": "serravel",
     "archetypes": [
      "sinter_blocks"
     ]
    }
   ]
  },
  {
   "number": "KHB-RV-2059-01",
   "seller_key": "kuppelwerk",
   "buyer_key": "lichtacker",
   "title": "Baustoffrahmen Verbundstahl und Habitatbaustoffe Tauvel/Myrrhen",
   "start_date": "2059-04-01",
   "start_year": 2059,
   "term_months": 24,
   "base_volume_mcr": 30,
   "price_formula": "cost_plus",
   "indexation": "fuel_index",
   "exclusivity": "none",
   "notice_days": 90,
   "scope": [
    "industrial_goods",
    "raw_materials"
   ],
   "cost_plus_pct": 10,
   "story": "folgt auf den Wegfall des Helix-Vorkaufsrechts (HMX-MSA-2057-01, 2059-03-15) und den Strafbescheid 653.162,16 CR",
   "amendments": [
    {
     "type": "product_addition",
     "effective_date": "2059-08-01",
     "status": "signed",
     "proposed_date": "2059-07-20",
     "initiated_by": "kuppelwerk",
     "archetypes": [
      "habitat_modules"
     ],
     "anchor_events": [
      53
     ]
    },
    {
     "type": "volume_increase",
     "effective_date": "rule",
     "status": "signed",
     "rule": "cumulative_over_90pct"
    },
    {
     "type": "exclusivity_clause",
     "effective_date": "2060-02-01",
     "status": "proposed",
     "proposed_date": "2059-12-10",
     "initiated_by": "kuppelwerk",
     "exclusivity": "regional_exclusive",
     "system_code": "myrrhen",
     "archetypes": [
      "sinter_blocks",
      "habitat_modules"
     ]
    }
   ]
  },
  {
   "number": "EFF-MSA-2059-01",
   "seller_key": "emberline",
   "buyer_key": "corvane",
   "title": "Helium-3 Supply Framework Halcyon Works VI",
   "start_date": "2059-04-01",
   "start_year": 2059,
   "term_months": 24,
   "base_volume_mcr": 40,
   "price_formula": "index_linked",
   "indexation": "fuel_index",
   "exclusivity": "none",
   "notice_days": 90,
   "scope": [
    "energy"
   ],
   "story": "direkt nach der Herausnahme von Helium-3 aus HMX-MSA-2057-02 (2059-03-15); Sturmzuschlag Pellora",
   "amendments": [
    {
     "type": "force_majeure_clause",
     "effective_date": "2059-09-15",
     "status": "signed",
     "proposed_date": "2059-09-05",
     "initiated_by": "emberline",
     "anchor_events": [
      59
     ]
    },
    {
     "type": "volume_increase",
     "effective_date": "rule",
     "status": "signed",
     "rule": "cumulative_over_90pct"
    },
    {
     "type": "exclusivity_clause",
     "effective_date": "2060-01-01",
     "status": "proposed",
     "proposed_date": "2059-12-05",
     "initiated_by": "emberline",
     "exclusivity": "buyer_exclusive",
     "archetypes": [
      "helium3"
     ],
     "system_code": "halcyon"
    }
   ]
  },
  {
   "number": "EFF-MSA-2059-02",
   "seller_key": "emberline",
   "buyer_key": "lichtacker",
   "title": "Energy Framework Agreement Agrarstation Seip",
   "start_date": "2059-11-15",
   "start_year": 2059,
   "term_months": 24,
   "base_volume_mcr": 18,
   "price_formula": "index_linked",
   "indexation": "fuel_index",
   "exclusivity": "none",
   "notice_days": 90,
   "scope": [
    "energy"
   ],
   "story": "Kette: EKM-VTR-2058-0099/-0105/-2059-0167 gebrochen -> Teilkündigung EKM-RV-2057-03 -> Emberline",
   "amendments": [
    {
     "type": "exclusivity_clause",
     "effective_date": "2060-01-18",
     "status": "signed",
     "proposed_date": "2059-11-15",
     "initiated_by": "lichtacker",
     "exclusivity": "right_of_first_refusal",
     "categories": [
      "energy"
     ],
     "system_code": "myrrhen",
     "note": "kein Käuferexklusiv, weil HMX-CTR-2059-0257 (Helix, Plasmagas an Seip) bis 2060-03-30 läuft"
    }
   ]
  },
  {
   "number": "RCS-MSA-2058-01",
   "seller_key": "ravenmoor",
   "buyer_key": "helix",
   "title": "Escort & Frontier Supply Framework Kharon Corridor",
   "start_date": "2058-08-01",
   "start_year": 2058,
   "term_months": 36,
   "base_volume_mcr": 90,
   "price_formula": "cost_plus",
   "indexation": "risk_index",
   "exclusivity": "regional_exclusive",
   "notice_days": 90,
   "scope": [
    "industrial_goods",
    "technology",
    "medical",
    "food"
   ],
   "cost_plus_pct": 15,
   "exclusive_archetypes": [
    "escort_drones",
    "sensor_arrays"
   ],
   "exclusivity_system": "kharon",
   "escort_key": "ravenmoor",
   "story": "vom Gegner (Razzia 26, 2058-06-30) zum Schutzpartner",
   "amendments": [
    {
     "type": "volume_increase",
     "effective_date": "2059-06-15",
     "status": "signed",
     "proposed_date": "2059-06-05",
     "initiated_by": "helix",
     "delta_mcr": 40,
     "anchor_events": [
      51
     ]
    },
    {
     "type": "escort_clause",
     "effective_date": "2060-02-01",
     "status": "proposed",
     "proposed_date": "2059-12-22",
     "initiated_by": "ravenmoor",
     "escort_key": "ravenmoor",
     "anchor_events": [
      74
     ],
     "linked_amendment": "EKM-RV-2057-02#escort_clause",
     "note": "dreiseitig: Geleit auch für Eisenkrone-Konvois nach Kharon"
    },
    {
     "type": "scope_extension",
     "effective_date": "2060-01-15",
     "status": "proposed",
     "proposed_date": "2059-12-23",
     "initiated_by": "helix",
     "station": "Kharon Landing IV",
     "anchor_events": [
      74
     ]
    }
   ]
  },
  {
   "number": "RVF-RV-2058-01",
   "seller_key": "raureif",
   "buyer_key": "pionierwerk",
   "title": "Versorgungsrahmen Isolde – Volatile",
   "start_date": "2058-01-01",
   "start_year": 2058,
   "term_months": 36,
   "base_volume_mcr": 80,
   "price_formula": "index_linked",
   "indexation": "fuel_index",
   "exclusivity": "regional_exclusive",
   "notice_days": 180,
   "scope": [
    "raw_materials",
    "energy"
   ],
   "exclusive_archetypes": [
    "water_ice"
   ],
   "exclusivity_system": "isolde",
   "amendments": [
    {
     "type": "exclusivity_clause",
     "effective_date": "2058-09-01",
     "status": "signed",
     "proposed_date": "2058-08-15",
     "initiated_by": "pionierwerk",
     "archetypes": [
      "nitrogen_ice"
     ],
     "note": "K7: Stickstoffeis ist über die Kategorie schon im Scope; neu ist nur die Exklusivität ab 2058-09-01",
     "exclusivity": "regional_exclusive",
     "system_code": "isolde"
    },
    {
     "type": "volume_increase",
     "effective_date": "2059-06-01",
     "status": "signed",
     "proposed_date": "2059-05-15",
     "initiated_by": "pionierwerk",
     "delta_mcr": 30
    },
    {
     "type": "price_adjustment",
     "effective_date": "2060-01-01",
     "status": "proposed",
     "proposed_date": "2059-11-20",
     "initiated_by": "raureif",
     "pct": 10,
     "note": "lange Wege, Piraterie"
    }
   ]
  },
  {
   "number": "RVF-RV-2058-02",
   "seller_key": "raureif",
   "buyer_key": "eisenkrone",
   "title": "Volatile-Liefervertrag Myrrhen/Brennus",
   "start_date": "2058-03-01",
   "start_year": 2058,
   "term_months": 24,
   "base_volume_mcr": 45,
   "price_formula": "index_linked",
   "indexation": "category_price_index",
   "exclusivity": "none",
   "notice_days": 90,
   "scope": [
    "raw_materials",
    "energy"
   ],
   "price_index_category": "raw_materials",
   "amendments": [
    {
     "type": "price_adjustment",
     "effective_date": "2059-08-01",
     "status": "signed",
     "proposed_date": "2059-07-25",
     "initiated_by": "eisenkrone",
     "pct": -6,
     "anchor_events": [
      52
     ],
     "note": "Eisenkrone verweist auf den Fund 52 bei Feldspat"
    },
    {
     "type": "term_extension",
     "effective_date": "2060-02-29",
     "status": "proposed",
     "proposed_date": "2059-12-15",
     "new_end_date": "2061-02-28",
     "initiated_by": "eisenkrone"
    }
   ]
  },
  {
   "number": "OSP-MSA-2058-01",
   "seller_key": "outmark",
   "buyer_key": "pionierwerk",
   "title": "Survey Data License Framework Serravel/Isolde",
   "start_date": "2058-02-01",
   "start_year": 2058,
   "term_months": 36,
   "base_volume_mcr": 25,
   "price_formula": "fixed",
   "indexation": "none",
   "exclusivity": "none",
   "notice_days": 180,
   "scope": [
    "technology",
    "raw_materials"
   ],
   "amendments": [
    {
     "type": "exclusivity_clause",
     "effective_date": "2059-08-15",
     "status": "signed",
     "proposed_date": "2059-07-30",
     "initiated_by": "pionierwerk",
     "exclusivity": "regional_exclusive",
     "system_code": "serravel",
     "archetypes": [
      "survey_charts"
     ],
     "anchor_events": [
      52
     ]
    },
    {
     "type": "product_addition",
     "effective_date": "2059-11-01",
     "status": "signed",
     "archetypes": [
      "terraforming_cultures"
     ],
     "condition": "nur wenn der Archetyp im Outmark-Produktpool liegt"
    }
   ]
  },
  {
   "number": "SGM-RV-2059-01",
   "seller_key": "morgengrund",
   "buyer_key": "pionierwerk",
   "title": "Versorgungsrahmen Isolde – Lebensmittel für Bautrupps",
   "start_date": "2059-01-01",
   "start_year": 2059,
   "term_months": 12,
   "base_volume_mcr": 5,
   "price_formula": "fixed",
   "indexation": "none",
   "exclusivity": "none",
   "notice_days": 60,
   "scope": [
    "food"
   ],
   "auto_renewal": true,
   "renewal_months": 12,
   "amendments": [
    {
     "type": "volume_increase",
     "effective_date": "2059-07-01",
     "status": "signed",
     "proposed_date": "2059-06-15",
     "initiated_by": "pionierwerk",
     "delta_mcr": 2
    },
    {
     "type": "term_extension",
     "effective_date": "2060-01-01",
     "status": "signed",
     "new_end_date": "2060-12-31",
     "note": "automatische Verlängerung um 12 Monate"
    }
   ]
  },
  {
   "number": "SGM-RV-2059-02",
   "seller_key": "morgengrund",
   "buyer_key": "ravenmoor",
   "title": "Garnisonsrationen Kharon und Brennus",
   "start_date": "2059-03-01",
   "start_year": 2059,
   "term_months": 12,
   "base_volume_mcr": 6,
   "price_formula": "fixed",
   "indexation": "none",
   "exclusivity": "none",
   "notice_days": 60,
   "scope": [
    "food"
   ],
   "story": "schließt die Nahrungslücke Kharon (0 Angebote bei 20 Nachfragen)",
   "amendments": [
    {
     "type": "force_majeure_clause",
     "effective_date": "2059-03-01",
     "status": "signed",
     "proposed_date": "2059-02-15",
     "initiated_by": "morgengrund",
     "note": "Ernteausfallklausel; Vorbild sind die Ernteausfälle bei Lichtacker (Ereignisse 61, 71)"
    },
    {
     "type": "term_extension",
     "effective_date": "2060-02-29",
     "status": "proposed",
     "proposed_date": "2059-12-20",
     "new_end_date": "2061-02-28",
     "initiated_by": "ravenmoor"
    }
   ]
  }
 ]
}
```
