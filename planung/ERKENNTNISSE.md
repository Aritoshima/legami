# Erkenntnisse aus dem Aufbau der Datenbasis

Stand: 21.10.2026, Branch `erweiterung-18-firmen`. Gilt für `generate_space_trading_data.py` und den Ordner `planung/`.

## Ergebnis

| Stufe | Inhalt | Prüfungen (Seed 42) | DB-Größe | Laufzeit |
|---|---|---:|---:|---:|
| Ausgangsskript | 6 Firmen, 18 Tabellen | 34/34 | 13,5 MB | ≈ 3 s |
| Phase 3b | 18 Firmen, 13 Systeme, 109 Stationen, Rahmenverträge mit Nachträgen | 50/50 | 39,8 MB | ≈ 15 s |
| Phase 3c | dazu Schriftverkehr (3.492 Schreiben, 20 Briefarten) | 62/62 | 42,4 MiB | ≈ 15–20 s |

Die Seeds 7 und 123 bestehen ebenfalls alle Prüfungen. Alle 115.705 Bestandszeilen der ursprünglichen sechs Firmen sind bei gleichem Seed unverändert (`planung/bestandsvergleich.md`).

## Was funktioniert hat

1. **Bestand zuerst sichern.** Vor jeder Erweiterung eine Referenz-Datenbank mit festem Seed erzeugen (`/home/user/bestand/space_trading_game_bestand.db`) und eine kurze Übersicht ins Repo legen (`bestand_uebersicht.md`). Die Teams haben dadurch echte Lücken gefunden (Orrin und Isolde ohne Stationen, Myrrhen ohne Industriegüter-Angebot) und ihre Ideen an echten Verträgen, Ereignissen und Mitarbeitern festgemacht.
2. **Planung in Dateien, nicht im Kopf der Agenten.** Jede Phase endet mit einem Markdown-Bericht in `planung/` und einem angehängten Eintrag in `NACHRICHTEN.md`. Damit kann jede spätere Phase und jeder neue Agent ohne Vorwissen weiterarbeiten.
3. **Themenfelder trennen.** Team A (Kernraum, Hochtechnologie) und Team B (Grenzraum, Kolonisierung) haben parallel geplant, ohne sich bei Firmen oder SKU-Präfixen zu überschneiden (A–M bzw. N–Z).
4. **Schiedsrichter statt Abstimmung.** Beide Teams lesen beide Berichte und schlagen Verknüpfungen vor; ein dritter Agent vergleicht Punkt für Punkt, übernimmt die besseren Elemente und zählt die Regeln selbst nach. Das Ergebnis ist eine maschinenlesbare Vorlage (`verknuepfungen.json`), an die sich die Umsetzung hält.
5. **Bestandsschutz über eigene Zufallsströme.** Die alten Firmen laufen unverändert im gemeinsamen Strom; jede neue Firma und jedes neue Merkmal bekommt einen eigenen, aus (Seed, Schlüssel, Schritt) abgeleiteten Strom (`derived_seed` mit SHA-256, `World.company_stream`). Schritte, die über alle Zeilen liefen, sind in „Bestand zuerst, dann Erweiterung“ geteilt. Neue Systeme und Archetypen werden hinten angehängt und nur in neuen Produkt-Pools verwendet.
6. **Prüfungen als Abnahme.** Jede neue Tabelle bekommt eigene Konsistenzprüfungen (Fremdschlüssel, Datumslogik, Rechenwege, Zugehörigkeit von Mitarbeitern, Sprache). Der Bestandsvergleich läuft bei Seed 42 automatisch mit (`--baseline`). Ein Test mit absichtlich verfälschter Datenbank hat gezeigt, dass die Prüfungen anschlagen.
7. **Eine Datei, ein Bearbeiter.** Das Skript ist eine einzige Datei. Umsetzungsschritte, die es ändern, laufen nacheinander (erst Integration und Rahmenverträge, dann Schriftverkehr), nicht parallel.

## Was schiefging und wie man es vermeidet

| Problem | Folge | Gegenmaßnahme |
|---|---|---|
| Session-Limit während Phase 3 | Zwei Agenten brachen ab, bevor sie etwas schrieben | Nach jeder Phase committen; Aufträge so schneiden, dass jeder für sich ein fertiges Ergebnis hinterlässt |
| Workflow-Fortsetzung ließ Phase 1 und 2 trotz Zwischenspeicher erneut laufen | ≈ 1,8 Mio. Tokens doppelt verbraucht (Berichte nur nachgeprüft, nicht neu entworfen) | Vor dem Fortsetzen das Journal prüfen; bei Zweifel nur den fehlenden Schritt als einzelnen Agenten starten |
| Auftrag nachträglich erweitert („vorhandene Daten einbeziehen“) | Lauf gestoppt, ≈ 5 Minuten Planung verloren | Bestand und Bestandsschutz von Anfang an in den Auftrag schreiben |
| Mitarbeiter in Schreiben vor ihrem Einstellungsdatum | In Phase 2 entdeckt und korrigiert | Personen immer gegen `hire_date`/`termination_date` prüfen (jetzt eine Prüfung im Skript) |
| Exklusivklauseln widersprachen dem Bestand | Drei Exklusivitäten wurden zu Vorkaufsrechten | Vertragsklauseln vor der Festlegung gegen die Bestandsdaten abfragen |
| Datenbank wächst mit jeder Erweiterung | Seed 7 bei 49,7 MB | Erste Stellschraube: längeres Preisintervall nur für Erweiterungsware |
| Größenanzeige sagt „MB“, rechnet in MiB | Leichte Verwirrung bei Grenzwerten | Bei nächster Gelegenheit Beschriftung korrigieren |

## Kosten

- Phase 1 und 2 (5 Agenten): ≈ 1,76 Mio. Tokens, ≈ 52 Minuten.
- Phase 3b (Integration und Rahmenverträge, 1 Agent): Hauptteil der zweiten Workflow-Runde (insgesamt ≈ 1,8 Mio. Tokens inkl. der doppelt gelaufenen Phasen 1 und 2).
- Phase 3c (Schriftverkehr, 1 Agent): ≈ 0,53 Mio. Tokens, ≈ 45 Minuten.

## Offene Punkte

- Dashboard zeigt noch den Stand mit 6 Firmen und kennt weder Rahmenverträge noch Schriftverkehr.
- Größenbeschriftung MB/MiB im Skript.
- Branch `erweiterung-18-firmen` ist noch nicht nach `main` gemergt.
