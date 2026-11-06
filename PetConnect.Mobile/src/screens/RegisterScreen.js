import { useRef, useState } from "react";
import {
  View,
  Text,
  TextInput,
  Pressable,
  ScrollView,
  KeyboardAvoidingView,
  Linking,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { registerUser, verifyCode, POLITICA_URL } from "../services/api";
import { useAuth } from "../context/AuthContext";

// NC-005 (ítem 3.1): textos de la Parte B de
// Documentacion/Legal/POLITICA-TRATAMIENTO-DATOS-v1.0-BORRADOR.md (los mismos de la web).
const MENSAJE_SIN_AUTORIZACION =
  "Para crear tu cuenta debes autorizar el tratamiento de tus datos personales.";

export default function RegisterScreen({ navigation }) {
  const { establecerSesion } = useAuth();
  const [step, setStep] = useState("form"); // form | code
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  // La casilla empieza SIN marcar: el silencio no es autorización (Ley 1581, art. 9).
  const [aceptaDatos, setAceptaDatos] = useState(false);
  const [code, setCode] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // En Android (pantalla de borde a borde) la ventana no se encoge con el teclado:
  // KeyboardAvoidingView necesita saber a qué altura de la pantalla empieza el
  // formulario (debajo del encabezado "Perfil") para no quedar tapado.
  const contenedorRef = useRef(null);
  const [inicioFormulario, setInicioFormulario] = useState(0);

  function medirInicio() {
    contenedorRef.current?.measureInWindow((_x, y) => setInicioFormulario(y));
  }

  async function handleRegister() {
    setError(null);
    // Sin la casilla no se llama a la API (mensaje B.3).
    if (!aceptaDatos) {
      setError(MENSAJE_SIN_AUTORIZACION);
      return;
    }
    setLoading(true);
    try {
      await registerUser(name.trim(), email.trim(), password, aceptaDatos);
      setStep("code");
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
      const data = await verifyCode(email.trim(), code.trim());
      await establecerSesion(data.token, data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function cambiarAutorizacion() {
    const marcada = !aceptaDatos;
    setAceptaDatos(marcada);
    // Si el aviso era por la casilla, se quita al marcarla.
    if (marcada && error === MENSAJE_SIN_AUTORIZACION) setError(null);
  }

  async function abrirPolitica() {
    // La pantalla sigue abierta detrás del navegador: lo escrito no se pierde.
    try {
      await Linking.openURL(POLITICA_URL);
    } catch {
      setError("No se pudo abrir la política en el navegador. Intenta de nuevo.");
    }
  }

  if (step === "code") {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Verifica tu correo</Text>
        <Text style={styles.subtitle}>
          Enviamos un código de 6 dígitos a {email}
        </Text>
        <TextInput
          style={styles.input}
          placeholder="Código de verificación"
          keyboardType="number-pad"
          value={code}
          onChangeText={setCode}
        />
        <View aria-live="polite">
          {error ? <Text style={styles.error}>{error}</Text> : null}
        </View>
        <Pressable
          style={({ pressed }) => [styles.button, pressed && styles.pressed]}
          onPress={handleVerify}
          disabled={loading}
          role="button"
          aria-disabled={loading}
          aria-busy={loading}
        >
          {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Verificar</Text>}
        </Pressable>
      </View>
    );
  }

  return (
    <View ref={contenedorRef} style={styles.flex} onLayout={medirInicio}>
      <KeyboardAvoidingView style={styles.flex} behavior="padding" keyboardVerticalOffset={inicioFormulario}>
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          <Text style={styles.title}>Crea tu cuenta</Text>

          <TextInput style={styles.input} placeholder="Nombre completo" value={name} onChangeText={setName} />
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

          {/* NC-005: autorización previa, expresa e informada (Ley 1581, arts. 9 y 12) */}
          <View style={styles.autorizacion}>
            <Pressable
              style={styles.casillaFila}
              onPress={cambiarAutorizacion}
              role="checkbox"
              aria-checked={aceptaDatos}
              accessibilityHint="Obligatoria para crear la cuenta"
            >
              <View style={[styles.casilla, aceptaDatos && styles.casillaMarcada]}>
                {aceptaDatos ? <Text style={styles.casillaCheck}>✓</Text> : null}
              </View>
              <Text style={styles.casillaTexto}>
                Soy mayor de 18 años, he leído la Política de tratamiento de datos personales y
                autorizo a PetConnect a tratar mis datos para crear y usar mi cuenta.
              </Text>
            </Pressable>

            {/* El enlace va en su propia línea: dentro de la casilla, TalkBack no lo
                podría activar por separado (leería todo como un solo elemento). */}
            <Pressable
              style={({ pressed }) => [styles.enlaceFila, pressed && styles.pressed]}
              onPress={abrirPolitica}
              role="link"
              aria-label="Leer los términos y condiciones que aceptas: Política de tratamiento de datos personales"
              accessibilityHint="Se abre en el navegador"
            >
              <Text style={styles.enlace}>
                Leer los términos y condiciones que aceptas: Política de tratamiento de datos personales ↗
              </Text>
            </Pressable>

            <Text style={styles.aviso}>
              Usaremos tu nombre y tu correo para crear tu cuenta y enviarte códigos de verificación.
              Puedes conocer, actualizar, rectificar o borrar tus datos y revocar este permiso escribiendo a{" "}
              {/* Correo de atención del proyecto (D.1, 06/11/2026); el mismo de la web (RegisterModal.jsx y PoliticaDatos.jsx) */}
              <Text style={styles.avisoCorreo}>proyectopetconnect+atencion@gmail.com.</Text>
            </Text>
          </View>

          {/* Zona que TalkBack lee sola cuando aparece un error */}
          <View aria-live="polite">
            {error ? <Text style={styles.error}>{error}</Text> : null}
          </View>

          <Pressable
            style={({ pressed }) => [styles.button, pressed && styles.pressed]}
            onPress={handleRegister}
            disabled={loading}
            role="button"
            aria-disabled={loading}
            aria-busy={loading}
          >
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Registrarme</Text>}
          </Pressable>

          <Pressable
            style={styles.linkFila}
            onPress={() => navigation.navigate("Login")}
            role="link"
          >
            <Text style={styles.link}>¿Ya tienes cuenta? Inicia sesión</Text>
          </Pressable>
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  container: { flex: 1, padding: 24, justifyContent: "center" },
  scrollContent: { flexGrow: 1, padding: 24, justifyContent: "center" },
  title: { fontSize: 22, fontWeight: "700", marginBottom: 8, color: "#0f172a", textAlign: "center" },
  subtitle: { fontSize: 14, color: "#64748b", marginBottom: 20, textAlign: "center" },
  input: {
    borderWidth: 1,
    borderColor: "#e2e8f0",
    borderRadius: 10,
    padding: 12,
    marginBottom: 12,
    fontSize: 15,
  },
  autorizacion: { marginTop: 4, marginBottom: 8 },
  // Área táctil de al menos 44 px de alto (B.4)
  casillaFila: { flexDirection: "row", alignItems: "flex-start", gap: 12, minHeight: 44, paddingVertical: 8 },
  casilla: {
    width: 24,
    height: 24,
    borderWidth: 2,
    borderColor: "#475569",
    borderRadius: 6,
    alignItems: "center",
    justifyContent: "center",
  },
  casillaMarcada: { backgroundColor: "#0f766e", borderColor: "#0f766e" },
  casillaCheck: { color: "#fff", fontSize: 16, fontWeight: "700", lineHeight: 18 },
  casillaTexto: { flex: 1, fontSize: 14, lineHeight: 20, color: "#0f172a" },
  enlaceFila: { minHeight: 44, justifyContent: "center", paddingLeft: 36 },
  enlace: { color: "#0f766e", fontSize: 14, fontWeight: "600", textDecorationLine: "underline", lineHeight: 20 },
  aviso: { fontSize: 12, lineHeight: 18, color: "#475569", paddingLeft: 36 },
  avisoCorreo: { fontWeight: "600", color: "#1e293b" },
  error: { color: "#b91c1c", marginBottom: 12, textAlign: "center" },
  button: { backgroundColor: "#0f766e", borderRadius: 10, padding: 14, alignItems: "center", marginTop: 8, minHeight: 48 },
  buttonText: { color: "#fff", fontWeight: "700", fontSize: 15 },
  pressed: { opacity: 0.7 },
  linkFila: { minHeight: 44, justifyContent: "center", marginTop: 8 },
  link: { color: "#0f766e", textAlign: "center" },
});
