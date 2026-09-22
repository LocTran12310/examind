import { useMutation, useQuery, useQueryClient, type UseMutationResult, type UseQueryResult } from "@tanstack/react-query";
import { CLASS_KEYS, GRADE_KEYS, SCHOOL_YEAR_KEYS, STRUCTURE_KEYS } from "@/constants/react-query-key.constant";
import type { ClassBody } from "@/dtos/class.dto";
import type { SearchBody } from "@/dtos/search.dto";
import type { ClassDetail, SchoolClass } from "@/interfaces/class.interface";
import type { RowsQueryOptions, SearchPage } from "@/interfaces/search-page.interface";
import { LIMIT_ALL } from "@/lib/common/search-body";
import type { ClassOverviewRow } from "@/lib/types";
import { classService } from "@/services/class.service";
import { invalidate } from "@/lib/common/query-client";
import { useSearchQuery } from "./use-search-query";

// a class change moves counts on years, grades and the structure tree too
const TOUCHED = [CLASS_KEYS.ALL, STRUCTURE_KEYS.ALL, SCHOOL_YEAR_KEYS.ALL, GRADE_KEYS.ALL] as const;

export function useClassSearchQuery(body: SearchBody, options?: RowsQueryOptions<SchoolClass>): UseQueryResult<SearchPage<SchoolClass>, Error> {
  return useSearchQuery(CLASS_KEYS.SEARCH(body), classService.search, body, options);
}

/** Every class (of one year when `yearId` is given) for pickers. */
export function useClassOptionsQuery(yearId: string | null = null, enabled = true): UseQueryResult<SchoolClass[], Error> {
  return useQuery<SchoolClass[], Error>({
    queryKey: CLASS_KEYS.OPTIONS(yearId),
    queryFn: async () => (await classService.search({ page: 1, limit: LIMIT_ALL, ...(yearId ? { school_year_id: yearId } : {}) })).data,
    enabled,
  });
}

export function useClassQuery(id: string): UseQueryResult<ClassDetail, Error> {
  return useQuery<ClassDetail, Error>({ queryKey: CLASS_KEYS.DETAIL(id), queryFn: () => classService.get(id) });
}

export function useClassOverviewQuery(id: string): UseQueryResult<ClassOverviewRow[], Error> {
  return useQuery<ClassOverviewRow[], Error>({ queryKey: CLASS_KEYS.OVERVIEW(id), queryFn: () => classService.overview(id) });
}

export function useSaveClassMutation(): UseMutationResult<SchoolClass, Error, { id?: string; body: ClassBody }> {
  const qc = useQueryClient();
  return useMutation<SchoolClass, Error, { id?: string; body: ClassBody }>({
    mutationFn: ({ id, body }) => (id ? classService.update(id, body) : classService.create(body)),
    onSuccess: () => invalidate(qc, ...TOUCHED),
  });
}

export function useDeleteClassesMutation(): UseMutationResult<void, Error, string[]> {
  const qc = useQueryClient();
  return useMutation<void, Error, string[]>({
    mutationFn: async (ids) => {
      for (const id of ids) await classService.remove(id);
    },
    onSettled: () => invalidate(qc, ...TOUCHED),
  });
}

export function useAddClassMembersMutation(classId: string): UseMutationResult<void, Error, string[]> {
  const qc = useQueryClient();
  return useMutation<void, Error, string[]>({
    mutationFn: (userIds) => classService.addMembers(classId, userIds),
    onSuccess: () => invalidate(qc, CLASS_KEYS.ALL, STRUCTURE_KEYS.ALL),
  });
}

export function useRemoveClassMembersMutation(classId: string): UseMutationResult<void, Error, string[]> {
  const qc = useQueryClient();
  return useMutation<void, Error, string[]>({
    mutationFn: async (userIds) => {
      for (const u of userIds) await classService.removeMember(classId, u);
    },
    onSettled: () => invalidate(qc, CLASS_KEYS.ALL, STRUCTURE_KEYS.ALL),
  });
}

/** Refetch the overview after work outside the class queries (personal reviews assigned). */
export function useRefreshClassOverview(id: string): () => Promise<void> {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: CLASS_KEYS.OVERVIEW(id) });
}
