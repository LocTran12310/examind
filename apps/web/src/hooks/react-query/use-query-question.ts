import { useMutation, useQuery, useQueryClient, type UseMutationResult, type UseQueryResult } from "@tanstack/react-query";
import { NO_SUBJECT } from "@/constants/question.constant";
import { QUESTION_EVENT_KEYS, QUESTION_KEYS, REVIEW_KEYS } from "@/constants/react-query-key.constant";
import type { BulkQuestionsBody, BulkTopicsBody, QuestionBody, QuestionSearchBody, UpdateQuestionBody } from "@/dtos/question.dto";
import type { SearchBody } from "@/dtos/search.dto";
import type { BankFacets, BulkResult, BulkTopicsResult, ParsedQuestion, Question, QuestionEvent, QuestionStats, TopicSuggestion, UndoResult } from "@/interfaces/question.interface";
import type { RowsQueryOptions, SearchPage } from "@/interfaces/search-page.interface";
import { invalidate } from "@/lib/common/query-client";
import { questionService } from "@/services/question.service";
import { useSearchQuery } from "./use-search-query";

// the review screens show questions too, and every change of a question is a row of "Thay đổi gần đây"
const TOUCHED = [QUESTION_KEYS.ALL, REVIEW_KEYS.ALL, QUESTION_EVENT_KEYS.ALL] as const;

// `POST /questions/suggest-topics` takes at most 50 ids (topic-coverage contract)
const SUGGEST_BATCH = 50;

export function useQuestionSearchQuery(
  body: QuestionSearchBody,
  options?: RowsQueryOptions<ParsedQuestion> & { enabled?: boolean },
): UseQueryResult<SearchPage<ParsedQuestion>, Error> {
  return useSearchQuery(QUESTION_KEYS.SEARCH(body), questionService.search, body, options);
}

/** Facet counts of the bank for the same filters; paging and sort do not change them. */
export function useQuestionFacetsQuery(body: QuestionSearchBody, enabled = true): UseQueryResult<BankFacets, Error> {
  const { sort, ...rest } = body; // facets ignore ordering
  const facetsBody: QuestionSearchBody = { ...rest, page: 1 };
  return useQuery<BankFacets, Error>({ queryKey: QUESTION_KEYS.FACETS(facetsBody), queryFn: () => questionService.facets(facetsBody), enabled });
}

/** How many usable questions each topic's subtree holds in one subject — the number a picker writes beside a
 *  topic (pickers-builder ADR-01, AC-02). Without a subject there is no honest number, so nothing is asked for
 *  and the picker shows none. Same source as the bank's filters, so the two never disagree.
 *  `allSubjects` counts the whole bank instead, for a screen whose tree is the whole taxonomy — an exam with no
 *  subject of its own; the number then covers exactly the tree that is shown. */
export function useTopicCountsQuery(subjectId: string | null | undefined, enabled = true, allSubjects = false): UseQueryResult<Record<string, number>, Error> {
  const scoped = Boolean(subjectId) && subjectId !== NO_SUBJECT;
  return useQuery<Record<string, number>, Error>({
    queryKey: QUESTION_KEYS.TOPIC_COUNTS(scoped ? subjectId! : "all"),
    queryFn: async () => (await questionService.facets({ page: 1, limit: 1, ...(scoped ? { subject_id: subjectId! } : {}) })).topics,
    enabled: enabled && (scoped || allSubjects),
  });
}

export function useQuestionQuery(id: string): UseQueryResult<ParsedQuestion, Error> {
  return useQuery<ParsedQuestion, Error>({ queryKey: QUESTION_KEYS.DETAIL(id), queryFn: () => questionService.get(id) });
}

/** Item statistics of one question; the panel shows "chưa đủ dữ liệu" until there are enough answers. */
export function useQuestionStatsQuery(id: string): UseQueryResult<QuestionStats, Error> {
  return useQuery<QuestionStats, Error>({ queryKey: QUESTION_KEYS.STATS(id), queryFn: () => questionService.stats(id), enabled: Boolean(id) });
}

/** Topic candidates for the questions shown on one page (topic-coverage ADR-01); a page longer than
 *  the endpoint's limit is asked for in batches and the answers merged. Nothing is stored server-side,
 *  so an assignment invalidates these together with the list. The rules answer in ~0.1 s and the model in tens of
 *  seconds, so the page asks twice: once without the model to fill the row at once, once with it. */
export function useTopicSuggestionsQuery(ids: string[], useModel = false): UseQueryResult<Record<string, TopicSuggestion[]>, Error> {
  return useQuery<Record<string, TopicSuggestion[]>, Error>({
    queryKey: QUESTION_KEYS.SUGGESTIONS(ids, useModel),
    queryFn: async () => {
      const out: Record<string, TopicSuggestion[]> = {};
      for (let i = 0; i < ids.length; i += SUGGEST_BATCH) {
        const { suggestions } = await questionService.suggestTopics({ question_ids: ids.slice(i, i + SUGGEST_BATCH), use_model: useModel });
        Object.assign(out, suggestions);
      }
      return out;
    },
    enabled: ids.length > 0,
  });
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

/** "Thay đổi gần đây": one row per request that changed the bank, newest first (bulk-safety AC-03). */
export function useQuestionEventSearchQuery(body: SearchBody, options?: RowsQueryOptions<QuestionEvent>): UseQueryResult<SearchPage<QuestionEvent>, Error> {
  return useSearchQuery(QUESTION_EVENT_KEYS.SEARCH(body), questionService.searchEvents, body, options);
}

/** Takes a whole batch back (AC-01). The restore is itself a change, so the history refreshes with the lists:
 *  the batch just undone turns read-only and the undo appears as its own row — from the server, not from here. */
export function useUndoBatchMutation(): UseMutationResult<UndoResult, Error, string> {
  const qc = useQueryClient();
  return useMutation<UndoResult, Error, string>({
    mutationFn: (batchId) => questionService.undo({ batch_id: batchId }),
    onSuccess: () => invalidate(qc, ...TOUCHED),
  });
}

/** A topic per question in one request (pickers-builder ADR-02): the tagging queue's "Gán theo gợi ý".
 *  The answer names what it skipped; the caller reports it. */
export function useBulkTopicsMutation(): UseMutationResult<BulkTopicsResult, Error, BulkTopicsBody> {
  const qc = useQueryClient();
  return useMutation<BulkTopicsResult, Error, BulkTopicsBody>({
    mutationFn: questionService.bulkTopics,
    // started, not awaited: one of the queries this refreshes is the queue's own suggestions, which the
    // model answers in tens of seconds — the teacher hears what the click did at once, not after it
    onSuccess: () => void invalidate(qc, ...TOUCHED),
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
