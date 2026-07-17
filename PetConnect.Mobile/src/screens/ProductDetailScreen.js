import { useEffect, useState } from "react";
import { View, Text, Image, ScrollView, StyleSheet, ActivityIndicator } from "react-native";
import { getProducto } from "../services/api";

export default function ProductDetailScreen({ route }) {
  const { id } = route.params;
  const [producto, setProducto] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getProducto(id).then(setProducto).catch((e) => setError(e.message));
  }, [id]);

  if (error) return <View style={styles.center}><Text style={styles.errorText}>{error}</Text></View>;
  if (!producto) return <View style={styles.center}><ActivityIndicator size="large" color="#0f766e" /></View>;

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Image source={{ uri: producto.image }} style={styles.image} />
      <Text style={styles.category}>{producto.category}</Text>
      <Text style={styles.name}>{producto.name}</Text>
      <Text style={styles.price}>$ {Number(producto.price).toLocaleString("es-CO")}</Text>
      <Text style={styles.description}>{producto.description}</Text>
      <Text style={styles.stock}>Stock disponible: {producto.stock} unidades</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  errorText: { color: "#b91c1c" },
  container: { padding: 16 },
  image: { width: "100%", height: 240, borderRadius: 12, marginBottom: 16 },
  category: { color: "#0f766e", fontWeight: "600", marginBottom: 4 },
  name: { fontSize: 22, fontWeight: "700", color: "#0f172a", marginBottom: 8 },
  price: { fontSize: 20, fontWeight: "700", color: "#0f766e", marginBottom: 12 },
  description: { fontSize: 15, color: "#475569", lineHeight: 22, marginBottom: 12 },
  stock: { fontSize: 13, color: "#64748b" },
});
