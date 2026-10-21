// Erzeugt konzept/legami-colony-spielkonzept.docx. Aufruf: node konzept/build_spielkonzept.js
// Inhalte stehen unten in CONTENT; Status je Festlegung: E = entschieden, V = Vorschlag, O = offen.
// Jeder Vorschlag bekommt eine Nummer (V1, V2, …) und erscheint zusätzlich in Anhang D.
const fs = require("fs");
const path = require("path");
const {
  AlignmentType, BorderStyle, Document, Footer, Header, HeadingLevel, LevelFormat, Packer, PageNumber,
  Paragraph, ShadingType, Table, TableCell, TableRow, TextRun, WidthType,
} = require("docx");

const FONT = "Calibri";
const WIDTH = 9638; // A4 mit 2 cm Rand, in DXA
const VERSION = "0.2";
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
let section = "";
const h1 = (text, { breakBefore = false } = {}) => {
  TOC.push(text);
  section = text.startsWith("Anhang") ? text.split(":")[0] : text.split(" ")[0];
  return new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: breakBefore, keepNext: true,
    children: [new TextRun({ text, font: FONT })] });
};
const h2 = (text) => {
  if (!section.startsWith("Anhang")) section = text.split(" ")[0];
  return new Paragraph({ heading: HeadingLevel.HEADING_2, keepNext: true, children: [new TextRun({ text, font: FONT })] });
};
const bullet = (t) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: runs(t), spacing: { after: 60 } });
const ul = (items) => items.map(bullet);
const NUMBERINGS = [];
const ol = (items) => {
  const ref = `num${NUMBERINGS.length + 1}`;
  NUMBERINGS.push(ref);
  return items.map((t) => new Paragraph({ numbering: { reference: ref, level: 0 }, children: runs(t), spacing: { after: 60 } }));
};

// Vorschläge zur Bestätigung (Anhang D)
const PROPOSALS = [];
function propose(topic, text) {
  const id = `V${PROPOSALS.length + 1}`;
  PROPOSALS.push({ id, section, topic, text });
  return id;
}
// Vorschlag in Fließtext, Liste oder Tabelle: kurzer Hinweis mit Nummer (description im Text, topic in Anhang D)
const vnote = (description, topic) => new Paragraph({ spacing: { after: 160 }, children: [
  new TextRun({ text: `Vorschlag ${propose(topic, description)}: `, font: FONT, bold: true, color: "7F6000", size: 20 }),
  new TextRun({ text: description, font: FONT, italics: true, color: "7F6000", size: 20 }),
] });

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

// Festlegungen: [Thema, Festlegung, Status]; Vorschläge bekommen ihre Nummer in der Statusspalte
function decisions(rows) {
  const widths = [2300, 5838, 1500];
  return [new Table({
    width: { size: WIDTH, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, cantSplit: true, children: ["Thema", "Festlegung", "Status"].map((h, i) => cell(h, widths[i], { header: true })) }),
      ...rows.map(([topic, text, status]) => {
        const label = status.split("/").map((s) => STATUS[s].label).join(" / ");
        const id = status.startsWith("V") ? ` ${propose(topic, text)}` : "";
        return new TableRow({
          cantSplit: true,
          children: [cell(`**${topic}**`, widths[0]), cell(text, widths[1]),
            cell(`${label}${id}`, widths[2], { fill: STATUS[status[0]].fill })],
        });
      }),
    ],
  }), new Paragraph({ spacing: { after: 120 }, children: [] })];
}

// ---------------------------------------------------------------------------
// Rezeptentwurf (Anhang C): Basispreise aus dem Generator, Mengen je Einheit des Produkts
// ---------------------------------------------------------------------------

const PRICE = {
  Eisenerz: 85, Titanerz: 420, Silizium: 260, Wassereis: 60, "Seltene Erden": 2400, "Nickel-Eisen": 140, Kobalt: 1100,
  "Regolith-Granulat": 30, Kohlenstoffkonzentrat: 180, "Ammoniak-Eis": 95, Quantenquarz: 9200, Platinmetalle: 15500,
  Stickstoffeis: 75, "Helium-3": 6500, Deuterium: 1800, Brennstoffzellen: 950, Plasmagas: 2100,
  "Antimaterie-Kapseln": 48000, Fusionspellets: 5200, Verbundstahl: 1300, Bauteile: 650, Reaktorkomponenten: 28000,
  Werkzeugmaschinen: 15000, Rumpfplatten: 3800, Triebwerksteile: 7200, Lebenserhaltungsmodule: 22000,
  Bergbaudrohnen: 18000, Polymere: 900, Glaskeramik: 1600, Habitatmodule: 46000, Sinterbausteine: 380,
  Geleitschutzdrohnen: 21000, Elektronik: 2400, "KI-Kerne": 36000, Sensorarrays: 8500, Navigationscomputer: 14000,
  Robotikeinheiten: 26000, Supraleiter: 11000, Quantenrelais: 19500, "Terraforming-Kulturen": 7800,
  Vermessungsdatenkerne: 5400, Proteinpaste: 140, Hydrokulturgemüse: 210, "Gefriergetrocknete Rationen": 180,
  Algenkonzentrat: 120, Kulturfleisch: 420, Orbitalgetreide: 520, Frischobst: 380, Medikamente: 1800,
  "Medizinische Ausrüstung": 9500, Bioproben: 4200, Impfstoffe: 3100, Nanomedizin: 12500,
  Strahlenschutzpräparate: 1400, Spirituosen: 1600, Unterhaltungselektronik: 3200, Designertextilien: 2200,
  Immersionskapseln: 13500,
};

const STAGE1 = [
  ["Bergbau", "Eisenerz, Titanerz, Silizium, Wassereis, Seltene Erden, Nickel-Eisen, Kobalt, Regolith-Granulat, Kohlenstoffkonzentrat, Ammoniak-Eis, Quantenquarz, Platinmetalle, Stickstoffeis, Edelsteine"],
  ["Gasförderung", "Helium-3, Deuterium, Plasmagas"],
  ["Anbau (Betriebsmittel: Wassereis, Ammoniak-Eis)", "Hydrokulturgemüse, Algenkonzentrat, Orbitalgetreide, Frischobst, Orbitalkaffee"],
  ["Forschung und Anbau", "Bioproben"],
  ["Einfuhr von der Erde", "Erd-Wein, Echtholzmöbel"],
  ["Unikate (Handelsstationen)", "Kunstobjekte"],
];

// [Produkt, Station, [[Ware, Menge], …], Zusatz]
const STAGE2 = [
  ["Verbundstahl", "Industrie", [["Eisenerz", 6], ["Nickel-Eisen", 1], ["Kohlenstoffkonzentrat", 1]]],
  ["Bauteile", "Industrie", [["Nickel-Eisen", 2], ["Titanerz", 0.3]]],
  ["Polymere", "Industrie", [["Kohlenstoffkonzentrat", 2], ["Ammoniak-Eis", 2]]],
  ["Glaskeramik", "Industrie", [["Silizium", 3], ["Regolith-Granulat", 4]]],
  ["Sinterbausteine", "Industrie", [["Regolith-Granulat", 8]]],
  ["Elektronik", "Industrie", [["Silizium", 2], ["Seltene Erden", 0.3], ["Kobalt", 0.2]]],
  ["Supraleiter", "Industrie", [["Seltene Erden", 2], ["Kobalt", 1], ["Stickstoffeis", 4]]],
  ["Brennstoffzellen", "Industrie", [["Wassereis", 4], ["Kobalt", 0.3]]],
  ["Fusionspellets", "Industrie", [["Deuterium", 1], ["Helium-3", 0.25]]],
  ["Proteinpaste", "Agrar", [["Algenkonzentrat", 0.7]]],
  ["Gefriergetrocknete Rationen", "Agrar", [["Hydrokulturgemüse", 0.4], ["Orbitalgetreide", 0.05]]],
  ["Kulturfleisch", "Agrar", [["Algenkonzentrat", 1], ["Orbitalgetreide", 0.25]]],
  ["Spirituosen", "Agrar", [["Orbitalgetreide", 1], ["Frischobst", 1]]],
  ["Medikamente", "Forschung", [["Bioproben", 0.2], ["Ammoniak-Eis", 2]]],
  ["Strahlenschutzpräparate", "Forschung", [["Algenkonzentrat", 2], ["Seltene Erden", 0.2]]],
  ["Terraforming-Kulturen", "Forschung", [["Bioproben", 1], ["Ammoniak-Eis", 3], ["Stickstoffeis", 3]]],
];

const STAGE3 = [
  ["Rumpfplatten", "Industrie", [["Verbundstahl", 1.6], ["Titanerz", 0.5]]],
  ["Triebwerksteile", "Industrie", [["Verbundstahl", 1], ["Bauteile", 2], ["Kobalt", 1], ["Supraleiter", 0.1]]],
  ["Werkzeugmaschinen", "Industrie", [["Verbundstahl", 3], ["Elektronik", 1], ["Bauteile", 4]]],
  ["Bergbaudrohnen", "Industrie", [["Bauteile", 6], ["Elektronik", 2], ["Brennstoffzellen", 3]]],
  ["Geleitschutzdrohnen", "Industrie, Militär", [["Bauteile", 6], ["Elektronik", 3], ["Brennstoffzellen", 2]]],
  ["Habitatmodule", "Industrie", [["Verbundstahl", 8], ["Glaskeramik", 5], ["Polymere", 6], ["Elektronik", 2]]],
  ["Lebenserhaltungsmodule", "Industrie", [["Polymere", 4], ["Elektronik", 3], ["Bauteile", 4]]],
  ["Reaktorkomponenten", "Industrie", [["Supraleiter", 1], ["Verbundstahl", 3], ["Titanerz", 4]]],
  ["Sensorarrays", "Industrie", [["Elektronik", 1.5], ["Glaskeramik", 1]]],
  ["Navigationscomputer", "Industrie", [["Elektronik", 2], ["Quantenquarz", 0.4]]],
  ["KI-Kerne", "Forschung", [["Elektronik", 3], ["Quantenquarz", 1], ["Supraleiter", 0.5]]],
  ["Robotikeinheiten", "Industrie", [["Elektronik", 3], ["Bauteile", 6], ["Supraleiter", 0.4]]],
  ["Quantenrelais", "Forschung", [["Quantenquarz", 0.8], ["Supraleiter", 0.4]]],
  ["Antimaterie-Kapseln", "Forschung", [["Plasmagas", 6], ["Supraleiter", 1], ["Fusionspellets", 1]]],
  ["Medizinische Ausrüstung", "Industrie", [["Elektronik", 1.5], ["Polymere", 2]]],
  ["Nanomedizin", "Forschung", [["Medikamente", 2], ["Elektronik", 1], ["Platinmetalle", 0.1]]],
  ["Impfstoffe", "Forschung", [["Bioproben", 0.3], ["Polymere", 0.5], ["Medikamente", 0.1]]],
  ["Unterhaltungselektronik", "Industrie", [["Elektronik", 0.6], ["Polymere", 0.5]]],
  ["Immersionskapseln", "Industrie", [["Elektronik", 2], ["Glaskeramik", 1], ["Polymere", 2]]],
  ["Designertextilien", "Industrie", [["Polymere", 1.5]]],
  ["Vermessungsdatenkerne", "Forschung", [["Elektronik", 1]], "plus Vermessungsflug"],
];

const fmt = (n) => n.toLocaleString("de-DE", { maximumFractionDigits: 2 });
function recipeRows(recipes) {
  return recipes.map(([product, station, inputs, extra]) => {
    const value = inputs.reduce((sum, [good, qty]) => sum + PRICE[good] * qty, 0);
    const text = inputs.map(([good, qty]) => `${fmt(qty)} × ${good}`).join(", ") + (extra ? `, ${extra}` : "");
    return [product, station, text, `${fmt(PRICE[product])} CR`, `${Math.round((100 * value) / PRICE[product])} %`];
  });
}

// ---------------------------------------------------------------------------
// Inhalt
// ---------------------------------------------------------------------------

const TOC_PLACEHOLDER = Symbol("toc");
const PROPOSALS_PLACEHOLDER = Symbol("proposals");
const PROPOSAL_COUNT_PLACEHOLDER = Symbol("proposal-count");
const CONTENT = [
  // Titelseite
  new Paragraph({ spacing: { before: 2400, after: 200 }, children: [new TextRun({ text: "Legami Colony", font: FONT, size: 64, bold: true, color: "1F3864" })] }),
  new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: "Spielkonzept", font: FONT, size: 36, color: "1F3864" })] }),
  new Paragraph({ spacing: { after: 600 }, children: [new TextRun({ text: `Version ${VERSION} · Stand 21.10.2026`, font: FONT, size: 24, color: "595959" })] }),
  p("Grundlage: deine Antworten aus drei Fragerunden vom 21.10.2026 (Anhang B), der Datengenerator auf dem Branch erweiterung-18-firmen im Repo legami und eine Bestandsaufnahme von Haulstar im Repo idlestar."),
  p("**Statusangaben in den Tabellen:**"),
  ...table(["Status", "Bedeutung"], [
    ["Entschieden", "Von dir festgelegt, auch dort, wo du meinen Vorschlag übernommen hast."],
    ["Vorschlag Vn", "Von mir gesetzt, wo du „weiß ich nicht“ oder „entscheidest du“ geantwortet hast oder etwas fehlte. Jeder Vorschlag hat eine Nummer und steht noch einmal in Anhang D, damit du ihn einzeln bestätigen oder ändern kannst."],
    ["Offen", "Muss noch geplant werden."],
  ], [1, 4]),
  p("Alle Zahlen sind Startwerte für Tests. Im Spiel gehören sie in Content-Dateien und werden dort als TBD markiert."),
  new Paragraph({ pageBreakBefore: true, children: [new TextRun({ text: "Inhalt", font: FONT, size: 32, bold: true, color: "1F3864" })] }),
  TOC_PLACEHOLDER,

  // 1
  h1("1 Zweck des Dokuments", { breakBefore: true }),
  p("Legami Colony ist ein neues, eigenständiges Spiel in der Welt aus legami. Es übernimmt den technischen Kern von Haulstar, ist aber deutlich tiefer. Haulstar selbst bleibt das Casual-Spiel und wird unabhängig weitergeführt und weiterentwickelt."),
  p("Dieses Dokument ist der Ausgangspunkt für die weitere Planung über mehrere Sessions, bis ein Phasenplan alles abdeckt. Code entsteht erst danach."),
  p("Jeder Abschnitt nennt zuerst die Festlegungen mit Status und erklärt dann, wie das im Spiel funktionieren soll. Abschnitt 18 sammelt die offenen Punkte und schlägt die Reihenfolge der nächsten Planungsdokumente vor. Anhang D legt dir alle Vorschläge noch einmal zur Bestätigung vor (deine Antwort in Runde 3, Frage 17)."),

  // 2
  h1("2 Spielidee"),
  p("Am 1. Januar 2060 öffnen die Konzerne den Weltraum für freie Händler. Der Spieler gründet eine kleine Firma mit **25.000 CR** und einem 16 Jahre alten Schiff (Baujahr 2044, Wert **125.000 CR**). Er handelt mit den etablierten Firmen, beliefert sie und transportiert in ihrem Auftrag. Er baut Kontakte und Ruf auf, steigt später in Förderung, Produktion und Forschung ein, kauft Anteile und übernimmt Firmen: freundlich, feindlich oder aus der Insolvenz. Noch später gründet er eine eigene Sicherheitsfirma (PMC), erobert Ressourcen und besiedelt Planeten. Die Wirtschaft rechnet weiter, auch wenn der Spieler gerade nicht spielt."),
  h2("2.1 Kernschleife"),
  ...ol([
    "**Informieren:** Auftragsbörsen der Firmen, Newsfeed, Kontakte, Marktpreise.",
    "**Entscheiden:** kaufen und verkaufen, Auftrag oder Vertrag annehmen, Route einrichten, Angebot schreiben.",
    "**Ausführen:** Schiffe fliegen in Spielzeit. Überfälle, Ausfälle und Verspätungen können eintreten.",
    "**Ergebnis:** Credits, Ruf, Vertrauen, neue Kontakte, unter Umständen Strafen.",
    "**Ausbauen:** Schiffe, Personal, Förderung und Produktion, Anteile, Übernahmen, Kolonien.",
  ]),
  h2("2.2 Drei Spielebenen"),
  ...table(["Ebene", "Der Spieler ist", "Typische Tätigkeiten", "Erreicht durch"], [
    ["Händler", "Kapitän und Kaufmann", "Handel, Transportaufträge, erste Lieferverträge", "Spielstart"],
    ["Unternehmer", "Chef einer Firma mit Flotte und Personal", "Rahmenverträge, Förderung, Produktion und Forschung, Lizenzen, Automatisierung", "Geld, Ruf, Technologie"],
    ["Konzernlenker", "Eigentümer mehrerer Firmen", "Börse, Beteiligungen, Übernahmen, Manager, eigene PMC, Eroberung von Ressourcen, Kolonien und Städte", "Kapital, Ruf, Kontakte"],
  ], [2, 3, 5, 3]),

  // 3
  h1("3 Plattform, Technik und Daten"),
  ...decisions([
    ["Spiel", "Eigenständiges Spiel „Legami Colony“. Haulstar wird als Casual-Spiel weitergeführt und weiterentwickelt; seine Spielstände und die Live-Version bleiben unberührt.", "E"],
    ["Repo", "Eigenes Repo mit eigenem Aufbau.", "E"],
    ["Technik", "Gleiche Technik wie Haulstar (Expo/React Native, offline, deterministisch), nur anders gegliedert. Der Kern von Haulstar wird einmalig kopiert, damit sich beide Spiele unabhängig weiterentwickeln.", "E"],
    ["Plattform", "Spielbar im Browser auf einer eigenen Subdomain von seritha.dev. Nach der Testphase als App im App Store und bei Google Play.", "E"],
    ["Geschäftsmodell", "Kostenlos, ohne Werbung, ohne Konto und ohne Datenerhebung.", "E"],
    ["Spieler", "Erst einmal Einzelspieler gegen NPC-Firmen.", "E"],
    ["Spielstände", "Mehrere Spielstände in verschiedenen Modi, jeder mit eigenem Verlauf (Abschnitt 4.3). Kein Cloud-Abgleich zwischen Browser und App; Spielstände lassen sich per Datei exportieren und importieren.", "E"],
    ["Simulation", "Beim Öffnen holt das Spiel die verstrichene Spielzeit nach (Lazy Tick wie in Haulstar).", "V"],
    ["Weltdaten", "legami ist eine Grundlage, aber nicht die einzige. Erweiterungen sind erlaubt, wenn das Setting sie trägt.", "E"],
    ["Datengenerator", "Der Python-Generator bleibt vorerst in legami. Einen faker.js-Generator baut später eine eigene Session.", "E"],
    ["Aufgabenteilung", "faker.js nur für Namen und Texte, mit festem Seed. Die Wirtschaftslogik (Bestellungen, Produktion, Preise) ist eigener, deterministischer Code im Spielkern.", "V"],
    ["Sprache", "Alle Texte und die gesamte Kommunikation auf Deutsch und Englisch.", "E"],
    ["Optik", "Wird vorerst nicht geplant.", "E"],
  ]),
  p("Hinweis zu den Stores: Auch eine kostenlose App ohne Werbung braucht Entwicklerkonten (Apple etwa 99 $ im Jahr, Google etwa 25 $ einmalig) und eine Datenschutzerklärung. Ohne Konto und ohne Datenerhebung bleibt die Datenschutzangabe aber sehr kurz."),
  h2("3.1 Datenweg von legami ins Spiel"),
  ...ol([
    "Der Python-Generator in legami erzeugt die Welt bis zum 31.12.2059, wie heute, mit festem Seed.",
    "Ein neuer Exportschritt schreibt daraus einen **Startstand**: JSON-Pakete je Bereich (Firmen, Stationen, Waren, Personen, laufende Verträge, Schreiben, Preise der letzten Monate).",
    "Das Spiel lädt den Startstand und rechnet ab dem 1.1.2060 mit eigener TypeScript-Logik weiter.",
    "Die 62 Prüfungen des Generators bleiben die Abnahme für den Startstand. Das Spiel bekommt eigene Tests für das Weiterrechnen.",
    "Später ergänzt oder ersetzt ein faker.js-Generator (eigene Session) den Python-Generator.",
  ]),
  p("Die Datenbank ist heute rund 42 MiB groß. Für Browser und Handy braucht es einen schlanken Startstand, der nur die Historie enthält, die das Spiel auch zeigt."),
  vnote("Startstand mit 12 Monaten Preisen und Monatsabschlüssen, laufenden Verträgen und Schreiben der letzten 6 Monate", "Startstand"),
  p("Der Spielkern von Haulstar verbietet Funktionen wie Math.sin oder Math.exp, damit die Rechnung auf allen Geräten gleich ausfällt. Das Preismodell aus legami (Saisonkurven, Rauschen) muss deshalb mit Festkomma-Rechnung oder Tabellen nachgebaut werden."),

  // 4
  h1("4 Zeit, Beschleunigung und Spielmodi"),
  ...decisions([
    ["Beschleunigung", "Das Spiel läuft schneller als die Echtzeit (logische Beschleunigung).", "E"],
    ["Nachtmodus", "Nachts zwischen 22:00 und 6:00 Uhr Ortszeit läuft die Zeit langsamer, damit man im Schlaf nicht zu viel verpasst. In den Einstellungen abschaltbar.", "E"],
    ["Faktoren", "Tagsüber 24 (1 Echtzeitstunde = 1 Spieltag), nachts 6 (1 Echtzeitstunde = 6 Spielstunden).", "V"],
  ]),
  h2("4.1 Was die Faktoren bedeuten"),
  ...table(["Spielzeit", "Echtzeit (mit Nachtmodus)"], [
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
    "Haulstar kennt heute keine Beschleunigung: Der Kern bekommt die Zeit nur als Parameter, und die Uhr-Schicht (env/clock.ts) ist die einzige Stelle mit Date.now(). Die Beschleunigung gehört deshalb in die Uhr-Schicht; der Kern rechnet nur in Spielzeit.",
    "Die Spielzeit ergibt sich aus der Echtzeit und einem gespeicherten **Zeitplan** aus Abschnitten mit Faktor. Damit bleibt das Nachrechnen nach langer Abwesenheit deterministisch.",
    "Die Ortszeit kommt aus der Zeitzone des Geräts. Ein Wechsel der Zeitzone oder der Einstellung gilt ab der nächsten vollen Minute und wird im Zeitplan vermerkt. Echtzeit, die schon vergangen ist, wird nie neu bewertet.",
    "Der Spielkalender beginnt am 1.1.2060 um 00:00. Monatsabschlüsse, Zinsen, Gehälter, Raten und Unterhalt laufen nach Spielkalender.",
  ]),
  vnote("Zeitplan in der Uhr-Schicht mit Abschnitten je Faktor und Zeitzone", "Zeitplan"),
  h2("4.3 Spielmodi „Real“ und „Fun“"),
  ...decisions([
    ["Wahl beim Start", "Man startet entweder im Modus „Real“ oder im Modus „Fun“.", "E"],
    ["Real", "Keine Pause und kein Urlaubsmodus. Ältere Spielstände lassen sich nicht laden; Strafen und Pleiten gelten in voller Härte.", "E"],
    ["Fun", "Pause, Urlaubsmodus und Kopien des Spielstands sind möglich. Die Pause hält die Welt ganz an; im Urlaubsmodus läuft sie langsamer weiter.", "E"],
    ["Wechsel", "Von Real nach Fun ist ein Wechsel möglich, zurück nicht.", "E"],
    ["Mehrere Stände", "Man kann mehrere Spielstände in verschiedenen Modi haben, jeder mit eigenem Verlauf.", "E"],
    ["Nachtmodus", "Gilt in beiden Modi.", "V"],
    ["Szenarien", "Beide Modi lassen sich mit allen drei Startszenarien kombinieren (Abschnitt 6).", "V"],
    ["Urlaubsfaktor", "Wie langsam läuft der Urlaubsmodus, und wie lange darf er dauern?", "O"],
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
    ["Institutionen", "Bank, Börse, Zoll, Justiz und Finanzaufsicht sind Institutionen, keine Firmen, und nicht übernehmbar.", "V"],
    ["Kartellamt", "Gibt es nicht.", "E"],
    ["Freie Händler", "6–10 NPC-Freihändler, die wie der Spieler 2060 starten und um Ausschreibungen konkurrieren.", "V"],
    ["Eigentümer", "Neu in den Daten: Aktionärs- bzw. Gesellschafterstruktur je Firma (Abschnitt 13).", "V"],
    ["Produktionsrezepte", "Neu: Rezepte mit drei Stufen (Abschnitt 7.4, Entwurf in Anhang C).", "E"],
    ["Open-Source-Plattform", "Neu: Plattform mit frei verfügbaren Bauplänen (Abschnitt 7.4).", "E"],
  ]),
  h2("5.4 Planeten und Kolonien"),
  ...decisions([
    ["Zu Beginn", "Besiedelt sind nur die Erde und 1–3 weitere Planeten mit sehr kleinen Außenposten, vor allem für Kolonisierung, Rohstoffförderung und Forschung.", "E"],
    ["Später", "Der Spieler kann selbst Planeten besiedeln und dort Städte aufbauen, ungefähr so wie heute in Haulstar.", "E"],
    ["Zählweise", "Gelten die 1–3 Planeten für die ganze Welt oder je System? Dieses Dokument geht von der ganzen Welt aus.", "O"],
    ["Ressourcenpunkte", "Lagerstätten auf Planeten, um die Firmen konkurrieren und kämpfen (Abschnitt 15). Der Spieler darf Ressourcenpunkte beanspruchen.", "V"],
    ["Städte", "Städte wachsen mit Versorgung und sind zugleich Absatzmarkt: Ihre Bevölkerung kauft Nahrung, Medizin, Konsum- und Luxusgüter.", "V"],
    ["Haulstar-Modul", "Grundlage ist das Planetenmodul von Haulstar (Besiedeln, Raster mit Hauptgebäude, Gelände, parallele Bauaufträge).", "V"],
  ]),

  // 6
  h1("6 Spielstart: drei Szenarien"),
  p("Für alle drei gilt: 25.000 CR, ein Schiff im Wert von 125.000 CR mit Baujahr 2044, Start in Sol an einer neutralen Handelsstation und eine geführte Einstiegsphase. Name, Logo und Rechtsform der Firma sind frei wählbar. Dazu wählt man den Modus Real oder Fun (Abschnitt 4.3)."),
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
  p("Entschieden ist, dass die Rechtsform wählbar ist. Die Bedingungen sind von mir:"),
  ...table(["Rechtsform", "Voraussetzung", "Haftung", "Besonderheit"], [
    ["Einzelunternehmen", "keine", "mit dem Privatvermögen", "einfach, kein Mindestkapital"],
    ["GmbH", "25.000 CR Stammkapital (genau das Startkapital)", "nur mit dem Firmenvermögen, außer bei schweren Straftaten", "Standardwahl"],
    ["AG", "50.000 CR Grundkapital, später Börsengang ab Größe und Ruf", "nur mit dem Firmenvermögen, außer bei schweren Straftaten", "Aktien, Kapital von der Börse; kann selbst übernommen werden"],
  ], [3, 3, 3, 3]),
  vnote("Rechtsformen der eigenen Firma mit Voraussetzungen wie in der Tabelle", "Rechtsformen der eigenen Firma"),

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
    ["Modell", "Preis je Station und Ware = Basispreis × Zyklus (Saison, Konjunktur) × Angebot/Nachfrage der NPC-Wirtschaft × Ereignisfaktor, mit deterministischem Rauschen. Das setzt das Preismodell des Generators fort. Der Spieler wirkt nur über große Mengen auf die Bestände, z. B. durch Horten oder große Lieferverträge.", "V"],
    ["Haulstar-Formel", "Die Haulstar-Formel (der Preis hängt am Lagerbestand, den der Spieler direkt verschiebt) passt nicht dazu und wird ersetzt.", "V"],
  ]),
  h2("7.3 Kosten je Fahrt"),
  ...decisions([
    ["Kosten aus dem Generator", "Treibstoff: Entfernung × (22 CR × Auslastung des Laderaums + 0,006 CR je Tonne Ladung). Einfuhrzoll am Zielort: 6 % (hohe Sicherheit), 4,5 % (mittel), 2,5 % (niedrig), 0 % (gesetzlos). Schmuggelware: 15 % Schutz- und Schmiergelder statt Zoll. Andockgebühr je Station. Versicherung: 0,2 / 0,5 / 1,2 / 2,5 % des Warenwerts je Risikostufe, 3 % Aufschlag bei illegaler Ladung. Zahlungsziel 30 Tage.", "V"],
  ]),
  h2("7.4 Produktion, Förderung und Technologie"),
  ...decisions([
    ["Produktionsketten", "Firmen produzieren aus Eingangswaren. Liefert ihnen niemand, sinkt ihre Produktion.", "E"],
    ["Tiefe", "Drei Stufen: Förderung und Anbau → Grundverarbeitung → Endprodukte. Ein erster Rezeptentwurf steht in Anhang C.", "E"],
    ["Eigene Produktion", "Der Spieler darf selbst fördern und produzieren, sobald er Geld und Technologie dafür hat.", "E"],
    ["Open Source", "Auf einer Plattform gibt es Open-Source-Projekte zum Erkunden, als Anregung für eigene Förderung oder Produktion. Ihre Qualität liegt unter der von Firmenprodukten. Mit genug Masse kann man damit Geld verdienen.", "E"],
    ["Lizenzen", "Wer genug Geld hat, für den soll sich ein Lizenzprodukt einer Firma lohnen.", "E"],
    ["Eigene Forschung", "Eine eigene Entwicklungsabteilung verbessert Baupläne. Eigene Entwicklungen kann man an Firmen lizenzieren oder als Open Source veröffentlichen.", "E"],
    ["Zeitpunkt Forschung", "Die eigene Entwicklung kommt erst später im Spiel, nach Open Source und Lizenzen.", "V"],
    ["Plattform im Spiel", "Durchsuchbare Sammlung von Projekten (z. B. „Regolith-Sinteranlage v0.4“) mit Bewertungen, Reifegrad und Fehlerrate. Das Erkunden kostet Zeit; manche Projekte sind veraltet oder fehlerhaft.", "V"],
    ["Lizenzkosten", "Einmalbetrag plus Lizenzgebühr je produzierter Einheit; der Lizenzgeber kann die Lizenz bei Vertragsbruch entziehen.", "V"],
    ["Energie", "Fertigung verbraucht zusätzlich Energie: Brennstoffzellen für leichte Fertigung, Fusionspellets für Schwerindustrie und Forschung.", "V"],
  ]),
  ...table(["Technologiequelle", "Kosten", "Qualität", "Wann sinnvoll"], [
    ["Open-Source-Projekt", "gering", "unter Firmenniveau", "Einstieg; lohnt sich über die Menge"],
    ["Lizenz einer Firma", "hoch", "Firmenniveau", "sobald man es sich leisten kann"],
    ["Eigene Entwicklung", "Personal und Labor", "kann Firmenniveau erreichen und übertreffen", "später; eigene Lizenzen verkaufen oder veröffentlichen"],
  ], [3, 2, 3, 3]),
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
    ["Öffentliche Nachrichten", "ja", "ja", "ja", "–"],
    ["Gerüchte", "nein", "ja", "ja", "Kontakt oder Abo"],
    ["Insiderinfos", "nein", "nein", "ja", "Kontakte mit hoher Zugriffsstufe, Bestechung, Hacking"],
    ["Interne Kommunikation einer Firma", "nein", "nein", "nein", "nur durch Übernahme oder Hacking (Entschieden)"],
  ], [3, 2, 2, 2, 3]),
  vnote("Solo-Gründer sieht öffentliche Nachrichten; Gerüchte über Kontakt oder Abo freischaltbar", "Informationszugang"),
  h2("9.3 Schriftverkehr"),
  p("Du hattest geantwortet: so, wie es die beste Nutzererfahrung ergibt. Mein Vorschlag:"),
  ...ul([
    "Der Spieler schreibt über **Vorlagen**: Art (Anfrage, Angebot, Gegenangebot, Beschwerde, Übernahmeangebot …), Felder (Ware, Menge, Preis, Frist) und Tonfall (freundlich, sachlich, hart). Das geht auf dem Handy schnell und lässt sich auswerten.",
    "Die Antworten der Firmen folgen Regeln (Vertrauen, Ruf, Persönlichkeit, Lage der Firma) und sind deterministisch. So bleibt das Spiel offline spielbar und testbar.",
    "Später optional: Eine KI formuliert den Brieftext aus. Sie ändert nur die Formulierung, nie die Entscheidung.",
    "Ein Posteingang mit Verläufen und Fristen („Antwort erforderlich bis …“).",
    "Jedes Schreiben gibt es auf Deutsch und Englisch; angezeigt wird die Spielsprache.",
  ]),
  vnote("Schriftverkehr über Vorlagen mit regelbasierten, deterministischen Antworten", "Schriftverkehr"),
  h2("9.4 Hacking"),
  p("Entschieden: Die interne Kommunikation einer Firma ist ohne Übernahme nur über Hacking zugänglich, mit verschiedenen Angriffsmethoden. Mein Vorschlag für die Methoden:"),
  ...table(["Methode", "Weg", "Aufwand", "Entdeckungsrisiko", "Ergebnis"], [
    ["Phishing", "gefälschte Schreiben an Mitarbeiter", "gering, kurz", "mittel", "Postfach einer Person bis zu deren Zugriffsstufe"],
    ["Bestechung", "Mitarbeiter mit hoher Bestechlichkeit oder niedriger Loyalität", "mittel", "mittel bis hoch", "Schreiben bis zur Zugriffsstufe der Person"],
    ["Lieferkette", "manipulierte Elektronik oder Navigationscomputer in Lieferungen an die Firma", "hoch, lang", "niedrig", "dauerhafter Zugang zu einer Station"],
    ["Schwarzmarkt-Werkzeug", "Kauf von Angriffswerkzeug, z. B. Gehackte KI-Kerne", "hoch", "wechselnd", "einmaliger tiefer Zugriff"],
    ["Eingeschleuster Mitarbeiter", "eigene Person bewirbt sich bei der Firma", "lang", "niedrig, bei Entdeckung großer Schaden", "laufender Insiderzugang"],
  ], [20, 30, 18, 25, 30]),
  vnote("Fünf Hacking-Methoden wie in der Tabelle", "Hacking-Methoden"),
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
  vnote("Vier Beziehungsgrößen mit Wirkungen und Quellen wie in der Tabelle", "Beziehungsgrößen"),
  h2("10.1 Kontakte"),
  ...ul([
    "Kontakte sind echte Personen aus den Mitarbeiterlisten der Firmen. Man gewinnt sie über Aufträge, Treffen auf Stationen oder Empfehlungen anderer Kontakte.",
    "Die Persönlichkeit aus den Daten bestimmt, was wirkt: Bei **gierig** zählt Geld, **loyal** ist schwer zu bestechen und hält zur eigenen Firma, **gesprächig** gibt Gerüchte weiter, **vorsichtig** braucht Zeit und Sicherheiten, **ehrgeizig** will Aufstieg, **idealistisch** achtet auf Belegschaft und Zukunft, **pragmatisch** rechnet nüchtern.",
    "Einfluss und Zugriffsstufe einer Person bestimmen, wie viel ein Kontakt bewirken und verraten kann.",
  ]),
  vnote("Kontaktaufbau und Wirkung der Persönlichkeiten wie beschrieben", "Kontakte"),

  // 11
  h1("11 Illegales und Justiz"),
  ...decisions([
    ["Schmuggel", "Ist erlaubt. Kommt es durch ein Leck, einen Whistleblower o. Ä. heraus, folgt nach einiger Zeit eine Strafe. Wird sie nicht bezahlt, werden Schiffe beschlagnahmt, so wie in echt.", "E"],
    ["Bestechung", "Ist möglich. Wer erwischt wird, zahlt Strafe. In schweren Fällen müssen eigene Angestellte für eine Zeit ins Gefängnis; der Spieler entscheidet dann, ob er sie kündigt oder behält.", "E"],
    ["Persönliche Haftung", "Der Spieler kann selbst belangt werden, aber nur in schweren Fällen. Dann haftet auch sein Privatvermögen.", "E"],
    ["Behörden", "Zoll, Justiz und Finanzaufsicht (für Börsenmanipulation und Insiderhandel).", "V"],
  ]),
  ...table(["Tat", "Fliegt auf durch", "Folge"], [
    ["Schmuggel", "Leck, Whistleblower, Zollkontrolle, Razzia", "Bußgeld, Ware wird eingezogen, Ruf sinkt"],
    ["Bestechung", "Whistleblower, interne Prüfung der Firma", "Bußgeld, Vertrauen und Ruf bei der Firma sinken, in schweren Fällen Haft"],
    ["Hacking", "Sicherheitsdienst der Firma, Spurensuche", "Bußgeld, Schadenersatz, Haft, Ruf sinkt"],
    ["Marktmanipulation, Insiderhandel", "Finanzaufsicht", "Bußgeld, Abschöpfung des Gewinns, Handelssperre"],
  ], [2, 3, 4]),
  h2("11.1 Ablauf"),
  ...ol([
    "Jede Tat hinterlässt eine **Spur** mit einer Entdeckungswahrscheinlichkeit je Monat. Sie steigt mit der Zahl der Mitwisser und dem Umfang.",
    "Die Entdeckung kommt verzögert, nach 1–6 Spielmonaten.",
    "Eine Ermittlung kündigt sich im Posteingang an. Dann kommt ein Bescheid mit Strafe und Zahlungsfrist. Die Strafe ist ein Vielfaches des Gewinns aus der Tat plus ein Grundbetrag.",
    "Wird nicht bezahlt, folgen Mahnung, Kontopfändung, Beschlagnahme von Schiffen und schließlich deren Versteigerung.",
    "In schweren Fällen gehen beteiligte Angestellte für 1–12 Spielmonate in Haft. Behält der Spieler sie, steigt ihre Loyalität, aber sie fallen so lange aus. Kündigt er sie, sinkt die Stimmung der übrigen Belegschaft leicht. Ist der Fall schwer genug, haftet auch der Spieler mit seinem Privatvermögen.",
  ]),
  vnote("Justizablauf in fünf Schritten mit Spur, Verzögerung, Bescheid, Vollstreckung und Haft", "Justizablauf"),

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
    ["Rohstoffbörse", "Zuerst nur sofortiger Kauf und Verkauf; Terminkontrakte kommen später.", "E"],
    ["Kursmodell", "Kurs = fairer Wert × Stimmung × Rauschen. Der faire Wert ergibt sich aus Monatsergebnissen, Kasse, Vermögen (Stationen, Flotte, Lager), Verträgen und der Rohstoffabhängigkeit. Steigen die Preise der Waren, die eine Firma verkauft, steigt ihr Kurs; steigen die Preise ihrer Einsatzstoffe, sinkt er. Die Stimmung kommt aus Newsfeed, Gerüchten und Ereignissen.", "V"],
  ]),
  ...table(["Manipulation", "Wirkung", "Risiko"], [
    ["Gerüchte streuen", "Stimmung und Kurs bewegen sich kurzfristig", "Finanzaufsicht, Ruf"],
    ["Rohstoff horten", "Rohstoffpreis und Kurse abhängiger Firmen bewegen sich", "bindet viel Kapital; Absprachen fallen auf"],
    ["Leerverkauf vor schlechter Nachricht", "Gewinn bei Kurssturz", "gilt als Insiderhandel, wenn man es vorher wusste"],
    ["Insiderhandel", "nahezu sicherer Gewinn", "hohe Strafe bei Entdeckung"],
  ], [3, 4, 3]),
  vnote("Vier Arten der Marktmanipulation wie in der Tabelle", "Marktmanipulation"),
  h2("12.3 Privatvermögen"),
  ...decisions([
    ["Neustart", "Bei einer Pleite durchläuft der Spieler ein Insolvenzverfahren und gründet danach mit dem zurückgelegten Privatvermögen eine neue Firma.", "E"],
    ["Einzahlung", "Der Spieler zahlt sich Gehalt, Entnahmen oder Dividenden ins Privatvermögen.", "V"],
    ["Schutz", "Bei GmbH und AG ist das Privatvermögen vor der Pleite der Firma geschützt, außer in schweren Straffällen (Abschnitt 11). Beim Einzelunternehmen haftet es immer.", "V"],
  ]),
  h2("12.4 Pleite des Spielers"),
  ...ol([
    "Die Firma ist zahlungsunfähig oder überschuldet (Prüfpunkte wie in 12.5).",
    "Insolvenzverfahren: Firma, Schiffe und Anteile werden verwertet, die Gläubiger bedient.",
    "Neugründung mit dem Privatvermögen. Kontakte bleiben, das Vertrauen sinkt, der persönliche Ruf bleibt zur Hälfte, Erfolge bleiben.",
  ]),
  vnote("Was nach einer Pleite bleibt: Kontakte, halber persönlicher Ruf, Erfolge", "Neustart nach Pleite"),
  p("Die Holding aus Haulstar (eine neue Firma gründen, etwas mitnehmen) liefert Ideen für diesen Neustart. Ihr Prestigebaum passt aber nicht zur Wirtschaftssimulation (Abschnitt 17)."),
  h2("12.5 Pleite von NPC-Firmen"),
  p("Entschieden ist: NPC-Firmen können pleitegehen. Die Prüfpunkte und die Insolvenzphase hast du mir überlassen:"),
  ...table(["Prüfpunkt", "Schwelle"], [
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
  vnote("Drei Prüfpunkte und eine Insolvenzzeit von 60 Spieltagen mit Bieterverfahren", "NPC-Insolvenz"),

  // 13
  h1("13 Beteiligungen und Übernahmen"),
  h2("13.1 Rechtsformen der 18 Firmen"),
  p("Entschieden: so, wie es für die drei Startszenarien am besten greift; weitere Rechtsformen können dazukommen. Meine Zuordnung:"),
  ...table(["Im Spiel", "Firmen", "Übernahme über"], [
    ["Börsennotiert (AG, Inc., Group, Consortium)", "Eisenkrone, Graufalk, Lichtacker, Kuppelwerk, Pionierwerk, Corvane, Cindervale, Emberline, Outmark, Helix Meridian, Ravenmoor (11)", "Börse, öffentliches Angebot, Verhandlung mit dem Vorstand"],
    ["Gesellschafter (GmbH, Co.)", "Feldspat, Kometenpost, Raureif, Driftwood, Lanternfish, Second Hull (6)", "Angebot an die Gesellschafter"],
    ["Genossenschaft (eG)", "Morgengrund (1)", "kein Kauf; Kooperation oder Verschmelzung per Mitgliederbeschluss"],
  ], [3, 5, 3]),
  vnote("Zuordnung der 18 Firmen zu börsennotiert, Gesellschafter und Genossenschaft", "Rechtsformen der 18 Firmen"),
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
    "Ablauf: Aktien leise kaufen (bis 3 % unbemerkt), danach werden die Meldeschwellen öffentlich. Dann ein öffentliches Angebot mit Prämie, mindestens zum Durchschnittskurs der letzten 3 Monate, mit einer Annahmefrist von 28 Spieltagen. Danach der Vollzug.",
    "Abwehr der Zielfirma: ein weißer Ritter (eine Partnerfirma bietet mehr), ein Rivale bietet mit, Aktienrückkauf, Kapitalerhöhung, Verkauf der wertvollsten Teile, Gegenangriff (wenn der Spieler eine AG ist), Streikdrohung der Belegschaft.",
    "Aktionärsgruppen (neu in den Daten): Gründer oder Familie, Partnerfirmen, Fonds, Streubesitz, Belegschaft. Jede Gruppe hat ihre eigene Annahmeschwelle.",
  ]),
  vnote("Ablauf, Abwehrmittel und Aktionärsgruppen bei feindlichen Übernahmen", "Feindliche Übernahme"),
  h2("13.4 Freundliche Übernahme"),
  p("Hast du mir überlassen. Ablauf in sechs Schritten:"),
  ...ol([
    "**Kontakt zum Vorstand**, über einen Kontakt oder ab einem bestimmten Ruf bei der Firma.",
    "**Absichtserklärung:** Preisrahmen und Zusagen (Belegschaft, Standorte, Marke).",
    "**Prüfung (Due Diligence):** kostet Geld und Zeit und deckt Risiken auf, etwa offene Vertragsstrafen, laufende Verfahren, Lecks oder schlechte Verträge.",
    "**Verbindliches Angebot:** Der Vorstand empfiehlt es oder lehnt ab. Das hängt ab von Vertrauen, der Persönlichkeit des Vorstandsvorsitzes, der Stimmung der Belegschaft und dem Preis im Verhältnis zum fairen Wert.",
    "**Annahme durch die Aktionäre:** Mit Empfehlung des Vorstands nehmen deutlich mehr an.",
    "**Vollzug:** Die Zusagen werden zu Pflichten. Wer sie bricht, verliert Ruf und die Stimmung der Belegschaft.",
  ]),
  vnote("Freundliche Übernahme in sechs Schritten", "Freundliche Übernahme"),
  h2("13.5 Angebot an eine GmbH oder Co."),
  p("Hast du mir überlassen:"),
  ...ul([
    "Jede Firma hat 1–4 Gesellschafter: Gründer, Familie, Partnerfirma oder Investor. Sie werden neu erzeugt; die Firmenbeschreibungen nennen schon Gründer und Gründungsjahr.",
    "Das Angebot geht als Brief raus: Anteil (auch ein Teilkauf ist möglich), Preis, Zusagen, Frist.",
    "Ob angenommen wird, ergibt sich aus: Preis gegenüber fairem Wert, Vertrauen, Ruf, Lage der Firma (Verluste und knappe Kasse machen einen Verkauf wahrscheinlicher) und Persönlichkeit. Bei gierig zählt der Preis doppelt, bei loyal die Zusagen an die Belegschaft, bei idealistisch die Zukunft der Firma; vorsichtig verlangt eine lange Frist und eine Prüfung.",
    "Mögliche Antworten: Annahme, Gegenangebot, Ablehnung mit Sperrfrist. Manchmal wird das Angebot auch an einen Rivalen durchgestochen und taucht als Gerücht auf.",
    "Die Mitgesellschafter haben ein Vorkaufsrecht.",
    "Eine Minderheitsbeteiligung bringt Einblick in die Monatsabschlüsse und eine Stimme in der Gesellschafterversammlung.",
  ]),
  vnote("Angebote an GmbH und Co. mit Gesellschaftern, Annahmeregeln, Vorkaufsrecht und Teilkauf", "Angebot an GmbH und Co."),
  h2("13.6 Nach der Übernahme"),
  ...decisions([
    ["Führung", "Der Spieler setzt einen Manager ein.", "E"],
    ["Belegschaft", "Mitarbeiter mit niedriger Loyalität kündigen.", "E"],
    ["Kommunikation", "Die interne Kommunikation der übernommenen Firma wird lesbar.", "E"],
    ["Manager", "Man wählt aus Bewerbern, eigenen Leuten oder Personen aus der Firma. Manager haben Fähigkeiten, Gehalt, Loyalität und eine Strategie (Gewinn, Wachstum, Sicherheit). Der Spieler gibt Ziele vor, steuert aber nicht jeden einzelnen Auftrag.", "V"],
    ["Gewinne", "Fließen als Dividende oder Gewinnabführung an die Firma des Spielers.", "V"],
  ]),
  h2("13.7 Übernahmen durch NPC-Firmen"),
  ...decisions([
    ["Grundsatz", "NPC-Firmen übernehmen sich gegenseitig und können auch die Firma des Spielers übernehmen, wenn sie eine AG ist.", "E"],
    ["Häufigkeit", "Solche Übernahmen sind selten (höchstens eine pro Spieljahr in der ganzen Welt) und kündigen sich vorher über Gerüchte an.", "V"],
  ]),

  // 14
  h1("14 Schiffe, Flotte und Personal"),
  h2("14.1 Schiffe"),
  ...decisions([
    ["Startschiff", "Wert 125.000 CR, Baujahr 2044. Durch das Alter sind die Wartungskosten höher, und das Schiff verliert an Wert.", "E"],
    ["Vorbilder", "Die Schiffe sind an X4 und Stellaris angelehnt.", "E"],
    ["Kriegsschiffe", "Haben nur einen kleinen Laderaum.", "E"],
    ["Größen", "Vier Größenklassen wie in X4: S, M, L, XL. Die Größe bestimmt Frachtraum, Steckplätze, Crew, Andockmöglichkeiten und Preis.", "V"],
    ["Rollen", "Handel (Kurier, Frachter, Massengutfrachter, Tanker, Kühlfrachter), Förderung (Erz, Gas), Bau (Stationen, Außenposten), Kolonisierung, Erkundung und Vermessung, Militär (Korvette, Fregatte, Zerstörer, Kreuzer, Schlachtschiff, wie in Stellaris), Versorgung.", "V"],
    ["Ausrüstung", "Jeder Rumpf hat Steckplätze für Module: Antrieb, Frachtmodule, Tank, Kühlraum, Panzerung, Schilde, Waffen, Sensoren, Crewquartiere. Damit lassen sich Schiffe wie im Schiffsdesigner von Stellaris ausrüsten.", "V"],
    ["Startschiff-Klasse", "Ein kleiner Frachter der Größe M.", "V"],
    ["Werte und Preise", "Klassen, Werte und Preise kommen in ein eigenes Planungsdokument.", "O"],
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
  ...table(["Rolle (aus den Daten)", "Monatsgehalt in den Daten", "Nutzen für den Spieler"], [
    ["Frachtpilot:in", "7.000–12.000 CR", "fliegt ein weiteres Schiff"],
    ["Handelsagent:in", "6.000–11.000 CR", "schließt kleine Aufträge selbstständig ab"],
    ["Frachtdisposition", "5.000–8.500 CR", "steuert mehrere Schiffe auf Routen"],
    ["Sicherheitsdienst", "4.500–8.000 CR", "senkt die Überfallrate, schützt vor Hacking"],
    ["Marktaufklärung", "9.000–16.000 CR", "bewertet Gerüchte, findet Insiderinfos"],
    ["Partnerbetreuung", "8.000–14.000 CR", "pflegt Kontakte, verhandelt Verträge"],
    ["Finanzbuchhaltung", "6.000–10.500 CR", "Kredite, Mahnwesen, Börse"],
    ["Forschung & Entwicklung", "7.000–13.000 CR", "verbessert Baupläne (eigene Entwicklung)"],
    ["Stationsleitung", "14.000–24.000 CR", "führt eine eigene Station oder Fabrik"],
  ], [3, 2, 4]),
  vnote("Nutzen der Rollen für den Spieler wie in der Tabelle", "Nutzen der Rollen"),

  // 15
  h1("15 Sicherheit, Überfälle und Krieg"),
  ...decisions([
    ["Überfallrate", "Sinkt mit steigendem Ruf und stärkeren Schiffen.", "E"],
    ["Sicherheitsfirmen", "Private Sicherheitsfirmen schützen die Routen.", "E"],
    ["Krieg", "Es gibt Kriege um Ressourcenpunkte auf Planeten. Die Kämpfer sind Freiwillige aus Sol. Krieg ist eher ein Mittel zum Zweck und fast schon Standard, weil die Regierungen auf anderen Planeten keinen dauerhaften Frieden durchsetzen können.", "E"],
    ["Eigene PMC", "Später im Spiel, mit dem nötigen Kapital, kann der Spieler eine eigene Sicherheitsfirma (PMC) gründen und Ressourcen erobern.", "E"],
    ["Handelsabbruch", "Greift der Spieler eine Firma an, bricht der Handel mit ihr sofort ab. Danach kann wieder gehandelt werden; die Firmen sind nicht nachtragend.", "E"],
    ["Formel", "Überfallrate je Flug = Grundrate der Route (Sicherheit der Systeme, Entfernung, Gefahrenstufe) × Ruffaktor × Stärkefaktor (Schutz des Schiffs, Geleitschutz) × Konfliktfaktor (Krieg im Sektor) × Wertfaktor (wertvolle Ladung lockt). Auf den ersten 12 Routen ist sie 0.", "V"],
    ["Folgen", "Ladung ganz oder teilweise verloren, Schiff beschädigt, selten ganz verloren. Eine Versicherung zahlt.", "V"],
    ["Geleitschutz", "Ravenmoor Convoy & Security Group (im Bestand) bietet Konvoi und Geleit an, je Fahrt oder per Vertrag.", "V"],
    ["Darstellung", "Kämpfe werden als Ereignisse und Berichte gezeigt, ohne detaillierte Gewalt. Das hält die Altersfreigabe in den Stores niedrig.", "V"],
  ]),
  h2("15.1 Konflikte um Ressourcenpunkte"),
  ...ul([
    "Ressourcenpunkte sind Lagerstätten auf Planeten, auf die Firmen Anspruch erheben. Konflikte entstehen zwischen Rivalen; die Daten enthalten schon Rivalitäten, auch solche um die Vorherrschaft in einem System.",
    "Wirkung: Im Sektor steigt die Nachfrage nach Rüstung, Nahrung, Medizin und Treibstoff. Die Überfallrate steigt, die Preise schwanken, und die Kurse der beteiligten Firmen bewegen sich.",
    "Ausgang: Die siegreiche Firma erhält den Ressourcenpunkt und damit mehr Förderung, was sich in Monatsabschluss und Kurs niederschlägt.",
  ]),
  vnote("Ablauf und Wirkung von Konflikten um Ressourcenpunkte", "Konflikte um Ressourcenpunkte"),
  h2("15.2 Eigene Sicherheitsfirma (PMC)"),
  ...ul([
    "Gründung: als eigene Tochterfirma, sobald Kapital, Ruf und mindestens ein Kriegsschiff vorhanden sind.",
    "Personal: Freiwillige aus Sol, die Sold bekommen; Loyalität und Ausbildung wirken auf den Erfolg.",
    "Aufträge: Geleitschutz für Handelsschiffe, Verteidigung von Ressourcenpunkten, Angriffe im Auftrag anderer Firmen.",
    "Eroberung: Die PMC kann Ressourcenpunkte für den Spieler erobern. Gegen die angegriffene Firma ruht der Handel bis zum Friedensschluss.",
    "Nach dem Frieden: Der Handel ist wieder möglich. Der Ruf bei der angegriffenen Firma sinkt und erholt sich mit der Zeit. Partner der Firma reagieren verhalten, Rivalen eher freundlich.",
  ]),
  vnote("Gründungsbedingungen, Aufträge und Folgen der eigenen PMC", "Eigene PMC"),

  // 16
  h1("16 Kampagne, Sandbox und Erfolge"),
  ...decisions([
    ["Grundform", "Endlose Sandbox mit Kampagne und drei Startszenarien.", "E"],
    ["Erfolge", "Nur als eigenes Erfahrungs- und Feedbacksystem. NPC-Firmen haben keine.", "E"],
    ["Kapitel", "10 Kapitel wie in der Tabelle unten. Sie passen sich dem Szenario an; beim Solo-Gründer dauern Kapitel 1 und 2 länger.", "V"],
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
    ["8 Forschung", "einen Bauplan selbst verbessern und lizenzieren", "Eigene Entwicklung"],
    ["9 Kolonie", "einen Planeten besiedeln", "Städte, Versorgung"],
    ["10 Konzern", "Mehrheit an einer börsennotierten Firma oder eigene PMC", "Konzernsteuerung, Konflikte"],
  ], [2, 4, 3]),

  // 17
  h1("17 Was aus Haulstar übernommen wird"),
  p("Entschieden: Legami Colony bekommt ein eigenes Repo; der Kern von Haulstar wird einmalig kopiert. Haulstar entwickelt sich unabhängig weiter. Welche Bausteine übernommen werden, hattest du offen gelassen. Grundlage für die Einschätzung ist eine Bestandsaufnahme des Repos idlestar vom 21.10.2026."),
  ...table(["Baustein", "Entscheidung", "Begründung"], [
    ["Spielkern: Ereignisschleife, Zeit als Parameter, Kalender, Zufall aus Seeds, Festkomma-Rechnung", "übernehmen", "Fachlich neutral und gut getestet (u. a. „10 h = 10 × 1 h“, 200-Seed-Test). Die Zeitbeschleunigung kommt in die Uhr-Schicht."],
    ["Abrechnen und Befehle (settle, applyCommand)", "übernehmen", "Muster passt für jede Simulation."],
    ["Spielstand, Migrationen, Speicher (SQLite/IndexedDB), Export/Import, mehrere Spielstände", "übernehmen", "Neues Schema ab Version 1; Modus Real/Fun je Spielstand."],
    ["Buchungsjournal und Bericht „Seit deinem letzten Besuch“", "übernehmen", "Neue Buchungsarten (Zoll, Vertragsstrafe, Dividende …)."],
    ["Content-Laden mit Schemaprüfung, Übersetzung de/en mit Prüfung der Schlüssel", "übernehmen", "Neuer Content aus dem legami-Export."],
    ["Werkzeuge: Lint-Regeln (kein Math.random), Modulgrenzen, Git-Hooks, CI", "übernehmen", "Sichert Determinismus und Struktur."],
    ["Web/PWA-Build, Cloudflare-Deploy, EAS-Profile und Updates", "übernehmen", "Deckt Browser und Stores ab."],
    ["App-Rahmen, UI-Bausteine, Zahlenformate, Hinweis-Overlays", "übernehmen und umbauen", "Bildschirme neu ordnen; Optik wird vorerst nicht geplant."],
    ["Markt und Preise", "umbauen", "Zyklusmodell statt Bestandsformel (Abschnitt 7.2)."],
    ["Flotte, Handelsrouten, Routenfinder", "umbauen", "Neu: Zoll, Versicherung, Treibstoff, Fremdaufträge, Haftung."],
    ["Lieferverträge (deliveries)", "umbauen", "Wird zur Auftragsbörse je Firma."],
    ["Manager und Automatisierung", "umbauen", "Angestellte statt Token; Manager für übernommene Firmen."],
    ["Werft und Schiffsklassen", "umbauen", "Neu: Größen und Rollen nach X4 und Stellaris, Module, Gebrauchtmarkt, Alter, Wartung, Wertverlust."],
    ["Quests, Meilensteine, Lehrzeit", "umbauen", "Werden zu Kampagne, Lehrzeit und Erfolgen."],
    ["Kampf, Überfälle, Eroberung", "umbauen", "Überfallrate nach Ruf, Schiffsstärke und Geleit; Eroberung wird zur Eroberung von Ressourcenpunkten durch die eigene PMC."],
    ["Planeten und Kolonien", "übernehmen und umbauen", "Grundlage für Besiedlung und Städte (Abschnitt 5.4)."],
    ["Claims und Förderstationen", "prüfen", "Möglich als Grundlage für Ressourcenpunkte und eigene Förderung."],
    ["Forschung", "umbauen", "Wird zur eigenen Entwicklung von Bauplänen (Abschnitt 7.4)."],
    ["Meisterschaft, Holding-Prestigebaum", "entfällt", "Passt nicht zur Wirtschaftssimulation; Ideen der Holding fließen in den Neustart nach der Pleite."],
    ["Kapitäne (Gacha), Akademie, Münzshop", "entfällt", "Passt nicht zu einer Wirtschaftssimulation."],
    ["Expeditionen, Energie-Pool", "entfällt", "Gehört zum alten Spielprinzip."],
    ["Alle Inhalte und Bilder", "neu", "Optik wird vorerst nicht geplant."],
  ], [4, 2, 5]),
  vnote("Übernahme, Umbau und Wegfall der Haulstar-Bausteine wie in der Tabelle", "Haulstar-Bausteine"),
  p("**Ganz neu** sind: NPC-Firmen als handelnde Akteure, Börse, Beteiligungen und Übernahmen, Gerüchte und Newsfeed, Schriftverkehr, Hacking, Justiz, Bank und Insolvenz, Produktionsrezepte, PMC und die Spielmodi Real/Fun. In Haulstar gibt es nichts davon; die NPC-Stationen sind dort reine Märkte. Diese Module bauen auf dem kopierten Kern auf."),

  // 18
  h1("18 Offene Punkte und nächste Planungsschritte"),
  h2("18.1 Offene Punkte"),
  ...ul([
    "Planeten: Gelten die 1–3 besiedelten Planeten zu Beginn für die ganze Welt oder je System? (5.4)",
    "Urlaubsmodus: Faktor und Höchstdauer. (4.3)",
    "Schiffe: Klassen, Werte, Preise in einem eigenen Dokument. (14.1)",
    "Produktansicht im Test ausprobieren. (7.1)",
    "Rezeptentwurf in Anhang C prüfen.",
    "Zahlen: Zeitfaktoren, Zinsen, Strafen, Schwellen, Überfallraten. Alles TBD, bis es im Test ausgewogen ist.",
    "Größe des Startstands für Browser und Handy. (3.1)",
    "Name des Repos und der Subdomain.",
  ]),
  PROPOSAL_COUNT_PLACEHOLDER,
  h2("18.2 Nächste Planungsdokumente"),
  ...ol([
    "Die Vorschläge aus Anhang D durchgehen.",
    "**Aufbau des neuen Repos:** was aus Haulstar kopiert wird, Gliederung, Module, Tests.",
    "**Wirtschaftskern:** Zeit und Spielmodi, Preise, Rezepte und Produktion, NPC-Firmen, Monatsabschluss. Darauf baut alles andere auf.",
    "**Schiffe und Personal** (Größen, Rollen, Module, Werte).",
    "**Handel, Aufträge, Verträge, Ruf und Kontakte.**",
    "**Information:** Newsfeed, Schriftverkehr, Hacking, Justiz.",
    "**Finanzen:** Bank, Börse, Übernahmen, Insolvenz.",
    "**Konflikte, PMC und Sicherheit.**",
    "**Planeten, Kolonien und Städte.**",
    "**Datenweg:** legami-Export, Startstand, später der faker.js-Generator.",
    "**Phasenplan** aus allem davor.",
  ]),
  vnote("Reihenfolge der nächsten Planungsdokumente wie in 18.2", "Planungsreihenfolge"),

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
  p("Kurzfassung deiner Antworten aus drei Runden mit Verweis auf den Abschnitt, in dem sie umgesetzt sind."),
  h2("Runde 1"),
  ...table(["Nr.", "Frage", "Antwort (kurz)", "Abschnitt"], [
    ["1", "Welches Spiel", "Haulstar neu mit der legami-Welt; Browser wie heute, nach der Testzeit App Store und Google Play (in Runde 2 geändert: eigenes Spiel)", "3"],
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
    ["45", "Ablage", "Branch in legami, docx im Chat", "–"],
  ], [1, 3, 7, 2]),
  h2("Runde 2"),
  ...table(["Nr.", "Frage", "Antwort (kurz)", "Abschnitt"], [
    ["1", "Pause oder Urlaubsmodus", "Start im Modus Real (ohne) oder Fun (mit)", "4.3"],
    ["2", "Haulstar-Spielstände und Live-Version", "Haulstar wird weitergeführt und weiterentwickelt, eher casual", "3"],
    ["3", "Ort im Code", "Eigenes Repo, auch anderer Aufbau", "3, 17"],
    ["4", "Geschäftsmodell", "Kostenlos, erst einmal ohne Bürokratie", "3"],
  ], [1, 3, 7, 2]),
  h2("Runde 3"),
  p("Allgemein: Wo du „Vorschlag“ geantwortet hast, gilt mein Vorschlag als entschieden."),
  ...table(["Nr.", "Frage", "Antwort (kurz)", "Abschnitt"], [
    ["1", "Eigene Forschung", "Ja: Entwicklungsabteilung, eigene Lizenzen oder Open Source", "7.4"],
    ["2", "Tiefe der Ketten", "3 Stufen, Rezeptentwurf ja", "7.4, Anhang C"],
    ["3", "Persönliche Haftung", "Vorschlag: ja, nur in schweren Fällen", "11"],
    ["4", "Rohstoffbörse", "Vorschlag: erst sofortiger Handel, Termingeschäfte später", "12.2"],
    ["5", "Schiffe", "Angelehnt an X4 und Stellaris; Kriegsschiffe mit kleinem Laderaum", "14.1"],
    ["6", "Konflikte", "Eigene PMC später mit Kapital, Ressourcen erobern; Handelsabbruch mit dem Angegriffenen, danach wieder Handel", "15"],
    ["7", "Planeten", "Zu Beginn nur Erde und 1–3 Planeten mit kleinen Außenposten; später eigene Besiedlung und Städte wie in Haulstar", "5.4"],
    ["8", "Spielstand-Abgleich", "Kein Abgleich, Export und Import per Datei", "3"],
    ["9", "Modi Real und Fun", "Vorschlag; mehrere Spielstände in verschiedenen Modi mit eigenem Verlauf", "4.3"],
    ["10", "Name", "Legami Colony", "Titel"],
    ["11", "Aufbau des Repos", "Gleiche Technik, anders gegliedert; Kern einmalig kopiert", "3, 17"],
    ["12", "Datengenerator", "Bleibt vorerst in legami; faker.js-Generator später in einer eigenen Session", "3.1"],
    ["13", "Web-Adresse", "Eigene Subdomain auf seritha.dev", "3"],
    ["14", "Kostenlos", "Ohne Werbung, ohne Konto, ohne Datenerhebung", "3"],
    ["15", "Mehrere Spielstände", "Siehe 9", "4.3"],
    ["16", "Optik", "Vorerst nicht darüber nachdenken", "3"],
    ["17", "Übrige Vorschläge", "Erneut ansprechen", "Anhang D"],
  ], [1, 3, 7, 2]),

  // Anhang C
  h1("Anhang C: Rezeptentwurf", { breakBefore: true }),
  p("Erster Entwurf für die drei Produktionsstufen, abgeleitet aus den 69 Grundwaren des Generators. Mengen gelten je Einheit des Produkts in den Einheiten der Eingangswaren (Tonne, Kiste, Kanister, Stück). Der **Einsatzwert** ist der Wert der Eingänge zu Basispreisen im Verhältnis zum Basispreis des Produkts. Er liegt überall zwischen etwa 45 und 70 %, damit jede Stufe Wert schöpft. Energie für die Fertigung ist nicht eingerechnet (Abschnitt 7.4)."),
  vnote("Rezeptentwurf mit drei Stufen wie in Anhang C", "Rezeptentwurf"),
  h2("Stufe 1: Förderung, Anbau und Einfuhr"),
  ...table(["Herkunft", "Waren"], STAGE1, [1, 3]),
  h2("Stufe 2: Grundverarbeitung"),
  ...table(["Produkt", "Station", "Eingänge je Einheit", "Basispreis", "Einsatzwert"], recipeRows(STAGE2), [6, 3, 8, 3, 3]),
  h2("Stufe 3: Endprodukte"),
  ...table(["Produkt", "Station", "Eingänge je Einheit", "Basispreis", "Einsatzwert"], recipeRows(STAGE3), [6, 3, 8, 3, 3]),
  h2("Schwarzmarkt"),
  p("Schmuggelware entsteht nicht in regulären Rezepten, sondern in illegalen Werkstätten und Laboren an Schmugglerhäfen und Freihäfen mit niedriger Sicherheit:"),
  ...table(["Ware", "Entsteht aus"], [
    ["Gestohlene Technologie", "Diebstahl oder Hacking bei Technologiefirmen"],
    ["Gehackte KI-Kerne", "KI-Kerne in einer illegalen Werkstatt"],
    ["Kampfstimulanzien", "Medikamente in einem illegalen Labor"],
    ["Verbotene Biotech-Waren", "Bioproben in einem illegalen Labor"],
    ["Unregistrierte Waffen", "Bauteile und Verbundstahl in einer illegalen Werkstatt"],
    ["Gefälschte Transitlizenzen", "Elektronik in einer Fälscherwerkstatt"],
  ], [1, 2]),

  // Anhang D
  h1("Anhang D: Vorschläge zur Bestätigung", { breakBefore: true }),
  p("Alle Vorschläge dieses Dokuments mit Nummer. Du kannst sie einzeln beantworten, z. B. „V12: ja“, „V30: nein, stattdessen …“ oder „V1–V20: ja“. Was du bestätigst, wird in der nächsten Fassung zu „Entschieden“."),
  PROPOSALS_PLACEHOLDER,
];

// ---------------------------------------------------------------------------
// Dokument
// ---------------------------------------------------------------------------

function proposalTable() {
  const shorten = (text) => (text.length > 170 ? `${text.slice(0, 167).replace(/\s+\S*$/, "")} …` : text);
  return table(["Nr.", "Abschnitt", "Thema", "Kurzfassung"],
    PROPOSALS.map(({ id, section: where, topic, text }) => [id, where, topic, shorten(text)]), [2, 3, 5, 9]);
}

function resolve(block) {
  if (block === TOC_PLACEHOLDER) {
    return TOC.map((title) => new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: title, font: FONT })] }));
  }
  if (block === PROPOSAL_COUNT_PLACEHOLDER) {
    return [bullet(`Vorschläge V1 bis V${PROPOSALS.length} in Anhang D bestätigen oder ändern.`), new Paragraph({ children: [] })];
  }
  if (block === PROPOSALS_PLACEHOLDER) return proposalTable();
  return [block];
}

const doc = new Document({
  creator: "Legami-Colony-Planung",
  title: "Legami Colony – Spielkonzept",
  description: `Spielkonzept Version ${VERSION}`,
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
      children: [new TextRun({ text: `Legami Colony · Spielkonzept ${VERSION}`, font: FONT, size: 16, color: "808080" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: ["Seite ", PageNumber.CURRENT, " von ", PageNumber.TOTAL_PAGES], font: FONT, size: 16, color: "808080" })] })] }) },
    children: CONTENT.flatMap(resolve),
  }],
});

const out = path.join(__dirname, "legami-colony-spielkonzept.docx");
Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(out, buffer);
  console.log(`geschrieben: ${out} (${PROPOSALS.length} Vorschläge)`);
});
