// Ítem 5.2, parte 2 (A-30): imagen de Docker de la web.
// Se corre con `npm test` (node --test). No necesita Docker: lee el Dockerfile,
// nginx.conf y el .dockerignore como texto y exige lo importante. La prueba real
// (docker build) la corre el dueño.
//
// Lo que se vigila:
// - El Dockerfile viejo (borrado en el 5.1) corría "npm run dev": el servidor de
//   desarrollo, con un proxy a localhost:5000 que dentro del contenedor no es la API.
//   Ahora: dos etapas, Node compila con npm ci + npm run build y nginx sirve dist/.
// - nginx pasa /api a la API (servicio "api", puerto 5000) con X-Forwarded-For,
//   que la API usa para contar el límite de intentos por la IP real.
// - Las rutas de React (/adopcion, /catalogo…) no dan 404 al recargar (try_files).
// - Ningún secreto en la imagen ni en variables VITE_ (se ven en el navegador).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const RAIZ = fileURLToPath(new URL("..", import.meta.url));
const leer = (nombre) => readFileSync(join(RAIZ, nombre), "utf8");

// Líneas útiles, sin comentarios ni líneas vacías (los comentarios pueden
// mencionar "npm run dev" para explicar por qué NO se usa).
function lineasSinComentarios(texto) {
  return texto
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter((l) => l && !l.startsWith("#"));
}

// Instrucciones del Dockerfile agrupadas por etapa (cada FROM abre una).
function etapasDelDockerfile() {
  const etapas = [];
  for (const linea of lineasSinComentarios(leer("Dockerfile"))) {
    if (/^FROM\s/i.test(linea)) etapas.push([]);
    assert.ok(etapas.length > 0, `instrucción antes del primer FROM: ${linea}`);
    etapas.at(-1).push(linea);
  }
  return etapas;
}

const nginx = () => lineasSinComentarios(leer("nginx.conf")).join("\n");

// Contenido de un bloque "location <ruta> { ... }" de nginx.conf (sin anidar).
function bloqueLocation(ruta) {
  const escapada = ruta.replace(/[.*+?^${}()|[\]\\/]/g, "\\$&");
  const m = nginx().match(new RegExp(`location\\s+${escapada}\\s*\\{([^}]*)\\}`));
  assert.ok(m, `nginx.conf no tiene "location ${ruta} { ... }"`);
  return m[1];
}

test("el Dockerfile tiene dos etapas: node:24-alpine y luego nginx 1.30.6-alpine", () => {
  const etapas = etapasDelDockerfile();
  assert.equal(etapas.length, 2, "deben ser exactamente dos FROM");
  assert.match(etapas[0][0], /^FROM\s+node:24-alpine\s+AS\s+compilacion$/i);
  // Versión exacta: ni "nginx", ni "nginx:latest", ni "nginx:alpine"
  assert.match(etapas[1][0], /^FROM\s+nginx:1\.30\.6-alpine$/i);
});

test("la etapa de Node instala con npm ci y compila con npm run build", () => {
  const [compilacion] = etapasDelDockerfile();
  const runs = compilacion.filter((l) => /^RUN\s/i.test(l));
  assert.ok(runs.some((l) => /\bnpm ci\b/.test(l)), "falta RUN npm ci");
  assert.ok(runs.some((l) => /\bnpm run build\b/.test(l)), "falta RUN npm run build");
  // npm install puede cambiar versiones; npm ci respeta el package-lock.json
  assert.ok(!runs.some((l) => /\bnpm (install|i)\b/.test(l)), "usar npm ci, no npm install");
  // El lockfile se copia antes de npm ci (si no, npm ci falla)
  const iCopiaLock = compilacion.findIndex((l) => /^COPY\s.*package-lock\.json/i.test(l));
  const iNpmCi = compilacion.findIndex((l) => /\bnpm ci\b/.test(l));
  assert.ok(iCopiaLock !== -1 && iCopiaLock < iNpmCi, "copiar package-lock.json antes de npm ci");
});

test("nada en el Dockerfile arranca el servidor de desarrollo", () => {
  const texto = lineasSinComentarios(leer("Dockerfile")).join("\n");
  assert.doesNotMatch(texto, /npm\s+run\s+dev|npm\s+start|\bvite(\s+(dev|preview))?\s*["\]]?$/m);
  assert.doesNotMatch(texto, /^(CMD|ENTRYPOINT)\s.*\b(npm|node|vite)\b/im);
});

test("la imagen final solo trae dist/ y la configuración de nginx", () => {
  const [, final] = etapasDelDockerfile();
  const copias = final.filter((l) => /^COPY\s/i.test(l));
  assert.deepEqual(copias.sort(), [
    "COPY --from=compilacion /app/dist /usr/share/nginx/html",
    "COPY nginx.conf /etc/nginx/conf.d/default.conf",
  ]);
  // Ni Node ni el código fuente en la imagen final
  assert.ok(!final.some((l) => /^RUN\s.*\bnpm\b/i.test(l)), "la etapa final no corre npm");
});

test("sin secretos: ningún ENV o ARG con claves en el Dockerfile", () => {
  const variables = lineasSinComentarios(leer("Dockerfile")).filter((l) =>
    /^(ENV|ARG)\s/i.test(l),
  );
  const sospechosas = variables.filter((l) =>
    /SECRET|KEY|PASS|TOKEN|CLAVE|JWT|FERNET|VITE_/i.test(l),
  );
  assert.deepEqual(sospechosas, []);
});

test("sin secretos: ninguna variable VITE_ con nombre de clave en src/", () => {
  const archivos = (carpeta) =>
    readdirSync(carpeta, { withFileTypes: true }).flatMap((e) => {
      const ruta = join(carpeta, e.name);
      if (e.isDirectory()) return archivos(ruta);
      return /\.(js|jsx)$/.test(e.name) ? [ruta] : [];
    });
  const VITE_SECRETA = /VITE_\w*(SECRET|KEY|PASS|TOKEN|CLAVE|JWT|FERNET)/i;
  const culpables = archivos(join(RAIZ, "src")).filter((ruta) =>
    VITE_SECRETA.test(readFileSync(ruta, "utf8")),
  );
  assert.deepEqual(culpables, []);
});

test("nginx pasa /api/ a la API (servicio api, puerto 5000) sin recortar la ruta", () => {
  const api = bloqueLocation("/api/");
  // Sin barra ni ruta al final: /api/mascotas llega como /api/mascotas
  assert.match(api, /^\s*proxy_pass\s+http:\/\/api:5000;\s*$/m);
});

test("nginx agrega la IP real al final de X-Forwarded-For", () => {
  const api = bloqueLocation("/api/");
  // $proxy_add_x_forwarded_for AGREGA $remote_addr: la última IP la pone nginx
  // y el usuario no la puede falsificar (la API toma la última con PROXY_CONFIABLE=1).
  assert.match(api, /proxy_set_header\s+X-Forwarded-For\s+\$proxy_add_x_forwarded_for;/);
  // Si nginx usara $http_x_forwarded_for, pasaría el encabezado tal cual llegó
  assert.doesNotMatch(api, /X-Forwarded-For\s+\$http_x_forwarded_for/);
});

test("las rutas de React caen en index.html (try_files)", () => {
  const raiz = bloqueLocation("/");
  assert.match(raiz, /try_files\s+\$uri\b[^;]*\s\/index\.html;/);
});

test("nginx no muestra su versión y sirve dist/", () => {
  const conf = nginx();
  assert.match(conf, /server_tokens\s+off;/);
  assert.match(conf, /root\s+\/usr\/share\/nginx\/html;/);
  assert.match(conf, /listen\s+80;/);
});

test("el .dockerignore deja pasar lo que el Dockerfile copia", () => {
  // Reglas activas del .dockerignore de la web (sin comentarios ni vacías)
  const reglas = lineasSinComentarios(leer(".dockerignore"));
  for (const necesario of ["nginx.conf", "package.json", "package-lock.json", "src", "index.html"]) {
    assert.ok(
      !reglas.some((r) => r.replace(/^\*\*\//, "") === necesario),
      `${necesario} está excluido en el .dockerignore y el Dockerfile lo necesita`,
    );
  }
  // Y sigue dejando fuera lo que no debe entrar (5.1)
  for (const fuera of ["**/.env", "**/node_modules", "dist"]) {
    assert.ok(reglas.includes(fuera), `falta "${fuera}" en el .dockerignore`);
  }
});
