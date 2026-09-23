import { useMutation, useQuery, useQueryClient, type UseMutationResult, type UseQueryResult } from "@tanstack/react-query";
import { QUESTION_KEYS, REVIEW_KEYS } from "@/constants/react-query-key.constant";
import type { DocumentQuestionSearchBody, ReviewDocumentSearchBody } from "@/dtos/review.dto";
import type { SearchBody } from "@/dtos/search.dto";
import type { ParsedQuestion } from "@/interfaces/question.interface";
import type { AnswerKeyResult, ApproveConfidentResult, ReviewAction, ReviewDocument } from "@/interfaces/review.interface";
import type { RowsQueryOptions, SearchPage } from "@/interfaces/search-page.interface";
import { invalidate } from "@/lib/common/query-client";
import { reviewService } from "@/services/review.service";
import { useSearchQuery } from "./use-search-query";

// reviewing changes questions of the bank too
const TOUCHED = [REVIEW_KEYS.ALL, QUESTION_KEYS.ALL] as const;

export function useReviewDocumentSearchQuery(body: ReviewDocumentSearchBody, options?: RowsQueryOptions<ReviewDocument>): UseQueryResult<SearchPage<ReviewDocument>, Error> {
  return useSearchQuery(REVIEW_KEYS.DOCUMENTS(body), reviewService.searchDocuments, body, options);
}

export function useFlaggedSearchQuery(body: SearchBody, options?: RowsQueryOptions<ParsedQuestion>): UseQueryResult<SearchPage<ParsedQuestion>, Error> {
  return useSearchQuery(REVIEW_KEYS.FLAGGED(body), reviewService.searchFlagged, body, options);
}

export function useReviewDocumentQuery(id: string): UseQueryResult<ReviewDocument, Error> {
  return useQuery<ReviewDocument, Error>({ queryKey: REVIEW_KEYS.DOCUMENT(id), queryFn: () => reviewService.getDocument(id) });
}

export function useReviewQueueQuery(id: string): UseQueryResult<ParsedQuestion[], Error> {
  return useQuery<ParsedQuestion[], Error>({ queryKey: REVIEW_KEYS.QUEUE(id), queryFn: () => reviewService.queue(id) });
}

/** One document's questions in the chosen state; `pending` is what the keyboard queue works on. */
export function useDocumentQuestionsSearchQuery(id: string, body: DocumentQuestionSearchBody, options?: RowsQueryOptions<ParsedQuestion> & { enabled?: boolean }): UseQueryResult<SearchPage<ParsedQuestion>, Error> {
  return useSearchQuery(REVIEW_KEYS.QUESTIONS(id, body), (b) => reviewService.searchQuestions(id, b), body, options);
}

export function useAssignReviewerMutation(): UseMutationResult<ReviewDocument, Error, { id: string; userId: string | null }> {
  const qc = useQueryClient();
  return useMutation<ReviewDocument, Error, { id: string; userId: string | null }>({
    mutationFn: ({ id, userId }) => reviewService.updateDocument(id, { assigned_to: userId }),
    onSuccess: () => invalidate(qc, ...TOUCHED),
  });
}

export function useReviewActionMutation(): UseMutationResult<ParsedQuestion, Error, { questionId: string; action: ReviewAction }> {
  const qc = useQueryClient();
  return useMutation<ParsedQuestion, Error, { questionId: string; action: ReviewAction }>({
    mutationFn: ({ questionId, action }) => reviewService.action(questionId, { action }),
    onSuccess: () => invalidate(qc, ...TOUCHED),
  });
}

export function useAnswerKeyMutation(docId: string): UseMutationResult<AnswerKeyResult, Error, string> {
  const qc = useQueryClient();
  return useMutation<AnswerKeyResult, Error, string>({
    mutationFn: (text) => reviewService.answerKey(docId, { text }),
    onSuccess: () => invalidate(qc, ...TOUCHED),
  });
}

export function useApproveConfidentMutation(docId: string): UseMutationResult<ApproveConfidentResult, Error, void> {
  const qc = useQueryClient();
  return useMutation<ApproveConfidentResult, Error, void>({
    mutationFn: () => reviewService.approveConfident(docId),
    onSuccess: () => invalidate(qc, ...TOUCHED),
  });
}
