import { useMutation, useQuery, useQueryClient, type UseMutationResult, type UseQueryResult } from "@tanstack/react-query";
import { CLASS_KEYS, SCHOOL_YEAR_KEYS, STRUCTURE_KEYS } from "@/constants/react-query-key.constant";
import type { CommitRolloverBody, CreateYearBody, UpdateYearBody, YearAction } from "@/dtos/school-year.dto";
import type { SearchBody } from "@/dtos/search.dto";
import type { RolloverPlan, RolloverResult, SchoolYear } from "@/interfaces/school-year.interface";
import type { RowsQueryOptions, SearchPage } from "@/interfaces/search-page.interface";
import { LIMIT_ALL } from "@/lib/common/search-body";
import { schoolYearService } from "@/services/school-year.service";
import { invalidate } from "@/lib/common/query-client";
import { useSearchQuery } from "./use-search-query";

export function useSchoolYearSearchQuery(body: SearchBody, options?: RowsQueryOptions<SchoolYear>): UseQueryResult<SearchPage<SchoolYear>, Error> {
  return useSearchQuery(SCHOOL_YEAR_KEYS.SEARCH(body), schoolYearService.search, body, options);
}

/** Every year of the org (header selector, pickers); staff only, so `enabled` follows the role. */
export function useSchoolYearOptionsQuery(enabled = true): UseQueryResult<SchoolYear[], Error> {
  return useQuery<SchoolYear[], Error>({
    queryKey: SCHOOL_YEAR_KEYS.OPTIONS,
    queryFn: async () => (await schoolYearService.search({ page: 1, limit: LIMIT_ALL })).data,
    enabled,
  });
}

export function useSaveSchoolYearMutation(): UseMutationResult<SchoolYear, Error, { id?: string; body: CreateYearBody | UpdateYearBody }> {
  const qc = useQueryClient();
  return useMutation<SchoolYear, Error, { id?: string; body: CreateYearBody | UpdateYearBody }>({
    mutationFn: ({ id, body }) => (id ? schoolYearService.update(id, body) : schoolYearService.create(body as CreateYearBody)),
    onSuccess: () => invalidate(qc, SCHOOL_YEAR_KEYS.ALL),
  });
}

export function useSchoolYearStatusMutation(): UseMutationResult<SchoolYear, Error, { id: string; action: YearAction }> {
  const qc = useQueryClient();
  return useMutation<SchoolYear, Error, { id: string; action: YearAction }>({
    mutationFn: ({ id, action }) => schoolYearService.setStatus(id, action),
    onSuccess: () => invalidate(qc, SCHOOL_YEAR_KEYS.ALL),
  });
}

export function useDeleteSchoolYearsMutation(): UseMutationResult<void, Error, string[]> {
  const qc = useQueryClient();
  return useMutation<void, Error, string[]>({
    mutationFn: async (ids) => {
      for (const id of ids) await schoolYearService.remove(id);
    },
    onSettled: () => invalidate(qc, SCHOOL_YEAR_KEYS.ALL),
  });
}

/** The proposed rollover of a year into `targetCode` (the next year when null). */
export function useRolloverPreviewQuery(yearId: string, targetCode: string | null): UseQueryResult<RolloverPlan, Error> {
  return useQuery<RolloverPlan, Error>({
    queryKey: SCHOOL_YEAR_KEYS.ROLLOVER(yearId, targetCode),
    queryFn: () => schoolYearService.previewRollover(yearId, targetCode),
    retry: false,
  });
}

export function useCommitRolloverMutation(yearId: string): UseMutationResult<RolloverResult, Error, CommitRolloverBody> {
  const qc = useQueryClient();
  return useMutation<RolloverResult, Error, CommitRolloverBody>({
    mutationFn: (body) => schoolYearService.commitRollover(yearId, body),
    // the result stays on screen (the plan is not refetched); lists and the header selector refresh behind it
    onSuccess: () => void invalidate(qc, SCHOOL_YEAR_KEYS.OPTIONS, SCHOOL_YEAR_KEYS.SEARCH_ALL, CLASS_KEYS.ALL, STRUCTURE_KEYS.ALL),
  });
}
