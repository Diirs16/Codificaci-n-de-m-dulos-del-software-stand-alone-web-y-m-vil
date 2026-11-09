import { View, Text, Pressable, ActivityIndicator, StyleSheet } from "react-native";

// Ítem 4.17 (NC-003): botón al pie de una lista que se carga por páginas
// (ListFooterComponent de la FlatList). No se muestra si ya no hay más.
// Mientras carga queda desactivado (un toque doble no pide dos veces) y, si
// falla, avisa sin borrar lo que ya se ve. Mismo texto que la web.
export default function BotonVerMas({ hayMas, cargando, error, onVerMas, texto = "Ver más" }) {
  if (!hayMas) return null;

  return (
    <View style={styles.contenedor}>
      {error ? (
        <Text style={styles.textoError} role="alert">
          No pudimos cargar más. Revisa tu conexión e inténtalo de nuevo.
        </Text>
      ) : null}
      <Pressable
        style={({ pressed }) => [styles.boton, pressed && styles.presionado, cargando && styles.inactivo]}
        onPress={onVerMas}
        disabled={cargando}
        role="button"
        aria-label={cargando ? "Cargando…" : texto}
        aria-disabled={cargando}
        aria-busy={cargando}
      >
        {cargando ? (
          <ActivityIndicator color="#0f766e" />
        ) : (
          <Text style={styles.texto}>{texto}</Text>
        )}
      </Pressable>
    </View>
  );
}

// Mismos colores y medidas que el botón secundario de FormularioSolicitud.js
const styles = StyleSheet.create({
  contenedor: { gap: 8, paddingTop: 4, paddingBottom: 16 },
  boton: {
    borderWidth: 1,
    borderColor: "#0f766e",
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 16,
    alignItems: "center",
    justifyContent: "center",
    minHeight: 48,
    backgroundColor: "#fff",
  },
  texto: { color: "#0f766e", fontWeight: "700", fontSize: 15 },
  inactivo: { borderColor: "#cbd5e1" },
  presionado: { opacity: 0.7 },
  textoError: { fontSize: 14, lineHeight: 20, color: "#991b1b", textAlign: "center" },
});
