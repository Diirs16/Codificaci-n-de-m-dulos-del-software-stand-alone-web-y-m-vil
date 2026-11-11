// Hook PreToolUse (Bash con "git commit"): antes de guardar partida revisa lo que
// está en el área de preparación (staged) y bloquea el commit si encuentra
// archivos de secretos o credenciales escritas en el código.
const fs = require("fs");
const { execSync } = require("child_process");

let entrada = {};
try {
  entrada = JSON.parse(fs.readFileSync(0, "utf8") || "{}");
} catch {
  process.exit(0); // entrada ilegible: no bloquear el trabajo
}
const comando = (entrada.tool_input || {}).command || "";
if (!/\bgit\b[^|;&]*\bcommit\b/.test(comando)) process.exit(0);

function git(args) {
  try {
    return execSync(`git ${args}`, { cwd: entrada.cwd || process.cwd(), encoding: "utf8", maxBuffer: 20 * 1024 * 1024 });
  } catch {
    return "";
  }
}

const problemas = [];

const archivos = git("diff --cached --name-only").split(/\r?\n/).filter(Boolean);
for (const archivo of archivos) {
  if (/(^|\/)\.env(\.(?!example$)[\w.-]+)?$|\.(pem|key|p12|jks)$/i.test(archivo)) {
    problemas.push(`Archivo de secretos preparado para commit: ${archivo}`);
  }
}

const PATRONES = [
  [/(password|passwd|contrasena|clave|secret|token|api_?key|jwt_secret|fernet_key)\s*[:=]\s*["'][^"'\s]{8,}["']/i, "credencial escrita en el código"],
  [/-----BEGIN (RSA |EC )?PRIVATE KEY-----/, "llave privada"],
  [/^(JWT_SECRET|FERNET_KEY|GMAIL_APP_PASSWORD|MAILTRAP_API_TOKEN|DB_PASSWORD)=\S+/, "variable de .env con valor real"],
];

let archivoActual = "";
for (const linea of git("diff --cached -U0").split(/\r?\n/)) {
  if (linea.startsWith("+++ b/")) archivoActual = linea.slice(6);
  if (!linea.startsWith("+") || linea.startsWith("+++")) continue;
  if (/[\\/]tests?[\\/]|\.test\.|\.md$/i.test(archivoActual)) continue;
  for (const [patron, descripcion] of PATRONES) {
    if (patron.test(linea.slice(1))) problemas.push(`${archivoActual}: ${descripcion}`);
  }
}

if (problemas.length) {
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason:
        "Commit bloqueado por la revisión de secretos de PetConnect:\n- " +
        [...new Set(problemas)].join("\n- ") +
        "\nSaca esos valores a .env (y quítalos del staging con 'git restore --staged <archivo>') antes de hacer commit.",
    },
  }));
}
process.exit(0);
