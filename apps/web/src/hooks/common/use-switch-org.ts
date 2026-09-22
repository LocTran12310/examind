"use client";

import { useRouter } from "next/navigation";
import { useSwitchOrgMutation } from "@/hooks/react-query/use-query-auth";
import type { Me } from "@/interfaces/auth.interface";
import { homeFor } from "@/lib/nav";

/** Move into another org: the API switches, the query cache is cleared (in the mutation), then the router
 *  re-renders the server layout (new `me`) and opens `to(next)` (default: the new role's home). */
export function useSwitchOrg() {
  const router = useRouter();
  const mutation = useSwitchOrgMutation();
  return {
    busy: mutation.isPending,
    switchTo: async (orgId: string, to: (next: Me) => string = (next) => homeFor(next.role)): Promise<Me> => {
      const next = await mutation.mutateAsync(orgId);
      router.push(to(next));
      router.refresh();
      return next;
    },
  };
}
