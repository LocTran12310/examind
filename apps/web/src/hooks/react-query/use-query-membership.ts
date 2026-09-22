import { useMutation, useQueryClient, type UseMutationResult, type UseQueryResult } from "@tanstack/react-query";
import { ACCOUNT_KEYS, MEMBERSHIP_KEYS, ORG_KEYS, USER_KEYS } from "@/constants/react-query-key.constant";
import type { AddMemberBody, AddMembershipBody, UpdateMembershipBody } from "@/dtos/org.dto";
import type { SearchBody } from "@/dtos/search.dto";
import type { Membership } from "@/interfaces/org.interface";
import type { RowsQueryOptions, SearchPage } from "@/interfaces/search-page.interface";
import { invalidate } from "@/lib/common/query-client";
import { membershipService, type MembershipSide } from "@/services/membership.service";
import { useSearchQuery } from "./use-search-query";

// a membership moves an org's user count, an account's org count and the org's users list
const TOUCHED = [MEMBERSHIP_KEYS.ALL, ORG_KEYS.ALL, ACCOUNT_KEYS.ALL, USER_KEYS.ALL] as const;

/** Memberships of one side: the body carries `org_id` (an org's members) or `user_id` (an account's orgs). */
export function useMembershipSearchQuery(body: SearchBody, options?: RowsQueryOptions<Membership>): UseQueryResult<SearchPage<Membership>, Error> {
  return useSearchQuery(MEMBERSHIP_KEYS.SEARCH(body), membershipService.search, body, options);
}

export function useAddMembershipMutation(side: MembershipSide): UseMutationResult<Membership, Error, AddMemberBody | AddMembershipBody> {
  const qc = useQueryClient();
  return useMutation<Membership, Error, AddMemberBody | AddMembershipBody>({
    mutationFn: (body) => membershipService.add(side, body),
    onSuccess: () => invalidate(qc, ...TOUCHED),
  });
}

/** Change the role or lock several memberships. */
export function useUpdateMembershipsMutation(side: MembershipSide): UseMutationResult<void, Error, { rows: Membership[]; body: UpdateMembershipBody }> {
  const qc = useQueryClient();
  return useMutation<void, Error, { rows: Membership[]; body: UpdateMembershipBody }>({
    mutationFn: async ({ rows, body }) => {
      for (const m of rows) await membershipService.update(side, m, body);
    },
    onSettled: () => invalidate(qc, ...TOUCHED),
  });
}

export function useRemoveMembershipsMutation(side: MembershipSide): UseMutationResult<void, Error, Membership[]> {
  const qc = useQueryClient();
  return useMutation<void, Error, Membership[]>({
    mutationFn: async (rows) => {
      for (const m of rows) await membershipService.remove(side, m);
    },
    onSettled: () => invalidate(qc, ...TOUCHED),
  });
}
