// Aviso "X agregado al carrito" (lo usan ProductCard.jsx y ProductDetail.jsx).
// Ítem 6.4 (A-25): todo se arma con funciones del DOM, sin innerHTML. El nombre
// del producto viene de la BD y se pone con textContent: si trajera
// "<img src=x onerror=...>", se ve como texto y el navegador no lo ejecuta (XSS).
const SVG_NS = "http://www.w3.org/2000/svg";

function crearIconoCheck() {
  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("width", "16");
  svg.setAttribute("height", "16");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("fill", "none");
  svg.setAttribute("stroke", "currentColor");
  svg.setAttribute("stroke-width", "2.5");
  svg.setAttribute("stroke-linecap", "round");
  svg.setAttribute("stroke-linejoin", "round");
  svg.setAttribute("aria-hidden", "true");

  const trazo = document.createElementNS(SVG_NS, "path");
  trazo.setAttribute("d", "M20 6L9 17l-5-5");
  svg.appendChild(trazo);
  return svg;
}

export function showAddToCartToast(productName) {
  const existing = document.querySelector(".cart-toast");
  if (existing) existing.remove();

  const toast = document.createElement("div");
  toast.className = "cart-toast toast-enter";
  // Zona de estado: los lectores de pantalla anuncian el aviso
  toast.setAttribute("role", "status");
  toast.style.cssText = `
    position: fixed;
    top: 80px;
    right: 20px;
    background: #111;
    color: #fff;
    padding: 12px 20px;
    border-radius: 8px;
    font-size: 14px;
    z-index: 100;
    box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    display: flex;
    align-items: center;
    gap: 8px;
    max-width: 320px;
  `;

  const texto = document.createElement("span");
  texto.textContent = `${productName} agregado al carrito`;

  toast.appendChild(crearIconoCheck());
  toast.appendChild(texto);
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.classList.remove("toast-enter");
    toast.classList.add("toast-exit");
    toast.addEventListener("animationend", () => toast.remove());
  }, 2500);
}
