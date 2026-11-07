// Ítem 3.6 parte 3 (A-21): solicitudes de adopción y mensajes de contacto en el móvil.
// Mismas reglas que la web (tests/solicitudes.test.js del Front). Datos inventados.
// - La validación (src/utils/solicitud.js) es JS puro: se ejecuta de verdad.
// - Los cuerpos (src/utils/peticiones.js) también: no llevan nombre ni correo.
// - Las pantallas tienen JSX y Node no lo entiende: se lee su texto.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { validarMensaje, validarTelefono, MENSAJE_MIN, MENSAJE_MAX } from "../src/utils/solicitud.js";
// Con "* as" la falta de una función hace fallar solo su prueba (no todo el archivo).
import * as peticiones from "../src/utils/peticiones.js";

const SRC = fileURLToPath(new URL("../src", import.meta.url));
const leer = (ruta) => readFileSync(join(SRC, ruta), "utf8");

function archivosDeCodigo(carpeta) {
  return readdirSync(carpeta, { withFileTypes: true }).flatMap((e) => {
    const ruta = join(carpeta, e.name);
    if (e.isDirectory()) return archivosDeCodigo(ruta);
    return /\.(js|jsx)$/.test(e.name) ? [ruta] : [];
  });
}

// --- Validación (copia de la web) ---

test("mensaje: entre 10 y 1000 caracteres sin contar los espacios de los extremos", () => {
  assert.equal(MENSAJE_MIN, 10);
  assert.equal(MENSAJE_MAX, 1000);
  assert.ok(validarMensaje(""));
  assert.ok(validarMensaje("   corto   "), "9 letras con espacios alrededor no alcanzan");
  assert.equal(validarMensaje("  Hola, quiero adoptar  "), null);
  assert.equal(validarMensaje("a".repeat(1000)), null);
  assert.ok(validarMensaje("a".repeat(1001)));
  assert.ok(validarMensaje(undefined));
});

test("teléfono: opcional; solo números, espacios y un + al inicio, de 7 a 15 dígitos", () => {
  for (const bien of ["", "   ", "3000000000", "+57 300 000 0000", "1234567"]) {
    assert.equal(validarTelefono(bien), null, `"${bien}" debe valer`);
  }
  for (const mal of ["300-000-0000", "123456", "1234567890123456", "+57+300000000", "abc1234567", "1".repeat(21)]) {
    assert.ok(validarTelefono(mal), `"${mal}" no debe valer`);
  }
});

test("src/utils/solicitud.js es la MISMA copia que la de la web (sin contar los comentarios //)", () => {
  const sinComentarios = (texto) =>
    texto
      .replaceAll("\r\n", "\n")
      .split("\n")
      .filter((linea) => !linea.startsWith("//"))
      .join("\n")
      .trim();
  const movil = leer("utils/solicitud.js");
  const web = readFileSync(
    new URL("../../PetConnect.Front/petconnect-app/src/utils/solicitud.js", import.meta.url),
    "utf8",
  );
  assert.equal(sinComentarios(movil), sinComentarios(web), "si cambia una regla, cambiarla en api.py, la web y el móvil");
});

// --- Lo que viaja a la API ---

test("adopción: la mascota va como número, con mensaje y teléfono, y sin nombre ni correo", () => {
  const cuerpo = peticiones.cuerpoSolicitudAdopcion("3", "Quiero conocer a Luna pronto", "3000000000");
  assert.deepEqual(cuerpo, { id_mascota: 3, mensaje: "Quiero conocer a Luna pronto", telefono: "3000000000" });
  assert.deepEqual(peticiones.cuerpoSolicitudAdopcion(3, "Quiero conocer a Luna pronto"), {
    id_mascota: 3,
    mensaje: "Quiero conocer a Luna pronto",
    telefono: "",
  });
});

test("contacto: solo el mensaje (sin mascota, teléfono, nombre ni correo)", () => {
  assert.deepEqual(peticiones.cuerpoMensajeContacto("Hola, tengo una pregunta"), { mensaje: "Hola, tengo una pregunta" });
});

test("api.js tiene las dos funciones, con POST a las rutas de la API y los cuerpos probados", () => {
  const codigo = leer("services/api.js");
  assert.ok(/export function enviarSolicitudAdopcion\(idMascota, mensaje, telefono = ""\)/.test(codigo));
  assert.ok(/export function enviarMensajeContacto\(mensaje\)/.test(codigo));
  assert.ok(
    /apiFetch\("\/solicitudes\/adopcion", \{\s*method: "POST",\s*body: JSON\.stringify\(cuerpoSolicitudAdopcion\(idMascota, mensaje, telefono\)\)/.test(codigo),
  );
  assert.ok(
    /apiFetch\("\/solicitudes\/contacto", \{\s*method: "POST",\s*body: JSON\.stringify\(cuerpoMensajeContacto\(mensaje\)\)/.test(codigo),
  );
  // El token lo pone apiFetch (desde AsyncStorage), igual que en /auth/me
  assert.ok(/Authorization: `Bearer \$\{token\}`/.test(codigo));
});

// --- El formulario ---

const FORMULARIO = "components/FormularioSolicitud.js";

test("el formulario dice 'enviada' solo después de la respuesta de la API", () => {
  const codigo = leer(FORMULARIO);
  assert.equal(codigo.match(/setEstado\("enviada"\)/g)?.length, 1, "un solo lugar marca 'enviada'");
  assert.ok(
    /await enviarSolicitudAdopcion\([\s\S]*?await enviarMensajeContacto\([\s\S]*?setEstado\("enviada"\)[\s\S]*?catch/.test(codigo),
    "'enviada' va después de los await y antes del catch",
  );
  assert.ok(codigo.includes("Solicitud enviada") && codigo.includes("Mensaje enviado"));
});

test("valida antes de llamar a la API y no borra lo escrito si la API falla", () => {
  const codigo = leer(FORMULARIO);
  assert.ok(
    /validarMensaje\(mensaje\)[\s\S]*?validarTelefono\(telefono\)[\s\S]*?return;[\s\S]*?setEstado\("enviando"\)/.test(codigo),
    "si la validación falla, sale antes de enviar",
  );
  const bloqueCatch = codigo.slice(codigo.indexOf("} catch (err) {"), codigo.indexOf("function iniciarSesion"));
  assert.ok(!/setMensaje\(|setTelefono\(/.test(bloqueCatch), "el catch no debe vaciar los campos");
});

test("401 y el 403 de autorización ofrecen volver a iniciar sesión sin perder lo escrito", () => {
  const codigo = leer(FORMULARIO);
  assert.ok(codigo.includes("err.status === 401"));
  assert.ok(codigo.includes("err.requiereAutorizacion"));
  assert.ok(codigo.includes("Volver a iniciar sesión"));
  assert.ok(codigo.includes("Tu sesión venció. Vuelve a iniciar sesión para enviar: lo que escribiste no se pierde."));
  // El inicio de sesión se abre ENCIMA (modal), no en la pestaña Perfil (cerraría la ficha)
  assert.ok(codigo.includes('navigation.navigate("IniciarSesion"'));
  assert.ok(!/navigate\("Perfil"|navigate\("Main"/.test(codigo));
  // Sin sesión no hay campos: solo el botón para iniciarla (B.3)
  assert.ok(codigo.includes("Inicia sesión para enviar"));
});

test("el formulario tiene el aviso B.5 (adopción y contacto), la política y el correo; sin casilla aparte", () => {
  const codigo = leer(FORMULARIO).replace(/\s+/g, " ");
  for (const parte of [
    "Al enviar, usaremos tu nombre, tu correo",
    ", tu teléfono (si lo escribes)",
    "gestionar tu solicitud de adopción de ${mascota.name}",
    "responder tu consulta",
    "según la Política de tratamiento de datos personales.",
    "Solo el equipo de PetConnect lee tu mensaje.",
    "No escribas datos sensibles (salud, creencias…).",
    "Puedes pedir que lo borremos escribiendo a",
  ]) {
    assert.ok(codigo.includes(parte), `falta en el aviso: ${parte}`);
  }
  assert.ok(codigo.includes("POLITICA_URL"), "debe abrir la política");
  assert.ok(codigo.includes("mailto:${CORREO_ATENCION}"), "debe ofrecer el correo de atención");
  assert.ok(codigo.includes('"proyectopetconnect+atencion@gmail.com"'));
  assert.ok(
    !codigo.includes("import CasillaAutorizacion") && !codigo.includes("<CasillaAutorizacion"),
    "decisión del dueño: sin casilla aparte",
  );
});

test("el aviso B.5 está solo en el componente, y la ficha, Contacto y el navegador lo usan", () => {
  const conAviso = archivosDeCodigo(SRC)
    .filter((ruta) => readFileSync(ruta, "utf8").includes("Solo el equipo de PetConnect lee tu mensaje"))
    .map((ruta) => relative(SRC, ruta).replaceAll("\\", "/"));
  assert.deepEqual(conAviso, [FORMULARIO]);

  const ficha = leer("screens/PetDetailScreen.js");
  assert.ok(ficha.includes('import FormularioSolicitud from "../components/FormularioSolicitud"'));
  assert.ok(ficha.includes('<FormularioSolicitud\n            tipo="adopcion"') || /<FormularioSolicitud\s+tipo="adopcion"/.test(ficha));
  assert.ok(ficha.includes("Solicitar adopción"));

  const contacto = leer("screens/ContactScreen.js");
  assert.ok(/<FormularioSolicitud tipo="contacto" \/>/.test(contacto));

  const navegador = leer("navigation/AppNavigator.js");
  assert.ok(/<Tab\.Screen\s+name="Contacto"\s+component=\{ContactScreen\}/.test(navegador), "pestaña Contacto");
  assert.ok(/<Stack\.Screen\s+name="IniciarSesion"\s+component=\{IniciarSesionModal\}/.test(navegador));
  assert.ok(navegador.includes('presentation: "modal"'), "el inicio de sesión se abre encima");
  assert.ok(/if \(user && navigation\.canGoBack\(\)\) navigation\.goBack\(\)/.test(navegador), "se cierra solo al entrar");
});
