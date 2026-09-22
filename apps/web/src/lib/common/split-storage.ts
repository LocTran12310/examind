/** Where a resizable split remembers its layout: the browser's localStorage, or nothing on the server / when blocked
 *  (react-resizable-panels falls back to the global `localStorage` when given undefined, which breaks server rendering). */
const NONE = { getItem: (): string | null => null, setItem: (): void => {} };

export function splitStorage(): Pick<Storage, "getItem" | "setItem"> {
  try {
    return typeof window === "undefined" ? NONE : window.localStorage;
  } catch {
    return NONE;
  }
}
