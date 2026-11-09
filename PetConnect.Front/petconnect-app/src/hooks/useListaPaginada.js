import { useEffect, useRef, useState } from "react";
import { hayMas, unirSinRepetir } from "../utils/paginacion.js";

// Ítem 4.17 (NC-003): lista que se carga por páginas, con "Ver más".
// La usan Adoption.jsx y Catalog.jsx para no repetir la misma lógica.
//
// pedirPagina: función de api.js que recibe { pagina, porPagina } y devuelve
//              una lista (getProductos, getMascotasAdopcion). Debe ser siempre
//              la misma función (no una creada en cada render).
// porPagina:   cuántos pide cada vez.
//
// Devuelve:
//   items      todo lo cargado hasta ahora
//   estado     "cargando" | "error" | "listo" (de la PRIMERA página, como antes)
//   reintentar vuelve a pedir la primera página
//   hayMas     true si la última página llegó llena
//   verMas     pide la página siguiente y la agrega al final
//   cargandoMas, errorMas: estado del último "Ver más". Si falla, lo ya
//              cargado se queda en pantalla y se puede intentar otra vez.
export function useListaPaginada(pedirPagina, porPagina) {
  const [items, setItems] = useState([]);
  const [estado, setEstado] = useState("cargando");
  const [intento, setIntento] = useState(0); // al sumar 1, se vuelve a pedir la primera página
  const [pagina, setPagina] = useState(1); // última página cargada
  const [masPaginas, setMasPaginas] = useState(false);
  const [cargandoMas, setCargandoMas] = useState(false);
  const [errorMas, setErrorMas] = useState(false);
  // Evita actualizar la página si el usuario ya se fue mientras llegaba la respuesta
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
        setErrorMas(false);
        setEstado("listo");
      })
      .catch(() => {
        if (vigente) setEstado("error");
      });
    return () => {
      vigente = false;
    };
  }, [pedirPagina, porPagina, intento]);

  function reintentar() {
    setEstado("cargando");
    setIntento((n) => n + 1);
  }

  async function verMas() {
    if (cargandoMas) return; // un clic doble no pide la misma página dos veces
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

  return { items, estado, reintentar, hayMas: masPaginas, verMas, cargandoMas, errorMas };
}
