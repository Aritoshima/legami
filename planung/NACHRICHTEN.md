# Nachrichten zwischen den Teams

Jeder Eintrag: Datum/Phase, Team, Datei, Kurzinhalt.


## Phase 1 – Team A: Bericht phase1_team_a.md fertig
Datei: `planung/phase1_team_a.md` · Firmen: Graufalk Orbitalwerften AG (large, de), Cindervale Cognitive Industries Inc. (large, en), Kuppelwerk Habitatbau AG (medium, de), Emberline Fusion Fuels Inc. (medium, en), Kometenpost Kurierdienste GmbH (small, de), Lanternfish Leisure Co. (small, en).
- Freie Plätze für Vereinbarungen bei den Bestandsfirmen sind knapp (nur 10): Feldspat ist voll (3/3), Corvane hat 1 frei, Helix 2, Eisenkrone 3, Lichtacker 2, Driftwood 2. Team A nimmt je 1 bei Helix, Eisenkrone, Lichtacker und Corvane. Für euch bleiben Helix 1, Eisenkrone 2, Lichtacker 1, Driftwood 2. FRAGE: Passt das, oder braucht ihr Corvane? Dann tauschen wir.
- Wir belegen: System `pellora` (Stufe 1, Koordinaten -58/-136/-92), Archetypen `fusion_pellets`, `habitat_modules`, `sinter_blocks`, `quantum_relays`, `immersion_pods`, SKU-Präfixe GFW, CCI, KHB, EFF, KPK, LFL. Orrin nutzen wir, Isolde lassen wir euch frei. FRAGE: Welche Codes und Koordinaten plant ihr?
- Bestandsschutz: Das Skript nutzt einen gemeinsamen rng und eine Faker-Instanz je Sprache. Neue Firmen brauchen eigene Zufallsströme und müssen in jedem Schritt nach den Bestandsfirmen laufen. Neue Archetypen dürfen nur für neue Firmen in den Produkt-Pool kommen. Vereinbarungen mit Bestandsfirmen legen wir nur in der Richtung "neue Firma -> Bestandsfirma" an, damit Routen und Verträge der Bestandsfirmen stabil bleiben. FRAGE: Macht ihr das auch so?
- Die Qualitätsprüfung "Sechs Firmen 2/2/2" muss auf 18 Firmen (6/6/6) umgestellt werden. Vorschlag: zusätzlicher Check, der die Stammdaten der Bestandsfirmen mit der Bestands-DB vergleicht.
- Angebot: Graufalk, Cindervale und Kuppelwerk haben noch bis zu 3 freie Plätze für Vereinbarungen mit euren Firmen (z. B. Rohstoffe an Graufalk oder Kuppelwerk, Habitatmodule von Kuppelwerk an eure Kolonien).

## Phase 1 – Team B: Bericht phase1_team_b.md fertig
Datei: `planung/phase1_team_b.md` · Firmen: Pionierwerk Kolonialausrüstung AG (large, de, Isolde), Ravenmoor Convoy & Security Group (large, en, Kharon), Raureif Volatilförderung GmbH (medium, de, Vaskar), Outmark Survey & Prospecting Inc. (medium, en, Serravel), Siedlergenossenschaft Morgengrund eG (small, de, Isolde), Second Hull Reclamation Co. (small, en, Nyx).
- Partnerplätze: Euer Vorschlag passt, Corvane brauchen wir nicht. Team B nimmt nur je 1 Platz bei Helix (`ravenmoor -> helix`) und Eisenkrone (`raureif -> eisenkrone`), beide in der Richtung „neue Firma -> Bestandsfirma“ wie bei euch. Danach sind noch frei: Eisenkrone 1, Lichtacker 1, Driftwood 2. Die übrigen 12 Vereinbarungen liegen innerhalb von Team B.
- Wir belegen: SKU-Präfixe PKB, RCS, RVF, OSP, SGM, SHR; neue Systeme `vaskar` (-462/438/336) und `serravel` (412/-96/388), beide Stufe 5, neuer Sektor `far_reach`; Archetypen `escort_drones`, `nitrogen_ice`, `terraforming_cultures`, optional `survey_charts`; neuer Rivalitätstyp `armed_conflict`. Orrin gehört euch: Outmark sitzt auf Serravel, kein Team-B-Standort in Orrin. `habitat_modules` gehört euch, wir streichen unseren gleichnamigen Archetyp und nutzen euren mit.
- Bestandsschutz: einverstanden (eigene RNG- und Faker-Ströme, neue Firmen nach den Bestandsfirmen, neue Archetypen nur in den Pools neuer Firmen, QA auf 18 Firmen 6/6/6 plus Vergleich mit der Bestands-DB). FRAGE: Wer setzt die gemeinsame Infrastruktur in Phase 2 um?
- FRAGE: Nehmt ihr die teamübergreifenden Kanten `kuppelwerk -> pionierwerk` (Habitatmodule) und `second_hull -> graufalk` (Recyclingmetall) an? Ist `fusion_pellets` aus Deuterium/Helium-3? Dann schlagen wir zusätzlich `raureif -> emberline` vor, falls Emberline einen Platz frei hat.
- FRAGE: Schema für Rahmenverträge und Schriftverkehr: Unser Vorschlag ist `framework_agreements` (mit optionalem `escort_company_id`) und `correspondence` mit Bezug auf contract, order oder event. Anker im Bestand: 8 Verträge, die wegen „Geleitschutz abgewartet“ gebrochen sind, und die Söldner-Razzien 26 und 58. Myrrhen wird voll (Kuppelwerk und bei uns Raureif und Pionierwerk). Ist das für euch in Ordnung?

## Phase 2 – Team B: Vorschlag Verknüpfungen fertig
Datei: `planung/phase2_vorschlag_team_b.md` (JSON-Block am Ende). Alles baut auf Abfragen der Bestands-DB auf.
- Netz: 47 aktive Vereinbarungen (14 Bestand, 16 Team A, 14 Team B, 3 teamübergreifend). Alle 18 Firmen liegen in ihrem Größenbereich, jede hat eine ausgehende Vereinbarung. Hub ist Helix (7 Partner, 10 Vereinbarungen, damit voll). 67 Paare sind nur indirekt verbunden, z. B. Feldspat ↔ Raureif über Eisenkrone, Driftwood ↔ Ravenmoor über Helix.
- AN TEAM A: (1) Neue Kante `graufalk -> ravenmoor` (Werftteile für die Geleitflotte) annehmen? (2) `raureif -> emberline` streichen wir (Vaskar–Pellora ≈ 820 Einheiten, Emberline fördert Helium-3 selbst). (3) `lanternfish -> kometenpost` bitte fest statt optional. (4) `kuppelwerk -> pionierwerk` und `second_hull -> graufalk` setzen wir als angenommen voraus. (5) Für Emberline–Eisenkrone und Lichtacker–Pionierwerk schlagen wir `RIVALRY_TEXT_OVERRIDES` statt neuer Typen vor, neu bleibt nur `armed_conflict`.
- Historisch neu: `lichtacker -> pionierwerk` (bis 2053), `outmark -> feldspat` (Lizenz bis 2058-06, Vorgeschichte zu Fund 52), `driftwood -> second_hull` (bis 2058-07, nach Razzia 26). Rivalitäten neu: 5, mit festen since/intensity/espionage-Werten aus Ankern.
- Rahmenverträge: 16, davon 6 für Bestandspaare. Darunter fallen per deterministischer Regel alle 337 passenden Bestandsverträge (2.308 Mio. CR). Neue Spalte `contracts.framework_agreement_id`, sonst bleiben die Bestandszeilen unverändert. 58 Nachträge, die Volumen-Nachträge sind aus kumulierten Vertragssummen abgeleitet. Kausalketten aus echten Daten: Verbundstahl-Brüche -> Helix verliert das Vorkaufsrecht -> Kuppelwerk; Helium-3-Brüche -> Helium-3 raus aus dem Helix-Rahmen -> Emberline; Geleitschutz-Brüche und Piraten 74 -> Geleitschutzklausel mit Ravenmoor; Förster 19/36/70 -> Kündigung Cindervale.
- Schriftverkehr: Tabelle `correspondence` (17 Brieftypen, FKs auf Rahmenvertrag, Nachtrag, Vertrag, Bestellung, Lieferung, Ereignis, Rivalität, Partnerschaft und Kunde; `confidentiality` entspricht `intel_access_level`). 27 angekerte Vorgänge mit echten Mitarbeiter-IDs. Schätzung ≈ 700 Schreiben zu Bestandsobjekten, ≈ 1.600–2.400 gesamt.
- Korrektur zu Phase 1 B: HMX-CTR-2059-0242 ist wegen Quarantäne gebrochen, EKM-VTR-2058-0107 startet in Halcyon (Hande).
- Vorschlag Aufteilung der Infrastruktur: Team A übernimmt den zweiten Durchlauf (RNG/Faker, Archetyp-Filter, QA 6/6/6 mit Bestandsvergleich), Team B Rahmenverträge, Nachträge, Geltungsbereich, Schriftverkehr und die QA dazu.

## Phase 2 – Team A: Vorschlag Verknüpfungen fertig
Datei: `planung/phase2_vorschlag_team_a.md` (JSON-Block am Ende). Grundlage sind Abfragen der Bestands-DB. Den Phase-2-Vorschlag von Team B haben wir gelesen und abgeglichen (Abschnitt 1.1).
- Netz: 48 aktive Vereinbarungen (14 Bestand inkl. `helix -> corvane`, 7 neue Firma -> Bestand, 12 Team A, 12 Team B, 3 teamübergreifend). Alle 18 Firmen liegen in ihrem Größenbereich, jede hat eine ausgehende Vereinbarung. Hub ist Helix (7 Partner/10), dahinter Graufalk (7/9) und Ravenmoor (7/8). 38 von 153 Paaren sind direkt verbunden, 66 nur indirekt, Durchmesser 4. Voll sind Helix, Lichtacker, Corvane und Emberline, Reserve gibt es bei Eisenkrone (1) und Driftwood (2).
- ANTWORTEN AN TEAM B: (1) `graufalk -> ravenmoor` angenommen. (2) Streichung von `raureif -> emberline` angenommen, `graufalk -> emberline` bleibt. (3) `lanternfish -> kometenpost` fest. (4) `kuppelwerk -> pionierwerk` und `second_hull -> graufalk` angenommen. (5) `RIVALRY_TEXT_OVERRIDES` angenommen, unseren Typ `price_war` ziehen wir zurück. (6) Aufteilung der Infrastruktur wie von euch vorgeschlagen: Team A macht den zweiten Durchlauf, RNG/Faker, Archetyp-Filter und QA 6/6/6 mit Bestandsvergleich; Team B macht Rahmenverträge, Nachträge, Scope, Schriftverkehr und die QA dazu. (7) Rahmenvertrag `graufalk <-> cindervale`: ja, GFW-RV-2057-02 (Allianzvertrag Navigationsplattform, 220 Mio. CR, 60 Monate).
- AN TEAM B, zur Entscheidung: (a) `emberline -> lichtacker` als echte Vereinbarung (letzter Platz bei Lichtacker) mit Rahmenvertrag EFF-MSA-2059-02 statt eures Kaltangebots K12. Begründung: Die Kette Bruch -> Teilkündigung Energie (EKM-RV, wirksam 2060-01-18) -> neuer Lieferant wird in Routen und Verträgen sichtbar. (b) Zusätzliche Rahmenverträge `feldspat -> eisenkrone` (FSP-RV-2059-01, 12 Mio. CR, Exklusivität für Quantenquarz Becker als Verrechnung der 25,5 Mio. CR Schulden), `graufalk -> ravenmoor` und optional `morgengrund -> ravenmoor`. Für gemeinsame Paare gelten eure Werte. (c) Historische Partnerschaften `cindervale -> helix` (Lizenz 2041–2054, erklärt die Technikimporte aus Kharon) und `emberline -> eisenkrone` (2047–2056). Eure Daten für eure drei Partnerschaften haben wir übernommen.
- HINWEIS (Datumsfehler bei Team B): Roswitha van der Dussen (168) ist laut `hire_date` erst seit 2059-07-07 bei Eisenkrone, Theodor Krause (1) erst seit 2057-11-22. Damit sind K10 (2058-08-28), die 2058er Schreiben in K13 und K24 (2057-08-28) nicht möglich. Vorschlag: Für Eisenkrone zeichnet vorher Esther Bauer (170), bei Feldspat Mikhail Gotthard (2). Weitere späte Einstellungen: Desiree Schwartz (299) 2059-11-24, Heinz Dieter Schmidtke (42) 2059-11-03, Eric Adkins (307) 2059-07-18, Erin Cisneros (26) 2057-12-27, Nathan Hines (33) 2058-01-20.
- Schriftverkehr: Briefarten zusammenführen (eure 17 und unsere 16; `quotation` = `offer`, `negotiation` = `counter_offer`, zusätzlich `delay_notice` und `suspension_notice`). Strafbescheide mit derselben Formel wie in `generate_financials` (z. B. HMX-CTR-2058-0159: 6 × 108.860,36 = 653.162,16 CR). Vorgeschlagener QA-Check: Summe der Strafbescheide je Firma und Monat = `contract_penalties`.

## Phase 2 – Schiedsrichter: Entscheidung Verknüpfungen
Dateien: `planung/phase2_entscheidung.md` (Bewertung, Begründung, Zählung), `planung/verknuepfungen.json` (verbindlich für die Umsetzung).
- Netz: **48 aktive Vereinbarungen** (Liste von Team A, also mit `emberline → lichtacker`). Selbst nachgezählt: alle 18 Firmen im Größenbereich, jede mit ausgehender Vereinbarung, Hub Helix (7/10), 38/153 Paare direkt, 66 nur indirekt, Durchmesser 4. `helix → corvane` bleibt in `optional_partnerships` (Bestandsstrom).
- Historie: 7 Einträge (Team A). Rivalitäten: 12. Alle 8 neuen haben feste since/intensity/espionage-Werte; für die drei Team-A-Rivalitäten hat der Schiedsrichter die Werte gesetzt.
- Rahmenverträge: **21** (7 Bestandspaare, 14 neue Paare), 78 Nachträge, davon 17 offen. Nachgerechnet: 341 von 475 Bestands-Abrufverträgen werden zugeordnet (2.309 Mio. CR). Außerhalb des Rahmens liegen absichtlich EKM-VTR-2060-0230 und FSP-VTR-2059-0001/-0005.
- AN TEAM A: Drei Exklusivitäten habt ihr im Bestand nicht geprüft. Sie sind jetzt Vorkaufsrechte: FSP Quantenquarz (4 Verkäufe an andere Kunden), EFF → Seip (HMX-CTR-2059-0257 läuft bis 2060-03-30), GFW → Ravenmoor (Rumpfplatten auch an Helix in Kharon). Die Allianz GFW ↔ CCI ist jetzt auf drive_parts/nav_computers exklusiv, nicht mehr auf KI-Kerne. KHB-RV-2059-01 beginnt erst am 2059-04-01, nach dem Wegfall des Helix-Vorkaufsrechts. Die Geleitschutzklausel bleibt offen.
- AN TEAM B: Eure Empfänger 2057/2058 (van der Dussen, Krause) sind korrigiert (Bauer, Stroh, Gotthard). Der Auslöser heißt HMX-CTR-2059-0236 statt -0235. Titel der englischsprachigen Rahmenverträge sind jetzt englisch. RVF-Nummern chronologisch: -01 Pionierwerk, -02 Eisenkrone. SGM-RV-2059-02 = Morgengrund → Ravenmoor ist zusätzlich aufgenommen. CCI läuft 48 Monate und wird zum 2059-12-15 ausgesetzt; die Kündigung wird nur im Schreiben angedroht.
- Schema: Spalten `company_id`/`partner_company_id` wie in `contracts`. Tabellennamen `framework_agreement_scope` und `correspondence` (Basis Team B, Leck-Felder Team A). 20 Briefarten, neu ist `offer_rejection`. 38 verankerte Vorgänge (Abschnitt 6.3) sind verbindlich.
- Zuständigkeit unverändert: Team A übernimmt Durchlauf 2 und die QA 6/6/6, Team B Rahmenverträge, Nachträge, Schriftverkehr und die QA dazu.

## Phase 1 – Team A: Bericht phase1_team_a.md fertig (Neudurchlauf 21.10.2026)
Datei: `planung/phase1_team_a.md` (neuer Abschnitt 7 „Prüfvermerk“). Die Firmen bleiben unverändert: Graufalk Orbitalwerften AG (large, de, orrin), Cindervale Cognitive Industries Inc. (large, en, sol), Kuppelwerk Habitatbau AG (medium, de, aurelis), Emberline Fusion Fuels Inc. (medium, en, pellora), Kometenpost Kurierdienste GmbH (small, de, sol), Lanternfish Leisure Co. (small, en, aurelis).
- Kein neuer Entwurf. `phase2_entscheidung.md` und `verknuepfungen.json` bauen schon auf diesen 6 Firmen auf. Gegen die Bestands-DB ist alles nachgeprüft: 20 Vertragsnummern, 16 Ereignis-IDs, Mitarbeiterdaten und die Lücken je System.
- Weiterhin belegt: System `pellora`, Archetypen `fusion_pellets`, `habitat_modules`, `sinter_blocks`, `quantum_relays`, `immersion_pods`, SKU-Präfixe GFW, CCI, KHB, EFF, KPK, LFL. Orrin gehört Team A, Isolde Team B.
- Datumshinweis für Schreiben: Dolores Mühle (171) ist erst seit 2058-11-10 dabei, Roswitha van der Dussen (168) seit 2059-07-07 und Desiree Schwartz (299) seit 2059-11-24. Vorgänge vor diesen Daten brauchen andere Absender oder Empfänger.
- FRAGE an Team B: Bleibt ihr bei eurem Phase-1-Stand (PKB, RCS, RVF, OSP, SGM, SHR; `vaskar` und `serravel`) und bei der Zuständigkeit aus Phase 2? Dann geht es direkt mit der Umsetzung nach `verknuepfungen.json` weiter.

## Phase 1 – Team B: Bericht phase1_team_b.md fertig (Revision 2, 21.10.2026)
Datei: `planung/phase1_team_b.md` (neuer Abschnitt 0 mit Prüfprotokoll, Korrekturen markiert mit *(korr. R2)*, neue Fragen in 7.1).
- Firmen **unverändert**, weil Phase 2 (`verknuepfungen.json`) darauf aufbaut: Pionierwerk (large, de, Isolde), Ravenmoor (large, en, Kharon), Raureif (medium, de, Vaskar), Outmark (medium, en, Serravel), Morgengrund (small, de, Isolde), Second Hull (small, en, Nyx). Präfixe PKB/RCS/RVF/OSP/SGM/SHR, Systeme `vaskar`/`serravel` (Stufe 5, Sektor `far_reach`), Archetypen `escort_drones`, `nitrogen_ice`, `terraforming_cultures` und optional `survey_charts`.
- Nachgeprüft gegen die Bestands-DB, korrigiert: HMX-CTR-2059-0242 ist wegen Quarantäne gebrochen. EKM-VTR-2058-0107 startet in Halcyon. Eisenkrone Brennus → Kharon gebrochen sind EKM-VTR-2057-0017 und -2059-0162 (Andockstau). Theodor Krause ist erst seit 2057-11-22 im Amt, vorher ist Mikhail Gotthard der Adressat.
- FRAGE R2-1: Nehmt ihr die Ankerobjekte (8 Geleitschutzbrüche, HMX-CTR-2059-0242, Ereignisse 26/52/58/74) in euren Bestandsvergleich der QA auf?
- FRAGE R2-2/R2-3: Prüft ihr eure Schreiben auch gegen `hire_date`? Deckt ihr die Rohstofflücken in Sol (1/40) und Aurelis (1/24) ab, oder soll Second Hull dorthin ausgreifen?

## Phase 2 – Team B: Vorschlag Verknüpfungen fertig (Revision 2, 21.10.2026)
Datei: `planung/phase2_vorschlag_team_b.md` (JSON-Block am Ende: 48 partnerships, 7 historic, 12 rivalries, 21 framework_agreements). Basis ist das verbindliche Netz aus `verknuepfungen.json`, unabhängig nachgeprüft mit eigenen Skripten gegen Skript und Bestands-DB.
- ANTWORT AN TEAM A: Ja, Team B bleibt beim Phase-1-Stand (PKB, RCS, RVF, OSP, SGM, SHR; `vaskar`/`serravel`) und bei der Zuständigkeit aus Phase 2.
- Bestätigt: 48 aktive Vereinbarungen, alle 18 Firmen im Größenbereich, jede mit ausgehender Vereinbarung. Hub Helix (7/10), 66 Paare nur indirekt, Durchmesser 4. Verbraucherprüfung: jede Kante ≥ 52 %. 341 von 475 Bestands-Abrufverträgen unter Rahmen (2.309,1 Mio. CR), alle 12 Volumen-Auslöser und 7 Strafbeträge reproduziert.
- KORREKTUREN: K1 CCI-MSA-2057-01 käuferexklusiv widerspricht dem Bestand (Corvane liefert Technik an Hande, u. a. CVB-CTR-2059-0066), jetzt Vorkaufsrecht und neuer Vorgang V39. K2 Geleitschutzklausel EKM-RV-2057-02 an die echten Geleitschutzbrüche EKM-VTR-2057-0043/-2058-0107, die Andockstau-Brüche begründen Ausweich-Liegeplätze bei Ravenmoor. K3–K5 Mahnfristen (V27 auf 2059-10-14, V1 auf 08-28/09-13/10-07, V32 auf 2059-03-29). K6 V36 und Eilabrufklausel auf 2059-12-31, Absender Kayla Cannon (HMX-ORD-2059-01788 entsteht erst am 12-29). K7 RVF-Exklusivität Stickstoffeis erst ab Nachtrag. K9 HMX-MSA-2057-02 nur, wenn `helix → corvane` gezogen wird. K10 Feldspat-Schulden nach Datum (22,94 / 24,22 / 25,52 Mio.).
- AN TEAM A (Durchlauf 2): Bitte die Sperrfristen K8 als Filter für Verträge und Bestellungen der neuen Verkäufer einbauen (Abschnitt 6.6): kein Energie-Verkauf Emberline → Corvane vor 2059-03-15, keine Industriegüter Kuppelwerk → Lichtacker vor 2059-03-15, keine Sensorarrays Graufalk → Helix-Kharon ab 2058-08-01, drive_parts/nav_computers gemäß GFW ↔ CCI, Wasser- und Stickstoffeis nach Isolde nur von Raureif.
- Antwort auf unsere R2-1: konkrete Ankerliste für den Bestandsvergleich in Abschnitt 8.2. Optional K11: Morgengrund bekommt eine zweite Pflichtstation `trade_hub` in Isolde.

## Phase 2 – Team A: Vorschlag Verknüpfungen fertig (Revision 2, 21.10.2026)
Datei: `planung/phase2_vorschlag_team_a.md` (JSON-Block am Ende: 47 partnerships + 1 optional = 48 aktiv, 7 historic, 12 rivalries, 21 framework_agreements mit 82 Nachträgen, dazu Filter, Einstellungsgrenzen, Ankerobjekte). Basis ist `verknuepfungen.json`, vollständig nachgerechnet gegen Skript und Bestands-DB. Den R2-Vorschlag von Team B haben wir gelesen und abgeglichen (Abschnitt 1.1).
- Bestätigt: 48 aktive Vereinbarungen, alle 18 Firmen im Größenbereich, jede mit ausgehender Kante. Hub Helix (7/10), 66 Paare nur indirekt, Durchmesser 4. Die Zuordnung 341/475 und alle 13 Volumen-Auslöser sind mit eigener Implementierung reproduziert.
- AN TEAM B: K1, K2, K3–K6, K7, K8, K9, K10 angenommen (K3–K6 im Bestand nachgeprüft). K11 Zustimmung. Euer V39 ersetzt unseren Entwurf. Unsere neuen Vorgänge heißen V40 (Lichtacker verdächtigt Erkan Hesse, Entlassung 2059-06-11) und V41 (Freddy Dörr verrät Förster-Protokolle an Graufalk).
- AN TEAM B, bitte prüfen: Δ2 Produktaufnahmen einzeln nach Regel (HMX-MSA-2057-03 Technik 2057-09-01 und Industriegüter 2057-11-01, EKM-RV-2057-01 Technik 2057-06-01, EKM-RV-2057-02 Technik 2057-10-01, +4 Nachträge). Δ3 KHB-RV-2059-01 Rohstoffe nur `regolith`/`water_ice`, weil Lichtacker andere Rohstoffe nicht verbraucht. Δ7 V14: Erkan Hesse (68/43) verletzt die Leck-Regel, Absender wird Kaspar Täsche 43. Datum 2059-01-27, weil das Gerücht vor dem Strafbescheid vom 01-25 lag.
- Δ6: Leck-Quellen der Rivalitäten nach Leck-Regel getrennt von Zeugen/Zielen. Neu sind Freddy Dörr 235 (graufalk → eisenkrone) und Darren Harris 319 (cindervale → helix, vor Schwartz die einzige Helix-Quelle). Schuchhardt 178 und Eberhardt 45 sind nur noch Ziel bzw. Zeuge.
- Antworten R2-1: Die QA vergleicht 57 Verträge, 9 Bestellungen, 2 Lieferungen, 31 Ereignisse und 49 Mitarbeiter feldweise mit dem Bestand (Obermenge eurer Liste 8.2). R2-2: Alle Bestandsmitarbeiter sind geprüft. Für die neuen Firmen setzt Durchlauf 2 Einstellungsgrenzen für Vorstand, Partnerbetreuung und Marktaufklärung (Δ8, z. B. Graufalk/Cindervale ≤ 2056-11-02). R2-3: Kuppelwerk bekommt die Pflichtstation `("mining", "aurelis")` (Δ9, optional). Sol bleibt bewusst Rohstoff-Importmarkt.
- K8 mit unserem Δ4 vereinigt (Abschnitt 6.4): zusätzlich Kuppelwerk bei `water_ice` nach Isolde und bei `nav_computers` an Graufalk, außerdem die Verkäuferexklusivität `habitat_modules`.

## Phase 2 – Schiedsrichter: Entscheidung Verknüpfungen (R2, 21.10.2026)
Dateien: `planung/phase2_entscheidung.md` (ersetzt die Fassung vom 20.10.), `planung/verknuepfungen.json` (verbindlich, neue Schlüssel `exclusivity_filter_new_pairs`, `hire_date_caps_new_firms`, `qa_anchor_objects`, `profile_changes_new_firms`).
- Netz **unverändert: 48 aktive** (47 fest + `helix → corvane` optional). Selbst nachgezählt: alle 18 Firmen im Größenbereich, jede mit ausgehender Kante, Hub Helix (7/10), Abstände 38/66/45/4. Historie (7) und Rivalitäten (12) bleiben gleich.
- Angenommen von B: K1–K11 (K11: Morgengrund mit Pflichtstation `trade_hub` Isolde). Angenommen von A: Δ1–Δ9 (Δ9: Kuppelwerk mit Pflichtstation `mining` Aurelis). Rahmen: 21 mit **82 Nachträgen** (64/17/1), 341 Zuordnungen, **13** Volumen-Auslöser. Vorgänge V1–V41 (V39 von B, V40/V41 von A).
- AN TEAM B: `helix → corvane` bleibt optional. Euer JSON hatte die Kante fest, das ist abgelehnt. Es sind 13 Volumen-Auslöser, nicht 12. `price_floor` (RVF-RV-2058-02) und `harvest_clause` (SGM-RV-2059-01) sind wieder drin. Δ2, Δ3, Δ6 und Δ7 von Team A habe ich im Bestand geprüft, sie gelten.
- AN TEAM A: `PKB-VTR-2058-0001` ist keine Bestandsnummer und fliegt aus `qa_anchor_objects` (jetzt 56 Verträge). Polina Zahn (83, 55/88) bleibt in V28 die Leck-Quelle (`third_party_leaks`). Hub-Sortierung in der QA bitte mit `company_id` als drittem Schlüssel und `kind="stable"`.
- Zuständigkeit unverändert: Team A übernimmt Durchlauf 2, Profile, Filter, Einstellungsgrenzen und die QA 6/6/6. Team B übernimmt Rahmen, Nachträge und Schriftverkehr samt QA.

## Phase 3b – Team A: Integration und Rahmenverträge im Generator fertig (21.10.2026)
Dateien: `generate_space_trading_data.py` (18 Firmen, ein eigenständiges Skript), `planung/bestandsvergleich.md`.
Qualitätsprüfung: Seed 42 50/50, Seed 7 47/47, Seed 123 47/47 (Bestandsvergleich nur bei Seed 42). Größe 39,8 MB, Laufzeit ≈ 11 s.
- Bestandsschutz: Alle 115.705 Bestandszeilen sind bei Seed 42 unverändert (18/18 Tabellen). Neu ist nur die Spalte
  `contracts.framework_agreement_id`. 341 Bestandsverträge sind zugeordnet, die 13 Volumen-Auslöser stimmen. Neue Firmen
  rechnen in eigenen Zufallsströmen (`World.company_stream`). Bestands-IDs gelten unverändert: Firmen 1–6,
  Partnerschaften 1–15, Rivalitäten 1–4, Ereignisse 1–74, Mitarbeiter 1–491.
- AN TEAM B, Tabellen für den Schriftverkehr (Spaltennamen verbindlich):
  - `framework_agreements` (`framework_agreement_id`, `agreement_number` UNIQUE, `partnership_id`, `company_id` =
    Verkäufer, `partner_company_id` = Käufer, `title`, `language`, `signed_date` = Beginn − 30 T, `start_date`,
    `end_date`, `current_end_date`, `status`, `base_volume`, `current_volume_cap`, Preis- und Exklusivitätsfelder,
    `escort_company_id`, `seller_signatory_id`/`buyer_signatory_id` → `employees`, `description` = Vertragstext in
    Verkäufersprache). Bei Seed 42 haben die IDs 1–21 die Reihenfolge von `verknuepfungen.json`. Bei Seed 123 fehlt
    HMX-MSA-2057-02 (K9), dann verschieben sich die IDs. **Bitte über `agreement_number` nachschlagen.**
  - `framework_agreement_amendments` (PK `amendment_id`, **nicht** `framework_amendments`; `amendment_number` =
    `{Rahmen}/N{k}` (de) bzw. `/A{k}` (en), `amendment_no`, `amendment_type`, `status`, `rule`, `proposed_date`,
    `signed_date`, `effective_date`, `initiated_by_company_id`, `volume_before/_delta/_after`, `price_change_pct`,
    `price_factor`, `end_date_new`, `trigger_contract_id`/`trigger_order_id`/`trigger_event_id`, `description`). Euer
    Feld `correspondence.amendment_id` muss auf diese Tabelle zeigen.
  - `framework_agreement_scope` (Sortiment mit `entry_kind` `include`/`exclude`/`exclusivity`, `valid_from/valid_to`,
    `added_by_amendment_id`/`removed_by_amendment_id`).
  - Datumsregel der Nachträge: Hat ein Nachtrag ein Angebotsdatum, gilt Unterzeichnung = min(Wirkung, Angebot + 7 T).
    Regel-Nachträge haben Angebot = Wirkung − 14 T und Unterzeichnung = Wirkung − 3 T. Angebote mit Wirkung 2060 sind
    `proposed`. Schreiben zu Nachträgen sollten diese Daten verwenden.
- Anker für eure Vorgänge (Seed 42, `amendment_number` → ID): V2 EKM-RV-2057-02/N4 (34) · V3 CCI-MSA-2057-01/A1 (60) ·
  V4 HMX-MSA-2057-03/A4 (21) · V8 EKM-RV-2057-03/N3 (42) · V11 CCI-MSA-2057-01/A2 (61) · V12 GFW-RV-2057-01/N3 (51) ·
  V15 HMX-MSA-2057-02/A6 + A7 (13, 14) · V16 HMX-MSA-2057-01/A5 (5) · V23 RVF-RV-2058-02/N1 (77) · V28
  EKM-RV-2057-03/N6 Teilkündigung (45) und N7 abgelehnt (46) · V31 CCI-MSA-2057-01/A4 Aussetzung (63) · V34
  EKM-RV-2057-02/N7 (37) + RCS-MSA-2058-01/A2 (72) · V36 GFW-RV-2057-01/N4 (52). Rahmen: V7 RCS-MSA-2058-01 (16), V17
  KHB-RV-2059-01 (13), V18 EFF-MSA-2059-01 (14), V22 FSP-RV-2059-01 (7), V28 EFF-MSA-2059-02 (15).
- Unterzeichner (Seed 42): Helix Elizabeth Lopez 293, Eisenkrone Esther Bauer 170, Lichtacker Reimar Rörricht 38,
  Corvane Jason Armstrong 115, Feldspat Theodor Krause 1. Die Vorstände der neuen Firmen haben die IDs Graufalk 492,
  Cindervale 661, Kuppelwerk 842, Emberline 898, Pionierwerk 989, Ravenmoor 1196, Raureif 1390, Outmark 1452,
  Morgengrund 1501. Vorstand, erste Partnerbetreuung und erste Marktaufklärung jeder neuen Firma sind nach
  `hire_date_caps_new_firms` eingestellt und aktiv.
- ABWEICHUNG: 90 statt 82 Nachträge (71/18/1). Die Regel-Nachträge neuer Paare ergeben sich aus den erzeugten Verträgen
  (Liste in `bestandsvergleich.md`, Abschnitt 6). Bei den Bestandspaaren gibt es keine Abweichung.
- Neue Ereignisse (IDs 75–255) entstehen an neuen Stationen und wirken nur auf Ware neuer Firmen. Die Bezüge auf
  Bestandsereignisse (z. B. 19, 36, 70, 74) gelten unverändert.
