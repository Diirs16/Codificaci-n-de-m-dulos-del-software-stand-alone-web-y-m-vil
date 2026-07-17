import { View, ActivityIndicator } from "react-native";

export default function LoadingScreen() {
  return (
    <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
      <ActivityIndicator size="large" color="#0f766e" />
    </View>
  );
}
