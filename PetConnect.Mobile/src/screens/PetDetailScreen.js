import { useEffect, useState } from "react";
import { View, Text, Image, ScrollView, Pressable, StyleSheet, ActivityIndicator } from "react-native";
import { getMascota } from "../services/api";
import { datosMascota } from "../utils/mascota";
import FormularioSolicitud from "../components/FormularioSolicitud";

export default function PetDetailScreen({ route }) {
  const { id } = route.params;
  const [mascota, setMascota] = useState(null);
  const [error, setError] = useState(null);
  // Ítem 3.6 parte 3 (A-21): el formulario de adopción se abre debajo de la ficha.
  const [formularioAbierto, setFormularioAbierto] = useState(false);

  useEffect(() => {
    getMascota(id).then(setMascota).catch((e) => setError(e.message));
  }, [id]);

  if (error) return <View style={styles.center}><Text style={styles.errorText}>{error}</Text></View>;
  if (!mascota) return <View style={styles.center}><ActivityIndicator size="large" color="#0f766e" /></View>;

  // Ítem 3.4 (A-22): solo lo que la API sabe ("Raza · Edad · Sexo"); la BD no
  // tiene vacunación, esterilización ni tamaño, así que no se muestran.
  const datos = datosMascota(mascota);

  return (
    <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
      <Image source={{ uri: mascota.image }} style={styles.image} role="img" aria-label={mascota.name} />
      <Text style={styles.name}>{mascota.name}</Text>
      {mascota.species ? <Text style={styles.meta}>{mascota.species}</Text> : null}
      {datos ? <Text style={styles.meta}>{datos}</Text> : null}
      <Text style={styles.description}>{mascota.description}</Text>

      <View style={styles.solicitud}>
        {formularioAbierto ? (
          <FormularioSolicitud
            tipo="adopcion"
            mascota={{ id, name: mascota.name }}
            onCerrar={() => setFormularioAbierto(false)}
          />
        ) : (
          <Pressable
            style={({ pressed }) => [styles.botonSolicitar, pressed && styles.pressed]}
            onPress={() => setFormularioAbierto(true)}
            role="button"
          >
            <Text style={styles.botonSolicitarTexto}>Solicitar adopción</Text>
          </Pressable>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  errorText: { color: "#b91c1c" },
  container: { padding: 16 },
  image: { width: "100%", height: 240, borderRadius: 12, marginBottom: 16 },
  name: { fontSize: 22, fontWeight: "700", color: "#0f172a" },
  meta: { fontSize: 14, color: "#64748b", marginTop: 4 },
  description: { fontSize: 15, color: "#475569", lineHeight: 22, marginTop: 12 },
  solicitud: { marginTop: 24, marginBottom: 8 },
  botonSolicitar: {
    backgroundColor: "#0f766e",
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: "center",
    justifyContent: "center",
    minHeight: 48,
  },
  botonSolicitarTexto: { color: "#fff", fontWeight: "700", fontSize: 15 },
  pressed: { opacity: 0.7 },
});
