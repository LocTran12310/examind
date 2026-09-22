"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useApi } from "@/lib/hooks";
import type { Me, Page, SchoolYear } from "@/lib/types";

interface YearState {
  years: SchoolYear[];
  year: SchoolYear | null;
  setYear: (id: string) => void;
  reload: () => Promise<void>;
}

const YearContext = createContext<YearState>({ years: [], year: null, setYear: () => {}, reload: async () => {} });

const key = (orgId: string) => `examind.year.${orgId}`;
function stored(orgId: string): string | null {
  try {
    return localStorage.getItem(key(orgId));
  } catch {
    return null;
  }
}

/** The school year chosen in the header: per org and browser, defaulting to the active year (school-years A-08). */
export function YearProvider({ me, children }: { me: Me; children: React.ReactNode }) {
  const staff = me.role === "org_admin" || me.role === "teacher";
  const { data, reload } = useApi<Page<SchoolYear>>(staff ? "/school-years?page_size=all" : null);
  const years = useMemo(() => data?.items ?? [], [data]);
  const [chosen, setChosen] = useState<string | null>(null);
  useEffect(() => setChosen(stored(me.org.id)), [me.org.id]);
  const year = years.find((y) => y.id === chosen) ?? years.find((y) => y.status === "active") ?? years[0] ?? null;
  const setYear = useCallback(
    (id: string) => {
      setChosen(id);
      try {
        localStorage.setItem(key(me.org.id), id);
      } catch {}
    },
    [me.org.id],
  );
  return <YearContext.Provider value={{ years, year, setYear, reload }}>{children}</YearContext.Provider>;
}

export const useYear = () => useContext(YearContext);
