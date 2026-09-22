"use client";

import { useEffect, useRef, useState } from "react";

/** Apple keyboards say ⌘, others Ctrl. */
export function isApple(): boolean {
  if (typeof navigator === "undefined") return false;
  return /Mac|iPhone|iPad|iPod/i.test(navigator.platform || navigator.userAgent);
}

/** "⌘ Enter" on a Mac, "Ctrl + Enter" elsewhere (after mount, so server and client render alike). */
export function useSaveHint(): string {
  const [hint, setHint] = useState("Ctrl + Enter");
  useEffect(() => setHint(isApple() ? "⌘ Enter" : "Ctrl + Enter"), []);
  return hint;
}

/** True for ⌘/Ctrl + Enter, also while an IME (Vietnamese Telex/VNI) is composing: then `key` is
 *  "Process" and only the physical `code` says Enter. */
export function isSaveKey(e: KeyboardEvent | React.KeyboardEvent): boolean {
  const k = e as KeyboardEvent;
  return (k.metaKey || k.ctrlKey) && (k.key === "Enter" || k.code === "Enter" || k.code === "NumpadEnter" || k.keyCode === 13);
}

/** ⌘/Ctrl + Enter anywhere on the page while mounted (ui-polish AC-05). */
export function useSaveShortcut(handler: () => void, enabled = true): void {
  const ref = useRef(handler);
  ref.current = handler;
  useEffect(() => {
    if (!enabled) return;
    const onKey = (e: KeyboardEvent) => {
      if (!isSaveKey(e)) return;
      e.preventDefault();
      e.stopPropagation();
      ref.current();
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [enabled]);
}
