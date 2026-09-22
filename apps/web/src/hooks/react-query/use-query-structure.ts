import { useMutation, useQuery, useQueryClient, type UseMutationResult, type UseQueryResult } from "@tanstack/react-query";
import { CLASS_KEYS, GRADE_KEYS, SCHOOL_LEVEL_KEYS, STRUCTURE_KEYS } from "@/constants/react-query-key.constant";
import type { SearchBody } from "@/dtos/search.dto";
import type { GradeBody, LevelBody } from "@/dtos/structure.dto";
import type { RowsQueryOptions, SearchPage } from "@/interfaces/search-page.interface";
import type { GradeRow, SchoolLevel, Structure } from "@/interfaces/structure.interface";
import { LIMIT_ALL } from "@/lib/common/search-body";
import { structureService } from "@/services/structure.service";
import { invalidate } from "@/lib/common/query-client";
import { useSearchQuery } from "./use-search-query";

/** Cấp học › Khối › Lớp with counts, for the classes of one year (all years when `yearId` is null). */
export function useStructureQuery(yearId: string | null): UseQueryResult<Structure, Error> {
  return useQuery<Structure, Error>({ queryKey: STRUCTURE_KEYS.TREE(yearId), queryFn: () => structureService.tree(yearId) });
}

export function useSchoolLevelSearchQuery(body: SearchBody, options?: RowsQueryOptions<SchoolLevel>): UseQueryResult<SearchPage<SchoolLevel>, Error> {
  return useSearchQuery(SCHOOL_LEVEL_KEYS.SEARCH(body), structureService.searchLevels, body, options);
}

export function useGradeSearchQuery(body: SearchBody, options?: RowsQueryOptions<GradeRow>): UseQueryResult<SearchPage<GradeRow>, Error> {
  return useSearchQuery(GRADE_KEYS.SEARCH(body), structureService.searchGrades, body, options);
}

export function useSchoolLevelOptionsQuery(): UseQueryResult<SchoolLevel[], Error> {
  return useQuery<SchoolLevel[], Error>({
    queryKey: SCHOOL_LEVEL_KEYS.OPTIONS,
    queryFn: async () => (await structureService.searchLevels({ page: 1, limit: LIMIT_ALL })).data,
  });
}

export function useGradeOptionsQuery(): UseQueryResult<GradeRow[], Error> {
  return useQuery<GradeRow[], Error>({
    queryKey: GRADE_KEYS.OPTIONS,
    queryFn: async () => (await structureService.searchGrades({ page: 1, limit: LIMIT_ALL })).data,
  });
}

// levels count their grades, grades their classes; renumbering a grade changes the classes' grade too
const LEVEL_TOUCHED = [SCHOOL_LEVEL_KEYS.ALL, STRUCTURE_KEYS.ALL] as const;
const GRADE_TOUCHED = [GRADE_KEYS.ALL, SCHOOL_LEVEL_KEYS.ALL, STRUCTURE_KEYS.ALL, CLASS_KEYS.ALL] as const;

export function useSaveLevelMutation(): UseMutationResult<SchoolLevel, Error, { id?: string; body: LevelBody }> {
  const qc = useQueryClient();
  return useMutation<SchoolLevel, Error, { id?: string; body: LevelBody }>({
    mutationFn: ({ id, body }) => (id ? structureService.updateLevel(id, body) : structureService.createLevel(body)),
    onSuccess: () => invalidate(qc, ...LEVEL_TOUCHED),
  });
}

export function useDeleteLevelsMutation(): UseMutationResult<void, Error, string[]> {
  const qc = useQueryClient();
  return useMutation<void, Error, string[]>({
    mutationFn: async (ids) => {
      for (const id of ids) await structureService.removeLevel(id);
    },
    onSettled: () => invalidate(qc, ...LEVEL_TOUCHED),
  });
}

export function useSaveGradeMutation(): UseMutationResult<GradeRow, Error, { id?: string; body: GradeBody }> {
  const qc = useQueryClient();
  return useMutation<GradeRow, Error, { id?: string; body: GradeBody }>({
    mutationFn: ({ id, body }) => (id ? structureService.updateGrade(id, body) : structureService.createGrade(body)),
    onSuccess: () => invalidate(qc, ...GRADE_TOUCHED),
  });
}

export function useDeleteGradesMutation(): UseMutationResult<void, Error, string[]> {
  const qc = useQueryClient();
  return useMutation<void, Error, string[]>({
    mutationFn: async (ids) => {
      for (const id of ids) await structureService.removeGrade(id);
    },
    onSettled: () => invalidate(qc, ...GRADE_TOUCHED),
  });
}
