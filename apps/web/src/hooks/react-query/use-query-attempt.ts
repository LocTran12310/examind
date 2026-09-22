import { useMutation, useQuery, useQueryClient, type UseMutationResult, type UseQueryResult } from "@tanstack/react-query";
import { ASSIGNMENT_KEYS, ATTEMPT_KEYS } from "@/constants/react-query-key.constant";
import type { GradeAnswerBody } from "@/dtos/attempt.dto";
import type { AttemptResult, AttemptView, GradeResult } from "@/interfaces/attempt.interface";
import { invalidate } from "@/lib/common/query-client";
import type { AnswerResponse } from "@/types/attempt.type";
import { attemptService } from "@/services/attempt.service";

/** An attempt as the runner sees it; `enabled` false when not needed (e.g. a student on the result page). */
export function useAttemptQuery(id: string, enabled = true): UseQueryResult<AttemptView, Error> {
  return useQuery<AttemptView, Error>({ queryKey: ATTEMPT_KEYS.DETAIL(id), queryFn: () => attemptService.get(id), enabled });
}

export function useAttemptResultQuery(id: string): UseQueryResult<AttemptResult, Error> {
  return useQuery<AttemptResult, Error>({ queryKey: ATTEMPT_KEYS.RESULT(id), queryFn: () => attemptService.result(id) });
}

/** Autosave of one answer. The runner owns the answers while the exam is open, so nothing is refetched
 *  (a refetch per keystroke would only move the clock); submitting refreshes the attempt. */
export function useSaveAnswerMutation(attemptId: string): UseMutationResult<unknown, Error, { questionId: string; response: AnswerResponse }> {
  return useMutation<unknown, Error, { questionId: string; response: AnswerResponse }>({
    mutationFn: ({ questionId, response }) => attemptService.saveAnswer(attemptId, questionId, { response }),
  });
}

export function useSubmitAttemptMutation(attemptId: string): UseMutationResult<unknown, Error, void> {
  const qc = useQueryClient();
  return useMutation<unknown, Error, void>({
    mutationFn: () => attemptService.submit(attemptId),
    onSettled: () => invalidate(qc, ATTEMPT_KEYS.ALL, ASSIGNMENT_KEYS.ALL),
  });
}

/** Report that the student left the tab; nothing cached shows the count to the student. */
export function useTabSwitchMutation(attemptId: string): UseMutationResult<unknown, Error, void> {
  return useMutation<unknown, Error, void>({ mutationFn: () => attemptService.tabSwitch(attemptId) });
}

/** A teacher grades an essay: the result and the assignment report change. */
export function useGradeAnswerMutation(attemptId: string): UseMutationResult<GradeResult, Error, { questionId: string; body: GradeAnswerBody }> {
  const qc = useQueryClient();
  return useMutation<GradeResult, Error, { questionId: string; body: GradeAnswerBody }>({
    mutationFn: ({ questionId, body }) => attemptService.grade(attemptId, questionId, body),
    onSuccess: () => invalidate(qc, ATTEMPT_KEYS.ALL, ASSIGNMENT_KEYS.ALL),
  });
}
