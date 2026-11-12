// Pruebas del ítem 6.4 (A-25): el aviso "X agregado al carrito"
// (src/assets/js/addToCartToast.js). Se corren con `npm test` (node --test, sin
// dependencias nuevas: en Node no hay navegador, así que se usa un `document`
// falso mínimo que solo sabe lo que el aviso necesita).
//
// Antes, el aviso se armaba con innerHTML y el nombre del producto dentro: un
// nombre como "<img src=x onerror=alert(1)>" se convertía en una etiqueta real y
// su código corría en la página (XSS). Ahora el nombre va con textContent y el
// ícono se crea con createElementNS. El `document` falso ANOTA cualquier intento
// de escribir HTML crudo (innerHTML, outerHTML, insertAdjacentHTML).
import { test, beforeEach, afterEach, mock } from "node:test";
import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const SVG_NS = "http://www.w3.org/2000/svg";
const NOMBRE_PELIGROSO = "<img src=x onerror=alert(1)>";

let creados = []; // todos los elementos que pidió el aviso
let htmlCrudo = []; // cada intento de escribir HTML como texto

class ElementoFalso {
  constructor(tagName, namespaceURI = null) {
    this.tagName = tagName;
    this.namespaceURI = namespaceURI;
    this.children = [];
    this.parent = null;
    this.atributos = new Map();
    this.style = { cssText: "" };
    this.escuchas = new Map();
    this._texto = "";
    this._clases = [];
    const clases = this._clases;
    this.classList = {
      add: (c) => {
        if (!clases.includes(c)) clases.push(c);
      },
      remove: (c) => {
        const i = clases.indexOf(c);
        if (i >= 0) clases.splice(i, 1);
      },
      contains: (c) => clases.includes(c),
    };
  }

  set className(valor) {
    this._clases.splice(0, this._clases.length, ...String(valor).split(/\s+/).filter(Boolean));
  }
  get className() {
    return this._clases.join(" ");
  }

  // textContent: guarda letras, nunca crea etiquetas (como el navegador)
  set textContent(valor) {
    this.children = [];
    this._texto = String(valor);
  }
  get textContent() {
    return this._texto + this.children.map((h) => h.textContent).join("");
  }

  set innerHTML(valor) {
    htmlCrudo.push({ en: this.tagName, html: String(valor) });
  }
  set outerHTML(valor) {
    htmlCrudo.push({ en: this.tagName, html: String(valor) });
  }
  insertAdjacentHTML(_posicion, valor) {
    htmlCrudo.push({ en: this.tagName, html: String(valor) });
  }

  setAttribute(nombre, valor) {
    this.atributos.set(nombre, String(valor));
  }
  getAttribute(nombre) {
    return this.atributos.has(nombre) ? this.atributos.get(nombre) : null;
  }
  appendChild(hijo) {
    hijo.parent = this;
    this.children.push(hijo);
    return hijo;
  }
  remove() {
    if (!this.parent) return;
    const hermanos = this.parent.children;
    hermanos.splice(hermanos.indexOf(this), 1);
    this.parent = null;
  }
  addEventListener(tipo, funcion) {
    this.escuchas.set(tipo, funcion);
  }
  disparar(tipo) {
    this.escuchas.get(tipo)?.();
  }
}

function todos(elemento) {
  return elemento.children.flatMap((h) => [h, ...todos(h)]);
}

beforeEach(() => {
  creados = [];
  htmlCrudo = [];
  const body = new ElementoFalso("body");
  globalThis.document = {
    body,
    createElement(tag) {
      const e = new ElementoFalso(tag);
      creados.push(e);
      return e;
    },
    createElementNS(ns, tag) {
      const e = new ElementoFalso(tag, ns);
      creados.push(e);
      return e;
    },
    // Solo entiende ".clase", que es lo que usa el aviso
    querySelector(selector) {
      const clase = selector.replace(/^\./, "");
      return todos(body).find((e) => e.classList.contains(clase)) ?? null;
    },
  };
  mock.timers.enable({ apis: ["setTimeout"] });
});

afterEach(() => {
  mock.timers.reset();
  delete globalThis.document;
});

const { showAddToCartToast } = await import("../src/assets/js/addToCartToast.js");
const avisos = () => document.body.children.filter((e) => e.classList.contains("cart-toast"));

test("un nombre con HTML queda como texto: no crea un <img> ni usa HTML crudo", () => {
  showAddToCartToast(NOMBRE_PELIGROSO);
  const [aviso] = avisos();
  assert.ok(aviso, "no se mostró el aviso");
  const span = aviso.children.find((e) => e.tagName === "span");
  assert.ok(span, "el texto debe ir en un <span> creado con createElement");
  assert.equal(span.textContent, `${NOMBRE_PELIGROSO} agregado al carrito`);
  assert.deepEqual(
    creados.map((e) => e.tagName).filter((t) => t.toLowerCase() === "img"),
    [],
    "no debe crearse ningún <img>",
  );
  assert.deepEqual(htmlCrudo, [], "no debe escribirse HTML crudo");
});

test("con un nombre normal tampoco se usa innerHTML", () => {
  showAddToCartToast("Collar reflectivo"); // producto inventado
  assert.deepEqual(htmlCrudo, []);
  assert.equal(avisos()[0].textContent, "Collar reflectivo agregado al carrito");
});

test("el ícono ✓ es un SVG creado con createElementNS, oculto para lectores; el aviso es role=status", () => {
  showAddToCartToast("Collar reflectivo");
  const [aviso] = avisos();
  assert.equal(aviso.getAttribute("role"), "status");
  const svg = aviso.children.find((e) => e.tagName === "svg");
  assert.ok(svg, "falta el ícono");
  assert.equal(svg.namespaceURI, SVG_NS);
  assert.equal(svg.getAttribute("aria-hidden"), "true");
  assert.equal(svg.getAttribute("viewBox"), "0 0 24 24");
  const [trazo] = svg.children;
  assert.equal(trazo?.tagName, "path");
  assert.equal(trazo.namespaceURI, SVG_NS);
  assert.equal(trazo.getAttribute("d"), "M20 6L9 17l-5-5");
  // Primero el ícono y después el texto, como antes
  assert.deepEqual(aviso.children.map((e) => e.tagName), ["svg", "span"]);
});

test("un aviso nuevo quita el anterior (solo queda uno)", () => {
  showAddToCartToast("Collar reflectivo");
  showAddToCartToast("Cama mediana");
  const lista = avisos();
  assert.equal(lista.length, 1);
  const divs = creados.filter((e) => e.tagName === "div");
  assert.equal(lista[0], divs.at(-1), "debe quedar el último aviso");
});

test("a los 2,5 s pasa a la animación de salida y se quita al terminarla", () => {
  showAddToCartToast("Collar reflectivo");
  const [aviso] = avisos();
  assert.ok(aviso.classList.contains("toast-enter"));
  mock.timers.tick(2499);
  assert.ok(aviso.classList.contains("toast-enter"), "todavía no debe salir");
  mock.timers.tick(1);
  assert.ok(!aviso.classList.contains("toast-enter"));
  assert.ok(aviso.classList.contains("toast-exit"));
  aviso.disparar("animationend");
  assert.equal(avisos().length, 0);
});

// --- Guardia: que no vuelva HTML crudo a ningún archivo de la web ---

const SRC = fileURLToPath(new URL("../src", import.meta.url));
const HTML_CRUDO = /\.innerHTML\b|\.outerHTML\b|insertAdjacentHTML|dangerouslySetInnerHTML|document\.write\(/;

function archivosDeCodigo(carpeta) {
  return readdirSync(carpeta, { withFileTypes: true }).flatMap((e) => {
    const ruta = join(carpeta, e.name);
    if (e.isDirectory()) return archivosDeCodigo(ruta);
    return /\.(js|jsx)$/.test(e.name) ? [ruta] : [];
  });
}

test("ningún archivo de src/ escribe HTML crudo (innerHTML y parecidos)", () => {
  const culpables = archivosDeCodigo(SRC)
    .filter((ruta) => HTML_CRUDO.test(readFileSync(ruta, "utf8")))
    .map((ruta) => relative(SRC, ruta));
  assert.deepEqual(culpables, []);
});
