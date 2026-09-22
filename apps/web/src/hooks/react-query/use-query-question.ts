import { useMutation, useQuery, useQueryClient, type UseMutationResult, type UseQueryResult } from "@tanstack/react-query";
import { QUESTION_KEYS, REVIEW_KEYS } from "@/constants/react-query-key.constant";
import type { BulkQuestionsBody, QuestionBody, QuestionSearchBody, UpdateQuestionBody } from "@/dtos/question.dto";
import type { BankFacets, BulkResult, ParsedQuestion, Question } from "@/interfaces/question.interface";
import type { RowsQueryOptions, SearchPage } from "@/interfaces/search-page.interface";
import { invalidate } from "@/lib/common/query-client";
import { questionService } from "@/services/question.service";
import { useSearchQuery } from "./use-search-query";

// the review screens show questions too
const TOUCHED = [QUESTION_KEYS.ALL, REVIEW_KEYS.ALL] as const;

export function useQuestionSearchQuery(
  body: QuestionSearchBody,
  options?: RowsQueryOptions<ParsedQuestion> & { enabled?: boolean },
): UseQueryResult<SearchPage<ParsedQuestion>, Error> {
  return useSearchQuery(QUESTION_KEYS.SEARCH(body), questionService.search, body, options);
}

/** Facet counts of the bank for the same filters; paging and sort do not change them. */
export function useQuestionFacetsQuery(body: QuestionSearchBody, enabled = true): UseQueryResult<BankFacets, Error> {
  const { sort: _sort, ...rest } = body;
  const facetsBody: QuestionSearchBody = { ...rest, page: 1 };
  return useQuery<BankFacets, Error>({ queryKey: QUESTION_KEYS.FACETS(facetsBody), queryFn: () => questionService.facets(facetsBody), enabled });
}

export function useQuestionQuery(id: string): UseQueryResult<ParsedQuestion, Error> {
  return useQuery<ParsedQuestion, Error>({ queryKey: QUESTION_KEYS.DETAIL(id), queryFn: () => questionService.get(id) });
}

export function useQuestionDemoQuery(): UseQueryResult<Question, Error> {
  return useQuery<Question, Error>({ queryKey: QUESTION_KEYS.DEMO, queryFn: questionService.demo });
}

export function useCreateQuestionMutation(): UseMutationResult<ParsedQuestion, Error, QuestionBody> {
  const qc = useQueryClient();
  return useMutation<ParsedQuestion, Error, QuestionBody>({
    mutationFn: questionService.create,
    onSuccess: () => invalidate(qc, ...TOUCHED),
  });
}

/** Saves a change; the answer also lands in the question's cache entry at once. */
export function useUpdateQuestionMutation(): UseMutationResult<ParsedQuestion, Error, { id: string; body: UpdateQuestionBody }> {
  const qc = useQueryClient();
  return useMutation<ParsedQuestion, Error, { id: string; body: UpdateQuestionBody }>({
    mutationFn: ({ id, body }) => questionService.update(id, body),
    onSuccess: (q) => {
      qc.setQueryData(QUESTION_KEYS.DETAIL(q.id), q);
      return invalidate(qc, ...TOUCHED);
    },
  });
}

export function useBulkUpdateQuestionsMutation(): UseMutationResult<BulkResult, Error, BulkQuestionsBody> {
  const qc = useQueryClient();
  return useMutation<BulkResult, Error, BulkQuestionsBody>({
    mutationFn: questionService.bulk,
    onSuccess: () => invalidate(qc, ...TOUCHED),
  });
}

/** Deletes one by one; questions used in an exam are refused and counted in `failed`. */
export function useDeleteQuestionsMutation(): UseMutationResult<{ failed: number }, Error, string[]> {
  const qc = useQueryClient();
  return useMutation<{ failed: number }, Error, string[]>({
    mutationFn: async (ids) => {
      let failed = 0;
      for (const id of ids) await questionService.remove(id).catch(() => failed++);
      return { failed };
    },
    onSettled: () => invalidate(qc, ...TOUCHED),
  });
}
