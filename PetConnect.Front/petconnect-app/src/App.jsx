import { Routes, Route } from "react-router-dom";
import Header from "./components/Header";
import Footer from "./components/Footer";
import CartModal from "./components/CartModal";
import LoginModal from "./components/LoginModal";
import RegisterModal from "./components/RegisterModal";
import Home from "./pages/Home";
import Catalog from "./pages/Catalog";
import ProductDetail from "./pages/ProductDetail";
import Checkout from "./pages/Checkout";
import Confirmation from "./pages/Confirmation";
import Adoption from "./pages/Adoption";
import PetDetail from "./pages/PetDetail";
import Contact from "./pages/Contact";

export default function App() {
  return (
    <>
      <Header />
      <div className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/catalogo" element={<Catalog />} />
          <Route path="/producto/:id" element={<ProductDetail />} />
          <Route path="/checkout" element={<Checkout />} />
          <Route path="/confirmacion" element={<Confirmation />} />
          <Route path="/adopcion" element={<Adoption />} />
          <Route path="/adopcion/:id" element={<PetDetail />} />
          <Route path="/contacto" element={<Contact />} />
        </Routes>
      </div>
      <Footer />
      <CartModal />
      <LoginModal />
      <RegisterModal />
    </>
  );
}
