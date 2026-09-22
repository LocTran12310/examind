import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import { TAXONOMY_KEYS } from "@/constants/react-query-key.constant";
import type { Taxonomy } from "@/interfaces/taxonomy.interface";
import { taxonomyService } from "@/services/taxonomy.service";

/** Subjects, grades, semesters of the organisation (rarely change). */
export function useTaxonomyQuery(): UseQueryResult<Taxonomy, Error> {
  return useQuery<Taxonomy, Error>({ queryKey: TAXONOMY_KEYS.ALL, queryFn: taxonomyService.get, staleTime: 5 * 60_000 });
}
