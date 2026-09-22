import { useMutation, useQuery, useQueryClient, type UseMutationResult, type UseQueryResult } from "@tanstack/react-query";
import { ASSIGNMENT_KEYS, CLASS_KEYS, EXAM_KEYS, PRACTICE_KEYS } from "@/constants/react-query-key.constant";
import type { ClassReviewBody, StartPracticeBody } from "@/dtos/practice.dto";
import type { MasteryRow } from "@/interfaces/mastery.interface";
import type { PracticeItem, PracticeStarted } from "@/interfaces/practice.interface";
import { invalidate } from "@/lib/common/query-client";
import { practiceService } from "@/services/practice.service";

/** The signed-in student's topic mastery. */
export function useMyMasteryQuery(): UseQueryResult<MasteryRow[], Error> {
  return useQuery<MasteryRow[], Error>({ queryKey: PRACTICE_KEYS.MASTERY, queryFn: practiceService.myMastery });
}

/** The signed-in student's last practice attempts. */
export function usePracticeHistoryQuery(): UseQueryResult<PracticeItem[], Error> {
  return useQuery<PracticeItem[], Error>({ queryKey: PRACTICE_KEYS.HISTORY, queryFn: practiceService.history });
}

export function useStartPracticeMutation(): UseMutationResult<PracticeStarted, Error, StartPracticeBody> {
  const qc = useQueryClient();
  return useMutation<PracticeStarted, Error, StartPracticeBody>({
    mutationFn: practiceService.start,
    onSuccess: () => invalidate(qc, PRACTICE_KEYS.ALL),
  });
}

/** Personal review exams for every student of a class: the class overview and the assignments change. */
export function useAssignClassReviewMutation(classId: string): UseMutationResult<{ created: number }, Error, ClassReviewBody> {
  const qc = useQueryClient();
  return useMutation<{ created: number }, Error, ClassReviewBody>({
    mutationFn: (body) => practiceService.assignClass(classId, body),
    onSuccess: () => invalidate(qc, CLASS_KEYS.OVERVIEW(classId), ASSIGNMENT_KEYS.ALL, EXAM_KEYS.ALL),
  });
}
