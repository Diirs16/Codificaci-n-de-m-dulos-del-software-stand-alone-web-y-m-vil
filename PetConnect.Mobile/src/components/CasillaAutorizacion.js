import { View, Text, Pressable, Linking, StyleSheet } from "react-native";
import { POLITICA_URL } from "../services/api";

// Casilla de autorización de datos (Ley 1581, arts. 9 y 12; ítems 3.1 y 3.5).
// Textos B.1 (casilla) y B.2 (aviso corto) de
// Documentacion/Legal/POLITICA-TRATAMIENTO-DATOS-v1.0-BORRADOR.md, los mismos de
// la web (src/components/CasillaAutorizacion.jsx).
// Es el ÚNICO lugar del móvil con este texto legal: lo usan el registro
// (RegisterScreen.js) y el inicio de sesión de cuentas sin autorización vigente
// (LoginScreen.js). Si cambia el texto, cambia también la web, el .md y la
// versión de la política (VERSION_POLITICA_DATOS en api.py).
//
// La casilla la controla quien la usa (marcada + onCambiar) y debe empezar SIN
// marcar: el silencio no es autorización. `pista` es lo que TalkBack dice después
// de leerla; `onErrorEnlace(mensaje)` avisa si el navegador no se pudo abrir.
export default function CasillaAutorizacion({ marcada, onCambiar, pista, onErrorEnlace }) {
  async function abrirPolitica() {
    // La pantalla sigue abierta detrás del navegador: lo escrito no se pierde.
    try {
      await Linking.openURL(POLITICA_URL);
    } catch {
      onErrorEnlace?.("No se pudo abrir la política en el navegador. Intenta de nuevo.");
    }
  }

  return (
    <View style={styles.autorizacion}>
      <Pressable
        style={styles.casillaFila}
        onPress={onCambiar}
        role="checkbox"
        aria-checked={marcada}
        accessibilityHint={pista}
      >
        <View style={[styles.casilla, marcada && styles.casillaMarcada]}>
          {marcada ? <Text style={styles.casillaCheck}>✓</Text> : null}
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
        {/* Correo de atención del proyecto (D.1, 06/11/2026); el mismo de la web (CasillaAutorizacion.jsx y PoliticaDatos.jsx) */}
        <Text style={styles.avisoCorreo}>proyectopetconnect+atencion@gmail.com.</Text>
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
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
  pressed: { opacity: 0.7 },
});
