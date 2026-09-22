import { useMutation, useQuery, useQueryClient, type UseMutationResult, type UseQueryResult } from "@tanstack/react-query";
import { TOPIC_KEYS } from "@/constants/react-query-key.constant";
import type { CreateTopicBody, UpdateTopicBody } from "@/dtos/topic.dto";
import type { Topic } from "@/interfaces/topic.interface";
import { topicService } from "@/services/topic.service";

/** The knowledge tree of one subject (all subjects with `null`); `enabled` false = not needed yet. */
export function useTopicsQuery(subjectId: string | null, enabled = true): UseQueryResult<Topic[], Error> {
  return useQuery<Topic[], Error>({ queryKey: TOPIC_KEYS.LIST(subjectId), queryFn: () => topicService.list(subjectId), enabled });
}

function useTopicMutation<V>(fn: (v: V) => Promise<unknown>): UseMutationResult<unknown, Error, V> {
  const qc = useQueryClient();
  return useMutation<unknown, Error, V>({ mutationFn: fn, onSuccess: () => void qc.invalidateQueries({ queryKey: TOPIC_KEYS.ALL }) });
}

export const useCreateTopicMutation = () => useTopicMutation<CreateTopicBody>(topicService.create);
export const useUpdateTopicMutation = () => useTopicMutation<{ id: string; body: UpdateTopicBody }>(({ id, body }) => topicService.update(id, body));
export const useMoveTopicMutation = () => useTopicMutation<{ id: string; parentId: string | null }>(({ id, parentId }) => topicService.move(id, parentId));
export const useMergeTopicMutation = () => useTopicMutation<{ id: string; targetId: string }>(({ id, targetId }) => topicService.merge(id, targetId));
export const useDeleteTopicMutation = () => useTopicMutation<string>(topicService.remove);
