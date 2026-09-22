import { useMutation, useQuery, useQueryClient, type UseMutationResult, type UseQueryResult } from "@tanstack/react-query";
import { ME_KEYS } from "@/constants/react-query-key.constant";
import type { ChangePasswordBody, LoginBody } from "@/dtos/auth.dto";
import type { Me, MyOrg } from "@/interfaces/auth.interface";
import { authService } from "@/services/auth.service";

/** The orgs of the header selector. */
export function useMyOrgsQuery(): UseQueryResult<MyOrg[], Error> {
  return useQuery<MyOrg[], Error>({ queryKey: ME_KEYS.ORGS, queryFn: authService.myOrgs });
}

/** Sign in; nothing cached for a previous session survives. */
export function useLoginMutation(): UseMutationResult<Me, Error, LoginBody> {
  const qc = useQueryClient();
  return useMutation<Me, Error, LoginBody>({
    mutationFn: authService.login,
    onSuccess: () => qc.clear(),
  });
}

/** Sign out (a failed call still ends the session here) and drop every cached query. */
export function useLogoutMutation(): UseMutationResult<void, Error, void> {
  const qc = useQueryClient();
  return useMutation<void, Error, void>({
    mutationFn: () => authService.logout().catch(() => undefined),
    onSettled: () => qc.clear(),
  });
}

/** The access cookie expired: ask for a new one with the refresh cookie. */
export function useRefreshSessionMutation(): UseMutationResult<void, Error, void> {
  return useMutation<void, Error, void>({ mutationFn: authService.refresh });
}

/** Change the password, then read the user again (the home page depends on the role). */
export function useChangePasswordMutation(): UseMutationResult<Me, Error, ChangePasswordBody> {
  return useMutation<Me, Error, ChangePasswordBody>({
    mutationFn: async (body) => {
      await authService.changePassword(body);
      return authService.me();
    },
  });
}

/** Work inside another org. Every cached query belongs to the old org, so the whole cache is cleared
 *  (architecture-refactor ADR-06); the caller navigates with the router. */
export function useSwitchOrgMutation(): UseMutationResult<Me, Error, string> {
  const qc = useQueryClient();
  return useMutation<Me, Error, string>({
    mutationFn: authService.switchOrg,
    onSuccess: () => qc.clear(),
  });
}
