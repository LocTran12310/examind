import { useMutation, useQuery, useQueryClient, type UseMutationResult, type UseQueryResult } from "@tanstack/react-query";
import { ACCOUNT_KEYS, MEMBERSHIP_KEYS, ORG_KEYS } from "@/constants/react-query-key.constant";
import type { CreateOrgBody, OrgAction, UpdateOrgBody } from "@/dtos/org.dto";
import type { SearchBody } from "@/dtos/search.dto";
import type { Org, OrgCreated } from "@/interfaces/org.interface";
import type { RowsQueryOptions, SearchPage } from "@/interfaces/search-page.interface";
import { invalidate } from "@/lib/common/query-client";
import { LIMIT_ALL } from "@/lib/common/search-body";
import { orgService } from "@/services/org.service";
import { useSearchQuery } from "./use-search-query";

// an org's name and status show on its memberships and on the accounts' org counts
const TOUCHED = [ORG_KEYS.ALL, MEMBERSHIP_KEYS.ALL, ACCOUNT_KEYS.ALL] as const;

export function useOrgSearchQuery(body: SearchBody, options?: RowsQueryOptions<Org>): UseQueryResult<SearchPage<Org>, Error> {
  return useSearchQuery(ORG_KEYS.SEARCH(body), orgService.search, body, options);
}

/** Every org (not deleted) for pickers; `enabled` false = not needed yet. */
export function useOrgOptionsQuery(enabled = true): UseQueryResult<Org[], Error> {
  return useQuery<Org[], Error>({
    queryKey: ORG_KEYS.OPTIONS,
    queryFn: async () => (await orgService.search({ page: 1, limit: LIMIT_ALL })).data,
    enabled,
  });
}

export function useCreateOrgMutation(): UseMutationResult<OrgCreated, Error, CreateOrgBody> {
  const qc = useQueryClient();
  return useMutation<OrgCreated, Error, CreateOrgBody>({
    mutationFn: orgService.create,
    onSuccess: () => invalidate(qc, ...TOUCHED),
  });
}

export function useUpdateOrgMutation(): UseMutationResult<Org, Error, { id: string; body: UpdateOrgBody }> {
  const qc = useQueryClient();
  return useMutation<Org, Error, { id: string; body: UpdateOrgBody }>({
    mutationFn: ({ id, body }) => orgService.update(id, body),
    onSuccess: () => invalidate(qc, ...TOUCHED),
  });
}

/** Suspend, activate or (soft) delete several orgs, one after the other. */
export function useOrgActionMutation(): UseMutationResult<void, Error, { action: OrgAction; ids: string[] }> {
  const qc = useQueryClient();
  return useMutation<void, Error, { action: OrgAction; ids: string[] }>({
    mutationFn: async ({ action, ids }) => {
      for (const id of ids) {
        if (action === "delete") await orgService.remove(id);
        else if (action === "suspend") await orgService.suspend(id);
        else await orgService.activate(id);
      }
    },
    onSettled: () => invalidate(qc, ...TOUCHED),
  });
}
