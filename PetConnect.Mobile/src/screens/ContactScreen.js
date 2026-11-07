import { ScrollView, Text, StyleSheet } from "react-native";
import FormularioSolicitud from "../components/FormularioSolicitud";

// Ítem 3.6 parte 3 (A-21): pestaña "Contacto" (decisión del dueño, 07/11/2026).
// Igual que la página Contacto de la web: el formulario real de contacto. Sin sesión,
// el formulario muestra "Inicia sesión para enviar" y no deja escribir.
export default function ContactScreen() {
  return (
    <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
      <Text style={styles.title} role="heading">
        ¿Tienes una pregunta?
      </Text>
      <Text style={styles.subtitle}>
        Escríbenos sobre la adopción, los productos o tu cuenta. El equipo de PetConnect te responderá al correo de
        tu cuenta.
      </Text>
      <FormularioSolicitud tipo="contacto" />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, paddingBottom: 32 },
  title: { fontSize: 22, fontWeight: "700", color: "#0f172a" },
  subtitle: { fontSize: 14, lineHeight: 20, color: "#475569", marginTop: 6, marginBottom: 16 },
});
