import { useEffect, useState } from "react";
import { View, Text, Image, ScrollView, StyleSheet, ActivityIndicator } from "react-native";
import { getMascota } from "../services/api";
import { datosMascota } from "../utils/mascota";

export default function PetDetailScreen({ route }) {
  const { id } = route.params;
  const [mascota, setMascota] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getMascota(id).then(setMascota).catch((e) => setError(e.message));
  }, [id]);

  if (error) return <View style={styles.center}><Text style={styles.errorText}>{error}</Text></View>;
  if (!mascota) return <View style={styles.center}><ActivityIndicator size="large" color="#0f766e" /></View>;

  // Ítem 3.4 (A-22): solo lo que la API sabe ("Raza · Edad · Sexo"); la BD no
  // tiene vacunación, esterilización ni tamaño, así que no se muestran.
  const datos = datosMascota(mascota);

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Image source={{ uri: mascota.image }} style={styles.image} role="img" aria-label={mascota.name} />
      <Text style={styles.name}>{mascota.name}</Text>
      {mascota.species ? <Text style={styles.meta}>{mascota.species}</Text> : null}
      {datos ? <Text style={styles.meta}>{datos}</Text> : null}
      <Text style={styles.description}>{mascota.description}</Text>
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
});
