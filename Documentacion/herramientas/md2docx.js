// Convierte un documento Markdown del proyecto (plan de pruebas, guías) a .docx con formato APA 7.
// Requiere el paquete npm "docx" (v9). Uso:
//   node md2docx.js entrada.md salida.docx "Título del documento"
// Marcas soportadas: # título de portada (hasta ---), ## / ### / #### títulos de nivel 1 a 3,
// tablas, bloques de código, listas numeradas y con viñetas, **Tabla N** / **Figura N** con su
// título en cursiva, *Nota.*, imágenes ![alt](archivo.png), \pagebreak y la sección "Referencias".
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType,
  AlignmentType, BorderStyle, ShadingType, PageOrientation, Header, PageNumber,
  LevelFormat, TableLayoutType, ImageRun,
} = require("docx");

const ancho_max = (dxa) => Math.floor(dxa / 15); // 1 px = 15 DXA a 96 ppp
const [, , entrada, salida, tituloDoc] = process.argv;
const lineas = fs.readFileSync(entrada, "utf8").split(/\r?\n/);

// ---------- Análisis del Markdown en bloques ----------
const bloques = [];
let enPortada = false;
let enReferencias = false;
for (let i = 0; i < lineas.length; i++) {
  const t = lineas[i].trim();
  if (t === "" || t === "<br>" || t.startsWith(">")) continue;
  if (t.startsWith("```")) {
    const codigo = [];
    for (i++; i < lineas.length && !lineas[i].trim().startsWith("```"); i++) codigo.push(lineas[i]);
    bloques.push({ tipo: "codigo", lineas: codigo });
    continue;
  }
  if (t.startsWith("# ")) { bloques.push({ tipo: "titulo", texto: t.slice(2) }); enPortada = true; continue; }
  if (t === "---") { bloques.push({ tipo: "salto" }); enPortada = false; continue; }
  if (t === "\\pagebreak") { bloques.push({ tipo: "salto" }); continue; }
  if (enPortada) { bloques.push({ tipo: "portada", texto: t }); continue; }
  const h = t.match(/^(#{2,4}) (.*)$/);
  if (h) {
    const nivel = h[1].length - 1;
    enReferencias = nivel === 1 && h[2] === "Referencias";
    bloques.push({ tipo: "h" + nivel, texto: h[2], salto: enReferencias });
    continue;
  }
  if (t.startsWith("|")) {
    const filas = [];
    for (; i < lineas.length && lineas[i].trim().startsWith("|"); i++) filas.push(dividirFila(lineas[i]));
    i--;
    bloques.push({ tipo: "tabla", encabezado: filas[0], filas: filas.slice(2) });
    continue;
  }
  if (/^\d+\. /.test(t)) {
    const items = [];
    for (; i < lineas.length && /^\d+\. /.test(lineas[i].trim()); i++) items.push(lineas[i].trim().replace(/^\d+\. /, ""));
    i--;
    bloques.push({ tipo: "lista", items });
    continue;
  }
  const img = t.match(/^!\[(.*)\]\((.+)\)$/);
  if (img) { bloques.push({ tipo: "imagen", alt: img[1], ruta: img[2] }); continue; }
  if (/^- /.test(t)) {
    const items = [];
    for (; i < lineas.length && /^- /.test(lineas[i].trim()); i++) items.push(lineas[i].trim().slice(2));
    i--;
    bloques.push({ tipo: "vinetas", items });
    continue;
  }
  if (/^\*\*(Tabla|Figura) \d+\*\*$/.test(t)) { bloques.push({ tipo: "rotulo", texto: t }); continue; }
  const previo = bloques[bloques.length - 1];
  if (previo && previo.tipo === "rotulo" && /^\*[^*].*\*$/.test(t)) { bloques.push({ tipo: "tituloTabla", texto: t }); continue; }
  if (t.startsWith("*Nota.*")) { bloques.push({ tipo: "nota", texto: t }); continue; }
  bloques.push({ tipo: enReferencias ? "referencia" : "parrafo", texto: t });
}

function dividirFila(linea) {
  const s = linea.trim().replace(/^\|/, "").replace(/\|$/, "");
  const celdas = [];
  let actual = "", enCodigo = false;
  for (const c of s) {
    if (c === "`") enCodigo = !enCodigo;
    if (c === "|" && !enCodigo) { celdas.push(actual.trim()); actual = ""; } else actual += c;
  }
  celdas.push(actual.trim());
  return celdas;
}

// ---------- Texto con formato en línea (**negrita**, *cursiva*, `código`) ----------
function runs(texto, base = {}) {
  const res = [];
  const re = /(\*\*[^*]+?\*\*|`[^`]+`|\*[^*\s][^*]*?\*)/g;
  let ultimo = 0, m;
  while ((m = re.exec(texto))) {
    if (m.index > ultimo) res.push(new TextRun({ text: texto.slice(ultimo, m.index), ...base }));
    const tok = m[0];
    if (tok.startsWith("**")) res.push(...runs(tok.slice(2, -2), { ...base, bold: true }));
    else if (tok.startsWith("`")) res.push(new TextRun({ text: tok.slice(1, -1), ...base, font: "Consolas", size: (base.size || 24) - 2 }));
    else res.push(...runs(tok.slice(1, -1), { ...base, italics: true }));
    ultimo = re.lastIndex;
  }
  if (ultimo < texto.length) res.push(new TextRun({ text: texto.slice(ultimo), ...base }));
  return res;
}

// ---------- Tablas con estilo APA (solo bordes horizontales) ----------
const ANCHO_VERTICAL = 9360;    // 6,5" útiles en carta vertical
const ANCHO_HORIZONTAL = 12960; // 9" útiles en carta horizontal
const linea = (tam, color = "000000") => ({ style: BorderStyle.SINGLE, size: tam, color });
const sinLinea = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };

function anchosColumnas(encabezado, filas, total, dxaPorCaracter) {
  const n = encabezado.length;
  const todas = [encabezado, ...filas];
  const plano = (s) => (s || "").replace(/[*`]/g, "");
  const palabraMasLarga = (textos, tope) => Math.min(Math.max(0, ...textos.flatMap((c) => c.split(/\s+/)).map((w) => w.length)), tope);
  const peso = [], minimo = [];
  for (let j = 0; j < n; j++) {
    const textos = todas.map((f) => plano(f[j]));
    const cuerpo = filas.map((f) => plano(f[j]));
    const prom = textos.reduce((a, c) => a + c.length, 0) / textos.length;
    const max = Math.max(...textos.map((c) => c.length));
    peso.push(Math.max(Math.min(prom * 0.7 + max * 0.3, 90), 3));
    // El encabezado puede partirse en dos líneas; el cuerpo no debería cortar palabras cortas
    const largo = Math.max(palabraMasLarga(cuerpo, 12), palabraMasLarga([plano(encabezado[j])], 9));
    minimo.push(largo * dxaPorCaracter + 260);
  }
  const sumaMinimos = minimo.reduce((a, b) => a + b, 0);
  if (sumaMinimos > total * 0.85) for (let j = 0; j < n; j++) minimo[j] = Math.floor((minimo[j] * total * 0.85) / sumaMinimos);
  let anchos = new Array(n).fill(0);
  const fijos = new Array(n).fill(false);
  for (let iter = 0; iter < n; iter++) {
    const libre = total - anchos.reduce((a, w, j) => a + (fijos[j] ? w : 0), 0);
    const pesoLibre = peso.reduce((a, p, j) => a + (fijos[j] ? 0 : p), 0);
    let cambio = false;
    for (let j = 0; j < n; j++) {
      if (fijos[j]) continue;
      anchos[j] = (peso[j] / pesoLibre) * libre;
      if (anchos[j] < minimo[j]) { anchos[j] = minimo[j]; fijos[j] = true; cambio = true; }
    }
    if (!cambio) break;
  }
  anchos = anchos.map(Math.round);
  anchos[n - 1] += total - anchos.reduce((a, b) => a + b, 0);
  return anchos;
}

function construirTabla(bloque, total) {
  const tam = bloque.encabezado.length >= 6 ? 18 : 20; // 9 pt o 10 pt
  const anchos = anchosColumnas(bloque.encabezado, bloque.filas, total, tam === 18 ? 110 : 120);
  const celda = (texto, j, esEncabezado) => new TableCell({
    width: { size: anchos[j], type: WidthType.DXA },
    margins: { top: 50, bottom: 50, left: 90, right: 90 },
    borders: esEncabezado ? { top: linea(8), bottom: linea(8), left: sinLinea, right: sinLinea } : undefined,
    children: [new Paragraph({ spacing: { line: 240, before: 0, after: 0 }, children: runs(texto || "", { size: tam, bold: esEncabezado || undefined }) })],
  });
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: anchos,
    layout: TableLayoutType.FIXED,
    borders: { top: linea(8), bottom: linea(8), left: sinLinea, right: sinLinea, insideHorizontal: linea(4, "BFBFBF"), insideVertical: sinLinea },
    rows: [
      new TableRow({ tableHeader: true, cantSplit: true, children: bloque.encabezado.map((c, j) => celda(c, j, true)) }),
      ...bloque.filas.map((f) => new TableRow({ cantSplit: true, children: bloque.encabezado.map((_, j) => celda(f[j], j, false)) })),
    ],
  });
}

// ---------- Conversión de bloques a elementos ----------
let instanciaLista = 0;
function aElementos(b, ancho) {
  switch (b.tipo) {
    case "titulo":
      return [...[1, 2, 3].map(() => new Paragraph({ children: [] })),
        new Paragraph({ alignment: AlignmentType.CENTER, children: runs(b.texto, { bold: true }) }),
        new Paragraph({ children: [] })];
    case "portada":
      return [new Paragraph({ alignment: AlignmentType.CENTER, children: runs(b.texto) })];
    case "salto":
      return [new Paragraph({ pageBreakBefore: true, spacing: { line: 240 }, children: [] })];
    case "h1":
      return [new Paragraph({ heading: "Heading1", pageBreakBefore: b.salto || undefined, children: runs(b.texto) })];
    case "h2":
      return [new Paragraph({ heading: "Heading2", children: runs(b.texto) })];
    case "h3":
      return [new Paragraph({ heading: "Heading3", children: runs(b.texto) })];
    case "rotulo":
      return [new Paragraph({ keepNext: true, spacing: { before: 240 }, children: runs(b.texto) })];
    case "tituloTabla":
      return [new Paragraph({ keepNext: true, children: runs(b.texto) })];
    case "nota":
      return [new Paragraph({ spacing: { line: 240, before: 120, after: 240 }, children: runs(b.texto, { size: 20 }) })];
    case "referencia":
      return [new Paragraph({ indent: { left: 720, hanging: 720 }, children: runs(b.texto) })];
    case "lista": {
      const inst = ++instanciaLista;
      return b.items.map((it) => new Paragraph({ numbering: { reference: "lista-num", level: 0, instance: inst }, children: runs(it) }));
    }
    case "imagen": {
      const datos = fs.readFileSync(path.resolve(path.dirname(entrada), b.ruta));
      const w0 = datos.readUInt32BE(16), h0 = datos.readUInt32BE(20);
      const anchoImg = Math.min(600, ancho_max(ancho)), altoImg = Math.round((anchoImg * h0) / w0);
      return [new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { line: 240, before: 120, after: 60 },
        children: [new ImageRun({ type: "png", data: datos, transformation: { width: anchoImg, height: altoImg },
                                  altText: { title: b.alt, description: b.alt, name: b.alt } })],
      })];
    }
    case "vinetas":
      return b.items.map((it) => new Paragraph({ numbering: { reference: "vinetas", level: 0 }, children: runs(it) }));
    case "codigo":
      return b.lineas.map((ln, k) => new Paragraph({
        spacing: { line: 240, before: k === 0 ? 60 : 0, after: k === b.lineas.length - 1 ? 60 : 0 },
        shading: { type: ShadingType.CLEAR, color: "auto", fill: "F2F2F2" },
        children: [new TextRun({ text: ln.length ? ln : " ", font: "Consolas", size: 17 })],
      }));
    case "tabla":
      return [construirTabla(b, ancho)];
    default:
      return [new Paragraph({ indent: { firstLine: 720 }, children: runs(b.texto) })];
  }
}

// ---------- Secciones: las tablas de 7 o más columnas van en página horizontal ----------
const esAncha = (b) => b && b.tipo === "tabla" && b.encabezado.length >= 7;
const secciones = [];
let actual = [];
const cerrar = (horizontal) => { if (actual.length) secciones.push({ horizontal, bloques: actual }); actual = []; };

for (let k = 0; k < bloques.length; k++) {
  const b = bloques[k];
  if (!esAncha(b)) { actual.push(b); continue; }
  // Lleva a la página horizontal el rótulo, el título y, si las hay, la introducción inmediata (título + párrafo)
  const arrastre = [];
  while (actual.length && ["rotulo", "tituloTabla"].includes(actual[actual.length - 1].tipo)) arrastre.unshift(actual.pop());
  if (actual.length >= 2 && actual[actual.length - 1].tipo === "parrafo" && /^h\d$/.test(actual[actual.length - 2].tipo)) {
    arrastre.unshift(actual.pop()); arrastre.unshift(actual.pop());
  }
  cerrar(false);
  actual = [...arrastre, b];
  if (bloques[k + 1] && bloques[k + 1].tipo === "nota") actual.push(bloques[++k]);
  // Si a continuación viene otra tabla ancha con solo una introducción breve de por medio, comparte la página horizontal
  for (;;) {
    let j = k + 1;
    while (j < bloques.length && j - k <= 4 && !esAncha(bloques[j]) && ["h1", "h2", "h3", "parrafo", "rotulo", "tituloTabla"].includes(bloques[j].tipo)) j++;
    if (!esAncha(bloques[j])) break;
    for (let x = k + 1; x <= j; x++) actual.push(bloques[x]);
    k = j;
    if (bloques[k + 1] && bloques[k + 1].tipo === "nota") actual.push(bloques[++k]);
  }
  cerrar(true);
}
cerrar(false);

// Separación después de las tablas que no llevan nota
const conEspaciado = (lista, ancho) => lista.flatMap((b, idx) => {
  const els = aElementos(b, ancho);
  const sig = lista[idx + 1];
  if (b.tipo === "tabla" && (!sig || sig.tipo !== "nota")) els.push(new Paragraph({ spacing: { line: 240 }, children: [] }));
  return els;
});

const encabezado = () => ({
  default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ children: [PageNumber.CURRENT] })] })] }),
});

const doc = new Document({
  creator: "Equipo PetConnect – ADSO 3235905",
  title: tituloDoc,
  styles: {
    default: { document: { run: { font: "Times New Roman", size: 24 }, paragraph: { spacing: { line: 480, before: 0, after: 0 } } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Times New Roman", size: 24, bold: true, color: "000000" },
        paragraph: { alignment: AlignmentType.CENTER, keepNext: true, outlineLevel: 0, spacing: { line: 480, before: 0, after: 0 } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Times New Roman", size: 24, bold: true, color: "000000" },
        paragraph: { alignment: AlignmentType.LEFT, keepNext: true, outlineLevel: 1, spacing: { line: 480, before: 0, after: 0 } } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Times New Roman", size: 24, bold: true, italics: true, color: "000000" },
        paragraph: { alignment: AlignmentType.LEFT, keepNext: true, outlineLevel: 2, spacing: { line: 480, before: 0, after: 0 } } },
    ],
  },
  numbering: {
    config: [
      { reference: "lista-num", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "vinetas", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ],
  },
  sections: secciones.map((s) => ({
    properties: {
      page: {
        size: { width: 12240, height: 15840, orientation: s.horizontal ? PageOrientation.LANDSCAPE : PageOrientation.PORTRAIT },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440, header: 720 },
      },
    },
    headers: encabezado(),
    children: conEspaciado(s.bloques, s.horizontal ? ANCHO_HORIZONTAL : ANCHO_VERTICAL),
  })),
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(salida, buf);
  console.log(`OK: ${salida} | bloques: ${bloques.length} | secciones: ${secciones.length} (${secciones.filter((s) => s.horizontal).length} horizontales) | tablas: ${bloques.filter((b) => b.tipo === "tabla").length}`);
});
