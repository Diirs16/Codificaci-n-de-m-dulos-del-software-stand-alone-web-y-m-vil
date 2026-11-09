import {
  View,
  Text,
  FlatList,
  Image,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { getProductos } from "../services/api";
import BotonVerMas from "../components/BotonVerMas";
import { useListaPaginada } from "../hooks/useListaPaginada";
import { POR_PAGINA_CATALOGO } from "../utils/paginacion";

export default function HomeScreen({ navigation }) {
  // Ítem 4.17 (NC-003): el catálogo se pide de 20 en 20; "Ver más" trae los siguientes.
  const {
    items: productos,
    loading,
    error,
    hayMas,
    verMas,
    cargandoMas,
    errorMas,
  } = useListaPaginada(getProductos, POR_PAGINA_CATALOGO);

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
      data={productos}
      keyExtractor={(item) => String(item.id)}
      numColumns={2}
      contentContainerStyle={styles.list}
      columnWrapperStyle={styles.row}
      ListHeaderComponent={
        <Text style={styles.title}>Catálogo de productos</Text>
      }
      ListFooterComponent={
        <BotonVerMas
          hayMas={hayMas}
          cargando={cargandoMas}
          error={errorMas}
          onVerMas={verMas}
          texto="Ver más productos"
        />
      }
      renderItem={({ item }) => (
        <TouchableOpacity
          style={styles.card}
          onPress={() => navigation.navigate("ProductDetail", { id: item.id })}
        >
          <Image source={{ uri: item.image }} style={styles.image} />
          <Text style={styles.name} numberOfLines={2}>{item.name}</Text>
          <Text style={styles.price}>$ {Number(item.price).toLocaleString("es-CO")}</Text>
        </TouchableOpacity>
      )}
    />
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24 },
  errorText: { color: "#b91c1c", textAlign: "center" },
  list: { padding: 12 },
  row: { justifyContent: "space-between" },
  title: { fontSize: 20, fontWeight: "700", marginBottom: 12, color: "#0f172a" },
  card: {
    width: "48%",
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 8,
    marginBottom: 14,
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 2,
  },
  image: { width: "100%", height: 110, borderRadius: 8, marginBottom: 6 },
  name: { fontSize: 13, fontWeight: "600", color: "#0f172a" },
  price: { fontSize: 14, fontWeight: "700", color: "#0f766e", marginTop: 4 },
});
