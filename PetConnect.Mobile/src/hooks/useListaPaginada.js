import { useEffect, useRef, useState } from "react";
import { hayMas, unirSinRepetir } from "../utils/paginacion";

// Ítem 4.17 (NC-003): lista que se carga por páginas, con "Ver más".
// La usan HomeScreen.js y AdoptionScreen.js. Es el mismo hook de la web
// (PetConnect.Front/petconnect-app/src/hooks/useListaPaginada.js).
//
// pedirPagina: función de api.js que recibe { pagina, porPagina } y devuelve
//              una lista (getProductos, getMascotasAdopcion). Debe ser siempre
//              la misma función (no una creada en cada render).
// porPagina:   cuántos pide cada vez.
//
// Devuelve:
//   items      todo lo cargado hasta ahora
//   loading    true mientras llega la PRIMERA página
//   error      mensaje si la primera página falló (null si no)
//   hayMas     true si la última página llegó llena
//   verMas     pide la página siguiente y la agrega al final
//   cargandoMas, errorMas: estado del último "Ver más". Si falla, lo ya
//              cargado se queda en pantalla y se puede intentar otra vez.
export function useListaPaginada(pedirPagina, porPagina) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagina, setPagina] = useState(1); // última página cargada
  const [masPaginas, setMasPaginas] = useState(false);
  const [cargandoMas, setCargandoMas] = useState(false);
  const [errorMas, setErrorMas] = useState(false);
  // Evita actualizar la pantalla si el usuario ya salió mientras llegaba la respuesta
  const montado = useRef(true);

  useEffect(() => {
    montado.current = true;
    return () => {
      montado.current = false;
    };
  }, []);

  useEffect(() => {
    let vigente = true;
    pedirPagina({ pagina: 1, porPagina })
      .then((data) => {
        if (!vigente) return;
        setItems(data);
        setPagina(1);
        setMasPaginas(hayMas(data, porPagina));
      })
      .catch((e) => {
        if (vigente) setError(e.message);
      })
      .finally(() => {
        if (vigente) setLoading(false);
      });
    return () => {
      vigente = false;
    };
  }, [pedirPagina, porPagina]);

  async function verMas() {
    if (cargandoMas) return; // un toque doble no pide la misma página dos veces
    setCargandoMas(true);
    setErrorMas(false);
    try {
      const siguiente = pagina + 1;
      const data = await pedirPagina({ pagina: siguiente, porPagina });
      if (!montado.current) return;
      setItems((actuales) => unirSinRepetir(actuales, data));
      setPagina(siguiente);
      setMasPaginas(hayMas(data, porPagina));
    } catch {
      if (montado.current) setErrorMas(true);
    } finally {
      if (montado.current) setCargandoMas(false);
    }
  }

  return { items, loading, error, hayMas: masPaginas, verMas, cargandoMas, errorMas };
}
