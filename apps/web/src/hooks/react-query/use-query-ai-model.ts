import { useMutation, useQuery, useQueryClient, type UseMutationResult, type UseQueryResult } from "@tanstack/react-query";
import { AI_MODEL_KEYS } from "@/constants/react-query-key.constant";
import type { CreateAiModelBody, DiscoverModelsBody, UpdateAiModelBody } from "@/dtos/ai-model.dto";
import type { SearchBody } from "@/dtos/search.dto";
import type { AiModel, DiscoverResult, ModelTestResult } from "@/interfaces/ai-model.interface";
import type { RowsQueryOptions, SearchPage } from "@/interfaces/search-page.interface";
import { LIMIT_ALL } from "@/lib/common/search-body";
import { aiModelService } from "@/services/ai-model.service";
import { useSearchQuery } from "./use-search-query";

export function useAiModelSearchQuery(body: SearchBody, options?: RowsQueryOptions<AiModel>): UseQueryResult<SearchPage<AiModel>, Error> {
  return useSearchQuery(AI_MODEL_KEYS.SEARCH(body), aiModelService.search, body, options);
}

/** Every enabled model, for the model pickers of a processing config; `enabled` false = not needed yet. */
export function useAiModelOptionsQuery(enabled = true): UseQueryResult<AiModel[], Error> {
  return useQuery<AiModel[], Error>({
    queryKey: AI_MODEL_KEYS.OPTIONS,
    queryFn: async () => (await aiModelService.search({ page: 1, limit: LIMIT_ALL, filters: { enabled: { value: true } } })).data,
    enabled,
  });
}

export function useCreateAiModelMutation(): UseMutationResult<AiModel, Error, CreateAiModelBody> {
  const qc = useQueryClient();
  return useMutation<AiModel, Error, CreateAiModelBody>({
    mutationFn: aiModelService.create,
    onSuccess: () => void qc.invalidateQueries({ queryKey: AI_MODEL_KEYS.ALL }),
  });
}

export function useUpdateAiModelMutation(): UseMutationResult<AiModel, Error, { id: string; body: UpdateAiModelBody }> {
  const qc = useQueryClient();
  return useMutation<AiModel, Error, { id: string; body: UpdateAiModelBody }>({
    mutationFn: ({ id, body }) => aiModelService.update(id, body),
    onSuccess: () => void qc.invalidateQueries({ queryKey: AI_MODEL_KEYS.ALL }),
  });
}

/** Switch each model on or off (the opposite of its current state). */
export function useToggleAiModelsMutation(): UseMutationResult<void, Error, AiModel[]> {
  const qc = useQueryClient();
  return useMutation<void, Error, AiModel[]>({
    mutationFn: async (models) => {
      for (const m of models) await aiModelService.update(m.id, { enabled: !m.enabled });
    },
    onSettled: () => void qc.invalidateQueries({ queryKey: AI_MODEL_KEYS.ALL }),
  });
}

export function useDeleteAiModelsMutation(): UseMutationResult<void, Error, string[]> {
  const qc = useQueryClient();
  return useMutation<void, Error, string[]>({
    mutationFn: async (ids) => {
      for (const id of ids) await aiModelService.remove(id);
    },
    onSettled: () => void qc.invalidateQueries({ queryKey: AI_MODEL_KEYS.ALL }),
  });
}

/** Ask an Ollama server which models it has; nothing cached depends on it. */
export function useDiscoverAiModelsMutation(): UseMutationResult<DiscoverResult, Error, DiscoverModelsBody> {
  return useMutation<DiscoverResult, Error, DiscoverModelsBody>({ mutationFn: aiModelService.discover });
}

/** Call a model once to check it answers. */
export function useTestAiModelMutation(): UseMutationResult<ModelTestResult, Error, string> {
  return useMutation<ModelTestResult, Error, string>({ mutationFn: aiModelService.test });
}
