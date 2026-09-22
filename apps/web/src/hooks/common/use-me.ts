"use client";

import { createContext, useContext } from "react";
import type { Me } from "@/interfaces/auth.interface";

const MeContext = createContext<Me | null>(null);

/** Provides the signed-in user; the shell sets it, tests and isolated widgets may too. */
export const MeProvider = MeContext.Provider;

/** The signed-in user when inside the shell, else null (components that also render standalone). */
export function useMeMaybe(): Me | null {
  return useContext(MeContext);
}

export function useMe(): Me {
  const me = useContext(MeContext);
  if (!me) throw new Error("useMe outside AppShell");
  return me;
}
