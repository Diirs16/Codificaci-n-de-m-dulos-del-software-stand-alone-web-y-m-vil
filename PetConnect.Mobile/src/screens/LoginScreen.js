import { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Pressable,
  ScrollView,
  Linking,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { loginUser } from "../services/api";
import { useAuth } from "../context/AuthContext";
import CasillaAutorizacion from "../components/CasillaAutorizacion";

// Ítem 3.5 (A-20, R05): las cuentas sin autorización vigente (creadas antes del 3.1
// o que aceptaron otra versión de la política) deben marcar la casilla para entrar.
// Textos de B.3 en Documentacion/Legal/POLITICA-TRATAMIENTO-DATOS-v1.0-BORRADOR.md
// (los mismos de la web, LoginModal.jsx).
const MENSAJE_SIN_AUTORIZACION = "Para continuar debes autorizar el tratamiento de tus datos personales.";
// Correo de atención del proyecto (D.1); el mismo de CasillaAutorizacion.js y de la web
const CORREO_ATENCION = "proyectopetconnect+atencion@gmail.com";

export default function LoginScreen({ navigation }) {
  const { iniciarLogin, verificarLogin, pendingLoginEmail, cancelarLogin } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  // Ítem 3.5: avisoAutorizacion guarda el mensaje del 403 de la API; si no está
  // vacío, la pantalla muestra el paso "Autoriza el uso de tus datos".
  const [avisoAutorizacion, setAvisoAutorizacion] = useState("");
  const [aceptaDatos, setAceptaDatos] = useState(false); // empieza SIN marcar

  // La API pidió la autorización: se muestra la casilla sin marcar. El correo y
  // la contraseña siguen en el estado para repetir el inicio de sesión con ella.
  function pedirAutorizacion(mensaje) {
    setError(null);
    setAceptaDatos(false);
    setAvisoAutorizacion(mensaje);
  }

  // Salir del paso de la casilla sin autorizar: se olvida la contraseña escrita.
  function salirDeAutorizacion() {
    setError(null);
    setAceptaDatos(false);
    setAvisoAutorizacion("");
    setPassword("");
  }

  function cambiarAutorizacion() {
    const marcada = !aceptaDatos;
    setAceptaDatos(marcada);
    // Si el aviso era por la casilla, se quita al marcarla.
    if (marcada && error === MENSAJE_SIN_AUTORIZACION) setError(null);
  }

  async function escribirAlCorreo() {
    try {
      await Linking.openURL(`mailto:${CORREO_ATENCION}`);
    } catch {
      setError(`No se pudo abrir el correo. Escríbenos a ${CORREO_ATENCION}.`);
    }
  }

  async function handleLogin() {
    setError(null);
    setLoading(true);
    try {
      await loginUser(email.trim(), password);
      iniciarLogin(email.trim());
    } catch (e) {
      if (e.requiereAutorizacion) pedirAutorizacion(e.message);
      else setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleAutorizar() {
    setError(null);
    // Sin la casilla no se llama a la API (y la API respondería 403 igual)
    if (!aceptaDatos) {
      setError(MENSAJE_SIN_AUTORIZACION);
      return;
    }
    setLoading(true);
    try {
      await loginUser(email.trim(), password, true);
      // La autorización se guarda solo cuando el código sea correcto (/login/verify)
      iniciarLogin(email.trim());
      setAvisoAutorizacion("");
      setAceptaDatos(false);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleVerify() {
    setError(null);
    setLoading(true);
    try {
      await verificarLogin(code);
    } catch (e) {
      // La versión de la política pudo cambiar mientras llegaba el código:
      // la API vuelve a pedir la casilla y no entrega el token.
      if (e.requiereAutorizacion) {
        setCode("");
        cancelarLogin();
        pedirAutorizacion(e.message);
      } else {
        setError(e.message);
      }
    } finally {
      setLoading(false);
    }
  }

  if (pendingLoginEmail) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Verificar inicio de sesión</Text>
        <Text style={styles.subtitle}>
          Ingresa el código de 6 dígitos que enviamos a {pendingLoginEmail}
        </Text>

        <TextInput
          style={[styles.input, styles.codeInput]}
          placeholder="------"
          keyboardType="number-pad"
          maxLength={6}
          value={code}
          onChangeText={(t) => setCode(t.replace(/\D/g, ""))}
          autoFocus
        />

        {error ? <Text style={styles.error}>{error}</Text> : null}

        <TouchableOpacity style={styles.button} onPress={handleVerify} disabled={loading || code.length !== 6}>
          {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Confirmar código</Text>}
        </TouchableOpacity>

        <TouchableOpacity onPress={() => { setError(null); setCode(""); cancelarLogin(); }}>
          <Text style={styles.link}>¿No recibiste el código? Volver e intentar de nuevo</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (avisoAutorizacion) {
    return (
      // ScrollView: a 375 px de ancho el paso es alto y debe poder desplazarse
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.title} role="heading">Autoriza el uso de tus datos</Text>
        {/* Mensaje del 403 de la API (B.3) */}
        <Text style={styles.subtitle}>{avisoAutorizacion}</Text>

        <CasillaAutorizacion
          marcada={aceptaDatos}
          onCambiar={cambiarAutorizacion}
          pista="Obligatoria para seguir usando tu cuenta"
          onErrorEnlace={setError}
        />

        {/* Zona que TalkBack lee sola cuando aparece un error */}
        <View aria-live="polite">
          {error ? <Text style={styles.error}>{error}</Text> : null}
        </View>

        <Pressable
          style={({ pressed }) => [styles.button, pressed && styles.pressed]}
          onPress={handleAutorizar}
          disabled={loading}
          role="button"
          aria-disabled={loading}
          aria-busy={loading}
        >
          {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Autorizar y continuar</Text>}
        </Pressable>

        {/* Desactivado mientras se envía: si se cancelara a mitad de la petición,
            al llegar la respuesta igual saldría la pantalla del código. */}
        <Pressable
          style={({ pressed }) => [styles.botonSecundario, pressed && styles.pressed, loading && styles.desactivado]}
          onPress={salirDeAutorizacion}
          disabled={loading}
          role="button"
          aria-disabled={loading}
        >
          <Text style={[styles.botonSecundarioTexto, loading && styles.textoDesactivado]}>Cancelar</Text>
        </Pressable>

        {/* B.3: si no autoriza, puede pedir que se borre su cuenta (proceso manual, C.8).
            El enlace va aparte para que TalkBack lo pueda activar solo. */}
        <View style={styles.borrarCuenta}>
          <Text style={styles.borrarCuentaTexto}>
            Si no quieres autorizarlo, escríbenos a{" "}
            <Text style={styles.correo}>{CORREO_ATENCION}</Text> y borraremos tu cuenta.
          </Text>
          <Pressable
            style={({ pressed }) => [styles.enlaceFila, pressed && styles.pressed]}
            onPress={escribirAlCorreo}
            role="link"
            aria-label={`Escribir a ${CORREO_ATENCION} para pedir que borren tu cuenta`}
            accessibilityHint="Se abre tu aplicación de correo"
          >
            <Text style={styles.enlace}>Escribir al correo de atención ↗</Text>
          </Pressable>
        </View>
      </ScrollView>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Inicia sesión en PetConnect</Text>

      <TextInput
        style={styles.input}
        placeholder="Correo electrónico"
        autoCapitalize="none"
        keyboardType="email-address"
        value={email}
        onChangeText={setEmail}
      />
      <TextInput
        style={styles.input}
        placeholder="Contraseña"
        secureTextEntry
        value={password}
        onChangeText={setPassword}
      />

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <TouchableOpacity style={styles.button} onPress={handleLogin} disabled={loading}>
        {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Ingresar</Text>}
      </TouchableOpacity>

      <TouchableOpacity onPress={() => navigation.navigate("Register")}>
        <Text style={styles.link}>¿No tienes cuenta? Regístrate</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 24, justifyContent: "center" },
  scrollContent: { flexGrow: 1, padding: 24, justifyContent: "center" },
  title: { fontSize: 22, fontWeight: "700", marginBottom: 8, color: "#0f172a", textAlign: "center" },
  subtitle: { fontSize: 14, color: "#64748b", textAlign: "center", marginBottom: 24 },
  codeInput: { textAlign: "center", fontSize: 22, fontWeight: "700", letterSpacing: 8 },
  input: {
    borderWidth: 1,
    borderColor: "#e2e8f0",
    borderRadius: 10,
    padding: 12,
    marginBottom: 12,
    fontSize: 15,
  },
  error: { color: "#b91c1c", marginBottom: 12, textAlign: "center" },
  button: { backgroundColor: "#0f766e", borderRadius: 10, padding: 14, alignItems: "center", marginTop: 8 },
  buttonText: { color: "#fff", fontWeight: "700", fontSize: 15 },
  link: { color: "#0f766e", textAlign: "center", marginTop: 16 },
  // Ítem 3.5: paso "Autoriza el uso de tus datos"
  pressed: { opacity: 0.7 },
  botonSecundario: {
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 10,
    padding: 14,
    alignItems: "center",
    marginTop: 12,
    minHeight: 48,
  },
  botonSecundarioTexto: { color: "#0f172a", fontWeight: "600", fontSize: 15 },
  desactivado: { borderColor: "#e2e8f0" },
  textoDesactivado: { color: "#94a3b8" },
  borrarCuenta: { marginTop: 20, paddingTop: 16, borderTopWidth: 1, borderTopColor: "#e2e8f0" },
  borrarCuentaTexto: { fontSize: 14, lineHeight: 20, color: "#475569" },
  correo: { fontWeight: "600", color: "#1e293b" },
  enlaceFila: { minHeight: 44, justifyContent: "center" },
  enlace: { color: "#0f766e", fontSize: 14, fontWeight: "600", textDecorationLine: "underline" },
});
