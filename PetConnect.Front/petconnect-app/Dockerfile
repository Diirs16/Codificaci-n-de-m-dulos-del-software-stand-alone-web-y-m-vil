# ================================================================
# PETCONNECT Web — imagen de la pagina (item 5.2 de la auditoria, A-30)
#
# Construir (desde la carpeta raiz Evidecia):
#   docker build -t petconnect-web PetConnect.Front/petconnect-app
#
# Dos etapas ("multi-stage"):
#   1. "compilacion": Node instala las dependencias y compila la web
#      (npm run build) a archivos estaticos en dist/.
#   2. nginx sirve SOLO esos archivos de dist/. Node, node_modules y el
#      codigo fuente se quedan en la etapa 1 y no entran en la imagen final.
#
# Aqui NO se usa "npm run dev": ese es el servidor de desarrollo de Vite y
# su proxy a localhost:5000 no existe dentro de un contenedor. En su lugar,
# nginx pasa /api a la API (ver nginx.conf).
#
# NO lleva secretos: la web no necesita ninguno. Todo lo que lleva VITE_
# queda visible en el navegador, asi que nunca pongas aqui un ENV o ARG
# con una clave. La prueba tests/docker.test.js revisa este archivo.
# ================================================================

# ---------- Etapa 1: compilar la web con Node 24 (el mismo de la CI) ----------
FROM node:24-alpine AS compilacion

WORKDIR /app

# Primero solo package.json y package-lock.json: si el codigo cambia pero las
# dependencias no, Docker reutiliza esta capa y no reinstala todo.
# "npm ci" instala exactamente lo del package-lock.json (no lo modifica).
COPY package.json package-lock.json ./
RUN npm ci

# El resto del codigo (lo que el .dockerignore deja pasar: sin .env, sin
# node_modules ni dist locales) y la compilacion a dist/
COPY . .
RUN npm run build

# ---------- Etapa 2: servir dist/ con nginx (rama estable 1.30) ----------
# Version exacta para que la imagen sea la misma hoy y en unos meses.
# El proceso que atiende las peticiones corre con el usuario "nginx" (sin root).
FROM nginx:1.30.6-alpine

# Nuestra configuracion reemplaza el sitio de ejemplo de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Solo la web compilada, traida de la etapa 1
COPY --from=compilacion /app/dist /usr/share/nginx/html

EXPOSE 80

# Sin CMD propio: la imagen de nginx ya arranca con "nginx -g 'daemon off;'"
