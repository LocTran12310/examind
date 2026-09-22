import { useMutation, useQuery, useQueryClient, type UseMutationResult, type UseQueryResult } from "@tanstack/react-query";
import { TAG_KEYS } from "@/constants/react-query-key.constant";
import type { SearchBody } from "@/dtos/search.dto";
import type { CreateTagBody, UpdateTagBody } from "@/dtos/tag.dto";
import type { RowsQueryOptions, SearchPage } from "@/interfaces/search-page.interface";
import type { Tag } from "@/interfaces/tag.interface";
import { LIMIT_ALL } from "@/lib/common/search-body";
import { tagService } from "@/services/tag.service";
import { useSearchQuery } from "./use-search-query";

export function useTagSearchQuery(body: SearchBody, options?: RowsQueryOptions<Tag>): UseQueryResult<SearchPage<Tag>, Error> {
  return useSearchQuery(TAG_KEYS.SEARCH(body), tagService.search, body, options);
}

/** Every tag a picker offers: a subject's tags plus shared ones, or only shared ones (`"shared"`),
 *  or all tags (`null`); `enabled` false = not needed yet. */
export function useTagOptionsQuery(subject: string | null, enabled = true): UseQueryResult<Tag[], Error> {
  return useQuery<Tag[], Error>({
    queryKey: TAG_KEYS.OPTIONS(subject),
    queryFn: async () => (await tagService.search({ page: 1, limit: LIMIT_ALL, ...(subject ? { subject_id: subject } : {}) })).data,
    enabled,
  });
}

export function useCreateTagMutation(): UseMutationResult<Tag, Error, CreateTagBody> {
  const qc = useQueryClient();
  return useMutation<Tag, Error, CreateTagBody>({
    mutationFn: tagService.create,
    onSuccess: () => void qc.invalidateQueries({ queryKey: TAG_KEYS.ALL }),
  });
}

export function useUpdateTagMutation(): UseMutationResult<Tag, Error, { id: string; body: UpdateTagBody }> {
  const qc = useQueryClient();
  return useMutation<Tag, Error, { id: string; body: UpdateTagBody }>({
    mutationFn: ({ id, body }) => tagService.update(id, body),
    onSuccess: () => void qc.invalidateQueries({ queryKey: TAG_KEYS.ALL }),
  });
}

export function useDeleteTagsMutation(): UseMutationResult<void, Error, string[]> {
  const qc = useQueryClient();
  return useMutation<void, Error, string[]>({
    mutationFn: async (ids) => {
      for (const id of ids) await tagService.remove(id);
    },
    onSettled: () => void qc.invalidateQueries({ queryKey: TAG_KEYS.ALL }),
  });
}
