import { useEffect } from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { Text } from "react-native";

import { useAuth } from "../context/AuthContext";
import LoadingScreen from "../screens/LoadingScreen";
import HomeScreen from "../screens/HomeScreen";
import ProductDetailScreen from "../screens/ProductDetailScreen";
import AdoptionScreen from "../screens/AdoptionScreen";
import PetDetailScreen from "../screens/PetDetailScreen";
import LoginScreen from "../screens/LoginScreen";
import RegisterScreen from "../screens/RegisterScreen";
import ProfileScreen from "../screens/ProfileScreen";
import ContactScreen from "../screens/ContactScreen";

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

function TabIcon({ emoji }) {
  return <Text style={{ fontSize: 18 }}>{emoji}</Text>;
}

function MainTabs() {
  const { user } = useAuth();
  return (
    <Tab.Navigator screenOptions={{ headerTintColor: "#0f172a", tabBarActiveTintColor: "#0f766e" }}>
      <Tab.Screen
        name="Catalogo"
        component={HomeScreen}
        options={{ title: "Tienda", tabBarIcon: () => <TabIcon emoji="🛍️" /> }}
      />
      <Tab.Screen
        name="Adopcion"
        component={AdoptionScreen}
        options={{ title: "Adopción", tabBarIcon: () => <TabIcon emoji="🐾" /> }}
      />
      {/* Ítem 3.6 parte 3: pestaña nueva (decisión del dueño, 07/11/2026) */}
      <Tab.Screen
        name="Contacto"
        component={ContactScreen}
        options={{ title: "Contacto", tabBarIcon: () => <TabIcon emoji="✉️" /> }}
      />
      <Tab.Screen
        name="Perfil"
        component={user ? ProfileScreen : LoginStack}
        options={{ title: "Perfil", tabBarIcon: () => <TabIcon emoji="👤" /> }}
      />
    </Tab.Navigator>
  );
}

function LoginStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="Register" component={RegisterScreen} />
    </Stack.Navigator>
  );
}

// Ítem 3.6 parte 3: el mismo inicio de sesión (y registro) que la pestaña Perfil, pero
// abierto ENCIMA de la pantalla actual. Así, desde el formulario de adopción o de
// contacto, la pantalla de abajo no se cierra y lo escrito no se pierde. Cuando la
// sesión queda iniciada, se cierra sola y vuelve al formulario.
function IniciarSesionModal({ navigation }) {
  const { user } = useAuth();
  useEffect(() => {
    if (user && navigation.canGoBack()) navigation.goBack();
  }, [user, navigation]);
  return <LoginStack />;
}

export default function AppNavigator() {
  const { loading } = useAuth();

  if (loading) return <LoadingScreen />;

  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen name="Main" component={MainTabs} options={{ headerShown: false }} />
        <Stack.Screen
          name="ProductDetail"
          component={ProductDetailScreen}
          options={{ title: "Producto" }}
        />
        <Stack.Screen
          name="PetDetail"
          component={PetDetailScreen}
          options={{ title: "Mascota" }}
        />
        <Stack.Screen
          name="IniciarSesion"
          component={IniciarSesionModal}
          options={{ title: "Iniciar sesión", presentation: "modal" }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
