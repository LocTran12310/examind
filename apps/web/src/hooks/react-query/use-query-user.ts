import { useMutation, useQuery, useQueryClient, type UseMutationResult, type UseQueryResult } from "@tanstack/react-query";
import { CLASS_KEYS, STRUCTURE_KEYS, USER_KEYS } from "@/constants/react-query-key.constant";
import type { SearchBody } from "@/dtos/search.dto";
import type { CreateUserBody, LinkUserBody, UpdateUserBody } from "@/dtos/user.dto";
import type { RowsQueryOptions, SearchPage } from "@/interfaces/search-page.interface";
import type { Credential, ImportCommitted, ImportPreview, ImportRow, User, UserCreated } from "@/interfaces/user.interface";
import { invalidate } from "@/lib/common/query-client";
import { LIMIT_ALL } from "@/lib/common/search-body";
import { userService } from "@/services/user.service";
import { useSearchQuery } from "./use-search-query";

// users carry their classes: joining, leaving or importing moves class sizes and the structure counts
const WITH_CLASSES = [USER_KEYS.ALL, CLASS_KEYS.ALL, STRUCTURE_KEYS.ALL] as const;

export function useUserSearchQuery(body: SearchBody, options?: RowsQueryOptions<User> & { enabled?: boolean }): UseQueryResult<SearchPage<User>, Error> {
  return useSearchQuery(USER_KEYS.SEARCH(body), userService.search, body, options);
}

/** Every user matching `params` (filters, `class_id`…) for pickers; `enabled` false = not needed. */
export function useUserOptionsQuery(params: Omit<SearchBody, "page" | "limit">, enabled = true): UseQueryResult<User[], Error> {
  return useQuery<User[], Error>({
    queryKey: USER_KEYS.OPTIONS(params),
    queryFn: async () => (await userService.search({ ...params, page: 1, limit: LIMIT_ALL })).data,
    enabled,
  });
}

/** Read every row of a search once (CSV export), through the cache. */
export function useFetchAllUsers(): (body: SearchBody) => Promise<User[]> {
  const qc = useQueryClient();
  return async (body) => {
    const all = { ...body, page: 1, limit: LIMIT_ALL };
    return (await qc.fetchQuery({ queryKey: USER_KEYS.SEARCH(all), queryFn: () => userService.search(all) })).data;
  };
}

export function useCreateUserMutation(): UseMutationResult<UserCreated, Error, CreateUserBody> {
  const qc = useQueryClient();
  return useMutation<UserCreated, Error, CreateUserBody>({
    mutationFn: userService.create,
    onSuccess: () => invalidate(qc, USER_KEYS.ALL),
  });
}

export function useUpdateUserMutation(): UseMutationResult<User, Error, { id: string; body: UpdateUserBody }> {
  const qc = useQueryClient();
  return useMutation<User, Error, { id: string; body: UpdateUserBody }>({
    mutationFn: ({ id, body }) => userService.update(id, body),
    onSuccess: () => invalidate(qc, USER_KEYS.ALL),
  });
}

/** Lock or unlock several accounts. */
export function useSetUsersActiveMutation(): UseMutationResult<void, Error, { ids: string[]; active: boolean }> {
  const qc = useQueryClient();
  return useMutation<void, Error, { ids: string[]; active: boolean }>({
    mutationFn: async ({ ids, active }) => {
      for (const id of ids) await userService.update(id, { is_active: active });
    },
    onSettled: () => invalidate(qc, USER_KEYS.ALL),
  });
}

export function useResetPasswordMutation(): UseMutationResult<Credential, Error, string> {
  const qc = useQueryClient();
  return useMutation<Credential, Error, string>({
    mutationFn: userService.resetPassword,
    onSuccess: () => invalidate(qc, USER_KEYS.ALL),
  });
}

export function useLinkUserMutation(): UseMutationResult<User, Error, LinkUserBody> {
  const qc = useQueryClient();
  return useMutation<User, Error, LinkUserBody>({
    mutationFn: userService.link,
    onSuccess: () => invalidate(qc, USER_KEYS.ALL),
  });
}

/** Remove accounts of other orgs from this org; they leave its classes too. */
export function useUnlinkUsersMutation(): UseMutationResult<void, Error, string[]> {
  const qc = useQueryClient();
  return useMutation<void, Error, string[]>({
    mutationFn: async (ids) => {
      for (const id of ids) await userService.unlink(id);
    },
    onSettled: () => invalidate(qc, ...WITH_CLASSES),
  });
}

export function useImportPreviewMutation(): UseMutationResult<ImportPreview, Error, File> {
  return useMutation<ImportPreview, Error, File>({ mutationFn: userService.importPreview });
}

export function useImportCommitMutation(): UseMutationResult<ImportCommitted, Error, ImportRow[]> {
  const qc = useQueryClient();
  return useMutation<ImportCommitted, Error, ImportRow[]>({
    mutationFn: (rows) => userService.importCommit({ rows }),
    onSuccess: () => invalidate(qc, ...WITH_CLASSES),
  });
}
