// Hook PreToolUse: impide que Claude lea, edite o muestre archivos de secretos
// (.env, llaves, certificados) y que escriba credenciales "quemadas" en el código.
// Recibe por stdin el JSON de la herramienta que Claude va a usar.
const fs = require("fs");

let entrada = {};
try {
  entrada = JSON.parse(fs.readFileSync(0, "utf8") || "{}");
} catch {
  process.exit(0); // entrada ilegible: no bloquear el trabajo
}
const herramienta = entrada.tool_name || "";
const datos = entrada.tool_input || {};

// .env, .env.local, .env.production... pero NO .env.example
const ARCHIVO_SECRETO = /(^|[\\/\s"'])\.env(\.(?!example\b)[\w.-]+)?(?=$|[\s"'|;&>)])|\.(pem|key|p12|jks)(?=$|[\s"'|;&>)])/i;

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
  if (ARCHIVO_SECRETO.test(" " + ruta)) {
    responder("deny", `Regla de PetConnect: no se leen ni editan archivos de secretos (${ruta}). Usa .env.example para ver qué variables existen.`);
  }
}

if (herramienta === "Bash" || herramienta === "PowerShell") {
  const comando = datos.command || "";
  const muestraContenido = /\b(cat|type|more|less|head|tail|Get-Content|gc|sed|awk|grep|rg|findstr|Select-String|cp|copy|scp|curl)\b/i;
  if (ARCHIVO_SECRETO.test(" " + comando) && muestraContenido.test(comando)) {
    responder("deny", "Regla de PetConnect: no se muestra ni copia el contenido de archivos .env o llaves desde la terminal.");
  }
  if (/\bgit\s+add\b[^|;&]*\.env(?!\.example)\b/i.test(comando) || /\bgit\s+add\s+(-f|--force)\b/i.test(comando)) {
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
