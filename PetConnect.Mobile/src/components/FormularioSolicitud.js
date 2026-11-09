import { useState } from "react";
import { View, Text, TextInput, Pressable, Linking, ActivityIndicator, StyleSheet } from "react-native";
import { useNavigation } from "@react-navigation/native";
import { useAuth } from "../context/AuthContext";
import { POLITICA_URL, enviarMensajeContacto, enviarSolicitudAdopcion } from "../services/api";
import { MENSAJE_MAX, MENSAJE_MIN, validarMensaje, validarTelefono } from "../utils/solicitud";

// Correo de atención de la política de datos (D.1). Si cambia, cambiarlo también en
// CasillaAutorizacion.js, LoginScreen.js, la web y el borrador .md.
const CORREO_ATENCION = "proyectopetconnect+atencion@gmail.com";
const ERROR_GENERICO = "No pudimos enviar. Revisa tu conexión e inténtalo de nuevo en unos minutos.";

/**
 * Formulario real de solicitud de adopción o de mensaje de contacto (ítem 3.6 parte 3,
 * A-21). Hace lo mismo que el de la web (FormularioSolicitud.jsx). Decisiones del dueño
 * (07/11/2026): solo con sesión (el nombre y el correo salen de la cuenta y no se piden),
 * teléfono opcional solo en adopción y SIN casilla aparte: el aviso B.5 informa la
 * finalidad y vale la autorización de la cuenta con la política 1.1.
 * Dice "enviada" solo cuando la API respondió 201.
 *
 * Para iniciar sesión abre la pantalla "IniciarSesion" ENCIMA de la actual (modal de
 * AppNavigator.js): esta pantalla no se cierra y lo escrito no se pierde.
 *
 * Props: tipo ("adopcion" | "contacto"), mascota ({ id, name }, solo adopción) y
 * onCerrar (opcional: muestra el botón "Cerrar").
 */
export default function FormularioSolicitud({ tipo, mascota, onCerrar }) {
  const { user, cerrarSesionLocal } = useAuth();
  const navigation = useNavigation();
  const esAdopcion = tipo === "adopcion";

  // Lo escrito se conserva aunque haya que volver a iniciar sesión.
  const [mensaje, setMensaje] = useState("");
  const [telefono, setTelefono] = useState("");
  const [estado, setEstado] = useState("editando"); // "editando" | "enviando" | "enviada"
  const [error, setError] = useState("");
  const [campoConError, setCampoConError] = useState(null); // "mensaje" | "telefono" | null
  const [volverAEntrar, setVolverAEntrar] = useState(false); // 401 o 403 de autorización
  const [numero, setNumero] = useState(null);

  async function enviar() {
    if (estado === "enviando") return;
    setError("");
    setVolverAEntrar(false);

    // Primero en el celular: así no se llama a la API con algo que va a rechazar.
    const errorMensaje = validarMensaje(mensaje);
    const errorTelefono = esAdopcion ? validarTelefono(telefono) : null;
    if (errorMensaje || errorTelefono) {
      setError(errorMensaje || errorTelefono);
      setCampoConError(errorMensaje ? "mensaje" : "telefono");
      return;
    }
    setCampoConError(null);

    setEstado("enviando");
    try {
      const respuesta = esAdopcion
        ? await enviarSolicitudAdopcion(mascota.id, mensaje.trim(), telefono.trim())
        : await enviarMensajeContacto(mensaje.trim());
      setNumero(respuesta?.id ?? null);
      setEstado("enviada");
    } catch (err) {
      setEstado("editando");
      if (err.status === 401) {
        setError("Tu sesión venció. Vuelve a iniciar sesión para enviar: lo que escribiste no se pierde.");
        setVolverAEntrar(true);
      } else if (err.requiereAutorizacion) {
        setError(err.message);
        setVolverAEntrar(true);
      } else if (!err.status) {
        // Sin respuesta del servidor (fetch falló): React Native diría "Network request failed".
        setError(ERROR_GENERICO);
      } else {
        setError(err.message || ERROR_GENERICO);
      }
    }
  }

  function iniciarSesion(pantalla) {
    navigation.navigate("IniciarSesion", pantalla ? { screen: pantalla } : undefined);
  }

  async function volverAIniciarSesion() {
    setError("");
    setVolverAEntrar(false);
    // Ítem 4.13: la API ya dijo que este token no vale (401) o pide la autorización
    // (403): solo se borra la sesión del celular, sin pedirle a la API que la cierre.
    await cerrarSesionLocal();
    iniciarSesion();
  }

  async function abrir(url, mensajeSiFalla) {
    try {
      await Linking.openURL(url);
    } catch {
      setError(mensajeSiFalla);
    }
  }

  // --- Sin sesión: no se muestra el formulario (no se recoge nada sin cuenta) ---
  if (!user) {
    return (
      <View style={styles.caja}>
        <Text style={styles.texto}>
          {esAdopcion
            ? `Para enviar una solicitud de adopción de ${mascota.name} necesitas iniciar sesión.`
            : "Para enviarnos un mensaje desde aquí necesitas iniciar sesión."}{" "}
          Usaremos el nombre y el correo de tu cuenta.
        </Text>
        <Boton texto="Inicia sesión para enviar" onPress={() => iniciarSesion()} principal />
        <Boton texto="Crear cuenta" onPress={() => iniciarSesion("Register")} />
        {onCerrar ? <Boton texto="Cerrar" onPress={onCerrar} /> : null}
      </View>
    );
  }

  // --- Enviada: solo llega aquí si la API respondió 201 ---
  if (estado === "enviada") {
    return (
      <View style={[styles.caja, styles.cajaEnviada]} aria-live="polite">
        <Text style={styles.tituloEnviada} role="heading">
          ✓ {esAdopcion ? "Solicitud enviada" : "Mensaje enviado"}
        </Text>
        <Text style={styles.textoEnviada}>
          {esAdopcion ? "Tu solicitud quedó guardada" : "Tu mensaje quedó guardado"}
          {numero ? ` con el número ${numero}` : ""}. El equipo de PetConnect {esAdopcion ? "la" : "lo"} revisará
          y te escribirá al correo de tu cuenta ({user.email}).
        </Text>
        {onCerrar ? <Boton texto="Cerrar" onPress={onCerrar} /> : null}
      </View>
    );
  }

  const enviando = estado === "enviando";
  const largo = mensaje.trim().length;
  const etiquetaMensaje = esAdopcion ? `¿Por qué quieres adoptar a ${mascota.name}?` : "Mensaje";

  return (
    <View style={styles.caja}>
      <Text style={styles.titulo} role="heading">
        {esAdopcion ? `Solicitud de adopción de ${mascota.name}` : "Escríbenos"}
      </Text>

      <Text style={styles.texto}>
        Envías como <Text style={styles.negrita}>{user.name}</Text> ({user.email}).
      </Text>

      {esAdopcion ? (
        <View>
          <Text style={styles.etiqueta}>
            Teléfono <Text style={styles.opcional}>(opcional)</Text>
          </Text>
          <TextInput
            style={[styles.campo, campoConError === "telefono" && styles.campoConError]}
            value={telefono}
            onChangeText={setTelefono}
            keyboardType="phone-pad"
            autoComplete="tel"
            maxLength={20}
            editable={!enviando}
            aria-label="Teléfono (opcional)"
            aria-invalid={campoConError === "telefono"}
          />
        </View>
      ) : null}

      <View>
        <Text style={styles.etiqueta}>{etiquetaMensaje}</Text>
        <TextInput
          style={[styles.campo, styles.campoMensaje, campoConError === "mensaje" && styles.campoConError]}
          value={mensaje}
          onChangeText={setMensaje}
          multiline
          numberOfLines={5}
          textAlignVertical="top"
          maxLength={MENSAJE_MAX}
          editable={!enviando}
          aria-label={etiquetaMensaje}
          aria-invalid={campoConError === "mensaje"}
          accessibilityHint={`Entre ${MENSAJE_MIN} y ${MENSAJE_MAX} caracteres`}
        />
        <View style={styles.ayudaFila}>
          <Text style={styles.ayuda}>
            Entre {MENSAJE_MIN} y {MENSAJE_MAX} caracteres.
          </Text>
          <Text style={styles.ayuda} aria-hidden>
            {largo}/{MENSAJE_MAX}
          </Text>
        </View>
      </View>

      {/* Aviso B.5 del borrador de la política (versión 1.1): informa la finalidad (Ley 1581, art. 12) */}
      <Text style={styles.aviso}>
        Al enviar, usaremos tu nombre, tu correo{esAdopcion ? ", tu teléfono (si lo escribes)" : ""} y este
        mensaje para{" "}
        {esAdopcion ? `gestionar tu solicitud de adopción de ${mascota.name}` : "responder tu consulta"}, según la
        Política de tratamiento de datos personales. Solo el equipo de PetConnect lee tu mensaje. No escribas datos
        sensibles (salud, creencias…). Puedes pedir que lo borremos escribiendo a{" "}
        <Text style={styles.negrita}>{CORREO_ATENCION}</Text>.
      </Text>
      {/* Los enlaces van en filas aparte: dentro del párrafo, TalkBack no los podría activar solos. */}
      <Enlace
        texto="Leer la Política de tratamiento de datos personales ↗"
        pista="Se abre en el navegador"
        onPress={() => abrir(POLITICA_URL, "No se pudo abrir la política en el navegador. Intenta de nuevo.")}
      />
      <Enlace
        texto="Escribir al correo de atención ↗"
        etiqueta={`Escribir a ${CORREO_ATENCION}`}
        pista="Se abre tu aplicación de correo"
        onPress={() => abrir(`mailto:${CORREO_ATENCION}`, `No se pudo abrir el correo. Escríbenos a ${CORREO_ATENCION}.`)}
      />

      {/* Zona que TalkBack lee sola cuando aparece un error. Lo escrito no se borra. */}
      <View aria-live="polite">
        {error ? (
          <View style={styles.cajaError} role="alert">
            <Text style={styles.textoError}>{error}</Text>
            {volverAEntrar ? <Boton texto="Volver a iniciar sesión" onPress={volverAIniciarSesion} /> : null}
          </View>
        ) : null}
      </View>

      <Boton
        texto={esAdopcion ? "Enviar solicitud" : "Enviar mensaje"}
        onPress={enviar}
        principal
        cargando={enviando}
      />
      {onCerrar ? <Boton texto="Cerrar" onPress={onCerrar} desactivado={enviando} /> : null}
    </View>
  );
}

// Botón con área táctil de 48 px y estado "ocupado" mientras se envía.
function Boton({ texto, onPress, principal, cargando, desactivado }) {
  const inactivo = cargando || desactivado;
  return (
    <Pressable
      style={({ pressed }) => [
        principal ? styles.botonPrincipal : styles.botonSecundario,
        pressed && styles.presionado,
        inactivo && (principal ? styles.botonPrincipalInactivo : styles.botonSecundarioInactivo),
      ]}
      onPress={onPress}
      disabled={inactivo}
      role="button"
      aria-label={cargando ? "Enviando…" : texto}
      aria-disabled={inactivo}
      aria-busy={cargando}
    >
      {cargando ? (
        <ActivityIndicator color="#fff" />
      ) : (
        <Text style={[principal ? styles.botonPrincipalTexto : styles.botonSecundarioTexto, desactivado && styles.textoInactivo]}>
          {texto}
        </Text>
      )}
    </Pressable>
  );
}

function Enlace({ texto, etiqueta, pista, onPress }) {
  return (
    <Pressable
      style={({ pressed }) => [styles.enlaceFila, pressed && styles.presionado]}
      onPress={onPress}
      role="link"
      aria-label={etiqueta ?? texto}
      accessibilityHint={pista}
    >
      <Text style={styles.enlace}>{texto}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  caja: { gap: 12, borderWidth: 1, borderColor: "#e2e8f0", borderRadius: 12, padding: 16, backgroundColor: "#fff" },
  cajaEnviada: { borderColor: "#86efac", backgroundColor: "#f0fdf4" },
  titulo: { fontSize: 18, fontWeight: "700", color: "#0f172a" },
  tituloEnviada: { fontSize: 18, fontWeight: "700", color: "#14532d" },
  textoEnviada: { fontSize: 14, lineHeight: 20, color: "#14532d" },
  texto: { fontSize: 14, lineHeight: 20, color: "#334155" },
  negrita: { fontWeight: "700", color: "#0f172a" },
  etiqueta: { fontSize: 14, fontWeight: "600", color: "#0f172a", marginBottom: 6 },
  opcional: { fontWeight: "400", color: "#475569" },
  campo: {
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 15,
    color: "#0f172a",
    backgroundColor: "#fff",
    minHeight: 48,
  },
  campoMensaje: { minHeight: 120 },
  campoConError: { borderColor: "#b91c1c", borderWidth: 2 },
  ayudaFila: { flexDirection: "row", justifyContent: "space-between", gap: 12, marginTop: 4 },
  ayuda: { fontSize: 12, color: "#475569" },
  aviso: { fontSize: 12, lineHeight: 18, color: "#475569" },
  enlaceFila: { minHeight: 44, justifyContent: "center" },
  enlace: { color: "#0f766e", fontSize: 14, fontWeight: "600", textDecorationLine: "underline", lineHeight: 20 },
  cajaError: { gap: 8, borderWidth: 1, borderColor: "#fca5a5", backgroundColor: "#fef2f2", borderRadius: 10, padding: 12 },
  textoError: { fontSize: 14, lineHeight: 20, color: "#991b1b" },
  botonPrincipal: {
    backgroundColor: "#0f766e",
    borderRadius: 10,
    paddingVertical: 14,
    paddingHorizontal: 16,
    alignItems: "center",
    justifyContent: "center",
    minHeight: 48,
  },
  botonPrincipalInactivo: { backgroundColor: "#64748b" },
  botonPrincipalTexto: { color: "#fff", fontWeight: "700", fontSize: 15 },
  botonSecundario: {
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 16,
    alignItems: "center",
    justifyContent: "center",
    minHeight: 48,
    backgroundColor: "#fff",
  },
  botonSecundarioInactivo: { borderColor: "#e2e8f0" },
  botonSecundarioTexto: { color: "#0f172a", fontWeight: "600", fontSize: 15 },
  textoInactivo: { color: "#94a3b8" },
  presionado: { opacity: 0.7 },
});
