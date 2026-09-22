"use client";

import { useCallback, useEffect, useMemo } from "react";
import { useMeMaybe } from "@/hooks/common/use-me";
import { useSchoolYearOptionsQuery } from "@/hooks/react-query/use-query-school-year";
import type { SchoolYear } from "@/interfaces/school-year.interface";
import { useYearStore } from "@/stores/common/year.store";

const NONE: SchoolYear[] = [];

/** The years of the org and the one chosen in the header (default: the active year). Staff only: other
 *  roles (and widgets outside the shell) get no years. */
export function useYear() {
  const me = useMeMaybe();
  const orgId = me?.org.id ?? "";
  const staff = me?.role === "org_admin" || me?.role === "teacher";
  const { data, refetch } = useSchoolYearOptionsQuery(staff);
  const years = data ?? NONE;
  const load = useYearStore((s) => s.load);
  const choose = useYearStore((s) => s.choose);
  const chosen = useYearStore((s) => s.chosen[orgId] ?? null);
  useEffect(() => {
    if (orgId) load(orgId);
  }, [orgId, load]);
  const year = useMemo(
    () => years.find((y) => y.id === chosen) ?? years.find((y) => y.status === "active") ?? years[0] ?? null,
    [years, chosen],
  );
  const setYear = useCallback((id: string) => orgId && choose(orgId, id), [orgId, choose]);
  const reload = useCallback(async () => void (await refetch()), [refetch]);
  return { years, year, setYear, reload };
}
