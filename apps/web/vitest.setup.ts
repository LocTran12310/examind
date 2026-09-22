import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(() => {
  cleanup();
  document.body.removeAttribute("style"); // Radix leaves pointer-events:none when a test ends with a menu open
});

// jsdom gaps used by Radix (shadcn), next-themes and the sidebar's useIsMobile.
if (!window.matchMedia) {
  window.matchMedia = (query: string) =>
    ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    }) as unknown as MediaQueryList;
}
class RO {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver ??= RO as unknown as typeof ResizeObserver;
const proto = Element.prototype as unknown as Record<string, unknown>;
proto.hasPointerCapture ??= () => false;
proto.setPointerCapture ??= () => {};
proto.releasePointerCapture ??= () => {};
proto.scrollIntoView ??= () => {};
// jsdom fires window "blur" when focus moves after a previous test's unmount; Radix menus close on
// window blur, so every menu after the first would close instantly. Tests never need window blur.
window.addEventListener("blur", (e) => e.stopImmediatePropagation(), { capture: true });
