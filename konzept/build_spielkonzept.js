// Erzeugt konzept/haulstar-spielkonzept.docx. Aufruf: node konzept/build_spielkonzept.js
// Inhalte stehen unten in CONTENT; Status je Festlegung: E = entschieden, V = Vorschlag, O = offen.
const fs = require("fs");
const path = require("path");
const {
  AlignmentType, BorderStyle, Document, Footer, Header, HeadingLevel, LevelFormat, Packer, PageNumber,
  Paragraph, ShadingType, Table, TableCell, TableRow, TextRun, WidthType,
} = require("docx");

const FONT = "Calibri";
const WIDTH = 9638; // A4 mit 2 cm Rand, in DXA
const STATUS = {
  E: { label: "Entschieden", fill: "E2F0D9" },
  V: { label: "Vorschlag", fill: "FFF2CC" },
  O: { label: "Offen", fill: "EDEDED" },
};
const BORDER = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const CELL_BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };

// **fett** im Fließtext
function runs(text, extra = {}) {
  return text.split(/(\*\*[^*]+\*\*)/).filter(Boolean).map((part) =>
    part.startsWith("**")
      ? new TextRun({ text: part.slice(2, -2), bold: true, font: FONT, ...extra })
      : new TextRun({ text: part, font: FONT, ...extra }));
}

const p = (text, opts = {}) => new Paragraph({ children: runs(text), spacing: { after: 120 }, ...opts });
const TOC = [];
const h1 = (text, { breakBefore = false } = {}) => {
  TOC.push(text);
  return new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: breakBefore, keepNext: true,
    children: [new TextRun({ text, font: FONT })] });
};
const h2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, keepNext: true, children: [new TextRun({ text, font: FONT })] });
const ul = (items) => items.map((t) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: runs(t), spacing: { after: 60 } }));
let olCounter = 0;
const ol = (items) => {
  olCounter += 1;
  const ref = `num${olCounter}`;
  NUMBERINGS.push(ref);
  return items.map((t) => new Paragraph({ numbering: { reference: ref, level: 0 }, children: runs(t), spacing: { after: 60 } }));
};
const NUMBERINGS = [];

function cell(text, width, { header = false, fill } = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    borders: CELL_BORDERS,
    shading: header ? { fill: "1F3864", type: ShadingType.CLEAR, color: "auto" }
      : fill ? { fill, type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: String(text).split("\n").map((line) => new Paragraph({
      children: runs(line, header ? { bold: true, color: "FFFFFF", size: 20 } : { size: 20 }),
    })),
  });
}

function table(head, rows, ratios) {
  const total = ratios.reduce((a, b) => a + b, 0);
  const widths = ratios.map((r) => Math.floor((WIDTH * r) / total));
  widths[widths.length - 1] += WIDTH - widths.reduce((a, b) => a + b, 0);
  return [new Table({
    width: { size: WIDTH, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, cantSplit: true, children: head.map((h, i) => cell(h, widths[i], { header: true })) }),
      ...rows.map((row) => new TableRow({ cantSplit: true, children: row.map((c, i) => cell(c, widths[i])) })),
    ],
  }), new Paragraph({ spacing: { after: 120 }, children: [] })];
}

// Festlegungen: [Thema, Festlegung, Status]
function decisions(rows) {
  const widths = [2300, 5938, 1400];
  return [new Table({
    width: { size: WIDTH, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, cantSplit: true, children: ["Thema", "Festlegung", "Status"].map((h, i) => cell(h, widths[i], { header: true })) }),
      ...rows.map(([topic, text, status]) => new TableRow({
        cantSplit: true,
        children: [cell(`**${topic}**`, widths[0]), cell(text, widths[1]),
          cell(status.split("/").map((s) => STATUS[s].label).join(" / "), widths[2], { fill: STATUS[status[0]].fill })],
      })),
    ],
  }), new Paragraph({ spacing: { after: 120 }, children: [] })];
}

// ---------------------------------------------------------------------------
// Inhalt
// ---------------------------------------------------------------------------

const TOC_PLACEHOLDER = Symbol("toc");
const CONTENT = [
  // Titelseite
  new Paragraph({ spacing: { before: 2400, after: 200 }, children: [new TextRun({ text: "Haulstar", font: FONT, size: 64, bold: true, color: "1F3864" })] }),
  new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: "Neuaufsetzung mit der legami-Welt", font: FONT, size: 36, color: "1F3864" })] }),
  new Paragraph({ spacing: { after: 600 }, children: [new TextRun({ text: "Spielkonzept · Version 0.1 · Stand 21.10.2026", font: FONT, size: 24, color: "595959" })] }),
  p("Grundlage: deine Antworten vom 21.10.2026 (Anhang B), der Datengenerator auf dem Branch erweiterung-18-firmen im Repo legami und der heutige Stand von Haulstar im Repo idlestar."),
  p("**Statusangaben in den Tabellen:**"),
  ...table(["Status", "Bedeutung"], [
    ["Entschieden", "Von dir festgelegt."],
    ["Vorschlag", "Von mir gesetzt, wo du „weiß ich nicht“ oder „entscheidest du“ geantwortet hast oder etwas fehlte. Gilt, bis du es bestätigst oder änderst."],
    ["Offen", "Muss noch geplant werden."],
  ], [1, 4]),
  p("Alle Zahlen sind Startwerte für Tests. Im Spiel gehören sie in Content-Dateien und werden dort als TBD markiert, wie bisher in Haulstar."),
  new Paragraph({ pageBreakBefore: true, children: [new TextRun({ text: "Inhalt", font: FONT, size: 32, bold: true, color: "1F3864" })] }),
  TOC_PLACEHOLDER,

  // 1
  h1("1 Zweck des Dokuments", { breakBefore: true }),
  p("Dieses Dokument beschreibt, wie Haulstar mit der Welt aus legami neu aufgesetzt wird. Es ist der Ausgangspunkt für die weitere Planung über mehrere Sessions, bis ein Phasenplan alles abdeckt. Code entsteht erst danach."),
  p("Jeder Abschnitt nennt zuerst die Festlegungen mit Status und erklärt dann, wie das im Spiel funktionieren soll. Abschnitt 18 sammelt die offenen Punkte und schlägt die Reihenfolge der nächsten Planungsdokumente vor."),

  // 2
  h1("2 Spielidee"),
  p("Am 1. Januar 2060 öffnen die Konzerne den Weltraum für freie Händler. Der Spieler gründet eine kleine Firma mit **25.000 CR** und einem 16 Jahre alten Schiff (Baujahr 2044, Wert **125.000 CR**). Er handelt mit den etablierten Firmen, beliefert sie und transportiert in ihrem Auftrag. Er baut Kontakte und Ruf auf, steigt später in Förderung und Produktion ein, kauft Anteile und übernimmt Firmen: freundlich, feindlich oder aus der Insolvenz. Die Wirtschaft rechnet weiter, auch wenn der Spieler gerade nicht spielt."),
  h2("2.1 Kernschleife"),
  ...ol([
    "**Informieren:** Auftragsbörsen der Firmen, Newsfeed, Kontakte, Marktpreise.",
    "**Entscheiden:** kaufen und verkaufen, Auftrag oder Vertrag annehmen, Route einrichten, Angebot schreiben.",
    "**Ausführen:** Schiffe fliegen in Spielzeit. Überfälle, Ausfälle und Verspätungen können eintreten.",
    "**Ergebnis:** Credits, Ruf, Vertrauen, neue Kontakte, unter Umständen Strafen.",
    "**Ausbauen:** Schiffe, Personal, Förderung und Produktion, Anteile, Übernahmen.",
  ]),
  h2("2.2 Drei Spielebenen"),
  ...table(["Ebene", "Der Spieler ist", "Typische Tätigkeiten", "Erreicht durch"], [
    ["Händler", "Kapitän und Kaufmann", "Handel, Transportaufträge, erste Lieferverträge", "Spielstart"],
    ["Unternehmer", "Chef einer Firma mit Flotte und Personal", "Rahmenverträge, Förderung und Produktion, Lizenzen, Automatisierung", "Geld, Ruf, Technologie"],
    ["Konzernlenker", "Eigentümer mehrerer Firmen", "Börse, Beteiligungen, Übernahmen, Manager, Konflikte um Ressourcen", "Kapital, Ruf, Kontakte"],
  ], [2, 3, 5, 3]),

  // 3
  h1("3 Plattform, Technik und Daten"),
  ...decisions([
    ["Plattform", "Spielbar im Browser wie heute (haulstar-test.seritha.dev, live haulstar.seritha.dev). Nach der Testphase als App im App Store und bei Google Play.", "E"],
    ["Codebasis", "Eine Codebasis für Web und Apps (Expo/React Native), wie heute. Die Store-Profile (EAS) sind schon angelegt, es fehlt nur noch „eas init“.", "V"],
    ["Spieler", "Erst einmal Einzelspieler gegen NPC-Firmen.", "E"],
    ["Simulation", "Deterministisch und offline lauffähig: Beim Öffnen holt das Spiel die verstrichene Spielzeit nach (Lazy Tick wie in Haulstar).", "V"],
    ["Weltdaten", "legami ist eine Grundlage, aber nicht die einzige. Erweiterungen sind erlaubt, wenn das Setting sie trägt.", "E"],
    ["Weiterrechnen", "Die Wirtschaft rechnet nach dem Stichtag weiter. faker.js erzeugt neue Namen, Personen und Kunden, angepasst an den Anwendungsfall.", "E"],
    ["Aufgabenteilung", "faker.js nur für Namen und Texte, mit festem Seed. Die Wirtschaftslogik (Bestellungen, Produktion, Preise) ist eigener, deterministischer Code im Spielkern.", "V"],
    ["Sprache", "Alle Texte und die gesamte Kommunikation auf Deutsch und Englisch.", "E"],
  ]),
  h2("3.1 Datenweg von legami ins Spiel"),
  ...ol([
    "Der Python-Generator in legami erzeugt die Welt bis zum 31.12.2059, wie heute, mit festem Seed.",
    "Ein neuer Exportschritt schreibt daraus einen **Startstand**: JSON-Pakete je Bereich (Firmen, Stationen, Waren, Personen, laufende Verträge, Schreiben, Preise der letzten Monate).",
    "Das Spiel lädt den Startstand und rechnet ab dem 1.1.2060 mit eigener TypeScript-Logik weiter.",
    "Die 62 Prüfungen des Generators bleiben die Abnahme für den Startstand. Das Spiel bekommt eigene Tests für das Weiterrechnen.",
  ]),
  p("Die Datenbank ist heute rund 42 MiB groß. Für Browser und Handy braucht es einen schlanken Startstand mit nur der Historie, die das Spiel auch zeigt (Vorschlag: 12 Monate Preise und Monatsabschlüsse, laufende Verträge, Schreiben der letzten 6 Monate). Die Zielgröße ist offen, bis sie gemessen ist."),
  p("Der Spielkern von Haulstar verbietet aus Gründen der Determinismus-Sicherheit Funktionen wie Math.sin oder Math.exp. Das Preismodell aus legami (Saisonkurven, Rauschen) muss deshalb mit Festkomma-Rechnung oder Tabellen nachgebaut werden."),

  // 4
  h1("4 Zeit und Beschleunigung"),
  ...decisions([
    ["Beschleunigung", "Das Spiel läuft schneller als die Echtzeit (logische Beschleunigung).", "E"],
    ["Nachtmodus", "Nachts zwischen 22:00 und 6:00 Uhr Ortszeit läuft die Zeit langsamer, damit man im Schlaf nicht zu viel verpasst. In den Einstellungen abschaltbar.", "E"],
    ["Faktoren", "Tagsüber 24 (1 Echtzeitstunde = 1 Spieltag), nachts 6 (1 Echtzeitstunde = 6 Spielstunden).", "V"],
    ["Pause / Urlaub", "Gibt es eine Pause oder einen Urlaubsmodus?", "O"],
  ]),
  h2("4.1 Was die Faktoren bedeuten"),
  ...table(["Spielzeit", "Echtzeit (Vorschlag, mit Nachtmodus)"], [
    ["1 Spieltag", "1 Stunde tagsüber, 4 Stunden nachts"],
    ["1 Echtzeittag", "18 Spieltage (16 h × 24 + 8 h × 6 = 432 Spielstunden)"],
    ["1 Spielmonat (30 Tage)", "etwa 1,7 Echtzeittage"],
    ["1 Spieljahr", "etwa 20 Echtzeittage"],
    ["Flug Sol → Halcyon (139 RE, 26 Spielstunden)", "etwa 65 Minuten tagsüber, 4,4 Stunden nachts"],
    ["Flug Sol → Vaskar (720 RE, 123 Spielstunden)", "etwa 5 Stunden tagsüber"],
  ], [1, 1]),
  p("Flugzeiten nach der Formel des Generators: 6 Raumeinheiten (RE) je Spielstunde plus 3 Stunden für An- und Abdocken."),
  h2("4.2 Regeln für die Umsetzung"),
  ...ul([
    "Haulstar kennt heute keine Beschleunigung: Der Kern bekommt die Zeit nur als Parameter, und env/clock.ts ist die einzige Stelle mit Date.now(). Die Beschleunigung gehört deshalb in diese Uhr-Schicht. Der Kern rechnet nur in Spielzeit.",
    "Die Spielzeit ergibt sich aus der Echtzeit und einem gespeicherten **Zeitplan** aus Abschnitten mit Faktor. Damit bleibt das Nachrechnen nach langer Abwesenheit deterministisch.",
    "Die Ortszeit kommt aus der Zeitzone des Geräts. Ein Wechsel der Zeitzone oder der Einstellung gilt ab der nächsten vollen Minute und wird im Zeitplan vermerkt. Echtzeit, die schon vergangen ist, wird nie neu bewertet.",
    "Der Spielkalender beginnt am 1.1.2060 um 00:00. Monatsabschlüsse, Zinsen, Gehälter, Raten und Unterhalt laufen nach Spielkalender, nicht nach Echtzeit-Mitternacht.",
  ]),

  // 5
  h1("5 Welt"),
  p("Ab 2030 übernehmen KI-Systeme große Teile der Industrie. Bis in die 2050er bauen die Konzerne mit KI-Leitsystemen eine automatisierte Infrastruktur im All auf. Am 1.1.2060 wird der Raum für freie Händler geöffnet. Außerhalb von Sol haben Regierungen weder die Informationen noch die Infrastruktur, um dauerhaft Frieden durchzusetzen. Private Sicherheitsfirmen schützen die Routen, und Konflikte um Ressourcen gehören fast zum Alltag."),
  h2("5.1 Was legami schon liefert"),
  ...table(["Bereich", "Umfang"], [
    ["Firmen", "18: je 6 kleine, mittlere und große, 9 deutschsprachig, 9 englischsprachig (Anhang A)"],
    ["Sternensysteme", "13, vom Kern (Sol) bis Far Reach"],
    ["Stationen", "109 in 8 Typen: Handel, Industrie, Bergbau, Forschung, Agrar, Freihafen, Militär, Schmugglerhafen"],
    ["Waren", "69 Grundwaren in 8 Kategorien, dazu Qualitätsvarianten"],
    ["Beziehungen", "Partnerschaften, Rivalitäten, Rahmenverträge mit Nachträgen"],
    ["Geschäftsdaten", "Verträge, Bestellungen, Lieferungen, Preisverläufe, Ereignisse, Monatsabschlüsse"],
    ["Menschen", "Mitarbeiter mit Rolle, Gehalt, Einfluss, Loyalität, Bestechlichkeit, Zugriffsstufe (0–3) und Persönlichkeit"],
    ["Schriftverkehr", "3.492 Schreiben in 20 Briefarten, darunter Gerüchte, vertrauliche Hinweise und Lecks"],
  ], [1, 3]),
  h2("5.2 Sternensysteme"),
  ...table(["System", "Ring", "Sicherheit", "Abstand zu Sol", "Flug ab Sol"], [
    ["Sol", "Kern", "hoch", "0 RE", "–"],
    ["Halcyon", "Innerer Ring", "hoch", "139 RE", "26 h"],
    ["Tauvel", "Innerer Ring", "hoch", "173 RE", "32 h"],
    ["Pellora", "Innerer Ring", "hoch", "174 RE", "32 h"],
    ["Aurelis", "Mittlerer Gürtel", "mittel", "216 RE", "39 h"],
    ["Myrrhen", "Mittlerer Gürtel", "mittel", "276 RE", "49 h"],
    ["Orrin", "Mittlerer Gürtel", "mittel", "293 RE", "52 h"],
    ["Brennus", "Äußerer Rand", "niedrig", "413 RE", "72 h"],
    ["Isolde", "Äußerer Rand", "mittel", "454 RE", "79 h"],
    ["Kharon", "Grenzraum", "niedrig", "551 RE", "95 h"],
    ["Serravel", "Far Reach", "mittel", "574 RE", "99 h"],
    ["Nyx", "Grenzraum", "gesetzlos", "635 RE", "109 h"],
    ["Vaskar", "Far Reach", "niedrig", "720 RE", "123 h"],
  ], [2, 3, 2, 2, 2]),
  h2("5.3 Änderungen und Erweiterungen"),
  ...decisions([
    ["Freischaltung", "Alles ist von Anfang an offen: Jeder Sektor ist sichtbar, man kann Schiffe überall hinschicken und mit allen Stationen handeln.", "E"],
    ["Freischaltstufe", "Das Feld unlock_tier wird zur Gefahrenstufe der Route (fließt in die Überfallrate ein, Abschnitt 15).", "V"],
    ["Neue Firmen", "Nur wenn das Setting sie trägt. Fehlt für eine Aufgabe eine passende Firma, kommt eine dazu, die ein Jahr vor Spielstart gegründet wurde (2059), nicht zu Beginn der Zeitlinie.", "E"],
    ["Startstation", "Neue Station „Freihafen Sol“ unter neutraler Hafenverwaltung, nicht übernehmbar.", "V"],
    ["Institutionen", "Bank, Börse, Zoll, Justiz und Finanzaufsicht sind Institutionen, keine Firmen, und nicht übernehmbar. Ein Kartellamt gibt es nicht.", "V/E"],
    ["Freie Händler", "6–10 NPC-Freihändler, die wie der Spieler 2060 starten und um Ausschreibungen konkurrieren.", "V"],
    ["Eigentümer", "Neu in den Daten: Aktionärs- bzw. Gesellschafterstruktur je Firma (Abschnitt 13).", "V"],
    ["Produktionsrezepte", "Neu: Eingangs- und Ausgangswaren je Station (Abschnitt 7.4).", "E/O"],
    ["Planeten", "Neu: Planeten mit umkämpften Ressourcenpunkten (Abschnitt 15).", "E/O"],
    ["Open-Source-Plattform", "Neu: Plattform mit frei verfügbaren Bauplänen (Abschnitt 7.4).", "E"],
  ]),

  // 6
  h1("6 Spielstart: drei Szenarien"),
  p("Für alle drei gilt: 25.000 CR, ein Schiff im Wert von 125.000 CR mit Baujahr 2044, Start in Sol an einer neutralen Handelsstation und eine geführte Einstiegsphase. Name, Logo und Rechtsform der Firma sind frei wählbar."),
  ...table(["", "Solo-Gründer", "Kleines Netzwerk", "Konzerner"], [
    ["Schwierigkeit", "schwer", "mittel", "leicht"],
    ["Schiff", "auf Kredit", "gebraucht", "gekauft"],
    ["Informationen", "nur öffentliche Ausschreibungen; keine Infos über andere Firmen, kein Zugriff auf Gerüchte", "Gerüchte, aber keine Insiderinfos", "Gerüchte und Insiderinfos"],
    ["Kontakte", "keine; müssen erst aufgebaut werden", "2 Kontakte bei 2 Firmen, die je einen Startauftrag anbieten", "8 Kontakte, verteilt auf kleine, mittlere und große Firmen; 6 davon machen Angebote"],
  ], [2, 3, 3, 3]),
  ...decisions([
    ["Kredit (Solo)", "125.000 CR von der Bank, 8 % Zins pro Jahr, 60 Monatsraten zu je etwa 2.535 CR. Das Schiff ist die Sicherheit. Bei Rückstand: Mahnung, dann Pfändung des Schiffs.", "V"],
    ["Gebraucht (Netzwerk)", "Von einem Kontakt übernommen und bezahlt, ohne Garantie. Die Wartungshistorie ist lückenhaft, deshalb fällt das Schiff in den ersten 6 Spielmonaten häufiger aus.", "V"],
    ["Gekauft (Konzerner)", "Über die Gebrauchtabteilung von Graufalk Orbitalwerften gekauft, mit Wartungsheft und ohne Mängel.", "V"],
    ["Kontakte (Konzerner)", "Verteilung 3 klein, 3 mittel, 2 groß. Die Kontakte sind echte Mitarbeiter aus den Daten, meist aus Partnerbetreuung oder Handel.", "V"],
    ["Gerüchte (Solo)", "Freischaltung später über einen ersten Kontakt oder ein Newsfeed-Abo.", "V"],
    ["Einstiegsphase", "Eine geführte Lehrzeit wie in Haulstar. Auf den ersten 12 Routen gibt es weder Überfälle noch Verluste.", "E"],
  ]),
  h2("6.1 Rechtsform der eigenen Firma"),
  ...table(["Rechtsform", "Voraussetzung", "Haftung", "Besonderheit"], [
    ["Einzelunternehmen", "keine", "mit dem Privatvermögen", "einfach, kein Mindestkapital"],
    ["GmbH", "25.000 CR Stammkapital (genau das Startkapital)", "nur mit dem Firmenvermögen", "Standardwahl"],
    ["AG", "50.000 CR Grundkapital, später Börsengang ab Größe und Ruf", "nur mit dem Firmenvermögen", "Aktien, Kapital von der Börse; kann selbst übernommen werden"],
  ], [2, 3, 2, 3]),
  p("Status: Vorschlag. Wählbar ist die Rechtsform laut deiner Antwort (Entschieden), die genauen Bedingungen sind von mir."),

  // 7
  h1("7 Waren, Produktion und Markt"),
  h2("7.1 Waren"),
  ...decisions([
    ["Grundwaren", "Der Markt ist um die Grundwaren aufgebaut (69 in 8 Kategorien).", "E"],
    ["Firmenprodukte", "Firmenprodukte sind an die Firma angepasst. Nicht jede Firma produziert alles, manche Waren gibt es exklusiv bei einem Hersteller. Große Firmen produzieren größere Mengen als mittlere und kleine.", "E"],
    ["Darstellung", "Unter jeder Grundware stehen die Angebote der Hersteller mit Qualitätsstufe. Die Varianten aus dem Generator (z. B. Güteklasse A/B, Mk I/Mk III) werden zu Qualitätsstufen mit Wirkung auf Preis, Ertrag und Ausfallrisiko.", "V"],
    ["Ausprobieren", "Du willst die Produktansicht selbst ausprobieren. Dafür sollte es früh einen Testaufbau geben, in dem man die Ansichten umschalten kann.", "O"],
  ]),
  ...table(["Kategorie", "Grundwaren", "Beispiele (Basispreis in CR)"], [
    ["Rohstoffe", "13", "Regolith-Granulat 30, Eisenerz 85, Titanerz 420, Seltene Erden 2.400, Platinmetalle 15.500"],
    ["Energie", "6", "Brennstoffzellen 950, Deuterium 1.800, Helium-3 6.500, Antimaterie-Kapseln 48.000"],
    ["Industriegüter", "13", "Sinterbausteine 380, Verbundstahl 1.300, Triebwerksteile 7.200, Habitatmodule 46.000"],
    ["Technologie", "9", "Elektronik 2.400, Navigationscomputer 14.000, KI-Kerne 36.000"],
    ["Nahrung", "7", "Algenkonzentrat 120, Proteinpaste 140, Kulturfleisch 420, Orbitalgetreide 520"],
    ["Medizin", "6", "Medikamente 1.800, Impfstoffe 3.100, Nanomedizin 12.500"],
    ["Luxus", "9", "Orbitalkaffee 950, Erd-Wein 2.600, Edelsteine 12.000, Kunstobjekte 45.000"],
    ["Schmuggelware", "6", "Kampfstimulanzien 6.800, Gestohlene Technologie 24.000, Gehackte KI-Kerne 52.000"],
  ], [20, 14, 66]),
  h2("7.2 Preise"),
  ...decisions([
    ["Spielereinfluss", "Käufe und Verkäufe des Spielers verschieben die Preise nicht spürbar.", "E"],
    ["Marktzyklen", "Preise folgen echten Marktzyklen. Ereignisse wirken auf die Preise.", "E"],
    ["Modell", "Preis je Station und Ware = Basispreis × Zyklus (Saison, Konjunktur) × Angebot/Nachfrage der NPC-Wirtschaft × Ereignisfaktor, mit deterministischem Rauschen. Das setzt das Preismodell des Generators fort (Saison, Rauschen, Engpässe, Nachfragespitzen, Preisbrüche, Ereignisschocks). Der Spieler wirkt nur über große Mengen auf die Bestände, z. B. durch Horten oder große Lieferverträge.", "V"],
    ["Haulstar-Formel", "Die heutige Haulstar-Formel (der Preis hängt am Lagerbestand, den der Spieler direkt verschiebt) passt nicht dazu und wird ersetzt.", "V"],
  ]),
  h2("7.3 Kosten je Fahrt"),
  p("Übernahme aus den Rechenwegen des Generators (Status: Vorschlag, du hattest „ich denke schon“ geantwortet):"),
  ...table(["Kostenart", "Regel"], [
    ["Treibstoff", "Entfernung × (22 CR × Auslastung des Laderaums + 0,006 CR je Tonne Ladung)"],
    ["Einfuhrzoll", "6 % (hohe Sicherheit), 4,5 % (mittel), 2,5 % (niedrig), 0 % (gesetzlos) des Warenwerts am Zielort"],
    ["Schmuggelware", "15 % Schutz- und Schmiergelder statt Zoll"],
    ["Andockgebühr", "je Station festgelegt"],
    ["Versicherung", "0,2 % / 0,5 % / 1,2 % / 2,5 % des Warenwerts je Risikostufe; 3 % Aufschlag bei illegaler Ladung"],
    ["Zahlungsziel", "30 Tage"],
  ], [1, 4]),
  h2("7.4 Produktion, Förderung und Technologie"),
  ...decisions([
    ["Produktionsketten", "Firmen produzieren aus Eingangswaren. Liefert ihnen niemand, sinkt ihre Produktion.", "E"],
    ["Eigene Produktion", "Der Spieler darf selbst fördern und produzieren, sobald er Geld und Technologie dafür hat.", "E"],
    ["Open Source", "Auf einer Plattform gibt es Open-Source-Projekte zum Erkunden, als Anregung für eigene Förderung oder Produktion. Ihre Qualität liegt unter der von Firmenprodukten. Mit genug Masse kann man damit Geld verdienen.", "E"],
    ["Lizenzen", "Wer genug Geld hat, für den soll sich ein Lizenzprodukt einer Firma lohnen.", "E"],
    ["Plattform im Spiel", "Durchsuchbare Sammlung von Projekten (z. B. „Regolith-Sinteranlage v0.4“) mit Bewertungen, Reifegrad und Fehlerrate. Das Erkunden kostet Zeit; manche Projekte sind veraltet oder fehlerhaft.", "V"],
    ["Lizenzkosten", "Einmalbetrag plus Lizenzgebühr je produzierter Einheit; der Lizenzgeber kann die Lizenz bei Vertragsbruch entziehen.", "V"],
    ["Rezepte", "Welche Ware woraus entsteht (z. B. Eisenerz + Kohlenstoffkonzentrat + Energie → Verbundstahl).", "O"],
    ["Eigene Forschung", "Gibt es zusätzlich eigene Entwicklung, etwa als Rest des Haulstar-Forschungsbaums?", "O"],
  ]),
  ...table(["Technologiequelle", "Kosten", "Qualität", "Wann sinnvoll"], [
    ["Open-Source-Projekt", "gering", "unter Firmenniveau", "Einstieg; lohnt sich über die Menge"],
    ["Lizenz einer Firma", "hoch", "Firmenniveau", "sobald man es sich leisten kann"],
    ["Eigene Entwicklung", "offen", "offen", "offen"],
  ], [3, 2, 2, 3]),
  h2("7.5 NPC-Wirtschaft"),
  ...ul([
    "Firmen bestellen, liefern, produzieren, schließen Verträge und machen Monatsabschlüsse. Das Monatsergebnis wird wie im Generator gerechnet: Umsatz minus Wareneinsatz, Zölle, Logistik, Flotte, Personal, Stationsunterhalt und Vertragsstrafen.",
    "Ereignisse sind zufällig (Entschieden). Die Daten kennen 10 Arten: Piratenangriff, Asteroidensturm, Streik, Maschinenausfall, Ernteausfall, Rohstofffund, Zollkontrolle, Quarantäne, Razzia auf dem Schwarzmarkt und Nachfrageboom. Neu kommen Konflikte um Ressourcen dazu (Abschnitt 15).",
    "Firmen können pleitegehen (Abschnitt 12.5).",
  ]),

  // 8
  h1("8 Handel, Aufträge und Verträge"),
  ...table(["Form", "Ware gehört", "Spieler verdient", "Risiko für den Spieler"], [
    ["Direkthandel", "dem Spieler", "Verkaufspreis − Einkaufspreis − Kosten", "Preisschwankung, Verlust der Ladung"],
    ["Transportauftrag", "dem Auftraggeber", "Frachtlohn", "Haftung bei Verlust oder Verspätung"],
    ["Liefervertrag", "dem Spieler bis zur Übergabe", "Vertragspreis", "Frist und Vertragsstrafe"],
    ["Rahmenvertrag", "dem Spieler bis zur Übergabe", "Vertragspreis über viele Abrufe", "Volumen, Fristen, Nachträge"],
  ], [2, 2, 3, 3]),
  ...decisions([
    ["Firmen versorgen", "Über Lieferverträge mit Frist und Vertragsstrafe. Rahmenverträge erst ab einem bestimmten Ruf.", "E"],
    ["Haftung", "Geht Ware im Auftrag verloren, erstattet der Spieler den Warenwert, sofern er keine Versicherung abgeschlossen hat.", "E"],
    ["Schutzphase", "Auf den ersten 12 Routen gibt es keine Überfälle und keine Verluste.", "E"],
    ["Auftragsbörse", "Jede Firma hat ihre eigene Auftragsbörse. Manche Aufträge stehen nur Firmen offen, die schon Ruf oder Kontakte haben.", "E"],
    ["Sichtbarkeit", "Vier Stufen: öffentlich / ab Ruf X bei der Firma / nur über einen Kontakt / nur auf Einladung (Rahmenverträge).", "V"],
    ["Vertragsstrafe", "Wie im Generator: 0,6 % des Abrufwerts je Verzugstag.", "V"],
    ["Kaution", "Bei Transportaufträgen ab einem bestimmten Warenwert 10 % Kaution; entfällt ab gutem Ruf bei der Firma.", "V"],
    ["Verhandeln", "Preis, Menge und Frist lassen sich per Gegenangebot verhandeln (Abschnitt 9.3).", "V"],
    ["Wiederholung", "Wiederkehrende Fahrten als Handelsroute wie in Haulstar (einmal, N-mal, endlos).", "V"],
  ]),

  // 9
  h1("9 Information"),
  h2("9.1 Newsfeed und Gerüchte"),
  ...decisions([
    ["Ort", "Gerüchte erscheinen im Newsfeed.", "E"],
    ["Wahrheit", "Gerüchte sind manchmal falsch.", "E"],
    ["Quellen", "Ob ein Gerücht stimmt, bleibt verborgen (in den Daten das Feld is_accurate). Jede Quelle hat eine Zuverlässigkeit, die der Spieler mit der Zeit kennenlernt. Falsche Gerüchte können gezielt gestreut sein, auch vom Spieler (Abschnitt 12.2).", "V"],
  ]),
  h2("9.2 Wer sieht was"),
  ...table(["Information", "Solo-Gründer", "Kleines Netzwerk", "Konzerner", "Später freischaltbar über"], [
    ["Öffentliche Ausschreibungen", "ja", "ja", "ja", "–"],
    ["Öffentliche Nachrichten", "ja (Vorschlag)", "ja", "ja", "–"],
    ["Gerüchte", "nein", "ja", "ja", "Kontakt oder Abo (Vorschlag)"],
    ["Insiderinfos", "nein", "nein", "ja", "Kontakte mit hoher Zugriffsstufe, Bestechung, Hacking"],
    ["Interne Kommunikation einer Firma", "nein", "nein", "nein", "nur durch Übernahme oder Hacking (Entschieden)"],
  ], [3, 2, 2, 2, 3]),
  h2("9.3 Schriftverkehr"),
  p("Du hattest geantwortet: so, wie es die beste Nutzererfahrung ergibt. Mein Vorschlag:"),
  ...ul([
    "Der Spieler schreibt über **Vorlagen**: Art (Anfrage, Angebot, Gegenangebot, Beschwerde, Übernahmeangebot …), Felder (Ware, Menge, Preis, Frist) und Tonfall (freundlich, sachlich, hart). Das geht auf dem Handy schnell und lässt sich auswerten.",
    "Die Antworten der Firmen folgen Regeln (Vertrauen, Ruf, Persönlichkeit, Lage der Firma) und sind deterministisch. So bleibt das Spiel offline spielbar und testbar.",
    "Später optional: Eine KI formuliert den Brieftext aus. Sie ändert nur die Formulierung, nie die Entscheidung.",
    "Ein Posteingang mit Verläufen und Fristen („Antwort erforderlich bis …“).",
    "Jedes Schreiben gibt es auf Deutsch und Englisch; angezeigt wird die Spielsprache.",
  ]),
  h2("9.4 Hacking"),
  p("Entschieden: Die interne Kommunikation einer Firma ist ohne Übernahme nur über Hacking zugänglich, mit verschiedenen Angriffsmethoden. Mein Vorschlag für die Methoden:"),
  ...table(["Methode", "Weg", "Aufwand", "Entdeckungsrisiko", "Ergebnis"], [
    ["Phishing", "gefälschte Schreiben an Mitarbeiter", "gering, kurz", "mittel", "Postfach einer Person bis zu deren Zugriffsstufe"],
    ["Bestechung", "Mitarbeiter mit hoher Bestechlichkeit oder niedriger Loyalität", "mittel", "mittel bis hoch", "Schreiben bis zur Zugriffsstufe der Person"],
    ["Lieferkette", "manipulierte Elektronik oder Navigationscomputer in Lieferungen an die Firma", "hoch, lang", "niedrig", "dauerhafter Zugang zu einer Station"],
    ["Schwarzmarkt-Werkzeug", "Kauf von Angriffswerkzeug, z. B. Gehackte KI-Kerne", "hoch", "wechselnd", "einmaliger tiefer Zugriff"],
    ["Eingeschleuster Mitarbeiter", "eigene Person bewirbt sich bei der Firma", "lang", "niedrig, bei Entdeckung großer Schaden", "laufender Insiderzugang"],
  ], [20, 30, 18, 25, 30]),
  p("Die Zugriffsstufe der Mitarbeiter (0–3) entscheidet, welche Schreiben sichtbar werden. Die Daten haben dafür schon das Feld min_intel_access_level. Was bei Entdeckung passiert, steht in Abschnitt 11."),

  // 10
  h1("10 Ruf, Vertrauen und Kontakte"),
  ...decisions([
    ["Ebenen", "Ruf je Firma und ein grundlegender Ruf.", "E"],
    ["Wirkung", "Ruf öffnet den Zugang zu Verträgen, Beziehungen und Firmenübernahmen und senkt die Überfallrate.", "E"],
    ["Belegschaft", "Wer eine gute Beziehung zum Großteil der Belegschaft hat, sei es durch Aktionen oder passiven Ruf, ist bei Verhandlungen im Vorteil.", "E"],
  ]),
  ...table(["Größe", "gilt für", "wirkt auf", "steigt durch", "sinkt durch"], [
    ["Ruf (grundlegend)", "Spielerfirma", "Überfallrate, öffentliche Aufträge, Kreditzins", "pünktliche Lieferungen, erfüllte Verträge", "Verluste, Strafen, öffentliche Skandale"],
    ["Ruf je Firma", "eine Firma", "Auftragsstufen, Rahmenverträge, Übernahmegespräche", "Aufträge für diese Firma, Hilfe bei Engpässen", "Verspätungen, Beschwerden, Angriffe auf die Firma"],
    ["Vertrauen", "eine Person", "Verhandlungen, Insiderinfos, Empfehlungen", "Gespräche, Gefallen, eingehaltene Zusagen", "gebrochene Zusagen, aufgeflogene Bestechung"],
    ["Stimmung der Belegschaft", "eine Firma", "Annahme von Übernahmen, Streikgefahr danach", "Ruf bei der Belegschaft, gute Bedingungen in übernommenen Firmen", "Entlassungen, gebrochene Zusagen"],
  ], [2, 2, 3, 3, 3]),
  h2("10.1 Kontakte"),
  ...ul([
    "Kontakte sind echte Personen aus den Mitarbeiterlisten der Firmen. Man gewinnt sie über Aufträge, Treffen auf Stationen oder Empfehlungen anderer Kontakte (Vorschlag).",
    "Die Persönlichkeit aus den Daten bestimmt, was wirkt (Vorschlag): Bei **gierig** zählt Geld, **loyal** ist schwer zu bestechen und hält zur eigenen Firma, **gesprächig** gibt Gerüchte weiter, **vorsichtig** braucht Zeit und Sicherheiten, **ehrgeizig** will Aufstieg, **idealistisch** achtet auf Belegschaft und Zukunft, **pragmatisch** rechnet nüchtern.",
    "Einfluss und Zugriffsstufe einer Person bestimmen, wie viel ein Kontakt bewirken und verraten kann.",
  ]),

  // 11
  h1("11 Illegales und Justiz"),
  ...decisions([
    ["Schmuggel", "Ist erlaubt. Kommt es durch ein Leck, einen Whistleblower o. Ä. heraus, folgt nach einiger Zeit eine Strafe. Wird sie nicht bezahlt, werden Schiffe beschlagnahmt, so wie in echt.", "E"],
    ["Bestechung", "Ist möglich. Wer erwischt wird, zahlt Strafe. In schweren Fällen müssen eigene Angestellte für eine Zeit ins Gefängnis; der Spieler entscheidet dann, ob er sie kündigt oder behält.", "E"],
    ["Behörden", "Zoll, Justiz und Finanzaufsicht (für Börsenmanipulation und Insiderhandel). Ein Kartellamt gibt es nicht.", "V/E"],
    ["Persönliche Haftung", "Kann der Spieler selbst belangt werden (z. B. Geschäftsführerhaftung)?", "O"],
  ]),
  ...table(["Tat", "Fliegt auf durch", "Folge"], [
    ["Schmuggel", "Leck, Whistleblower, Zollkontrolle, Razzia", "Bußgeld, Ware wird eingezogen, Ruf sinkt"],
    ["Bestechung", "Whistleblower, interne Prüfung der Firma", "Bußgeld, Vertrauen und Ruf bei der Firma sinken, in schweren Fällen Haft"],
    ["Hacking", "Sicherheitsdienst der Firma, Spurensuche", "Bußgeld, Schadenersatz, Haft, Ruf sinkt"],
    ["Marktmanipulation, Insiderhandel", "Finanzaufsicht", "Bußgeld, Abschöpfung des Gewinns, Handelssperre"],
  ], [2, 3, 4]),
  h2("11.1 Ablauf (Vorschlag)"),
  ...ol([
    "Jede Tat hinterlässt eine **Spur** mit einer Entdeckungswahrscheinlichkeit je Monat. Sie steigt mit der Zahl der Mitwisser und dem Umfang.",
    "Die Entdeckung kommt verzögert, nach 1–6 Spielmonaten.",
    "Eine Ermittlung kündigt sich im Posteingang an. Dann kommt ein Bescheid mit Strafe und Zahlungsfrist. Die Strafe ist ein Vielfaches des Gewinns aus der Tat plus ein Grundbetrag.",
    "Wird nicht bezahlt, folgen Mahnung, Kontopfändung, Beschlagnahme von Schiffen und schließlich deren Versteigerung.",
    "In schweren Fällen gehen beteiligte Angestellte für 1–12 Spielmonate in Haft. Behält der Spieler sie, steigt ihre Loyalität, aber sie fallen so lange aus. Kündigt er sie, sinkt die Stimmung der übrigen Belegschaft leicht.",
  ]),

  // 12
  h1("12 Finanzen"),
  h2("12.1 Bank und Kredite"),
  ...decisions([
    ["Übernahme auf Pump", "Ist erlaubt, solange sie sich wirtschaftlich rechnet.", "E"],
    ["Kreditrahmen", "Hängt von der Bonität ab (die Daten haben schon eine Bonitätsnote je Firma, z. B. BBB+), von Sicherheiten (Schiffe, Stationen, Anteile) und vom Ruf. Zins = Grundzins + Risikoaufschlag.", "V"],
    ["Übernahmekredit", "Die Anteile der Zielfirma können als Sicherheit dienen.", "V"],
  ]),
  h2("12.2 Börse"),
  ...decisions([
    ["Börse", "Es gibt eine Börse, und man kann sie manipulieren.", "E"],
    ["Rohstoffe", "Rohstoffpreise wirken tatsächlich auf die Kursentwicklung der Firmen.", "E"],
    ["Kursmodell", "Kurs = fairer Wert × Stimmung × Rauschen. Der faire Wert ergibt sich aus Monatsergebnissen, Kasse, Vermögen (Stationen, Flotte, Lager), Verträgen und der Rohstoffabhängigkeit. Steigen die Preise der Waren, die eine Firma verkauft, steigt ihr Kurs; steigen die Preise ihrer Einsatzstoffe, sinkt er. Die Stimmung kommt aus Newsfeed, Gerüchten und Ereignissen.", "V"],
    ["Rohstoffbörse", "Handel mit Terminkontrakten auf Grundwaren?", "O"],
  ]),
  ...table(["Manipulation", "Wirkung", "Risiko"], [
    ["Gerüchte streuen", "Stimmung und Kurs bewegen sich kurzfristig", "Finanzaufsicht, Ruf"],
    ["Rohstoff horten", "Rohstoffpreis und Kurse abhängiger Firmen bewegen sich", "bindet viel Kapital; Absprachen fallen auf"],
    ["Leerverkauf vor schlechter Nachricht", "Gewinn bei Kurssturz", "gilt als Insiderhandel, wenn man es vorher wusste"],
    ["Insiderhandel", "nahezu sicherer Gewinn", "hohe Strafe bei Entdeckung"],
  ], [3, 4, 3]),
  h2("12.3 Privatvermögen"),
  ...ul([
    "Der Spieler zahlt sich Gehalt, Entnahmen oder Dividenden ins **Privatvermögen** (Vorschlag).",
    "Bei GmbH und AG ist das Privatvermögen vor der Pleite der Firma geschützt, beim Einzelunternehmen nicht (Vorschlag).",
    "Bei einer Pleite durchläuft der Spieler ein Insolvenzverfahren und gründet danach mit dem zurückgelegten Privatvermögen eine neue Firma (Entschieden).",
  ]),
  h2("12.4 Pleite des Spielers"),
  ...ol([
    "Die Firma ist zahlungsunfähig oder überschuldet (Prüfpunkte wie in 12.5).",
    "Insolvenzverfahren: Firma, Schiffe und Anteile werden verwertet, die Gläubiger bedient.",
    "Neugründung mit dem Privatvermögen. Vorschlag: Kontakte bleiben, das Vertrauen sinkt, der persönliche Ruf bleibt zur Hälfte, Erfolge bleiben.",
  ]),
  p("Die Holding aus Haulstar (eine neue Firma gründen, etwas mitnehmen) liefert Ideen für diesen Neustart. Ihr Prestigebaum passt aber nicht zur Wirtschaftssimulation (Abschnitt 17)."),
  h2("12.5 Pleite von NPC-Firmen"),
  p("Entschieden ist: NPC-Firmen können pleitegehen. Die Prüfpunkte und die Insolvenzphase hast du mir überlassen:"),
  ...table(["Prüfpunkt", "Schwelle (Vorschlag)"], [
    ["Warnstufe", "6 Monatsabschlüsse in Folge negativ und Kasse unter 3 Monaten Fixkosten; erste Gerüchte im Newsfeed"],
    ["Zahlungsunfähigkeit", "Kasse unter 0 und fällige Rechnungen seit mehr als 30 Tagen offen"],
    ["Überschuldung", "Verbindlichkeiten höher als das Vermögen (Stationen, Flotte, Lager, Forderungen)"],
  ], [1, 3]),
  ...ol([
    "Warnstufe: Gerüchte, Kursverfall, Partner werden vorsichtig. Eine Rettung durch Partner oder Bank ist noch möglich.",
    "Insolvenzantrag: öffentliche Nachricht.",
    "Insolvenzzeit von 60 Spieltagen mit Bieterverfahren. Geboten werden kann auf die ganze Firma oder auf Teile (Stationen, Schiffe, Lizenzen, Verträge), von NPC-Firmen und vom Spieler.",
    "Zuschlag an das beste Gebot. Gibt es keines, wird die Firma abgewickelt, und ihre Stationen gehen an die Gläubiger oder die Hafenverwaltung.",
  ]),

  // 13
  h1("13 Beteiligungen und Übernahmen"),
  h2("13.1 Rechtsformen der 18 Firmen"),
  p("Entschieden: so, wie es für die drei Startszenarien am besten greift; weitere Rechtsformen können dazukommen. Mein Vorschlag:"),
  ...table(["Im Spiel", "Firmen", "Übernahme über"], [
    ["Börsennotiert (AG, Inc., Group, Consortium)", "Eisenkrone, Graufalk, Lichtacker, Kuppelwerk, Pionierwerk, Corvane, Cindervale, Emberline, Outmark, Helix Meridian, Ravenmoor (11)", "Börse, öffentliches Angebot, Verhandlung mit dem Vorstand"],
    ["Gesellschafter (GmbH, Co.)", "Feldspat, Kometenpost, Raureif, Driftwood, Lanternfish, Second Hull (6)", "Angebot an die Gesellschafter"],
    ["Genossenschaft (eG)", "Morgengrund (1)", "kein Kauf; Kooperation oder Verschmelzung per Mitgliederbeschluss"],
  ], [3, 5, 3]),
  p("Das passt zu den Szenarien: Die kleinen Firmen sind fast alle GmbH oder Co. und damit die ersten realistischen Ziele für Solo-Gründer und Kleines Netzwerk. Der Konzerner kann dank seiner Insiderinfos früh Minderheitsbeteiligungen an börsennotierten Firmen aufbauen."),
  h2("13.2 Schwellen bei börsennotierten Firmen"),
  p("Entschieden wie vorgeschlagen:"),
  ...table(["Anteil", "Folge"], [
    ["3 %", "Meldepflicht: Die Beteiligung erscheint im Newsfeed"],
    ["30 %", "Kontrolle: Pflichtangebot an alle Aktionäre"],
    ["50 %", "Mehrheit: Der Spieler kann einen Manager einsetzen"],
    ["75 %", "Satzungsmehrheit: Verschmelzung, Beherrschung, Verkauf von Teilen"],
    ["95 %", "Squeeze-out: Die restlichen Aktionäre werden gegen Abfindung herausgedrängt"],
  ], [1, 5]),
  h2("13.3 Feindliche Übernahme"),
  ...ul([
    "Ablauf (Vorschlag): Aktien leise kaufen (bis 3 % unbemerkt), danach werden die Meldeschwellen öffentlich. Dann ein öffentliches Angebot mit Prämie, mindestens zum Durchschnittskurs der letzten 3 Monate, mit einer Annahmefrist von 28 Spieltagen. Danach der Vollzug.",
    "Abwehr der Zielfirma (Vorschlag): ein weißer Ritter (eine Partnerfirma bietet mehr), ein Rivale bietet mit, Aktienrückkauf, Kapitalerhöhung, Verkauf der wertvollsten Teile, Gegenangriff (wenn der Spieler eine AG ist), Streikdrohung der Belegschaft.",
    "Aktionärsgruppen (neu in den Daten): Gründer oder Familie, Partnerfirmen, Fonds, Streubesitz, Belegschaft. Jede Gruppe hat ihre eigene Annahmeschwelle.",
  ]),
  h2("13.4 Freundliche Übernahme"),
  p("Hast du mir überlassen. Vorschlag in sechs Schritten:"),
  ...ol([
    "**Kontakt zum Vorstand**, über einen Kontakt oder ab einem bestimmten Ruf bei der Firma.",
    "**Absichtserklärung:** Preisrahmen und Zusagen (Belegschaft, Standorte, Marke).",
    "**Prüfung (Due Diligence):** kostet Geld und Zeit und deckt Risiken auf, etwa offene Vertragsstrafen, laufende Verfahren, Lecks oder schlechte Verträge.",
    "**Verbindliches Angebot:** Der Vorstand empfiehlt es oder lehnt ab. Das hängt ab von Vertrauen, der Persönlichkeit des Vorstandsvorsitzes, der Stimmung der Belegschaft und dem Preis im Verhältnis zum fairen Wert.",
    "**Annahme durch die Aktionäre:** Mit Empfehlung des Vorstands nehmen deutlich mehr an.",
    "**Vollzug:** Die Zusagen werden zu Pflichten. Wer sie bricht, verliert Ruf und die Stimmung der Belegschaft.",
  ]),
  h2("13.5 Angebot an eine GmbH oder Co."),
  p("Hast du mir überlassen. Vorschlag:"),
  ...ul([
    "Jede Firma hat 1–4 Gesellschafter: Gründer, Familie, Partnerfirma oder Investor. Sie werden neu erzeugt; die Firmenbeschreibungen nennen schon Gründer und Gründungsjahr.",
    "Das Angebot geht als Brief raus: Anteil (auch ein Teilkauf ist möglich), Preis, Zusagen, Frist.",
    "Ob angenommen wird, ergibt sich aus: Preis gegenüber fairem Wert, Vertrauen, Ruf, Lage der Firma (Verluste und knappe Kasse machen einen Verkauf wahrscheinlicher) und Persönlichkeit. Bei gierig zählt der Preis doppelt, bei loyal die Zusagen an die Belegschaft, bei idealistisch die Zukunft der Firma; vorsichtig verlangt eine lange Frist und eine Prüfung.",
    "Mögliche Antworten: Annahme, Gegenangebot, Ablehnung mit Sperrfrist. Manchmal wird das Angebot auch an einen Rivalen durchgestochen und taucht als Gerücht auf.",
    "Die Mitgesellschafter haben ein Vorkaufsrecht.",
    "Eine Minderheitsbeteiligung bringt Einblick in die Monatsabschlüsse und eine Stimme in der Gesellschafterversammlung.",
  ]),
  h2("13.6 Nach der Übernahme"),
  ...decisions([
    ["Führung", "Der Spieler setzt einen Manager ein.", "E"],
    ["Belegschaft", "Mitarbeiter mit niedriger Loyalität kündigen.", "E"],
    ["Kartellamt", "Gibt es nicht.", "E"],
    ["Manager", "Man wählt aus Bewerbern, eigenen Leuten oder Personen aus der Firma. Manager haben Fähigkeiten, Gehalt, Loyalität und eine Strategie (Gewinn, Wachstum, Sicherheit). Der Spieler gibt Ziele vor, steuert aber nicht jeden einzelnen Auftrag.", "V"],
    ["Kommunikation", "Die interne Kommunikation der übernommenen Firma wird lesbar.", "E"],
    ["Gewinne", "Fließen als Dividende oder Gewinnabführung an die Firma des Spielers.", "V"],
  ]),
  h2("13.7 Übernahmen durch NPC-Firmen"),
  p("Entschieden: NPC-Firmen übernehmen sich gegenseitig und können auch die Firma des Spielers übernehmen, wenn sie eine AG ist. Vorschlag: Solche Übernahmen sind selten (höchstens eine pro Spieljahr in der ganzen Welt) und kündigen sich vorher über Gerüchte an."),

  // 14
  h1("14 Schiffe, Flotte und Personal"),
  h2("14.1 Schiffe"),
  ...decisions([
    ["Startschiff", "Wert 125.000 CR, Baujahr 2044. Durch das Alter sind die Wartungskosten höher, und das Schiff verliert an Wert.", "E"],
    ["Schiffsplanung", "Die Schiffe selbst müssen noch geplant werden: Klassen, Werte, Preise.", "O"],
    ["Klassen", "Kurier, Frachter, Massengutfrachter, Tanker, Kühlfrachter, Bergbauschiff, Geleitschiff.", "V"],
    ["Werte", "Frachtraum (m³), Nutzlast (t), Geschwindigkeit, Reichweite, Schutz (Panzerung, Abwehr), Crewbedarf, Zustand (%), Baujahr.", "V"],
    ["Wertverlust", "Restwert = Neupreis × 0,94 hoch Alter in Jahren, mindestens 15 %. Das Startschiff hätte dann einen Neupreis von rund 336.000 CR.", "V"],
    ["Wartung", "Pro Jahr 3 % des Neupreises plus 0,25 % je Lebensjahr. Beim Startschiff sind das 7 %, also etwa 1.960 CR im Monat.", "V"],
    ["Ausfälle", "Die Ausfallwahrscheinlichkeit je Flug steigt mit dem Alter und sinkendem Zustand; ein Werftbesuch stellt den Zustand wieder her.", "V"],
    ["Bezugsquellen", "Neubau bei Graufalk Orbitalwerften. Gebrauchtschiffe, Schrott und Ersatzteile bei Second Hull Reclamation und Driftwood Salvage. Leasing über die Bank.", "V"],
    ["Fehlende Anbieter", "Passt für etwas keine bestehende Firma (z. B. eine Schiffsversicherung), kommt eine Firma dazu, die 2059 gegründet wurde.", "E"],
  ]),
  h2("14.2 Personal"),
  ...decisions([
    ["Einstellen", "Der Spieler stellt Personal ein.", "E"],
    ["Automatisierung", "Routen lassen sich automatisieren, auch über Angestellte.", "E"],
    ["Erstes Schiff", "Fliegt der Spieler am Anfang selbst, ohne Crewkosten.", "V"],
    ["Gehälter", "Die Gehälter in den Daten sind Konzerngehälter. Für den Spieler gibt es eine eigene Bewerberliste mit niedrigeren Einstiegsgehältern.", "V"],
    ["Eigenschaften", "Angestellte haben wie NPC-Mitarbeiter Loyalität, Bestechlichkeit und Persönlichkeit. Sie können abgeworben, bestochen oder verhaftet werden.", "V"],
  ]),
  ...table(["Rolle (aus den Daten)", "Monatsgehalt in den Daten", "Nutzen für den Spieler (Vorschlag)"], [
    ["Frachtpilot:in", "7.000–12.000 CR", "fliegt ein weiteres Schiff"],
    ["Handelsagent:in", "6.000–11.000 CR", "schließt kleine Aufträge selbstständig ab"],
    ["Frachtdisposition", "5.000–8.500 CR", "steuert mehrere Schiffe auf Routen"],
    ["Sicherheitsdienst", "4.500–8.000 CR", "senkt die Überfallrate, schützt vor Hacking"],
    ["Marktaufklärung", "9.000–16.000 CR", "bewertet Gerüchte, findet Insiderinfos"],
    ["Partnerbetreuung", "8.000–14.000 CR", "pflegt Kontakte, verhandelt Verträge"],
    ["Finanzbuchhaltung", "6.000–10.500 CR", "Kredite, Mahnwesen, Börse"],
    ["Stationsleitung", "14.000–24.000 CR", "führt eine eigene Station oder Fabrik"],
  ], [3, 2, 4]),

  // 15
  h1("15 Sicherheit, Überfälle und Krieg"),
  ...decisions([
    ["Überfallrate", "Sinkt mit steigendem Ruf und stärkeren Schiffen.", "E"],
    ["Sicherheitsfirmen", "Private Sicherheitsfirmen schützen die Routen.", "E"],
    ["Krieg", "Es gibt Kriege um Ressourcenpunkte auf Planeten. Die Kämpfer sind Freiwillige aus Sol. Krieg ist eher ein Mittel zum Zweck und fast schon Standard, weil die Regierungen auf anderen Planeten keinen dauerhaften Frieden durchsetzen können.", "E"],
    ["Formel", "Überfallrate je Flug = Grundrate der Route (Sicherheit der Systeme, Entfernung, Gefahrenstufe) × Ruffaktor × Stärkefaktor (Schutz des Schiffs, Geleitschutz) × Konfliktfaktor (Krieg im Sektor) × Wertfaktor (wertvolle Ladung lockt). Auf den ersten 12 Routen ist sie 0.", "V"],
    ["Folgen", "Ladung ganz oder teilweise verloren, Schiff beschädigt, selten ganz verloren. Eine Versicherung zahlt.", "V"],
    ["Geleitschutz", "Ravenmoor Convoy & Security Group (im Bestand) bietet Konvoi und Geleit an, je Fahrt oder per Vertrag.", "V"],
    ["Rolle des Spielers", "Der Spieler ist Lieferant, Transporteur und Geldgeber in Konflikten. Ob er später eigene Sicherheitsleute oder Söldnerverträge bekommt, ist offen.", "V/O"],
    ["Darstellung", "Kämpfe werden als Ereignisse und Berichte gezeigt, ohne detaillierte Gewalt. Das hält die Altersfreigabe in den Stores niedrig.", "V"],
  ]),
  h2("15.1 Konflikte um Ressourcenpunkte"),
  ...ul([
    "Ressourcenpunkte sind Lagerstätten auf Planeten, auf die Firmen Anspruch erheben. Konflikte entstehen zwischen Rivalen; die Daten enthalten schon Rivalitäten, auch solche um die Vorherrschaft in einem System.",
    "Wirkung: Im Sektor steigt die Nachfrage nach Rüstung, Nahrung, Medizin und Treibstoff. Die Überfallrate steigt, die Preise schwanken, und die Kurse der beteiligten Firmen bewegen sich.",
    "Ausgang: Die siegreiche Firma erhält den Ressourcenpunkt und damit mehr Förderung, was sich in Monatsabschluss und Kurs niederschlägt.",
  ]),

  // 16
  h1("16 Kampagne, Sandbox und Erfolge"),
  ...decisions([
    ["Grundform", "Endlose Sandbox mit Kampagne und drei Startszenarien.", "E"],
    ["Erfolge", "Nur als eigenes Erfahrungs- und Feedbacksystem. NPC-Firmen haben keine.", "E"],
    ["Kapitel", "8 Kapitel wie in der Tabelle unten. Sie passen sich dem Szenario an; beim Solo-Gründer dauern Kapitel 1 und 2 länger.", "V"],
    ["Feedback", "Monats- und Jahresbericht der eigenen Firma mit Hinweisen, was gut lief und was nicht, dazu Statistiken und Meilensteine.", "V"],
  ]),
  ...table(["Kapitel", "Ziel", "Lernt bzw. öffnet"], [
    ["1 Erste Fracht", "die 12 geschützten Routen fliegen", "Handel, Aufträge, Kosten, Kredit"],
    ["2 Einen Namen machen", "Ruf bei 3 Firmen, 5 Kontakte", "Gerüchte, Verhandeln"],
    ["3 Flotte", "zweites Schiff, erste Angestellte", "Personal, Automatisierung"],
    ["4 Verträge", "einen Liefervertrag ohne Strafe erfüllen, erster Rahmenvertrag", "Vertragswesen"],
    ["5 Eigene Produktion", "erste Förderung oder Produktion (Open Source oder Lizenz)", "Technologie"],
    ["6 Börse", "erste Beteiligung über 3 %", "Börse, Finanzaufsicht"],
    ["7 Übernahme", "eine erste Firma übernehmen (GmbH oder aus der Insolvenz)", "Manager"],
    ["8 Konzern", "Mehrheit an einer börsennotierten Firma", "Konzernsteuerung"],
  ], [2, 4, 3]),

  // 17
  h1("17 Was aus Haulstar weiterverwendet wird"),
  p("Du hattest „weiß ich nicht“ geantwortet. Grundlage für diese Einschätzung ist eine Bestandsaufnahme des Repos idlestar vom 21.10.2026. Status aller Zeilen: Vorschlag."),
  ...table(["Baustein", "Entscheidung", "Begründung"], [
    ["Spielkern: Ereignisschleife, Zeit als Parameter, Kalender, Zufall aus Seeds, Festkomma-Rechnung", "übernehmen", "Fachlich neutral und gut getestet (u. a. „10 h = 10 × 1 h“, 200-Seed-Test). Die Zeitbeschleunigung kommt in die Uhr-Schicht."],
    ["Abrechnen und Befehle (settle, applyCommand)", "übernehmen", "Muster passt für jede Simulation."],
    ["Spielstand, Migrationen, Speicher (SQLite/IndexedDB), Export/Import", "übernehmen", "Neues Schema ab Version 1 für das neue Spiel."],
    ["Buchungsjournal und Bericht „Seit deinem letzten Besuch“", "übernehmen", "Neue Buchungsarten (Zoll, Vertragsstrafe, Dividende …)."],
    ["Content-Laden mit Schemaprüfung, Übersetzung de/en mit Prüfung der Schlüssel", "übernehmen", "Neuer Content aus dem legami-Export."],
    ["Werkzeuge: Lint-Regeln (kein Math.random), Modulgrenzen, Git-Hooks, CI", "übernehmen", "Sichert Determinismus und Struktur."],
    ["Web/PWA-Build, Cloudflare-Deploy, EAS-Profile und Updates", "übernehmen", "Deckt Browser und Stores ab."],
    ["App-Rahmen, Space-UI-Bausteine, Zahlenformate, Hinweis-Overlays", "übernehmen und umbauen", "Tabs und Bildschirme neu ordnen."],
    ["Markt und Preise", "umbauen", "Zyklusmodell statt Bestandsformel (Abschnitt 7.2)."],
    ["Flotte, Handelsrouten, Routenfinder", "umbauen", "Neu: Zoll, Versicherung, Treibstoff, Fremdaufträge, Haftung."],
    ["Lieferverträge (deliveries)", "umbauen", "Wird zur Auftragsbörse je Firma."],
    ["Manager und Automatisierung", "umbauen", "Angestellte statt Token; Manager für übernommene Firmen."],
    ["Werft und Schiffsklassen", "umbauen", "Neu: Gebrauchtmarkt, Alter, Wartung, Wertverlust."],
    ["Quests, Meilensteine, Lehrzeit", "umbauen", "Werden zu Kampagne, Lehrzeit und Erfolgen."],
    ["Kampf und Überfälle", "umbauen", "Überfallrate nach Ruf, Schiffsstärke und Geleit; Eroberung entfällt."],
    ["Planeten, Claims, Förderstationen", "prüfen", "Möglich als Grundlage für Ressourcenpunkte und eigene Förderung."],
    ["Holding (Prestige)", "prüfen", "Ideen für den Neustart nach der Insolvenz; der Prestigebaum entfällt."],
    ["Forschung und Meisterschaft", "entfällt", "Technologie kommt über Open Source und Lizenzen (offen: eigene Entwicklung)."],
    ["Kapitäne (Gacha), Akademie, Münzshop", "entfällt", "Passt nicht zu einer Wirtschaftssimulation."],
    ["Expeditionen, Energie-Pool", "entfällt", "Gehört zum alten Spielprinzip."],
    ["Alle Inhalte und Bilder", "neu", "Hausstil und Bild-Werkzeug (Skill bild-assets, Slicer) bleiben."],
  ], [4, 2, 5]),
  p("**Ganz neu** sind: NPC-Firmen als handelnde Akteure, Börse, Beteiligungen und Übernahmen, Gerüchte und Newsfeed, Schriftverkehr, Hacking, Justiz, Bank und Insolvenz. In Haulstar gibt es nichts davon; die NPC-Stationen sind dort reine Märkte. Diese Module bauen auf dem bestehenden Kern auf."),
  ...decisions([
    ["Alte Spielstände", "Was passiert mit bestehenden Haulstar-Spielständen und der Live-Version, wenn das neue Spiel kommt?", "O"],
    ["Ort im Code", "Neuaufbau im Repo idlestar (neuer Branch) oder neues Repo, das den Kern übernimmt?", "O"],
  ]),

  // 18
  h1("18 Offene Punkte und nächste Planungsschritte"),
  h2("18.1 Offene Punkte"),
  ...ul([
    "Schiffe: Klassen, Werte, Preise, Neu- und Gebrauchtmarkt (14.1).",
    "Produktansicht im Test ausprobieren (7.1).",
    "Rezepte und Produktionsketten (7.4); eigene Forschung ja oder nein.",
    "Zahlen: Zeitfaktoren, Zinsen, Strafen, Schwellen, Überfallraten. Alles TBD, bis es im Test ausgewogen ist.",
    "Pause oder Urlaubsmodus (4).",
    "Wie tief der Spieler in Konflikte einsteigt: eigene Sicherheitsleute, Söldnerverträge (15).",
    "Rohstoffbörse mit Terminkontrakten (12.2).",
    "Persönliche Haftung des Spielers (11).",
    "Größe des Startstands für Browser und Handy (3.1).",
    "Alte Haulstar-Spielstände, Ort im Code (17).",
    "Geschäftsmodell für die Stores: kostenlos, Kaufpreis oder In-App-Käufe.",
    "Abgleich der Spielstände zwischen Browser und App (Cloud) – bisher ist keiner geplant.",
  ]),
  h2("18.2 Nächste Planungsdokumente (Vorschlag)"),
  ...ol([
    "Dieses Konzept durchgehen und die Vorschläge bestätigen oder ändern.",
    "**Wirtschaftskern:** Zeit, Preise, Produktion, NPC-Firmen, Monatsabschluss. Darauf baut alles andere auf.",
    "**Schiffe und Personal.**",
    "**Handel, Aufträge, Verträge, Ruf und Kontakte.**",
    "**Information:** Newsfeed, Schriftverkehr, Hacking, Justiz.",
    "**Finanzen:** Bank, Börse, Übernahmen, Insolvenz.",
    "**Konflikte und Sicherheit.**",
    "**Datenweg:** legami-Export und Startstand.",
    "**Phasenplan** aus allem davor.",
  ]),

  // Anhang A
  h1("Anhang A: Die 18 Firmen", { breakBefore: true }),
  ...table(["Firma", "Größe", "Rechtsform", "Sprache", "Schwerpunkt"], [
    ["Feldspat Orbitalbergbau GmbH", "klein", "GmbH", "de", "Asteroidenbergbau"],
    ["Driftwood Salvage & Supply Co.", "klein", "Co.", "en", "Bergung und Graumarkthandel"],
    ["Kometenpost Kurierdienste GmbH", "klein", "GmbH", "de", "Expresskurier"],
    ["Lanternfish Leisure Co.", "klein", "Co.", "en", "Unterhaltung und Konsumgüter"],
    ["Siedlergenossenschaft Morgengrund eG", "klein", "eG", "de", "Siedlergenossenschaft"],
    ["Second Hull Reclamation Co.", "klein", "Co.", "en", "Schrottverwertung"],
    ["Lichtacker Agrarsysteme AG", "mittel", "AG", "de", "Hydrokultur-Landwirtschaft"],
    ["Corvane Biomedical Inc.", "mittel", "Inc.", "en", "Biomedizinische Forschung"],
    ["Kuppelwerk Habitatbau AG", "mittel", "AG", "de", "Habitatbau"],
    ["Emberline Fusion Fuels Inc.", "mittel", "Inc.", "en", "Fusionsbrennstoffe"],
    ["Raureif Volatilförderung GmbH", "mittel", "GmbH", "de", "Eis- und Gasförderung"],
    ["Outmark Survey & Prospecting Inc.", "mittel", "Inc.", "en", "Vermessung und Prospektion"],
    ["Eisenkrone Montan- und Industrie-AG", "groß", "AG", "de", "Schwerindustrie"],
    ["Helix Meridian Trading Consortium", "groß", "Consortium", "en", "Interstellarer Handel"],
    ["Graufalk Orbitalwerften AG", "groß", "AG", "de", "Schiffbau"],
    ["Cindervale Cognitive Industries Inc.", "groß", "Inc.", "en", "KI-Rechenleistung und Robotik"],
    ["Pionierwerk Kolonialausrüstung AG", "groß", "AG", "de", "Kolonieausrüstung"],
    ["Ravenmoor Convoy & Security Group", "groß", "Group", "en", "Konvoischutz und Versorgung"],
  ], [10, 3, 4, 3, 8]),

  // Anhang B
  h1("Anhang B: Antworten vom 21.10.2026", { breakBefore: true }),
  p("Kurzfassung deiner Antworten mit Verweis auf den Abschnitt, in dem sie umgesetzt sind."),
  ...table(["Nr.", "Frage", "Antwort (kurz)", "Abschnitt"], [
    ["1", "Welches Spiel", "Haulstar neu mit der legami-Welt; Browser wie heute, nach der Testzeit App Store und Google Play", "3"],
    ["2", "Zeit", "Logische Beschleunigung; 22–6 Uhr Ortszeit langsamer; abschaltbar", "4"],
    ["3", "Spieler", "Erst allein gegen NPC-Firmen", "3"],
    ["4", "Was aus Haulstar bleibt", "Weiß ich nicht", "17"],
    ["5", "Ziel", "Endlose Sandbox mit Kampagne; drei Startszenarien", "6, 16"],
    ["6", "Daten", "Grundlage, nicht die einzige; Wirtschaft rechnet weiter (faker.js)", "3, 5"],
    ["7", "Freischaltung", "Alles offen; Überfallrate sinkt mit Ruf und Schiffsstärke", "5.3, 15"],
    ["8", "Freie Händler", "Weiß ich nicht, macht schon Sinn", "5.3"],
    ["9", "Sprache", "Alles de/en; Firmenkommunikation erst durch Übernahme oder Hacking", "9"],
    ["10", "Schiff", "Solo: Kredit; Netzwerk: gebraucht; Konzerner: gekauft", "6"],
    ["11", "Schiffstyp und Alter", "Höhere Wartung, Wertverlust; Schiffe noch planen", "14.1"],
    ["12", "Startort", "Sol, neutrale Handelsstation", "6"],
    ["13", "Eigene Firma", "Rechtsform, Name und Logo wählbar", "6.1"],
    ["14", "Tutorial", "Ja", "6"],
    ["15", "Produkte", "Grundwaren; Firmenprodukte angepasst, teils exklusiv; Große produzieren mehr", "7.1"],
    ["16", "Preise", "Spieler nicht spürbar; Marktzyklen; Ereignisse wirken", "7.2"],
    ["17", "Schmuggel", "Erlaubt; Strafe nach Entdeckung; sonst Beschlagnahme", "11"],
    ["18", "Kosten", "Ich denke schon", "7.3"],
    ["19", "Firmen versorgen", "Lieferverträge mit Frist und Strafe; Rahmenverträge ab Ruf", "8"],
    ["20", "Transportauftrag", "Ohne Versicherung Erstattung; erste 12 Routen ohne Verlust", "8"],
    ["21", "Aufträge finden", "Auftragsbörse je Firma; manche nur mit Ruf oder Kontakt", "8"],
    ["22", "Produktionsketten", "Ja", "7.4"],
    ["23", "Eigene Produktion", "Ja, mit Geld und Technologie; Open Source schwächer, Lizenz lohnt", "7.4"],
    ["24", "Ereignisse", "Zufällig", "7.5"],
    ["25", "Pleiten", "Möglich; Prüfpunkte und Insolvenzzeit legst du fest", "12.5"],
    ["26", "Gerüchte", "Newsfeed; manchmal falsch", "9.1"],
    ["27", "Bestechung", "Möglich; Strafen; schwere Fälle Haft für Angestellte", "11"],
    ["28", "Schriftverkehr", "Was die beste Nutzererfahrung ergibt", "9.3"],
    ["29", "Beziehungen", "Vertrauen, Ruf, Kontakte; Belegschaft zählt bei Verhandlungen", "10"],
    ["30", "Rechtsformen", "Was für die Startszenarien am besten greift; weitere möglich", "13.1"],
    ["31", "Börse", "Ja, manipulierbar; Rohstoffe wirken auf Kurse", "12.2"],
    ["32", "Feindliche Übernahme", "Wie vorgeschlagen (Schwellen)", "13.2, 13.3"],
    ["33", "Freundliche Übernahme", "Entscheidest du", "13.4"],
    ["34", "GmbH-Angebot", "Entscheidest du", "13.5"],
    ["35", "Finanzierung", "Auf Pump erlaubt; bei Pleite Insolvenz, dann Neustart mit Privatvermögen", "12"],
    ["36", "Nach der Übernahme", "Manager einsetzen; Kündigungen ja; kein Kartellamt", "13.6"],
    ["37", "NPC-Übernahmen", "Ja", "13.7"],
    ["38", "Schiffskauf", "Fehlt eine passende Firma: neue, 2059 gegründete Firma", "14.1"],
    ["39", "Personal", "Ja", "14.2"],
    ["40", "Risiken", "Ja, auch Krieg; Sicherheitsfirmen; Freiwillige aus Sol", "15"],
    ["41", "Automatisierung", "Ja, auch über Angestellte", "14.2"],
    ["42", "Ruf", "Je Firma und grundlegend; öffnet Verträge, Beziehungen, Übernahmen", "10"],
    ["43", "Erfolge", "Nur als eigenes Erfahrungs- und Feedbacksystem", "16"],
    ["44", "Dokument", "Für dich, als Grundlage für die weitere Planung bis zum Phasenplan", "1"],
    ["45", "Ablage", "Branch in legami, docx hier im Chat", "–"],
  ], [1, 3, 7, 2]),
];

// ---------------------------------------------------------------------------
// Dokument
// ---------------------------------------------------------------------------

const doc = new Document({
  creator: "Haulstar-Planung",
  title: "Haulstar – Neuaufsetzung mit der legami-Welt",
  description: "Spielkonzept Version 0.1",
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: FONT, color: "1F3864" },
        paragraph: { spacing: { before: 240, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: FONT, color: "2E5395" },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      ...NUMBERINGS.map((reference) => ({ reference, levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.",
        alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] })),
    ],
  },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, right: 1134, bottom: 1134, left: 1134 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: "Haulstar · Spielkonzept 0.1", font: FONT, size: 16, color: "808080" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: ["Seite ", PageNumber.CURRENT, " von ", PageNumber.TOTAL_PAGES], font: FONT, size: 16, color: "808080" })] })] }) },
    children: CONTENT.flatMap((block) => block === TOC_PLACEHOLDER
      ? TOC.map((title) => new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: title, font: FONT })] }))
      : [block]),
  }],
});

const out = path.join(__dirname, "haulstar-spielkonzept.docx");
Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(out, buffer);
  console.log(`geschrieben: ${out}`);
});
