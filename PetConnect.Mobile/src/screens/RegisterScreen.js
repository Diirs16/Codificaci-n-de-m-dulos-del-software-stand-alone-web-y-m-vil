import { useRef, useState } from "react";
import {
  View,
  Text,
  TextInput,
  Pressable,
  ScrollView,
  KeyboardAvoidingView,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { registerUser, verifyCode } from "../services/api";
import { useAuth } from "../context/AuthContext";
import CasillaAutorizacion from "../components/CasillaAutorizacion";
// Ítem 4.1 (A-17, NC-004): las mismas reglas de contraseña que la API y la web
import { validarContrasena, LARGO_MIN, LARGO_MAX, CARACTERES_ESPECIALES } from "../utils/contrasena";

const PISTA_CONTRASENA =
  `Entre ${LARGO_MIN} y ${LARGO_MAX} caracteres, con mayúscula, minúscula, número ` +
  `y un carácter especial: ${CARACTERES_ESPECIALES}`;

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
    // Antes solo la API revisaba la contraseña; ahora se avisa sin llamarla.
    const errorContrasena = validarContrasena(password);
    if (errorContrasena) {
      setError(errorContrasena);
      return;
    }
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
            accessibilityHint={PISTA_CONTRASENA}
          />
          <Text style={styles.pista}>{PISTA_CONTRASENA}</Text>

          {/* NC-005: autorización previa, expresa e informada (Ley 1581, arts. 9 y 12) */}
          <CasillaAutorizacion
            marcada={aceptaDatos}
            onCambiar={cambiarAutorizacion}
            pista="Obligatoria para crear la cuenta"
            onErrorEnlace={setError}
          />

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
  // Debajo del campo de contraseña (gris #64748b sobre blanco: contraste 4.7:1, AA)
  pista: { fontSize: 12, color: "#64748b", marginTop: -6, marginBottom: 12 },
  error: { color: "#b91c1c", marginBottom: 12, textAlign: "center" },
  button: { backgroundColor: "#0f766e", borderRadius: 10, padding: 14, alignItems: "center", marginTop: 8, minHeight: 48 },
  buttonText: { color: "#fff", fontWeight: "700", fontSize: 15 },
  pressed: { opacity: 0.7 },
  linkFila: { minHeight: 44, justifyContent: "center", marginTop: 8 },
  link: { color: "#0f766e", textAlign: "center" },
});
