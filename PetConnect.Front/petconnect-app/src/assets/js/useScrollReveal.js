import { useEffect } from "react";
import { initScrollReveal } from "./scrollReveal";

export function useScrollReveal() {
  useEffect(() => {
    const timer = setTimeout(() => {
      const cleanup = initScrollReveal();
      return cleanup;
    }, 100);
    return () => clearTimeout(timer);
  });
}
