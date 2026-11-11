// Hook PostToolUse: cuando Claude edita un archivo .js/.jsx del Front web,
// corre oxlint solo sobre ese archivo y le devuelve los avisos a Claude para
// que los corrija en el momento (no bloquea, solo informa).
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

let entrada = {};
try {
  entrada = JSON.parse(fs.readFileSync(0, "utf8") || "{}");
} catch {
  process.exit(0); // entrada ilegible: no bloquear el trabajo
}
const datos = entrada.tool_input || {};
const ruta = path.resolve(datos.file_path || "");
const raizFront = path.resolve(__dirname, "..", "..", "PetConnect.Front", "petconnect-app");

if (!/\.(js|jsx|mjs)$/i.test(ruta) || !ruta.toLowerCase().startsWith(path.join(raizFront, "src").toLowerCase())) {
  process.exit(0);
}

const oxlint = path.join(raizFront, "node_modules", "oxlint", "bin", "oxlint");
if (!fs.existsSync(oxlint)) process.exit(0); // sin node_modules no hay linter que correr

// oxlint sale con código 0 cuando solo hay advertencias, así que se revisa el texto
let salida = "";
try {
  salida = execFileSync(process.execPath, [oxlint, ruta], { cwd: raizFront, encoding: "utf8" });
} catch (error) {
  salida = `${error.stdout || ""}${error.stderr || ""}`;
}
salida = salida.trim();

if (/\b(warning|error)\b/i.test(salida)) {
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: "PostToolUse",
      additionalContext: `oxlint encontró problemas en ${path.relative(raizFront, ruta)}; corrígelos:\n${salida.slice(0, 4000)}`,
    },
  }));
}
process.exit(0);
