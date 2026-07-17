import { useEffect, useState } from "react";
import {
  View,
  Text,
  FlatList,
  Image,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { getMascotasAdopcion } from "../services/api";

export default function AdoptionScreen({ navigation }) {
  const [mascotas, setMascotas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getMascotasAdopcion()
      .then(setMascotas)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#0f766e" />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>No se pudo conectar con la API: {error}</Text>
      </View>
    );
  }

  return (
    <FlatList
      data={mascotas}
      keyExtractor={(item) => String(item.id)}
      contentContainerStyle={styles.list}
      ListHeaderComponent={
        <Text style={styles.title}>Mascotas en adopción</Text>
      }
      ListEmptyComponent={
        <Text style={styles.empty}>
          No hay mascotas en adopción registradas en este momento.
        </Text>
      }
      renderItem={({ item }) => (
        <TouchableOpacity
          style={styles.card}
          onPress={() => navigation.navigate("PetDetail", { id: item.id })}
        >
          <Image source={{ uri: item.image }} style={styles.image} />
          <View style={{ flex: 1 }}>
            <Text style={styles.name}>{item.name}</Text>
            <Text style={styles.meta}>{item.species} · {item.breed}</Text>
            <Text style={styles.meta}>{item.age ? `${item.age} años` : ""} {item.gender}</Text>
          </View>
        </TouchableOpacity>
      )}
    />
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24 },
  errorText: { color: "#b91c1c", textAlign: "center" },
  list: { padding: 12 },
  title: { fontSize: 20, fontWeight: "700", marginBottom: 12, color: "#0f172a" },
  empty: { textAlign: "center", color: "#64748b", marginTop: 20 },
  card: {
    flexDirection: "row",
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 10,
    marginBottom: 12,
    alignItems: "center",
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 2,
  },
  image: { width: 70, height: 70, borderRadius: 10, marginRight: 12 },
  name: { fontSize: 16, fontWeight: "700", color: "#0f172a" },
  meta: { fontSize: 13, color: "#64748b" },
});
