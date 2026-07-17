export function showAddToCartToast(productName) {
  const existing = document.querySelector(".cart-toast");
  if (existing) existing.remove();

  const toast = document.createElement("div");
  toast.className = "cart-toast toast-enter";
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
  toast.innerHTML = `
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M20 6L9 17l-5-5"/>
    </svg>
    <span>${productName} agregado al carrito</span>
  `;

  document.body.appendChild(toast);

  setTimeout(() => {
    toast.classList.remove("toast-enter");
    toast.classList.add("toast-exit");
    toast.addEventListener("animationend", () => toast.remove());
  }, 2500);
}
