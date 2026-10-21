# Phase 2 – Vorschlag Team B: Verknüpfungen der 18 Firmen

Stand: 20.10.2026 · Grundlage: beide Phase-1-Berichte, `NACHRICHTEN.md`, das Skript
`generate_space_trading_data.py` und eigene Auswertungen der Bestands-DB
`/home/user/bestand/space_trading_game_bestand.db` (Seed 42, nur lesend, pandas/sqlite3). Alle Vertrags-, Bestell-,
Ereignis- und Mitarbeiternummern unten stammen aus dieser Datenbank.

## Kurzfassung

| Thema | Ergebnis |
|---|---|
| Aktive Handelsvereinbarungen | **47** gerichtete Vereinbarungen: 14 Bestand (13 Blueprint + die im Bestand aktive optionale `helix -> corvane`), 16 von Team A, 14 von Team B, 3 teamübergreifend. Es gibt 37 direkt verbundene Firmenpaare von 153 möglichen. |
| Größenregeln | Alle 18 Firmen liegen in ihrem Bereich, alle haben mindestens eine ausgehende Vereinbarung (Tabelle 3.2). |
| Hub | **Helix Meridian** (large) mit 7 direkten Partnern und 10 Vereinbarungen. Graufalk und Ravenmoor haben ebenfalls 7 Partner, aber weniger Vereinbarungen (9 bzw. 8), und sind ebenfalls large. |
| Nur indirekt verbunden | 67 Paare mit gemeinsamem Zwischenhändler, zum Beispiel Feldspat ↔ Raureif (über Eisenkrone), Driftwood ↔ Ravenmoor (über Helix), Lichtacker ↔ Pionierwerk (über Kuppelwerk), Kometenpost ↔ Graufalk (über Cindervale/Lanternfish) |
| Historische Partnerschaften | 5 (1 Bestand, 1 Team A, 3 neu von Team B) |
| Rivalitäten | 12 (4 Bestand, 3 Team A, 5 Team B) |
| Rahmenverträge | **16**: 6 für Bestandspaare (darunter fallen 337 bestehende Verträge mit 2.308 Mio. CR), 4 für Team A, 5 für Team B, 1 teamübergreifend. Dazu 58 Nachträge. |
| Schriftverkehr | Tabelle `correspondence` mit 17 Brieftypen. Schätzung: etwa 700 Schreiben zu Bestandsobjekten, insgesamt etwa 2.000–2.400 |

Der Zusammenhang in einem Satz: **Echte Brüche im Bestand erzeugen die neuen Partnerschaften.** Bei Helix brechen
Verbundstahl-Verträge, daraufhin fällt das Vorkaufsrecht im Rahmenvertrag weg und Kuppelwerk kommt ins Geschäft.
Helium-3-Verträge an Corvane brechen, Helium-3 wird per Nachtrag aus dem Helix-Rahmen genommen und Emberline
übernimmt. Lieferungen warten auf Geleitschutz, daraus entsteht die Geleitschutzklausel mit Ravenmoor. Die
KI-Ausfälle in Förster führen zur Kündigungsandrohung gegen Cindervale.

---

## 1. Antworten auf NACHRICHTEN.md und Abgleich

- **Fragen von Team A an Team B** (Phase 1): wurden alle schon im Phase-1-Eintrag von Team B beantwortet. Corvane
  brauchen wir nicht, die Richtung ist „neue Firma -> Bestandsfirma“, die Codes stehen fest. Neue Fragen an uns gibt es
  nicht.
- **Unsere offenen Fragen an Team A** sind noch unbeantwortet. Für diesen Vorschlag nehmen wir deshalb an:
  1. `kuppelwerk -> pionierwerk` und `second_hull -> graufalk` werden angenommen (Team A hatte freie Plätze angeboten).
  2. `raureif -> emberline` **streichen wir**. Vaskar und Pellora liegen etwa 820 Raumeinheiten auseinander, und
     Emberline fördert Helium-3 selbst. Die Kante wäre also unplausibel, und Emberline bliebe ohne sie bei 5 Plätzen.
  3. **Neue teamübergreifende Kante `graufalk -> ravenmoor`** (supply_agreement): Die Werft liefert Rumpfplatten und
     Triebwerksteile für die Geleitflotte. Graufalk käme damit auf 9 Plätze, Ravenmoor auf 8. Team A bitte bestätigen.
  4. Die optionale Vereinbarung `lanternfish -> kometenpost` (p = 0,5) schlagen wir als **feste** Kante vor. Sie hängt
     dann nicht mehr vom Zufallsstrom ab, und Lanternfish und Kometenpost kommen beide auf 3 von 3. Team A entscheidet.
  5. Infrastruktur in Phase 2 (Vorschlag zur Aufteilung): **Team A** übernimmt den zweiten Durchlauf (eigener RNG und
     Faker, Archetyp-Filter, QA 6/6/6 mit Bestandsvergleich). **Team B** übernimmt `framework_agreements`,
     `framework_amendments`, `framework_agreement_scope`, `correspondence` und die neuen QA-Prüfungen dazu.
- **Korrekturen an unserem Phase-1-Bericht** nach genauerer Abfrage:
  - `HMX-CTR-2059-0242` ist wegen einer **Quarantäneprüfung** gebrochen, nicht wegen Piraterie.
  - `EKM-VTR-2058-0107` startet in der Bergbaustation Hande (**Halcyon**), nicht in Brennus.
  - Der Rahmenvertrag Eisenkrone -> Helix heißt deshalb „Erze und Energie Brennus/Halcyon – Kharon/Sol“.

## 2. Was aus dem Bestand genutzt wird (Auswertung)

| Befund (Bestands-DB) | Verwendung |
|---|---|
| Es gibt 475 Verträge der Typen `framework`, `recurring_supply` und `exclusive_supply`. 337 davon gehören zu den 6 Bestandspaaren, die einen Rahmenvertrag bekommen, mit zusammen 2.308 Mio. CR (ohne stornierte). | Diese Verträge kommen unter Rahmenverträge (Abschnitt 6). Aus ihrem kumulierten Volumen leiten sich die Volumen-Nachträge ab. |
| Erstes Auftreten jeder Warenkategorie je Paar (z. B. Helix -> Lichtacker: Medizin erst ab 19.09.2057) | Daraus ergeben sich datierte Nachträge „neue Waren“. |
| 80 Verträge sind gebrochen. 8 davon wegen „Geleitschutz abgewartet“, 14 Lieferungen mit diesem Zwischenfall laufen über Kharon. | Daraus entstehen Verzugsbeschwerden, Vertragsstrafenbescheide und die Geleitschutzklausel. |
| Helix -> Corvane: Helium-3 bis 18.12.2058, danach nur noch Antimaterie (`HMX-CTR-2059-0217`, Entwurf `HMX-CTR-2060-0281`) | Nachtrag „Helium-3 aus dem Rahmen genommen“ zum 15.03.2059, danach übernimmt Emberline |
| Lichtacker verkauft Rohstoffe exklusiv an Corvane (`LAK-VTR-2058-0033`, `-0039` **storniert**, `-0045`), obwohl Eisenkrone im Joint Venture Rohstoffe liefert | Abmahnung wegen Vorkaufsrecht. Die echte Stornierung von `LAK-VTR-2058-0039` wird damit erklärt. |
| Eisenkrone -> Lichtacker: drei Energieverträge gebrochen, trotzdem neuer Helium-3-Vertrag `EKM-VTR-2059-0197` (aktiv) und Entwurf `EKM-VTR-2060-0230` | Daraus wird keine Kündigung, sondern eine Kündigungs**androhung**, auf die ein Preisnachlass per Nachtrag folgt. Der Bestand bleibt dadurch widerspruchsfrei. |
| 182 überfällige Bestellungen, 93 davon von Partnerfirmen. Die älteste ist `EKM-BST-2057-00352` von Feldspat (4,79 Mio. CR, seit Juli 2057 überfällig). | Daraus entstehen Mahnungen und die Geschichte „Feldspat ist bei Eisenkrone verschuldet“. |
| 7 Bestellungen sind zum Stichtag verspätet und offen, z. B. `EKM-BST-2059-02343` (Brennus Schacht VII -> Kharon Exchange IX, 3,63 Mio. CR) | Offene Fälle im Posteingang zum Spielstart |
| Ereignisse 19/36/70 (KI-Ausfall Förster), 26/58 (Söldner-Razzien), 30 (Asteroidensturm Halcyon Works VI), 51/74 (Piraten Kharon), 52 (Rohstofffund Becker), 61/71 (Ernteausfall Hartmann-Gartenring) | Auslöser für Nachträge, Rivalitäten und Gerüchte |
| Schlüsselmitarbeiter mit IDs (Vorstände, Partnerbetreuung, Marktaufklärung, Stationsleitungen, Finanzen) | Absender und Empfänger der Schreiben (Abschnitt 7.4) |
| Plausibilitäts-Hinweis: Einkäufe bei Partnern erscheinen beim Käufer nicht als Kosten. Feldspat kauft zum Beispiel für 290,8 Mio. CR bei Eisenkrone, setzt aber selbst nur 31,7 Mio. CR um. | Diese Unstimmigkeit lassen wir im Bestand bewusst stehen (Bestandsschutz). Feldspat bekommt deshalb **keinen** Rahmenvertrag, die Lücke wird als Verschuldungsgeschichte erzählt. |

---

## 3. Gerichtete Handelsvereinbarungen

### 3.1 Liste (Verkäufer -> Käufer)

Spalte „Käufer-Stationen“: Stationstypen des Käufers, die laut `CATEGORY_CONSUMERS` die Waren verbrauchen. Es zählen
nur Pflichtstationen, die Zuordnung ist also garantiert. B = Bestand, A = Team A, T = teamübergreifend.

**Bestand (unverändert, 14):** `eisenkrone->helix` supply_agreement, `helix->eisenkrone` strategic_alliance,
`helix->lichtacker` distribution_agreement, `lichtacker->helix` supply_agreement, `corvane->helix` licensing,
`feldspat->helix` consignment, `driftwood->helix` consignment, `feldspat->eisenkrone` supply_agreement,
`eisenkrone->feldspat` supply_agreement, `eisenkrone->lichtacker` supply_agreement, `corvane->eisenkrone`
supply_agreement, `eisenkrone->corvane` joint_venture, `lichtacker->corvane` supply_agreement sowie
`helix->corvane` logistics_partnership. Die letzte stammt aus `OPTIONAL_PARTNERSHIPS`, ist im Bestand aktiv und bleibt
im Bestandsstrom, damit das Würfelergebnis gleich bleibt.

**Team A (16, aus phase1_team_a.md übernommen, Prüfung der Verbraucher siehe dort):** `graufalk->helix`,
`cindervale->eisenkrone`, `kuppelwerk->lichtacker`, `emberline->corvane`, `cindervale->graufalk`,
`graufalk->cindervale` (strategic_alliance), `emberline->graufalk`, `kuppelwerk->graufalk`, `graufalk->emberline`,
`emberline->kuppelwerk`, `emberline->cindervale`, `cindervale->kometenpost` (consignment), `kometenpost->cindervale`
(logistics_partnership), `cindervale->lanternfish`, `lanternfish->graufalk` und `lanternfish->kometenpost`
(consignment, Vorschlag: fest). Wir haben nachgeprüft: `cindervale -> eisenkrone` funktioniert nur über die 3
Bergbaustationen der Eisenkrone, weil sie keine Forschungsstation hat. Das reicht für ≥ 4 Routen.

**Team B und teamübergreifend (17):**

| # | Verkäufer -> Käufer | Typ | Waren | Käufer-Stationen | Plausibilität | Spielspaß | Anker im Bestand |
|---|---|---|---|---|---|---|---|
| 1 | raureif -> pionierwerk | supply_agreement | Wasser-, Ammoniak-, Stickstoffeis, Helium-3, Deuterium | industrial ×2, trade_hub (Isolde, Myrrhen) | Ohne Volatile gibt es in den Kolonien keine Luft, kein Wasser und keinen Brennstoff | Langstrecken-Massengut Vaskar–Isolde (≈ 283 Einheiten) | Isolde hat heute 0 Stationen |
| 2 | pionierwerk -> morgengrund | supply_agreement | Lebenserhaltung, Polymere, Habitatmodule (von Kuppelwerk), Terraforming-Kulturen | agricultural (Isolde) | Ein Generalausrüster beliefert die Genossenschaft | Erste Kolonie-Aufträge für Einsteiger | – |
| 3 | morgengrund -> pionierwerk | supply_agreement | Lebensmittel, Spirituosen | industrial, trade_hub | Die Bautrupps essen vor Ort | Kurze, sichere Route innerhalb von Isolde | Ernteausfälle bei Lichtacker (61, 71) |
| 4 | ravenmoor -> pionierwerk | logistics_partnership | Feldbedarf, Sensorarrays, Geleitschutzdrohnen | trade_hub, agricultural, research | Baustellen am Rand brauchen Schutz | Geleitschutz als Vertragsbestandteil | – |
| 5 | pionierwerk -> ravenmoor | supply_agreement | Bauteile, Lebenserhaltung, Module für Bastionen | military ×2, trade_hub, free_port | Bastionen werden ausgebaut | Ravenmoor ist Kunde und Lieferant zugleich | – |
| 6 | outmark -> pionierwerk | licensing | Vermessungsdatenkerne, Sensorarrays | trade_hub | Kolonien werden dort gebaut, wo vermessen wurde | Daten als Spionageziel | Fund 52 Becker |
| 7 | second_hull -> pionierwerk | supply_agreement | Recyclingmetall (Nickel-Eisen, Titan, Platinmetalle) | industrial ×2, trade_hub | Billigster Metalllieferant am Rand | Billige Ware, aber riskante Route aus Nyx | Nyx hat heute 1 Station |
| 8 | second_hull -> ravenmoor | consignment | Aufbereitete Rumpfplatten, Triebwerksteile | military, trade_hub, free_port | Ravenmoor verkauft in Kommission weiter | Herkunft der Teile fraglich (Driftwood-Wracks?) | – |
| 9 | raureif -> ravenmoor | supply_agreement | Treibstoff, Plasmagas, Brennstoffzellen | military ×2, trade_hub, free_port | Die Geleitflotte braucht Treibstoff | Freihafen Vaskar ist `lawless` | – |
| 10 | ravenmoor -> outmark | logistics_partnership | Expeditionsversorgung: Rationen, Feldmedizin, Bauteile | research, mining (Serravel) | Vermesser arbeiten im Niemandsland | Expeditionen mit Begleitschutz | – |
| 11 | morgengrund -> ravenmoor | supply_agreement | Rationen | military ×2, trade_hub | Füllt die Lücke Kharon food 0/20 und Brennus food 0/7 | Kleine Genossenschaft beliefert Söldner (moralischer Konflikt) | Bestandslücke |
| 12 | outmark -> raureif | supply_agreement | Bergbaudrohnen, Sensorarrays | mining ×2 | Prospektion für Eismonde | – | – |
| 13 | raureif -> eisenkrone | supply_agreement | Eis, Helium-3, Deuterium | industrial ×4, mining ×3 | Konkurrenz zu Feldspat (heute nur 6,0 Mio. CR an Eisenkrone) | Preiskampf nach Fund 52 | Fund 52, `feldspat->eisenkrone` |
| 14 | ravenmoor -> helix | logistics_partnership | Geleitschutzdrohnen, Sensoren, Rationen, Feldmedizin | trade_hub ×3, free_port ×4, military ×2 | Kharon: Medizin 3/12, food 0/20; 8 Verträge brechen wegen Geleitschutz | Geleitschutz-Rahmenvertrag, Partner und Rivale zugleich | Razzia 26, Piraten 16/51/74 |
| T1 | kuppelwerk -> pionierwerk | supply_agreement | Habitatmodule, Sinterbausteine | industrial (Extra-Verbraucher), agricultural, trade_hub | Kuppelwerk baut die Habitate, Pionierwerk rüstet sie aus | Großvolumige Module als Fortschrittsziel | – |
| T2 | second_hull -> graufalk | supply_agreement | Recyclingmetall, Rumpfplatten | industrial ×2, trade_hub (Orrin, Sol) | Werften verarbeiten Schrott | Kernraum gegen Nyx | Förster-Ausfälle (Eisenkrone-Engpass) |
| T3 | graufalk -> ravenmoor | supply_agreement | Rumpfplatten, Triebwerksteile, Reaktorkomponenten | military ×2, trade_hub, free_port | Die Geleitflotte braucht Werftteile | Bindet die beiden neuen Cluster direkt | 86 Verspätungen wegen Triebwerksschäden |

Alle Vereinbarungen mit Bestandsfirmen laufen in der Richtung „neue Firma -> Bestandsfirma“. Routen, Verträge und
Kunden der Bestandsfirmen bleiben dadurch unverändert. Bestandsstationen sind nur zusätzliche Ziele neuer Routen.

### 3.2 Zählung (aktive Vereinbarungen, beide Richtungen)

| Firma | Größe | Vereinbarungen | erlaubt | direkte Partner | ausgehend | frei |
|---|---|---|---|---|---|---|
| Feldspat | small | 3 | 1–3 | 2 | 2 | 0 |
| Driftwood | small | 1 | 1–3 | 1 | 1 | 2 |
| Lichtacker | medium | 5 | 3–6 | 4 | 2 | 1 |
| Corvane | medium | 6 | 3–6 | 4 | 2 | 0 |
| Eisenkrone | large | 9 | 6–10 | 6 | 4 | 1 |
| **Helix (Hub)** | large | **10** | 6–10 | **7** | 3 | 0 |
| Graufalk | large | 9 | 6–10 | 7 | 4 | 1 |
| Cindervale | large | 7 | 6–10 | 5 | 4 | 3 |
| Kuppelwerk | medium | 4 | 3–6 | 4 | 3 | 2 |
| Emberline | medium | 5 | 3–6 | 4 | 4 | 1 |
| Kometenpost | small | 3 | 1–3 | 2 | 1 | 0 |
| Lanternfish | small | 3 | 1–3 | 3 | 2 | 0 |
| Pionierwerk | large | 8 | 6–10 | 6 | 2 | 2 |
| Ravenmoor | large | 8 | 6–10 | 7 | 3 | 2 |
| Raureif | medium | 4 | 3–6 | 4 | 3 | 2 |
| Outmark | medium | 3 | 3–6 | 3 | 2 | 3 |
| Morgengrund | small | 3 | 1–3 | 2 | 2 | 0 |
| Second Hull | small | 3 | 1–3 | 3 | 3 | 0 |

Summe: 94 Beteiligungen, also 47 Vereinbarungen. Die Prüfung lief per Skript über die Liste im JSON-Block.

**Netzprüfung:** Das Netz ist zusammenhängend (18 von 18 Firmen erreichbar) und deutlich unvollständig (37 von 153
Paaren direkt verbunden). Hub ist Helix: Die QA sortiert nach Partnern und dann nach Vereinbarungen, Helix kommt auf
7/10, Graufalk auf 7/9, Ravenmoor auf 7/8. Selbst wenn sich die Reihenfolge ändert, bleibt der Hub eine große Firma.
Hinweis: Helix ist mit 10 voll. Weitere Kanten zu Helix sind nicht mehr möglich, freie Plätze für spätere
Spielereignisse gibt es bei Cindervale, Outmark, Kuppelwerk, Raureif, Pionierwerk und Ravenmoor.

**Paare, die nur über Zwischenhändler verbunden sind (Auswahl mit Geschichte):**

| Paar | Zwischenhändler | Warum das Spaß macht |
|---|---|---|
| Feldspat ↔ Raureif | Eisenkrone | Beide liefern Eis und Helium-3 an Eisenkrone, ohne direkten Kontakt. Eisenkrone spielt sie gegeneinander aus. |
| Driftwood ↔ Ravenmoor | Helix | Erbitterte Gegner mit demselben Großkunden. Helix wird zum heiklen Vermittler. |
| Lichtacker ↔ Pionierwerk | Kuppelwerk | Rivalen um Isolde. Kuppelwerk kennt die Baupläne beider Seiten, das ist eine Informationsquelle. |
| Eisenkrone ↔ Pionierwerk | Raureif | Konkurrenten bei Industriegütern, die beide vom selben Volatile-Lieferanten abhängen. |
| Helix ↔ Morgengrund | Ravenmoor | Die Rationen der Genossenschaft erreichen die Kharon-Stationen nur über Ravenmoor. |
| Kometenpost ↔ Graufalk | Cindervale, Lanternfish | Beispiel von Team A |

---

## 4. Historische (beendete) Partnerschaften

Die Daten sind fest vorgegeben statt gewürfelt, damit sie zu den Ankern passen. Alle liegen innerhalb der Bedingung
aus `generate_partnerships`: Beginn frühestens im Jahr nach der Gründung, Ende spätestens 120 Tage vor dem
Datenzeitraum des Käufers.

| Verkäufer -> Käufer | Typ | Zeitraum | Ende, Anlass | Story-Hook |
|---|---|---|---|---|
| corvane -> driftwood | supply_agreement | Bestand (2057-04-27 bis 2058-07-17) | unverändert | Vorgeschichte der Spionagerivalität |
| eisenkrone -> graufalk | supply_agreement | Team A | Ausgliederung der Werftsparte | „offene Rechnung“ |
| lichtacker -> pionierwerk | supply_agreement | 2045-03 bis 2053-06-30 | Pionierwerk baut eigene Gartenringe auf Serravel und erklärt die Pachtansprüche von Lichtacker auf Isolde für Makulatur | Grundlage der Rivalität `territorial_claims` Isolde. Kurz danach gründet sich Morgengrund (2053–2057) mit Rückendeckung von Pionierwerk. |
| outmark -> feldspat | licensing | 2055-02 bis 2058-06-30 | Feldspat kündigt die Datenlizenz, weil sie zu teuer ist | Ein Jahr später findet Feldspat genau dort ein Vorkommen (Ereignis 52, 14.07.2059). Hat Feldspat die Daten behalten oder gekauft? |
| driftwood -> second_hull | consignment | 2057-05 bis 2058-07-01 | Second Hull kündigt wegen der Lizenzauflagen für Bergegut aus Nyx. Zwei Tage vorher fand die Söldner-Razzia 26 statt (30.06.2058). | Ehemalige Partner werden Rivalen, dasselbe Muster wie Corvane/Driftwood im Bestand |

---

## 5. Rivalitäten und Spionage-Potenzial

| # | Firma | Rivale | Typ | System | seit | Intensität / Spionagerisiko | Anker | Spionage-Zugang (Mitarbeiter-ID) |
|---|---|---|---|---|---|---|---|---|
| B1 | eisenkrone | helix | market_dominance | sol | Bestand | Bestand | – | Desiree Schwartz (299, Bestechlichkeit 78) |
| B2 | driftwood | corvane | industrial_espionage | halcyon | Bestand | Bestand | – | Richard Chavez (120) |
| B3 | feldspat | driftwood | territorial_claims | kharon | Bestand | Bestand | – | – |
| B4 | lichtacker | eisenkrone | resource_competition | myrrhen | Bestand | Bestand | – | Kaspar Täsche (43) |
| A1 | graufalk | eisenkrone | market_dominance | halcyon | Team A | Team A | Ereignisse 19/36/70 | Esther Bauer (170, 76) |
| A2 | cindervale | helix | market_dominance | sol | Team A | Team A | HMX-CTR-2057-0050, -2058-0121 | Desiree Schwartz (299) |
| A3 | emberline | eisenkrone | resource_competition (eigener Text) | myrrhen | Team A | Team A | EKM-VTR-2058-0099, -2059-0167, Seip | Hans-Werner Eberhardt (45) als Adressat |
| N1 | lichtacker | pionierwerk | territorial_claims (eigener Text „Pachtrechte“) | isolde | 2053-07-01 | 60 / 55 | historische Partnerschaft, Isolde im Lichtacker-Territorium ohne Station | Kaspar Täsche (43, Bestechlichkeit 61, gierig) |
| N2 | ravenmoor | driftwood | **armed_conflict** (neu) | nyx | 2058-06-30 | 85 / 70 | Razzien 26 und 58, Piraten 45/54/57/67 | Carlos Osborne (29, Loyalität 3, Bestechlichkeit 100), Nathan Hines (33, 81) |
| N3 | outmark | feldspat | territorial_claims | brennus | 2059-07-14 | 65 / 80 | Fund 52, historische Lizenz | Slavko Geisel (16, Bestechlichkeit 96) |
| N4 | ravenmoor | helix | market_dominance | kharon | 2057-11-17 | 55 / 45 | Piratenangriff 16 auf Kharon Landing IV, Razzia 26 | Wayne Jacobson (302, gierig, 73), Tyler Garcia (395, 71) |
| N5 | second_hull | driftwood | territorial_claims | nyx | 2058-07-01 | 50 / 40 | historische Partnerschaft, Wracks in Nyx | Douglas Lawson (27, Leitung Smugglers' Haven Hall) |

**Technik:**
1. Neuer Typ `armed_conflict` mit `intensity_ranges["armed_conflict"] = (60, 90)` (Texte wie in Phase 1).
2. Statt eines weiteren Typs für Emberline und Lichtacker/Pionierwerk schlagen wir eine Tabelle
   `RIVALRY_TEXT_OVERRIDES[(company_key, rival_key)] = {"de_DE": …, "en_US": …}` vor. Der Text zu `resource_competition`
   („Wassereis“) und zu `territorial_claims` („Schürfrechte“) passt dort nicht.
3. Für angekerte Rivalitäten werden `since_date`, `intensity` und `espionage_risk` fest gesetzt (siehe Spalten). Das
   ist Datenpflege, kein Würfeln.
4. Driftwood hat damit 4 Rivalitäten (Corvane, Feldspat, Ravenmoor, Second Hull). Das ist gewollt: Driftwood ist der
   Paria des Grenzlands. Eisenkrone hat ebenfalls 4 (Helix, Lichtacker, Graufalk, Emberline) als Gegenspieler im
   Kernraum.

**Spielspaß:** Jede Rivalität hat mindestens einen bestechlichen oder gesprächigen Mitarbeiter mit echter ID.
Spionage läuft im Spiel über diese Personen und über vertrauliche Schreiben (Abschnitt 7). Bei N2 und N3 kann der
Spieler die Wahrheit herausfinden: Hat Osborne geredet? Hat Geisel die Daten gekauft?

---

## 6. Rahmenverträge

### 6.1 Begriff und Abgrenzung

Im Bestand gibt es schon den Vertragstyp `contract_type = 'framework'`, Bezeichnung „Rahmenvertrag“. Das ist aber ein
**einzelner Vertrag mit 2–5 Abrufen**. Der neue **Rahmenvertrag** (`framework_agreements`) liegt eine Ebene höher: Er
legt Laufzeit, Volumen, Preisformel, Exklusivität und Kündigung für alle Einzelverträge eines Paares fest. Die
Bezeichnung von `CONTRACT_TYPES["framework"]` bleibt unverändert, weil sie in den Beschreibungstexten der
Bestandsverträge steht. Zur Unterscheidung tragen Rahmenverträge eine eigene Nummer: `{SKU}-RV-{Jahr}-{nn}` (de_DE)
bzw. `{SKU}-MSA-{Jahr}-{nn}` (en_US, „Master Supply Agreement“).

### 6.2 Welche Vereinbarungen bekommen einen Rahmenvertrag?

Regel:
- **immer** bei `strategic_alliance`, `joint_venture`, `distribution_agreement` und `logistics_partnership`, wenn das
  Vertragsvolumen der Richtung ≥ 50 Mio. CR ist oder ein Anker vorliegt
- bei `supply_agreement` nur mit Anker im Bestand (gebrochene Verträge, Ereignis, Lückenschluss) oder als
  Versorgungsrückgrat einer neuen Region
- bei `licensing` nur mit Exklusivität
- **nie** bei `consignment`, weil Kommissionsware keine Mindestabnahme hat

Daraus ergeben sich 16 Rahmenverträge. Nicht berücksichtigt sind kleine Bestandspaare (`corvane->helix`,
`corvane->eisenkrone`, `lichtacker->helix`, `lichtacker->corvane` mit jeweils unter 70 Mio. CR) und
`eisenkrone->feldspat` (Plausibilitäts-Hinweis aus Abschnitt 2).

### 6.3 Datenmodell

```sql
CREATE TABLE framework_agreements (
    framework_agreement_id INTEGER PRIMARY KEY,
    agreement_number TEXT NOT NULL UNIQUE,             -- HMX-MSA-2057-01, EKM-RV-2057-01
    partnership_id INTEGER NOT NULL REFERENCES trade_partnerships(partnership_id),
    seller_company_id INTEGER NOT NULL REFERENCES companies(company_id),
    buyer_company_id INTEGER NOT NULL REFERENCES companies(company_id),
    title TEXT NOT NULL,
    language TEXT NOT NULL,                            -- Sprache des Verkäufers
    signed_date TEXT NOT NULL,
    start_date TEXT NOT NULL,
    term_months INTEGER NOT NULL CHECK(term_months > 0),
    original_end_date TEXT NOT NULL,
    current_end_date TEXT NOT NULL,                    -- nach Verlängerungen
    status TEXT NOT NULL CHECK(status IN ('negotiating','active','expired','terminated','suspended')),
    base_volume REAL NOT NULL CHECK(base_volume > 0),  -- CR, bei Abschluss
    current_volume REAL NOT NULL CHECK(current_volume > 0),
    min_offtake_pct INTEGER NOT NULL CHECK(min_offtake_pct BETWEEN 0 AND 100),
    price_formula TEXT NOT NULL CHECK(price_formula IN ('fixed','index_linked','cost_plus','spot_discount')),
    price_index_category TEXT,                         -- Kategorie, deren Preisindex gilt
    base_discount_pct REAL NOT NULL DEFAULT 0,
    adjustment_cap_pct REAL,                           -- max. Anpassung pro Jahr
    exclusivity TEXT NOT NULL CHECK(exclusivity IN ('none','right_of_first_refusal','category_exclusive',
                                                     'system_exclusive')),
    exclusive_category TEXT,
    exclusive_system_id INTEGER REFERENCES star_systems(system_id),
    notice_period_days INTEGER NOT NULL,
    auto_renewal INTEGER NOT NULL DEFAULT 0 CHECK(auto_renewal IN (0,1)),
    renewal_months INTEGER,
    penalty_rate_pct_per_day REAL NOT NULL,            -- Vertragsstrafe in % des offenen Werts je Tag
    escort_company_id INTEGER REFERENCES companies(company_id),   -- z. B. Ravenmoor
    seller_signatory_id INTEGER REFERENCES employees(employee_id),
    buyer_signatory_id INTEGER REFERENCES employees(employee_id),
    description TEXT NOT NULL,
    CHECK(seller_company_id <> buyer_company_id),
    CHECK(current_end_date >= original_end_date)
);
CREATE TABLE framework_agreement_scope (               -- welche Waren gedeckt sind, mit Gültigkeit
    scope_id INTEGER PRIMARY KEY,
    framework_agreement_id INTEGER NOT NULL REFERENCES framework_agreements(framework_agreement_id),
    category_code TEXT NOT NULL,
    archetype_code TEXT,                               -- NULL = ganze Kategorie
    valid_from TEXT NOT NULL,
    valid_to TEXT,
    added_by_amendment_id INTEGER REFERENCES framework_amendments(amendment_id),
    removed_by_amendment_id INTEGER REFERENCES framework_amendments(amendment_id)
);
CREATE TABLE framework_amendments (
    amendment_id INTEGER PRIMARY KEY,
    framework_agreement_id INTEGER NOT NULL REFERENCES framework_agreements(framework_agreement_id),
    amendment_no INTEGER NOT NULL,
    amendment_type TEXT NOT NULL CHECK(amendment_type IN ('volume_increase','volume_reduction','product_addition',
        'product_removal','price_adjustment','term_extension','exclusivity_added','exclusivity_removed',
        'penalty_clause','escort_clause','termination_notice')),
    proposed_date TEXT NOT NULL,                       -- ≤ 2059-12-31
    signed_date TEXT,
    effective_date TEXT NOT NULL,                      -- darf nach dem Stichtag liegen
    status TEXT NOT NULL CHECK(status IN ('proposed','signed','rejected','withdrawn')),
    volume_after REAL, end_date_after TEXT, price_change_pct REAL,
    category_code TEXT, archetype_code TEXT,
    exclusive_system_id INTEGER REFERENCES star_systems(system_id),
    escort_company_id INTEGER REFERENCES companies(company_id),
    trigger_event_id INTEGER REFERENCES events(event_id),
    trigger_contract_id INTEGER REFERENCES contracts(contract_id),
    trigger_order_id INTEGER REFERENCES orders(order_id),
    description TEXT NOT NULL,
    UNIQUE(framework_agreement_id, amendment_no)
);
-- contracts: neue Spalte (nullable), Bestandszeilen sonst unverändert
ALTER TABLE contracts ADD COLUMN framework_agreement_id INTEGER REFERENCES framework_agreements(framework_agreement_id);
```

### 6.4 Wie Einzelverträge an Rahmenverträgen hängen

Ein Vertrag `c` gehört zum Rahmenvertrag `f`, wenn alle folgenden Bedingungen gelten. Die Zuordnung ist eine **reine
Funktion der Daten** und verbraucht keine Zufallszahlen, sie verschiebt also keinen Zufallsstrom.
1. `c.company_id = f.seller_company_id` und `c.partner_company_id = f.buyer_company_id`
2. `c.contract_type IN ('framework','recurring_supply','exclusive_supply')`. `spot`, `emergency_supply` und
   `consignment` bleiben bewusst außerhalb, damit es für den Spieler sichtbare Spotgeschäfte gibt.
3. `f.start_date ≤ c.start_date ≤` Laufzeitende, das zum Vertragsbeginn galt (einschließlich unterschriebener
   Verlängerungen)
4. Die Warenkategorie bzw. der Archetyp des Produkts liegt am Vertragsbeginn im Geltungsbereich (`framework_agreement_scope`)

**Nachweis am Bestand:** Mit den Parametern aus 6.5 werden **alle 337** Kandidatenverträge der 6 Bestandspaare
zugeordnet (2.308 Mio. CR, darunter 39 gebrochene). Keiner fällt aus dem Geltungsbereich, weil die Nachträge über neue
Waren genau auf das erste Auftreten jeder Kategorie datiert sind.

**Nachträge aus den Daten ableiten (Bestandspaare):**
- **Volumen:** Überschreitet die kumulierte Summe der zugeordneten (nicht stornierten) Verträge 90 % des aktuellen
  Volumens, entsteht ein `volume_increase` um eine feste Stufe. Wirksam wird er zum Monatsersten des auslösenden
  Vertrags, der Auslöser wird als `trigger_contract_id` gespeichert. Liegt der Auslöser nach dem Stichtag (Entwurf
  2060), ist der Nachtrag `proposed` und wurde im Dezember 2059 angeboten.
- **Neue Waren:** `product_addition` zum Monatsersten vor dem ersten Vertrag einer neuen Kategorie
- **Verlängerung:** wenn Verträge (auch Entwürfe) nach dem ursprünglichen Laufzeitende beginnen
- **Strafklausel, Exklusivität, Herausnahme von Waren:** aus gebrochenen Verträgen und Ereignissen (handverlesen, siehe 6.5)

Für neue Paare erzeugt der zweite Durchlauf die Verträge wie bisher. Danach gelten dieselben Regeln. Zusätzlich gibt es
die angekerten Nachträge aus der Tabelle.

### 6.5 Die 16 Rahmenverträge

Volumen in Mio. CR. Indexierung: `index_linked:<Kategorie>` heißt, der Basispreis folgt dem Kategorie-Preisindex
der Zielstation aus `price_history` (Mittel der letzten 3 Stützpunkte), höchstens ± Deckel pro Jahr.

**Bestandspaare (zugeordnete Bestandsverträge in Klammern):**

| Nr. | Paar | Titel | Beginn, Laufzeit | Basis -> aktuell | Preis | Exklusivität | Kündigung | Nachträge (Datum, Typ, Anker) |
|---|---|---|---|---|---|---|---|---|
| HMX-MSA-2057-01 | helix -> lichtacker (54 Verträge, 423,6) | Distributionsrahmenvertrag Agrarringe Tauvel/Aurelis/Myrrhen | 2057-01-01, 36 M. | 250 -> 550 | index_linked, Deckel 8 %/Jahr | Vorkaufsrecht `industrial_goods` | 180 Tage | 2057-04 neue Waren energy, technology · 2057-09 medical · 2058-09 Volumen 400 (HMX-CTR-2058-0161) · **2059-03-15 Vorkaufsrecht entfällt** (HMX-CTR-2057-0043, -2058-0139, -2058-0159 gebrochen, Strafen 47.849 + 129.876 + 653.162 CR) · 2059-10 Volumen 550 und Verlängerung bis 2060-12-31 (HMX-CTR-2059-0259, Entwürfe bis 2060-03) |
| HMX-MSA-2057-02 | helix -> corvane (68, 549,4) | Logistik- und Versorgungsrahmenvertrag Halcyon/Aurelis | 2057-01-01, 36 M. | 300 -> 600 (750 angeboten) | spot_discount 4 % | keine | 120 Tage | 2057-03 technology · 2057-05 energy · 2058-01 industrial_goods, medical · 2058-08 Volumen 450 (HMX-CTR-2058-0152, später gebrochen) · **2059-03-15 Helium-3 herausgenommen** (HMX-CTR-2058-0131: 5 Tage Verzug, 332.509 CR Strafe; HMX-CTR-2057-0014; Sturm 30) · 2059-04 Volumen 600 (HMX-CTR-2059-0213) · 2059-11 Verlängerung bis 2061-12-31 · 2059-12 angeboten: Volumen 750 (Entwurf HMX-CTR-2060-0281) |
| HMX-MSA-2057-03 | helix -> eisenkrone (75, 438,7) | Strategischer Versorgungsrahmen Sol/Halcyon/Brennus | 2057-01-01, 48 M. | 300 -> 450 (550 angeboten) | cost_plus 9 % | keine | 360 Tage | 2057-07 medical, technology, industrial_goods · **2058-03 Volumen auf 250 gesenkt** (KI-Ausfall Förster, Ereignis 19, Einbruch 2058: 53,5 statt 155 Mio.) · 2059-01 Volumen 350 (HMX-CTR-2059-0192) · 2059-06 Volumen 450 (HMX-CTR-2059-0235) · 2059-12 angeboten: Volumen 550 (Entwurf HMX-CTR-2060-0275) |
| EKM-RV-2057-01 | eisenkrone -> corvane (65, 440,9) | Joint-Venture-Liefervertrag Halcyon | 2057-01-01, 60 M. | 350 -> 450 (550 angeboten) | cost_plus 12 % | **Vorkaufsrecht `raw_materials`** | 360 Tage | 2057-05 luxury, technology · 2058-05 Strafklausel verschärft (EKM-VTR-2057-0064, Reaktorkomponenten) · 2059-03 Volumen 450 (EKM-VTR-2059-0160, später gebrochen) · 2059-12 angeboten: Volumen 550 (Entwurf EKM-VTR-2060-0219). Abmahnungen wegen Rohstoffkäufen bei Lichtacker/Helix siehe 7.4 |
| EKM-RV-2057-02 | eisenkrone -> helix (39, 275,9) | Rahmenvertrag Erze und Energie Brennus/Halcyon – Kharon/Sol | 2057-01-01, 42 M. | 200 -> 300 | index_linked raw_materials, Deckel 10 % | keine | 180 Tage | 2057-06 food, technology · 2058-01 industrial_goods · 2058-08 luxury · 2059-02 Volumen 300 (EKM-VTR-2059-0151) · **2059-12-22 angeboten: Geleitschutzklausel, `escort_company_id` = Ravenmoor** (EKM-VTR-2057-0017, -2058-0107, -2059-0162 gebrochen; offen EKM-BST-2059-02343; Piraten 74) · angeboten: Volumen 400 und Verlängerung bis 2061-06-30 (Entwurf EKM-VTR-2060-0234) |
| EKM-RV-2057-03 | eisenkrone -> lichtacker (36, 179,5) | Liefervertrag Industriegüter und Energie Myrrhen/Tauvel | 2057-01-01, 36 M. | 150 -> 200 | index_linked energy, Deckel 6 % | keine | 90 Tage | 2057-08 energy · 2058-02 technology · **2059-10-12 Kündigungsandrohung für Energie** (Lichtacker; EKM-VTR-2058-0099, -2058-0105, -2059-0167, Strafen 219.445 + 60.263 + 58.590 CR), zurückgezogen nach dem Nachtrag · 2059-10-15 Preis −5 % auf Energie und strengere Strafklausel · 2059-11 Volumen 200 und Verlängerung bis 2060-12-31 (EKM-VTR-2059-0211, Entwürfe 2060) |

**Neue Paare:**

| Nr. | Paar | Titel | Beginn, Laufzeit | Basis | Preis | Exklusivität | Nachträge |
|---|---|---|---|---|---|---|---|
| GFW-RV-2057-01 | graufalk -> helix | Flottenrahmenvertrag Rumpf- und Triebwerksteile | 2057-03-01, 48 M. | 180 | index_linked industrial_goods | keine | 2058-12 Volumen +60 (HMX-CTR-2058-0173 Triebwerksteile gebrochen, 86 Verspätungen wegen Triebwerksschäden) · 2059-12-28 angeboten: Eilabrufklausel (offen HMX-ORD-2059-01763, -01788) |
| CCI-MSA-2057-01 | cindervale -> eisenkrone | Rahmenvertrag KI-Leitsysteme und Robotik | 2057-01-01, 36 M. | 120 | fixed + Gewährleistung | Kategorie `technology` für Halcyon-Werke | 2058-03 Gewährleistungsklausel (Ereignis 19) · 2058-12 Preis −8 % (Ereignis 36) · **2059-12-05 Kündigung durch Eisenkrone, 180 Tage Frist** (Ereignis 70), Status `proposed` = Kündigung angekündigt, Ende 2060-06 offen |
| KHB-RV-2059-01 | kuppelwerk -> lichtacker | Rahmenvertrag Verbundstahl und Habitatbaustoffe Tauvel/Myrrhen | 2059-04-01, 24 M. | 60 | index_linked industrial_goods | keine | 2059-10 neue Ware `habitat_modules` für Myrrhen · 2059-12 angeboten: Volumen +30 |
| EFF-MSA-2059-01 | emberline -> corvane | Helium-3-Rahmenvertrag Halcyon Works VI | 2059-04-01, 24 M. | 40 | index_linked energy + Sturmklausel | keine | 2059-10 Volumen +20 · 2059-12 angeboten: Exklusivität Helium-3 in Halcyon |
| RCS-MSA-2058-01 | ravenmoor -> helix | Geleitschutz- und Versorgungsrahmenvertrag Kharon-Korridor | 2058-08-01, 36 M. | 90 | cost_plus 15 % (Geleitpauschale) | System `kharon` für Sicherheitsgüter | 2059-06-15 Volumen +40 (Piraten 51 an Kharon Exchange V) · 2059-12-22 angeboten: Geleitschutz auch für Eisenkrone-Konvois (dreiseitig, siehe EKM-RV-2057-02) |
| RVF-RV-2058-01 | raureif -> eisenkrone | Volatile-Liefervertrag Myrrhen/Brennus | 2058-03-01, 24 M. | 45 | index_linked raw_materials, Mindestpreis | keine | 2059-08-01 Preis −6 % (Eisenkrone verweist auf Fund 52 bei Feldspat: Wassereis und Helium-3 +90 %) · 2059-12 angeboten: Verlängerung 12 M. |
| RVF-RV-2058-02 | raureif -> pionierwerk | Versorgungsrahmen Isolde – Volatile | 2058-01-01, 36 M. | 80 | index_linked energy | System `isolde` | 2058-09 neue Ware `nitrogen_ice` (Terraforming beginnt) · 2059-06 Volumen +30 · 2059-12 angeboten: Preis +10 % (Raureif: lange Wege, Piraterie), in Verhandlung |
| OSP-MSA-2058-01 | outmark -> pionierwerk | Lizenzrahmen Vermessungsdaten Serravel/Isolde | 2058-02-01, 36 M. | 25 | fixed (Lizenz + Stückpreis) | anfangs keine | **2059-08-15 Exklusivität System `serravel`** (Pionierwerk fürchtet Datenlecks nach Fund 52) · 2059-11 neue Ware `terraforming_cultures` |
| SGM-RV-2059-01 | morgengrund -> pionierwerk | Versorgungsrahmen Isolde – Lebensmittel für Bautrupps | 2059-01-01, 12 M., automatische Verlängerung um 12 M. | 5 | fixed + Ernteklausel | keine | 2059-07 Volumen +2 · 2060-01-01 automatische Verlängerung (signed) |
| KHB-RV-2058-01 | kuppelwerk -> pionierwerk | Rahmenvertrag Habitatmodule Isolde | 2058-06-01, 36 M. | 70 | index_linked industrial_goods | Vorkaufsrecht `habitat_modules` | 2059-05 Volumen +35 (zweite Ausbaustufe Serravel) · 2059-11 neue Ware `sinter_blocks` |

Insgesamt 58 Nachträge (36 bei Bestandspaaren, 22 bei neuen Paaren), davon 13 zum Stichtag `proposed` und 1 `withdrawn`, also offene
Verhandlungen zum Spielstart.

**Plausibilität:** Die Volumen liegen bei den Bestandspaaren knapp über den tatsächlichen Vertragssummen (Auslastung
77–98 %). Die Laufzeiten decken den Datenzeitraum der großen Firmen ab (36 Monate). Gebrochene Verträge führen zu
Nachträgen, nicht zum Abbruch. Das entspricht der Realität: Man verhandelt nach, statt einen 400-Mio.-Rahmen
aufzugeben.

**Spielspaß:** Offene Nachträge sind Verhandlungsziele für den Spieler (zum Beispiel als Vermittler der
Geleitschutzklausel). Bei Exklusivitäten lohnt sich Spionage, denn Verstöße lösen Abmahnungen aus. Die Indexierung
koppelt Preise an echte Marktbewegungen (Ereignisse).

### 6.6 QA-Prüfungen (neu)

1. Jeder Rahmenvertrag verweist auf eine aktive Vereinbarung in derselben Richtung.
2. Jeder zugeordnete Vertrag erfüllt die 4 Regeln aus 6.4. Umgekehrt muss jeder Vertrag, der alle Regeln erfüllt,
   auch zugeordnet sein.
3. `current_volume` ≥ Summe der zugeordneten (nicht stornierten) Verträge, Auslastung ≤ 100 %.
4. `current_end_date` = letzte unterschriebene `term_extension`. Nachträge innerhalb eines Rahmenvertrags sind
   fortlaufend nummeriert, `proposed_date` ≤ 2059-12-31.
5. Bestandsschutz: Alle Spalten der Bestandsverträge außer `framework_agreement_id` sind identisch mit der Bestands-DB.

---

## 7. Schriftverkehr

### 7.1 Brieftypen

| `letter_type` | Deutsch | Auslöser (Daten) | Absender -> Empfänger (Rollen) | Kontext-FK | Ton |
|---|---|---|---|---|---|
| `inquiry` | Anfrage | Rahmenvertrag 30–60 Tage vor Beginn, Lücke im Angebot | Partnerbetreuung Käufer -> Partnerbetreuung Verkäufer | partnership | neutral |
| `offer` | Angebot | Antwort auf Anfrage; auch ohne Partnerschaft (Kaltangebot) | Partnerbetreuung Verkäufer | partnership/–, framework | cordial |
| `counter_offer` | Verhandlung / Gegenangebot | 0–2 Runden, nach Vertrauensstufe | Partnerbetreuung/Vorstand | framework | firm |
| `contract_confirmation` | Vertragsbestätigung | Unterschrift des Rahmenvertrags | Vorstand Verkäufer -> Vorstand Käufer | framework | cordial |
| `amendment_offer` | Nachtragsangebot | jeder Nachtrag | Antragsteller laut Nachtrag | amendment | neutral/firm |
| `amendment_confirmation` / `amendment_rejection` | Nachtragsbestätigung / -ablehnung | Nachtrag `signed` / `rejected` | Gegenseite | amendment | – |
| `delivery_notice` | Lieferavis / Verzögerungsavis | Abruf mit Zwischenfall oder offene Bestellung zum Stichtag | Frachtdisposition/Stationsleitung Herkunft -> Stationsleitung Ziel bzw. Kunde | order, shipment | neutral |
| `payment_reminder` | Mahnung (1., 2., letzte) | `payment_status = 'overdue'` | Finanzbuchhaltung Verkäufer -> Firma oder Kunde (`recipient_customer_id`) | order | neutral -> firm |
| `delay_complaint` | Verzugsbeschwerde | Lieferung > 48 h verspätet bei einem Vertragsabruf, oder Vertrag `breached` | Stationsleitung Ziel -> Stationsleitung Herkunft | contract, shipment | firm |
| `penalty_notice` | Vertragsstrafenbescheid | Vertrag `breached`. Betrag = Verzugstage × `penalty_per_day`, wie in `generate_financials` | Vorstand oder Partnerbetreuung Käufer -> Verkäufer | contract | firm/hostile |
| `breach_warning` | Abmahnung | Verstoß gegen Exklusivität oder Gewährleistung | Partnerbetreuung -> Partnerbetreuung | framework, contract | firm |
| `termination_notice` | Kündigung / Kündigungsandrohung | Nachtrag `termination_notice`, Ende einer historischen Partnerschaft | Vorstand -> Vorstand | framework/partnership | hostile |
| `protest` | Protestschreiben | Razzia, Claim-Streit | Vorstand -> Vorstand des Rivalen | rivalry, event | hostile |
| `confidential_tip` | Vertrauliche Mitteilung | Mitarbeiter mit Bestechlichkeit ≥ 70 oder `greedy`/`talkative` gibt Wissen an einen Rivalen | Mitarbeiter -> Marktaufklärung des Rivalen | rivalry, event, contract | – |
| `rumor` | Gerücht | wie oben, aber Wahrheitsgehalt offen (`is_accurate` NULL/0/1) | Mitarbeiter oder anonym -> beliebige Person | rivalry | – |
| `internal_memo` | Interne Notiz | Lagebericht der Marktaufklärung, Bericht nach Ereignis | Mitarbeiter -> Vorstand derselben Firma | event, rivalry | – |

### 7.2 Tabelle `correspondence`

```sql
CREATE TABLE correspondence (
    correspondence_id INTEGER PRIMARY KEY,
    reference_number TEXT NOT NULL UNIQUE,          -- {SKU}-KOR-{Jahr}-{nnnnn} (de) / {SKU}-COR-… (en), Präfix des Absenders
    thread_id INTEGER NOT NULL REFERENCES correspondence(correspondence_id),   -- erstes Schreiben des Vorgangs
    in_reply_to_id INTEGER REFERENCES correspondence(correspondence_id),
    refers_to_correspondence_id INTEGER REFERENCES correspondence(correspondence_id), -- z. B. Leck eines Schreibens
    letter_type TEXT NOT NULL CHECK(letter_type IN ('inquiry','offer','counter_offer','contract_confirmation',
        'amendment_offer','amendment_confirmation','amendment_rejection','delivery_notice','payment_reminder',
        'delay_complaint','penalty_notice','breach_warning','termination_notice','protest','confidential_tip',
        'rumor','internal_memo')),
    sent_at TEXT NOT NULL,                          -- ≤ 2059-12-31T23:59
    read_at TEXT,                                   -- NULL = ungelesen zum Stichtag (Posteingang)
    sender_company_id INTEGER NOT NULL REFERENCES companies(company_id),
    sender_employee_id INTEGER REFERENCES employees(employee_id),   -- NULL nur bei anonymen Gerüchten
    sender_station_id INTEGER REFERENCES stations(station_id),
    recipient_company_id INTEGER REFERENCES companies(company_id),
    recipient_employee_id INTEGER REFERENCES employees(employee_id),
    recipient_customer_id INTEGER REFERENCES customers(customer_id),  -- Mahnungen/Avis an Nicht-Firmenkunden
    language TEXT NOT NULL CHECK(language IN ('de_DE','en_US')),       -- Sprache der Absenderfirma
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    confidentiality TEXT NOT NULL CHECK(confidentiality IN ('public','business','confidential','secret')),
    tone TEXT NOT NULL CHECK(tone IN ('cordial','neutral','firm','hostile')),
    amount REAL CHECK(amount IS NULL OR amount >= 0),                  -- Forderung, Strafe, Angebotswert (CR)
    due_date TEXT,
    response_required INTEGER NOT NULL DEFAULT 0 CHECK(response_required IN (0,1)),
    status TEXT NOT NULL CHECK(status IN ('sent','read','answered','escalated','closed')),
    trust_effect INTEGER NOT NULL DEFAULT 0 CHECK(trust_effect BETWEEN -20 AND 10),
    is_accurate INTEGER CHECK(is_accurate IS NULL OR is_accurate IN (0,1)),  -- nur Tipps/Gerüchte
    intel_value INTEGER NOT NULL DEFAULT 0 CHECK(intel_value BETWEEN 0 AND 100),
    partnership_id INTEGER REFERENCES trade_partnerships(partnership_id),
    framework_agreement_id INTEGER REFERENCES framework_agreements(framework_agreement_id),
    amendment_id INTEGER REFERENCES framework_amendments(amendment_id),
    contract_id INTEGER REFERENCES contracts(contract_id),
    order_id INTEGER REFERENCES orders(order_id),
    shipment_id INTEGER REFERENCES shipments(shipment_id),
    event_id INTEGER REFERENCES events(event_id),
    rivalry_id INTEGER REFERENCES company_rivalries(rivalry_id),
    CHECK(recipient_company_id IS NOT NULL OR recipient_customer_id IS NOT NULL)
);
```

**Bedeutung für das Spiel:** Die Stufen von `confidentiality` entsprechen dem `intel_access_level` (0–3). Ein
Mitarbeiter kann ein Schreiben nur kennen und verraten, wenn seine Stufe ≥ der Vertraulichkeit ist. Das ist die
Brücke zur Spionage. `trust_effect` beschreibt die Wirkung auf `trust_level`, der Generator speichert ihn nur
beschreibend. `read_at` = NULL ergibt den Posteingang beim Spielstart.

### 7.3 Erzeugungsregeln

- **Personen:** Offizielle Schreiben gehen von der Partnerbetreuung mit dem höchsten Einfluss oder von der
  Stationsleitung der betroffenen Station aus. Vertragsbestätigung, Kündigung und Strafen über 250.000 CR
  unterschreibt der Vorstand. Mahnungen kommen von der Finanzbuchhaltung am Hauptsitz, Avis von Frachtdisposition oder
  Stationsleitung der Herkunftsstation. Der Mitarbeiter muss am `sent_at` beschäftigt sein
  (`hire_date ≤ sent_at`, nicht gekündigt).
- **Sprache:** immer die der Absenderfirma. Ein deutsches Haus schreibt an ein englisches auf Deutsch, wie heute bei
  den Vertragstexten. Vorlagen in de_DE und en_US, Datums- und Zahlenformat über `fmt_human_date` und `fmt_number`.
- **Zeitfolge:** Antwort 1–10 Tage nach dem Bezugsschreiben, Verzugsbeschwerde 0–3 Tage nach der tatsächlichen
  Ankunft, Strafbescheid 3–14 Tage nach der Frist, Mahnungen 14/28/45 Tage nach dem Zahlungsziel (`PAYMENT_TERMS_DAYS`).
  Alles vor dem 01.01.2060.
- **Zufall:** Für Bestandsobjekte nutzt die Erzeugung einen **eigenen** Zufallsstrom
  (`random.Random(f"{seed}:correspondence")`), der Bestand bleibt dadurch unberührt. Für Bestandsfirmen werden nur
  vorhandene Mitarbeiter verwendet, es entstehen keine neuen Personen.

### 7.4 Angekerte Vorgänge (Bestandsobjekte, echte IDs)

| # | Datum | Typ | Absender (ID) -> Empfänger (ID) | Bezug | Inhalt, Spielfunktion |
|---|---|---|---|---|---|
| K1 | 2058-07-02 | internal_memo | Wayne Jacobson (302) -> Elizabeth Lopez (293) | Ereignis 26 | Bericht über die Söldner-Razzia in Kharon Landing IV |
| K2 | 2058-07-15 -> 08-01 | offer -> counter_offer -> contract_confirmation | Ravenmoor (Partnerbetreuung, neu) -> David Hendricks (304); Bestätigung Lopez (293) | RCS-MSA-2058-01 | Vom Gegner zum Geleitschutzpartner |
| K3 | 2058-09-12 | rumor (`is_accurate` NULL) | Erin Cisneros (26, Driftwood) -> Elizabeth Lopez (293) | Rivalität N4 | „Jacobson kassiert von Ravenmoor.“ Der Spieler kann nachforschen. |
| K4 | 2058-08-20 / 2058-10-05 | breach_warning -> Antwort | Esther Bauer (170) -> John Aguirre (119) | EKM-RV-2057-01, LAK-VTR-2058-0033 | Abmahnung wegen Vorkaufsrecht für Rohstoffe. Corvane storniert daraufhin LAK-VTR-2058-0039 (im Bestand am 2058-10-12 storniert). |
| K5 | 2059-01-18 / 01-25 | delay_complaint, penalty_notice | Toralf Gerlach (47) -> Kayla Cannon (332); Reimar Rörricht (38) -> Elizabeth Lopez (293) | HMX-CTR-2058-0159 | 6 Tage Verzug, **653.162 CR** Strafe |
| K6 | 2059-03-10 -> 03-15 | breach_warning -> amendment_offer -> amendment_confirmation | Hülya Matthäi (41) -> Kayla Cannon (332) | HMX-CTR-2058-0139, HMX-MSA-2057-01 | Das Vorkaufsrecht für Industriegüter entfällt. |
| K7 | 2059-03-20 | offer -> contract_confirmation (04-01) | Kuppelwerk -> Hülya Matthäi (41) | KHB-RV-2059-01 | Ersatz für den gebrochenen Verbundstahl |
| K8 | 2059-03-07 / 03-12 | delay_complaint, penalty_notice | Matthew Thomas (123) -> Catherine Perry (308, Blair Landing); Jason Armstrong (115) -> Lopez (293) | HMX-CTR-2058-0131 | 332.509 CR, danach Herausnahme von Helium-3 |
| K9 | 2059-03-20 | offer | Emberline -> Matthew Thomas (123) | EFF-MSA-2059-01, Sturm 30 | Helium-3 von Pellora |
| K10 | 2058-08-19 / 08-28 | delay_complaint, penalty_notice | Hans-Werner Eberhardt (45) -> Irmingard Scholl (179); Rörricht (38) -> Roswitha van der Dussen (168) | EKM-VTR-2058-0099 | „Geleitschutz abgewartet“, 219.445 CR |
| K11 | 2059-10-12 -> 10-15 | termination_notice (Androhung) -> amendment_offer -> confirmation | Rörricht (38) -> van der Dussen (168) | EKM-RV-2057-03, EKM-VTR-2059-0167 | Drohung, die Energie zu kündigen, endet mit −5 % |
| K12 | 2059-10-20 | offer (kalt, ohne Partnerschaft) | Emberline -> Eberhardt (45, Agrarstation Seip) | Rivalität A3 | Unbeantwortet. Der Spieler kann vermitteln und so eine spätere Vereinbarung freischalten. |
| K13 | 2058-02-10, 2058-11-20, 2059-12-05 | breach_warning, amendment_offer, termination_notice | Annekatrin Schuchhardt (178), van der Dussen (168) -> Cindervale | Ereignisse 19/36/70, CCI-MSA-2057-01 | Steigerung bis zur Kündigung |
| K14 | 2059-12-10 / 12-14 | internal_memo, rumor (`is_accurate` NULL) | Dolores Mühle (171) -> van der Dussen (168); Richard Chavez (120) -> Josip Sölzer (172) | Rivalität A1 / A2 | „Cindervale wusste vom Firmwarefehler.“ Ein offener Spionagefall. |
| K15 | 2059-11-29 / 12-02 | delay_complaint, penalty_notice / Antwort | Claire Rust (174) -> Wayne Jacobson (302) | HMX-CTR-2059-0242 | Quarantäne, 60.720 CR. Jacobson empfiehlt in seiner Antwort „Ravenmoor-gesicherte Korridore“. |
| K16 | 2059-12-22 | amendment_offer (offen) | Ravenmoor -> David Hendricks (304), weitergeleitet an Esther Bauer (170) | EKM-RV-2057-02, RCS-MSA-2058-01, Piraten 74 | Dreiseitige Geleitschutzklausel. Offen zum Spielstart. |
| K17 | 2059-12-26 / 12-31 | delivery_notice, delay_complaint (Vorbehalt) | Claire Rust (174) -> Eric Adkins (307); Edward Bennett (370) -> Esther Bauer (170) | EKM-BST-2059-02343 (offen) | Offen zum Stichtag |
| K18 | 2059-12-28 | inquiry | Helix (Kurt Sullivan, 301) -> Graufalk | HMX-ORD-2059-01763, -01788 (Triebwerksschaden, offen) | Eilabruf von Triebwerksteilen |
| K19 | 2059-08-27 | confidential_tip (`is_accurate` 1) | Carlos Osborne (29) -> Ravenmoor Marktaufklärung | Razzia 58 | Der Verrat vor der Razzia |
| K20 | 2059-09-03 / 09-10 | protest; rumor | Tina Gould (23) -> Ravenmoor Vorstand; Nathan Hines (33) -> Tina Gould (23) | Rivalität N2, Ereignis 58 | Protest. Hines lenkt den Verdacht auf Osborne, ist aber selbst Kandidat. |
| K21 | 2059-05-20 | confidential_tip (`is_accurate` 1) | Outmark-Analyst -> Slavko Geisel (16) | historische Lizenz, Fund 52 | Koordinaten „Becker-Ost“ gegen Geld |
| K22 | 2059-07-28 / 08-05 | protest; Antwort (hostile) | Outmark Vorstand -> Theodor Krause (1) | Rivalität N3, Ereignis 52 | Claim-Streit |
| K23 | 2059-07-25 / 08-20 | amendment_offer; confidential_tip | Henryk Ullmann (175) -> Raureif; Esther Bauer (170) -> Aleksandra Koch (4) | RVF-RV-2058-01, Fund 52 | Preisdruck auf Raureif. Bauer verrät Feldspat die Raureif-Konditionen. |
| K24 | 2057-08-28 ff. | payment_reminder (1., 2., letzte) | Pamela Stroh (169) -> Theodor Krause (1) | EKM-BST-2057-00352 (4,79 Mio. CR) | Feldspat ist bei Eisenkrone verschuldet, ein Hebel für Erpressung und Spionage |
| K25 | 2059-12-28 | payment_reminder | Donald Morris (294) -> John Aguirre (119) | HMX-ORD-2059-01645 (3,78 Mio. CR) | Corvane zahlt schleppend |
| K26 | 2059-11-05 / 12-15 | internal_memo; offer (kalt) | Kaspar Täsche (43) -> Rörricht (38); Morgengrund -> Tilman Christoph (49) | Rivalität N1, Ernteausfälle 61/71 | Lichtacker beobachtet Isolde. Morgengrund bietet nach dem Ernteausfall Saatgut an. |
| K27 | 2058-04-01 | termination_notice | Second Hull -> Erin Cisneros (26) | historische Partnerschaft `driftwood->second_hull` | Ende zum 01.07.2058, Beginn der Rivalität N5 |

### 7.5 Mengengerüst

| Quelle | Bestandsobjekte | alle 18 Firmen (Schätzung) |
|---|---|---|
| Rahmenvertrag-Vorgänge (Anfrage, Angebot, 0–2 Verhandlungsrunden, Bestätigung) | 6 × 4–5 ≈ 27 | 16 × 4–5 ≈ 72 |
| Nachträge (Angebot und Antwort) | 36 × 2 = 72 | 58 × 2 = 116 |
| Gebrochene Verträge (Beschwerde und Strafbescheid) | 80 × 2 = 160 | ≈ 330 |
| Verspätete Abrufe > 48 h (Avis und Beschwerde) | 74 × 2 ≈ 150 | ≈ 320 |
| Mahnungen (überfällige Bestellungen, Firmenkunden bis 3 Stufen) | 182 + 93 ≈ 275 | ≈ 600 |
| Rivalitäten, Ereignisse, Spionage (Tipps, Gerüchte, Proteste, Memos) | ≈ 40 | ≈ 150–250 |
| Kaltangebote ohne Partnerschaft | ≈ 5 | ≈ 20 |
| **Summe** | **≈ 700** | **≈ 1.600–1.700**, mit Lieferavis für alle Abrufe mit Zwischenfall **≈ 2.000–2.400** |

Bei etwa 0,6 KB Text je Schreiben sind das unter 2 MB, die Datenbankgröße (≈ 40–45 MB) ändert sich kaum.

### 7.6 QA-Prüfungen (neu)

1. Absender und Empfänger gehören zur angegebenen Firma bzw. zum Kunden und sind am `sent_at` beschäftigt.
2. Kontext passt: Die Parteien von Vertrag, Bestellung und Rahmenvertrag sind Absender- und Empfängerfirma.
   Ausnahmen: `confidential_tip`, `rumor`, `internal_memo` und `protest` (Rivalität).
3. `penalty_notice.amount` = Verzugstage × `penalty_per_day`, mit derselben Formel wie `generate_financials`.
4. `delay_complaint` nur bei tatsächlich verspäteter Lieferung oder bei Bestellungen, die zum Stichtag `delayed` sind.
5. Antworten liegen zeitlich nach dem Bezugsschreiben, `thread_id` zeigt auf das erste Schreiben, alle `sent_at` liegen vor dem 01.01.2060.
6. `language` ist die Sprache der Absenderfirma, `is_accurate` ist nur bei `confidential_tip` und `rumor` gesetzt.

---

## 8. Reihenfolge im Skript (Bestandsschutz)

1. Durchlauf 1 (Bestandsstrom) bleibt Schritt für Schritt unverändert, dazu gehören `OPTIONAL_PARTNERSHIPS` und
   `HISTORIC_PARTNERSHIPS` des Bestands. **Wichtig:** Neue aktive und historische Vereinbarungen werden *nach* der
   historischen Bestandszeile `corvane->driftwood` angelegt, sonst verschiebt sich deren `partnership_id`.
2. Durchlauf 2 (Erweiterungsstrom) legt Vereinbarungen, historische Partnerschaften und Rivalitäten der neuen Firmen
   an. Rivalitäten mit festen Werten aus Abschnitt 5.
3. Nach `generate_contracts`: `generate_framework_agreements(world)`. Anlegen, Geltungsbereich, Nachträge und Zuordnung
   sind deterministisch, nur die neuen Paare nutzen den Erweiterungsstrom.
4. Nach `generate_events` und `generate_financials`: `generate_correspondence(world)` mit eigenem Zufallsstrom.
5. `INSERT_ORDER` ergänzen: `framework_agreements`, `framework_amendments`, `framework_agreement_scope` (nach
   `contracts`; der Fremdschlüssel `contracts.framework_agreement_id` erfordert, dass die Rahmenverträge vor den
   Verträgen eingefügt werden oder die Spalte nachträglich per UPDATE gesetzt wird) und `correspondence` (zuletzt).
6. QA: Prüfungen aus 6.6 und 7.6, die Firmenprüfung auf 18 (6/6/6) umstellen, Bestandsvergleich gegen die Bestands-DB.

## 9. Offene Punkte an Team A

1. Kante `graufalk -> ravenmoor` annehmen? Und `lanternfish -> kometenpost` fest statt optional?
2. Streichung von `raureif -> emberline` in Ordnung? Statt einer Kante gibt es das Kaltangebot Emberline -> Lichtacker (K12).
3. `RIVALRY_TEXT_OVERRIDES` statt eines neuen Typs für Emberline–Eisenkrone?
4. Rahmenverträge eurer Paare (GFW, CCI, KHB, EFF): Passen Volumen und Nachträge? Wollt ihr für
   `graufalk <-> cindervale` (strategic_alliance) einen weiteren Rahmenvertrag? Nach unserer Regel stünde er euch zu.
5. Aufteilung der Infrastruktur wie in Abschnitt 1, Punkt 5?

---

## 10. Daten (JSON)

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
    ["helix", "corvane", "logistics_partnership"],
    ["graufalk", "helix", "supply_agreement"],
    ["cindervale", "eisenkrone", "supply_agreement"],
    ["kuppelwerk", "lichtacker", "supply_agreement"],
    ["emberline", "corvane", "supply_agreement"],
    ["cindervale", "graufalk", "supply_agreement"],
    ["graufalk", "cindervale", "strategic_alliance"],
    ["emberline", "graufalk", "supply_agreement"],
    ["kuppelwerk", "graufalk", "supply_agreement"],
    ["graufalk", "emberline", "supply_agreement"],
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
    ["raureif", "eisenkrone", "supply_agreement"],
    ["ravenmoor", "helix", "logistics_partnership"],
    ["kuppelwerk", "pionierwerk", "supply_agreement"],
    ["second_hull", "graufalk", "supply_agreement"],
    ["graufalk", "ravenmoor", "supply_agreement"]
  ],
  "historic": [
    ["corvane", "driftwood", "supply_agreement"],
    ["eisenkrone", "graufalk", "supply_agreement"],
    ["lichtacker", "pionierwerk", "supply_agreement"],
    ["outmark", "feldspat", "licensing"],
    ["driftwood", "second_hull", "consignment"]
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
  "framework_agreements": [
    {"seller_key": "helix", "buyer_key": "lichtacker", "title": "Distributionsrahmenvertrag Agrarringe Tauvel/Aurelis/Myrrhen", "start_year": 2057, "term_months": 36, "base_volume_mcr": 250, "indexation": "index_linked:category_price_index,cap_8pct", "exclusivity": "right_of_first_refusal:industrial_goods",
     "amendments": [
       {"effective": "2057-04-01", "type": "product_addition", "status": "signed", "detail": "energy, technology"},
       {"effective": "2057-09-01", "type": "product_addition", "status": "signed", "detail": "medical"},
       {"effective": "2058-09-01", "type": "volume_increase", "status": "signed", "detail": "volume 400; trigger HMX-CTR-2058-0161"},
       {"effective": "2059-03-15", "type": "exclusivity_removed", "status": "signed", "detail": "industrial_goods; breached HMX-CTR-2057-0043, HMX-CTR-2058-0139, HMX-CTR-2058-0159"},
       {"effective": "2059-10-01", "type": "volume_increase", "status": "signed", "detail": "volume 550; trigger HMX-CTR-2059-0259"},
       {"effective": "2059-10-01", "type": "term_extension", "status": "signed", "detail": "end 2060-12-31"}]},
    {"seller_key": "helix", "buyer_key": "corvane", "title": "Logistik- und Versorgungsrahmenvertrag Halcyon/Aurelis", "start_year": 2057, "term_months": 36, "base_volume_mcr": 300, "indexation": "spot_discount:4pct", "exclusivity": "none",
     "amendments": [
       {"effective": "2057-03-01", "type": "product_addition", "status": "signed", "detail": "technology"},
       {"effective": "2057-05-01", "type": "product_addition", "status": "signed", "detail": "energy"},
       {"effective": "2058-01-01", "type": "product_addition", "status": "signed", "detail": "industrial_goods, medical"},
       {"effective": "2058-08-01", "type": "volume_increase", "status": "signed", "detail": "volume 450; trigger HMX-CTR-2058-0152"},
       {"effective": "2059-03-15", "type": "product_removal", "status": "signed", "detail": "archetype helium3; breached HMX-CTR-2058-0131, HMX-CTR-2057-0014; event 30"},
       {"effective": "2059-04-01", "type": "volume_increase", "status": "signed", "detail": "volume 600; trigger HMX-CTR-2059-0213"},
       {"effective": "2059-11-15", "type": "term_extension", "status": "signed", "detail": "end 2061-12-31"},
       {"effective": "2060-02-01", "type": "volume_increase", "status": "proposed", "detail": "volume 750; draft HMX-CTR-2060-0281"}]},
    {"seller_key": "helix", "buyer_key": "eisenkrone", "title": "Strategischer Versorgungsrahmen Sol/Halcyon/Brennus", "start_year": 2057, "term_months": 48, "base_volume_mcr": 300, "indexation": "cost_plus:9pct", "exclusivity": "none",
     "amendments": [
       {"effective": "2057-07-01", "type": "product_addition", "status": "signed", "detail": "medical, technology, industrial_goods"},
       {"effective": "2058-03-01", "type": "volume_reduction", "status": "signed", "detail": "volume 250; event 19 (AI control failure Foerster)"},
       {"effective": "2059-01-01", "type": "volume_increase", "status": "signed", "detail": "volume 350; trigger HMX-CTR-2059-0192"},
       {"effective": "2059-06-01", "type": "volume_increase", "status": "signed", "detail": "volume 450; trigger HMX-CTR-2059-0235"},
       {"effective": "2060-01-01", "type": "volume_increase", "status": "proposed", "detail": "volume 550; draft HMX-CTR-2060-0275"}]},
    {"seller_key": "eisenkrone", "buyer_key": "corvane", "title": "Joint-Venture-Liefervertrag Halcyon", "start_year": 2057, "term_months": 60, "base_volume_mcr": 350, "indexation": "cost_plus:12pct", "exclusivity": "right_of_first_refusal:raw_materials",
     "amendments": [
       {"effective": "2057-05-01", "type": "product_addition", "status": "signed", "detail": "luxury, technology"},
       {"effective": "2058-05-01", "type": "penalty_clause", "status": "signed", "detail": "breached EKM-VTR-2057-0064"},
       {"effective": "2059-03-01", "type": "volume_increase", "status": "signed", "detail": "volume 450; trigger EKM-VTR-2059-0160"},
       {"effective": "2060-01-01", "type": "volume_increase", "status": "proposed", "detail": "volume 550; draft EKM-VTR-2060-0219"}]},
    {"seller_key": "eisenkrone", "buyer_key": "helix", "title": "Rahmenvertrag Erze und Energie Brennus/Halcyon - Kharon/Sol", "start_year": 2057, "term_months": 42, "base_volume_mcr": 200, "indexation": "index_linked:raw_materials,cap_10pct", "exclusivity": "none",
     "amendments": [
       {"effective": "2057-06-01", "type": "product_addition", "status": "signed", "detail": "food, technology"},
       {"effective": "2058-01-01", "type": "product_addition", "status": "signed", "detail": "industrial_goods"},
       {"effective": "2058-08-01", "type": "product_addition", "status": "signed", "detail": "luxury"},
       {"effective": "2059-02-01", "type": "volume_increase", "status": "signed", "detail": "volume 300; trigger EKM-VTR-2059-0151"},
       {"effective": "2060-02-01", "type": "escort_clause", "status": "proposed", "detail": "escort_company ravenmoor; breached EKM-VTR-2057-0017, EKM-VTR-2058-0107, EKM-VTR-2059-0162; open EKM-BST-2059-02343; event 74"},
       {"effective": "2060-02-01", "type": "volume_increase", "status": "proposed", "detail": "volume 400; draft EKM-VTR-2060-0234"},
       {"effective": "2060-07-01", "type": "term_extension", "status": "proposed", "detail": "end 2061-06-30"}]},
    {"seller_key": "eisenkrone", "buyer_key": "lichtacker", "title": "Liefervertrag Industriegueter und Energie Myrrhen/Tauvel", "start_year": 2057, "term_months": 36, "base_volume_mcr": 150, "indexation": "index_linked:energy,cap_6pct", "exclusivity": "none",
     "amendments": [
       {"effective": "2057-08-01", "type": "product_addition", "status": "signed", "detail": "energy"},
       {"effective": "2058-02-01", "type": "product_addition", "status": "signed", "detail": "technology"},
       {"effective": "2060-01-10", "type": "termination_notice", "status": "withdrawn", "detail": "energy scope; breached EKM-VTR-2058-0099, EKM-VTR-2058-0105, EKM-VTR-2059-0167"},
       {"effective": "2059-10-15", "type": "price_adjustment", "status": "signed", "detail": "energy -5 pct, stricter penalty clause"},
       {"effective": "2059-11-01", "type": "volume_increase", "status": "signed", "detail": "volume 200; trigger EKM-VTR-2059-0211"},
       {"effective": "2059-11-01", "type": "term_extension", "status": "signed", "detail": "end 2060-12-31"}]},
    {"seller_key": "graufalk", "buyer_key": "helix", "title": "Flottenrahmenvertrag Rumpf- und Triebwerksteile", "start_year": 2057, "term_months": 48, "base_volume_mcr": 180, "indexation": "index_linked:industrial_goods", "exclusivity": "none",
     "amendments": [
       {"effective": "2058-12-01", "type": "volume_increase", "status": "signed", "detail": "+60; breached HMX-CTR-2058-0173 (drive components)"},
       {"effective": "2060-01-15", "type": "price_adjustment", "status": "proposed", "detail": "rush call-off surcharge; open HMX-ORD-2059-01763, HMX-ORD-2059-01788"}]},
    {"seller_key": "cindervale", "buyer_key": "eisenkrone", "title": "Rahmenvertrag KI-Leitsysteme und Robotik", "start_year": 2057, "term_months": 36, "base_volume_mcr": 120, "indexation": "fixed+warranty", "exclusivity": "category_exclusive:technology",
     "amendments": [
       {"effective": "2058-03-01", "type": "penalty_clause", "status": "signed", "detail": "warranty clause; event 19"},
       {"effective": "2058-12-01", "type": "price_adjustment", "status": "signed", "detail": "-8 pct; event 36"},
       {"effective": "2060-06-03", "type": "termination_notice", "status": "proposed", "detail": "notice by eisenkrone 2059-12-05, 180 days; event 70"}]},
    {"seller_key": "kuppelwerk", "buyer_key": "lichtacker", "title": "Rahmenvertrag Verbundstahl und Habitatbaustoffe Tauvel/Myrrhen", "start_year": 2059, "term_months": 24, "base_volume_mcr": 60, "indexation": "index_linked:industrial_goods", "exclusivity": "none",
     "amendments": [
       {"effective": "2059-10-01", "type": "product_addition", "status": "signed", "detail": "habitat_modules for myrrhen"},
       {"effective": "2060-01-01", "type": "volume_increase", "status": "proposed", "detail": "+30"}]},
    {"seller_key": "emberline", "buyer_key": "corvane", "title": "Helium-3-Rahmenvertrag Halcyon Works VI", "start_year": 2059, "term_months": 24, "base_volume_mcr": 40, "indexation": "index_linked:energy+storm_clause", "exclusivity": "none",
     "amendments": [
       {"effective": "2059-10-01", "type": "volume_increase", "status": "signed", "detail": "+20"},
       {"effective": "2060-01-01", "type": "exclusivity_added", "status": "proposed", "detail": "helium3 in halcyon"}]},
    {"seller_key": "ravenmoor", "buyer_key": "helix", "title": "Geleitschutz- und Versorgungsrahmenvertrag Kharon-Korridor", "start_year": 2058, "term_months": 36, "base_volume_mcr": 90, "indexation": "cost_plus:15pct", "exclusivity": "system_exclusive:kharon",
     "amendments": [
       {"effective": "2059-06-15", "type": "volume_increase", "status": "signed", "detail": "+40; event 51"},
       {"effective": "2060-02-01", "type": "escort_clause", "status": "proposed", "detail": "extend escort to eisenkrone convoys (tripartite); event 74"}]},
    {"seller_key": "raureif", "buyer_key": "eisenkrone", "title": "Volatile-Liefervertrag Myrrhen/Brennus", "start_year": 2058, "term_months": 24, "base_volume_mcr": 45, "indexation": "index_linked:raw_materials,floor", "exclusivity": "none",
     "amendments": [
       {"effective": "2059-08-01", "type": "price_adjustment", "status": "signed", "detail": "-6 pct; event 52 (feldspat discovery)"},
       {"effective": "2060-03-01", "type": "term_extension", "status": "proposed", "detail": "+12 months"}]},
    {"seller_key": "raureif", "buyer_key": "pionierwerk", "title": "Versorgungsrahmen Isolde - Volatile", "start_year": 2058, "term_months": 36, "base_volume_mcr": 80, "indexation": "index_linked:energy", "exclusivity": "system_exclusive:isolde",
     "amendments": [
       {"effective": "2058-09-01", "type": "product_addition", "status": "signed", "detail": "nitrogen_ice"},
       {"effective": "2059-06-01", "type": "volume_increase", "status": "signed", "detail": "+30"},
       {"effective": "2060-01-01", "type": "price_adjustment", "status": "proposed", "detail": "+10 pct requested by raureif"}]},
    {"seller_key": "outmark", "buyer_key": "pionierwerk", "title": "Lizenzrahmen Vermessungsdaten Serravel/Isolde", "start_year": 2058, "term_months": 36, "base_volume_mcr": 25, "indexation": "fixed", "exclusivity": "none",
     "amendments": [
       {"effective": "2059-08-15", "type": "exclusivity_added", "status": "signed", "detail": "system_exclusive serravel; event 52"},
       {"effective": "2059-11-01", "type": "product_addition", "status": "signed", "detail": "terraforming_cultures"}]},
    {"seller_key": "morgengrund", "buyer_key": "pionierwerk", "title": "Versorgungsrahmen Isolde - Lebensmittel fuer Bautrupps", "start_year": 2059, "term_months": 12, "base_volume_mcr": 5, "indexation": "fixed+harvest_clause", "exclusivity": "none",
     "amendments": [
       {"effective": "2059-07-01", "type": "volume_increase", "status": "signed", "detail": "+2"},
       {"effective": "2060-01-01", "type": "term_extension", "status": "signed", "detail": "auto renewal 12 months"}]},
    {"seller_key": "kuppelwerk", "buyer_key": "pionierwerk", "title": "Rahmenvertrag Habitatmodule Isolde", "start_year": 2058, "term_months": 36, "base_volume_mcr": 70, "indexation": "index_linked:industrial_goods", "exclusivity": "right_of_first_refusal:habitat_modules",
     "amendments": [
       {"effective": "2059-05-01", "type": "volume_increase", "status": "signed", "detail": "+35"},
       {"effective": "2059-11-01", "type": "product_addition", "status": "signed", "detail": "sinter_blocks"}]}
  ]
}
```
