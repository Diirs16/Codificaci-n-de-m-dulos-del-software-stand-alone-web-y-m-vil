# Web PetConnect — reglas del módulo

Se carga además del `CLAUDE.md` de la raíz cuando Claude trabaja dentro de esta carpeta.

## Estructura
- `src/pages/` — una página por ruta (Home, Catalog, Adoption, PetDetail, ProductDetail, Checkout, Confirmation, Contact).
- `src/components/` — piezas reutilizables (Header, Footer, ProductCard, modales).
- `src/context/` — estado global (`AuthContext`, `CartContext`).
- `src/services/api.js` — **única** puerta hacia el backend (`/api`, con el token JWT en `localStorage`).
- Sin datos de ejemplo: todo sale de la API. Las páginas muestran cargando / vacío / error con
  `src/components/EstadoCarga.jsx` (ítem 3.3); `tests/sin-datos-falsos.test.js` impide volver a importar `data/`.
- Estilos con Tailwind 4 (`src/index.css`) y animaciones en `src/assets/css/animations.css`. Iconos con `lucide-react`.

## Reglas
- Las llamadas HTTP nuevas se agregan como funciones en `src/services/api.js`; las páginas no usan `fetch` directo.
- Componentes funcionales con hooks. Nada de librerías nuevas de UI sin preguntar.
- Diseño *mobile first*: probar a 375 px de ancho. Botones de acción grandes y visibles.
- Accesibilidad: `alt` en imágenes, `label` en formularios, foco visible, contraste AA.
- Variables de entorno del navegador solo con prefijo `VITE_` y **nunca** secretos (todo lo que lleva
  `VITE_` lo puede ver cualquiera en el navegador).

## Verificar
```bash
npm run lint
npm run build
npm run dev   # http://localhost:5173 (necesita el backend en :5000)
```
