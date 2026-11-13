// Hook PreToolUse: impide que Claude lea, edite o muestre archivos de secretos
// (.env, api.env, llaves, certificados) y que escriba credenciales "quemadas" en el código.
// Recibe por stdin el JSON de la herramienta que Claude va a usar.
//
// Ítem 6.9 (A-40): antes bastaba con que el texto ".env" apareciera en un comando que
// tuviera grep, cat, etc., así que una búsqueda como  grep -n "\.env" .gitignore  se
// bloqueaba sin abrir ningún secreto. Ahora el comando se parte en palabras y, en los
// comandos de búsqueda (grep, rg, git grep, findstr, Select-String), se aparta SOLO el
// patrón que se busca. Todo lo demás se revisa igual o más estricto que antes.
// Prueba: node --test .claude/hooks/   (proteger-secretos.test.js, sin dependencias)
const fs = require("fs");

let entrada = {};
try {
  entrada = JSON.parse(fs.readFileSync(0, "utf8") || "{}");
} catch {
  process.exit(0); // entrada ilegible: no bloquear el trabajo
}
const herramienta = entrada.tool_name || "";
const datos = entrada.tool_input || {};

// ---------------------------------------------------------------------------
// 1. ¿Qué nombre de archivo es un secreto?
// ---------------------------------------------------------------------------
// Secretos: .env, .env.local, .env.production..., nombre.env (docker/api.env, docker/bd.env)
// y llaves o certificados. Las plantillas que terminan en ".example" sí se pueden leer.
const LLAVE = /\.(pem|key|p12|pfx|jks|keystore|p8)$/i;
const NOMBRES_DE_MUESTRA = [
  ".env", ".env.local", ".env.production", "api.env", "bd.env",
  "a.pem", "a.key", "a.p12", "a.pfx", "a.jks", "a.keystore", "a.p8",
];

function nombreBase(ruta) {
  return String(ruta).split(/[\\/]/).pop();
}

function esNombreSecreto(nombre) {
  const n = String(nombre).toLowerCase();
  if (!n || n.endsWith(".example")) return false;
  return /^\.env(\..+)?$/.test(n) || /^.+\.env$/.test(n) || LLAVE.test(n);
}

// Un comodín (.env*, *.env, *.{env,js}, *.pem) es secreto si podría alcanzar un archivo
// de secretos. Un "*" suelto o "*.js" no cuentan: no nombran nada de secretos.
function esComodinSecreto(nombre) {
  if (!/[*?[{]/.test(nombre)) return false;
  if (!/env|pem|key|p12|pfx|jks|keystore|p8/i.test(nombre)) return false;
  try {
    const fuente = nombre
      .replace(/[.+^$()|\\]/g, "\\$&")
      .replace(/\*/g, ".*")
      .replace(/\?/g, ".")
      .replace(/\{/g, "(?:")
      .replace(/\}/g, ")")
      .replace(/,/g, "|");
    const regex = new RegExp("^" + fuente + "$", "i");
    return NOMBRES_DE_MUESTRA.some((m) => regex.test(m));
  } catch {
    return true; // comodín raro que no se entiende: mejor bloquear
  }
}

function esRutaSecreta(ruta) {
  const nombre = nombreBase(ruta);
  return esNombreSecreto(nombre) || esComodinSecreto(nombre);
}

// Una palabra de un comando puede traer la ruta pegada a otras cosas:
// $f='.env'  archivo=@.env  open('.env')  -Path:.env  <.env
const SEPARADORES = /[\s'"`=@<>();|&:$]+/;
function nombraSecreto(palabra) {
  return palabra.split(SEPARADORES).some(esRutaSecreta);
}

// ---------------------------------------------------------------------------
// 2. Partir un comando en tramos y palabras
// ---------------------------------------------------------------------------
// Los tramos se separan con | ; & o salto de línea (fuera de comillas). Las comillas se
// quitan. La barra invertida se deja tal cual porque en Windows separa carpetas.
function partirComando(comando) {
  const tramos = [[]];
  let palabra = null; // null = no hay una palabra abierta
  let comilla = null;
  const cerrarPalabra = () => {
    if (palabra !== null) tramos[tramos.length - 1].push(palabra);
    palabra = null;
  };
  for (const c of String(comando)) {
    if (comilla) {
      if (c === comilla) comilla = null;
      else palabra += c;
    } else if (c === '"' || c === "'") {
      comilla = c;
      if (palabra === null) palabra = "";
    } else if ("|;&\n\r".includes(c)) {
      cerrarPalabra();
      if (tramos[tramos.length - 1].length) tramos.push([]);
    } else if (/\s/.test(c)) {
      cerrarPalabra();
    } else {
      palabra = (palabra === null ? "" : palabra) + c;
    }
  }
  cerrarPalabra();
  return tramos.filter((t) => t.length);
}

// Nombre del programa: sin "(", "$(", "&" al inicio, sin carpeta, sin ".exe", en minúsculas.
function programa(palabra) {
  return nombreBase(String(palabra).replace(/^[({$&!@]+/, "")).toLowerCase().replace(/\.exe$/, "");
}

const BUSCADORES = new Set(["grep", "egrep", "fgrep", "rg", "findstr", "select-string", "sls"]);
const PREFIJOS = new Set(["sudo", "xargs", "command", "time", "nohup", "env"]);

// Opciones que llevan un valor aparte. Ese valor NO es el patrón: se sigue revisando
// (por ejemplo  rg -g "*.env"  o  grep -f .env  sí leen secretos).
const CON_VALOR = {
  grep: ["-e", "--regexp", "-f", "--file", "-m", "--max-count", "-A", "--after-context",
    "-B", "--before-context", "-C", "--context", "-d", "--directories", "-D", "--devices",
    "--include", "--exclude", "--exclude-dir", "--exclude-from", "--label"],
  rg: ["-e", "--regexp", "-f", "--file", "-g", "--glob", "--iglob", "-t", "--type", "-T",
    "--type-not", "--type-add", "-m", "--max-count", "-A", "--after-context", "-B",
    "--before-context", "-C", "--context", "-M", "--max-columns", "-j", "--threads", "-r",
    "--replace", "-d", "--max-depth", "--pre", "--pre-glob", "--ignore-file", "-E",
    "--encoding", "--sort", "--sortr", "--color", "--colors", "--path-separator",
    "--context-separator", "--field-match-separator"],
  "git grep": ["-e", "-f", "-A", "--after-context", "-B", "--before-context", "-C",
    "--context", "-m", "--max-count", "--max-depth", "--threads"],
};
const SWITCHES_SELECT_STRING = new Set(["-casesensitive", "-simplematch", "-notmatch",
  "-allmatches", "-list", "-quiet", "-raw", "-noemphasis"]);

// Devuelve las palabras del tramo que hay que revisar: todas menos el patrón de búsqueda.
function palabrasARevisar(tramo) {
  // Buscar el programa del tramo, saltando prefijos (sudo, xargs -0...) y asignaciones.
  let i = 0;
  let soloPrefijos = true;
  while (i < tramo.length) {
    const p = programa(tramo[i]);
    if (PREFIJOS.has(p) || /^\w+=/.test(tramo[i]) || (soloPrefijos && i > 0 && tramo[i].startsWith("-"))) {
      i++;
      continue;
    }
    soloPrefijos = false;
    break;
  }
  if (i >= tramo.length) return tramo;
  let tipo = programa(tramo[i]);
  let inicio = i + 1;
  if (tipo === "git" && programa(tramo[i + 1] || "") === "grep") {
    tipo = "git grep";
    inicio = i + 2;
  }
  if (!BUSCADORES.has(tipo) && tipo !== "git grep") return tramo;
  if (["egrep", "fgrep"].includes(tipo)) tipo = "grep";
  if (tipo === "sls") tipo = "select-string";

  const revisar = tramo.slice(0, inicio);
  const args = tramo.slice(inicio);
  let patronVisto = false;
  let soloRutas = false;

  for (let k = 0; k < args.length; k++) {
    const a = args[k];

    if (tipo === "select-string") {
      const opcion = a.toLowerCase();
      if (opcion === "-pattern") { patronVisto = true; k++; continue; } // se aparta el patrón
      if (opcion.startsWith("-")) {
        revisar.push(a);
        if (!SWITCHES_SELECT_STRING.has(opcion) && k + 1 < args.length) revisar.push(args[++k]);
        continue;
      }
      if (!patronVisto) { patronVisto = true; continue; } // primer posicional = patrón
      revisar.push(a);
      continue;
    }

    if (tipo === "findstr") {
      if (/^\/c:/i.test(a)) { patronVisto = true; continue; } // /c:"texto" es el patrón
      if (a.startsWith("/")) { revisar.push(a); continue; } // /g:archivo, /s, /n...
      if (!patronVisto) { patronVisto = true; continue; }
      revisar.push(a);
      continue;
    }

    // grep, rg y git grep
    if (soloRutas) { revisar.push(a); continue; }
    if (a === "--") {
      if (tipo === "git grep" || patronVisto) soloRutas = true;
      else if (k + 1 < args.length) { patronVisto = true; k++; soloRutas = true; }
      continue;
    }
    if (a.startsWith("--")) {
      const [nombre, valor] = a.split(/=(.*)/s);
      const esPatron = nombre === "--regexp";
      if (esPatron) patronVisto = true;
      if (valor !== undefined) { if (!esPatron) revisar.push(a); continue; }
      if (!esPatron) revisar.push(a);
      if (CON_VALOR[tipo].includes(nombre) && k + 1 < args.length) {
        k++;
        if (!esPatron) revisar.push(args[k]);
      }
      continue;
    }
    if (a.startsWith("-") && a.length > 1) {
      // Grupo de opciones cortas: -rn, -rne PATRON, -A3, -eFOO, -g*.env
      revisar.push(a);
      for (let j = 1; j < a.length; j++) {
        const corta = "-" + a[j];
        if (!CON_VALOR[tipo].includes(corta)) continue;
        const pegado = a.slice(j + 1);
        if (corta === "-e") {
          patronVisto = true;
          if (pegado) revisar.pop(); // el patrón venía pegado: se aparta toda la palabra
          else k++; // el patrón es la palabra siguiente: se salta
        } else if (!pegado && k + 1 < args.length) {
          revisar.push(args[++k]);
        }
        break;
      }
      continue;
    }
    if (!patronVisto) { patronVisto = true; continue; } // primer posicional = patrón
    revisar.push(a);
  }
  return revisar;
}

// Programas que leen, muestran, copian, mueven o envían el contenido de un archivo.
const LEE_O_COPIA = new RegExp("\\b(" + [
  "cat", "type", "more", "less", "head", "tail", "Get-Content", "gc", "sed", "awk",
  "grep", "egrep", "fgrep", "rg", "findstr", "Select-String", "sls",
  "cp", "copy", "Copy-Item", "xcopy", "robocopy", "scp", "rsync", "mv", "move", "Move-Item",
  "curl", "wget", "Invoke-WebRequest", "iwr", "Invoke-RestMethod", "irm",
  "tee", "xxd", "od", "strings", "base64", "certutil", "nl", "tac", "cut", "sort", "uniq",
  "diff", "cmp", "comm", "fc", "iconv", "tar", "zip", "7z", "Compress-Archive", "Format-Hex",
  "python", "python3", "py", "node", "deno", "bun", "ruby", "perl", "php",
  "bash", "sh", "pwsh", "powershell", "cmd",
  "ReadAllText", "ReadAllLines", "ReadAllBytes", "OpenRead", "OpenText", "StreamReader",
  "Import-Csv", "ConvertFrom-StringData",
].join("|") + ")\\b", "i");
const REDIRIGE_ENTRADA = /<(?![<=])/; // more < .env

// ---------------------------------------------------------------------------
// 3. Decisiones
// ---------------------------------------------------------------------------
// Patrones de credenciales escritas directamente en el código
const CREDENCIAL_QUEMADA = [
  /(password|passwd|contrasena|clave|secret|token|api_?key|jwt_secret|fernet_key)\s*[:=]\s*["'][^"'\s]{8,}["']/i,
  /-----BEGIN (RSA |EC )?PRIVATE KEY-----/,
  /["'][a-z]{4} [a-z]{4} [a-z]{4} [a-z]{4}["']/, // contraseña de aplicación de Gmail
];

function responder(decision, motivo) {
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: decision,
      permissionDecisionReason: motivo,
    },
  }));
  process.exit(0);
}

if (["Read", "Edit", "Write", "NotebookEdit"].includes(herramienta)) {
  const ruta = datos.file_path || datos.notebook_path || "";
  if (esRutaSecreta(ruta)) {
    responder("deny", `Regla de PetConnect: no se leen ni editan archivos de secretos (${ruta}). Usa .env.example para ver qué variables existen.`);
  }
}

if (herramienta === "Grep") {
  // La herramienta Grep de Claude también puede mostrar el contenido de un archivo.
  const ruta = datos.path || "";
  const comodin = datos.glob || "";
  if ((ruta && esRutaSecreta(ruta)) || (comodin && comodin.split(/\s+/).some(esRutaSecreta))) {
    responder("deny", "Regla de PetConnect: no se busca dentro de archivos .env ni de llaves. Usa .env.example para ver qué variables existen.");
  }
}

if (herramienta === "Bash" || herramienta === "PowerShell") {
  const comando = datos.command || "";
  const tramos = partirComando(comando);
  const nombraUnSecreto = tramos.some((t) => palabrasARevisar(t).some(nombraSecreto));
  if (nombraUnSecreto && (LEE_O_COPIA.test(comando) || REDIRIGE_ENTRADA.test(comando))) {
    responder("deny", "Regla de PetConnect: no se muestra ni copia el contenido de archivos .env o llaves desde la terminal.");
  }
  const agregaSecreto = tramos.some((t) => {
    const i = t.findIndex((p, k) => programa(p) === "git" && programa(t[k + 1] || "") === "add");
    return i >= 0 && t.slice(i + 2).some(nombraSecreto);
  });
  if (agregaSecreto || /\bgit\s+add\s+(-f|--force)\b/i.test(comando)) {
    responder("deny", "Regla de PetConnect: no se agregan a git archivos .env ni se fuerza 'git add -f' sobre archivos ignorados.");
  }
}

if (herramienta === "Write" || herramienta === "Edit") {
  const ruta = datos.file_path || "";
  const texto = datos.content || datos.new_string || "";
  const esPlantillaOPrueba = /\.env\.example$|[\\/]tests?[\\/]|\.test\.|\.md$/i.test(ruta);
  if (!esPlantillaOPrueba && CREDENCIAL_QUEMADA.some((p) => p.test(texto))) {
    responder("ask", "Parece que se va a escribir una contraseña o clave directamente en el código. En PetConnect los secretos van en .env. ¿Seguro que es un valor de ejemplo?");
  }
}

process.exit(0);
