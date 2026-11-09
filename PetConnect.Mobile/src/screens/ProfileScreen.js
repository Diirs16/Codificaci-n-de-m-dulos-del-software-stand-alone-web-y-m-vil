import { useState } from "react";
import { View, Text, TouchableOpacity, StyleSheet, Alert } from "react-native";
import { useAuth } from "../context/AuthContext";

// Ítem 4.13 (A-03, decisión A1 del dueño): mismo aviso que la web cuando el servidor
// no pudo confirmar el cierre. Va en un Alert.alert (ventana nativa) porque, al
// borrarse la sesión, esta pantalla desaparece y en su lugar sale "Iniciar sesión":
// un texto puesto aquí no alcanzaría a verse. TalkBack lee el Alert solo.
export const AVISO_CIERRE_TITULO = "Sesión cerrada en este celular";
export const AVISO_CIERRE_TEXTO =
  "Cerraste sesión en este celular, pero no pudimos confirmarlo con el servidor. " +
  "Si usas PetConnect en otro aparato, cierra sesión también allí.";

export default function ProfileScreen() {
  const { user, logout } = useAuth();
  const [cerrando, setCerrando] = useState(false);

  // Decisión B1 del dueño: el botón queda desactivado mientras se espera a la API
  // (máximo 8 s, TIEMPO_CIERRE_MS); así no se manda dos veces.
  async function salir() {
    if (cerrando) return;
    setCerrando(true);
    try {
      const resultado = await logout();
      if (resultado === "sin-confirmar") {
        Alert.alert(AVISO_CIERRE_TITULO, AVISO_CIERRE_TEXTO, [{ text: "Entendido" }]);
      }
    } finally {
      setCerrando(false);
    }
  }

  return (
    <View style={styles.container}>
      <View style={styles.avatar}>
        <Text style={styles.avatarText}>{user?.name?.charAt(0)?.toUpperCase() ?? "?"}</Text>
      </View>
      <Text style={styles.name}>{user?.name}</Text>
      <Text style={styles.email}>{user?.email}</Text>

      <TouchableOpacity
        style={[styles.button, cerrando && styles.buttonEsperando]}
        onPress={salir}
        disabled={cerrando}
        accessibilityRole="button"
        accessibilityState={{ disabled: cerrando, busy: cerrando }}
      >
        <Text style={styles.buttonText}>{cerrando ? "Cerrando sesión…" : "Cerrar sesión"}</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24 },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: "#0f766e",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 16,
  },
  avatarText: { color: "#fff", fontSize: 32, fontWeight: "700" },
  name: { fontSize: 20, fontWeight: "700", color: "#0f172a" },
  email: { fontSize: 14, color: "#64748b", marginTop: 4, marginBottom: 24 },
  button: {
    backgroundColor: "#b91c1c",
    borderRadius: 10,
    minHeight: 48, // tamaño mínimo de toque recomendado en Android
    justifyContent: "center",
    paddingVertical: 12,
    paddingHorizontal: 24,
  },
  // Mientras espera: rojo más oscuro (no más tenue: con transparencia el texto blanco
  // bajaría de 4,5:1 de contraste)
  buttonEsperando: { backgroundColor: "#7f1d1d" },
  buttonText: { color: "#fff", fontWeight: "700" },
});
