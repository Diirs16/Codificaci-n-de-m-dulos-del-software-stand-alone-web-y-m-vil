import { useEffect, useState } from "react";
import { View, Text, Image, ScrollView, StyleSheet, ActivityIndicator } from "react-native";
import { getMascota } from "../services/api";

function Badge({ label, value }) {
  return (
    <View style={styles.badge}>
      <Text style={styles.badgeLabel}>{label}</Text>
      <Text style={styles.badgeValue}>{value ? "Sí" : "No"}</Text>
    </View>
  );
}

export default function PetDetailScreen({ route }) {
  const { id } = route.params;
  const [mascota, setMascota] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getMascota(id).then(setMascota).catch((e) => setError(e.message));
  }, [id]);

  if (error) return <View style={styles.center}><Text style={styles.errorText}>{error}</Text></View>;
  if (!mascota) return <View style={styles.center}><ActivityIndicator size="large" color="#0f766e" /></View>;

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Image source={{ uri: mascota.image }} style={styles.image} />
      <Text style={styles.name}>{mascota.name}</Text>
      <Text style={styles.meta}>{mascota.species} · {mascota.breed}</Text>
      <Text style={styles.meta}>{mascota.age ? `${mascota.age} años` : ""} · {mascota.gender} · Talla {mascota.size}</Text>
      <Text style={styles.description}>{mascota.description}</Text>
      <View style={styles.badges}>
        <Badge label="Vacunada" value={mascota.vaccinated} />
        <Badge label="Esterilizada" value={mascota.sterilized} />
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
  badges: { flexDirection: "row", gap: 12, marginTop: 16 },
  badge: { backgroundColor: "#f0fdfa", borderRadius: 10, padding: 10, alignItems: "center", flex: 1 },
  badgeLabel: { fontSize: 12, color: "#0f766e" },
  badgeValue: { fontSize: 15, fontWeight: "700", color: "#0f172a", marginTop: 2 },
});
