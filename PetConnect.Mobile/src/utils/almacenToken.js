// Ítem 5.3, parte 2 (A-28): dónde guarda el móvil el token de la sesión.
// JavaScript puro (sin React Native) para que `npm test` lo pruebe con Node
// (tests/almacen-token.test.mjs). Lo usa src/services/api.js.
//
// Antes el token iba en AsyncStorage: un archivo SIN cifrar dentro de la app.
// Ahora, en Android e iOS, va en expo-secure-store (SecureStore): Android lo
// cifra con una llave del Keystore del sistema e iOS lo guarda en el Keychain.
// En web SecureStore no existe (documentación de Expo 57): ahí el token sigue
// en AsyncStorage, que en el navegador es localStorage, igual que la web React
// (decisión del dueño, 10/11/2026).
//
// Quien ya tenía sesión iniciada antes de este cambio tiene el token en
// AsyncStorage: la primera vez que se lee, se pasa a SecureStore y se borra de
// AsyncStorage (no se le cierra la sesión a nadie).
//
// Los avisos (avisar) van solo a la consola de Metro y NUNCA llevan el token.

// SecureStore solo acepta letras, números, ".", "-" y "_" en la clave.
export const CLAVE_TOKEN = "petconnect_token";

/**
 * Crea el almacén del token.
 *   seguro: SecureStore (getItemAsync, setItemAsync, deleteItemAsync), o null en web.
 *   viejo:  AsyncStorage (getItem, setItem, removeItem).
 *   avisar: función que recibe un texto sin datos (p. ej. console.warn).
 * Devuelve { leer, guardar, borrar }. Ninguna lanza error: si un almacén falla,
 * se avisa y se sigue (el usuario no queda atrapado en una pantalla de error).
 */
export function crearAlmacenToken({ seguro = null, viejo, clave = CLAVE_TOKEN, avisar = () => {} }) {
  // Respaldo si el celular no deja guardar el token (setItemAsync rechaza): la
  // sesión sirve mientras la app esté abierta, pero NO se guarda sin cifrar.
  // Al cerrar la app hay que volver a iniciar sesión.
  let enMemoria = null;

  // Ejecuta una operación de un almacén; si falla, avisa y devuelve `siFalla`.
  async function intentar(operacion, aviso, siFalla = null) {
    try {
      return await operacion();
    } catch {
      avisar(aviso);
      return siFalla;
    }
  }

  // En web (sin SecureStore) se usa solo AsyncStorage, como antes.
  async function leerWeb() {
    return (await intentar(() => viejo.getItem(clave), "no se pudo leer la sesión guardada")) || null;
  }

  async function leer() {
    if (enMemoria) return enMemoria;
    if (!seguro) return leerWeb();

    const token = await intentar(() => seguro.getItemAsync(clave), "no se pudo leer el almacén seguro");
    if (token) return token;

    // ¿Sesión de antes de este cambio? Pasarla de AsyncStorage a SecureStore.
    const tokenViejo = await intentar(() => viejo.getItem(clave), "no se pudo leer la sesión anterior");
    if (!tokenViejo) return null;

    const copiado = await intentar(
      async () => {
        await seguro.setItemAsync(clave, tokenViejo);
        return true;
      },
      "no se pudo pasar la sesión al almacén seguro; se intentará de nuevo",
      false,
    );
    // Solo se borra de AsyncStorage si ya quedó en SecureStore: si no, la sesión
    // se perdería. Queda donde estaba y se vuelve a intentar en la próxima lectura.
    if (copiado) {
      await intentar(() => viejo.removeItem(clave), "no se pudo borrar la sesión anterior sin cifrar");
    }
    return tokenViejo;
  }

  async function guardar(token) {
    enMemoria = null;
    if (!seguro) {
      const guardado = await intentar(
        async () => {
          await viejo.setItem(clave, token);
          return true;
        },
        "no se pudo guardar la sesión; durará hasta cerrar la página",
        false,
      );
      if (!guardado) enMemoria = token;
      return;
    }

    const guardado = await intentar(
      async () => {
        await seguro.setItemAsync(clave, token);
        return true;
      },
      "no se pudo guardar la sesión en el almacén seguro; durará hasta cerrar la app",
      false,
    );
    if (!guardado) enMemoria = token;
    // Un token viejo sin cifrar que haya quedado (de antes del cambio) sobra.
    await intentar(() => viejo.removeItem(clave), "no se pudo borrar la sesión anterior sin cifrar");
  }

  async function borrar() {
    enMemoria = null;
    if (seguro) {
      await intentar(() => seguro.deleteItemAsync(clave), "no se pudo borrar la sesión del almacén seguro");
    }
    // También en móvil: por si quedaba un token de antes del cambio.
    await intentar(() => viejo.removeItem(clave), "no se pudo borrar la sesión guardada");
  }

  return { leer, guardar, borrar };
}

/** SecureStore solo existe en Android e iOS (en web el módulo viene vacío). */
export function tieneAlmacenSeguro(plataforma) {
  return plataforma === "android" || plataforma === "ios";
}
