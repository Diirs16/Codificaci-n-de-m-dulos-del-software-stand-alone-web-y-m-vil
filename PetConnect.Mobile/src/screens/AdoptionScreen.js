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
import BotonVerMas from "../components/BotonVerMas";
import { useListaPaginada } from "../hooks/useListaPaginada";
import { datosMascota } from "../utils/mascota";
import { POR_PAGINA_ADOPCION } from "../utils/paginacion";

export default function AdoptionScreen({ navigation }) {
  // Ítem 4.17 (NC-003): se pide de 12 en 12; "Ver más" trae las siguientes.
  const {
    items: mascotas,
    loading,
    error,
    hayMas,
    verMas,
    cargandoMas,
    errorMas,
  } = useListaPaginada(getMascotasAdopcion, POR_PAGINA_ADOPCION);

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
      ListFooterComponent={
        <BotonVerMas
          hayMas={hayMas}
          cargando={cargandoMas}
          error={errorMas}
          onVerMas={verMas}
          texto="Ver más mascotas"
        />
      }
      renderItem={({ item }) => (
        <TouchableOpacity
          style={styles.card}
          onPress={() => navigation.navigate("PetDetail", { id: item.id })}
        >
          <Image source={{ uri: item.image }} style={styles.image} role="img" aria-label={item.name} />
          <View style={{ flex: 1 }}>
            <Text style={styles.name}>{item.name}</Text>
            {item.species ? <Text style={styles.meta}>{item.species}</Text> : null}
            {/* Ítem 3.4 (A-22): "Raza · Edad · Sexo" solo con lo que se conoce. */}
            {datosMascota(item) ? <Text style={styles.meta}>{datosMascota(item)}</Text> : null}
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
