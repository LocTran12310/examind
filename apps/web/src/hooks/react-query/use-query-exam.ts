import { useMutation, useQuery, useQueryClient, type UseMutationResult, type UseQueryResult } from "@tanstack/react-query";
import { EXAM_KEYS } from "@/constants/react-query-key.constant";
import type { BlueprintBody, CreateExamBody, ExamSearchBody, UpdateExamBody } from "@/dtos/exam.dto";
import type { SearchBody } from "@/dtos/search.dto";
import type { BlueprintResult, Exam, ExamQuestion } from "@/interfaces/exam.interface";
import type { RowsQueryOptions, SearchPage } from "@/interfaces/search-page.interface";
import { invalidate } from "@/lib/common/query-client";
import { examService } from "@/services/exam.service";
import { useSearchQuery } from "./use-search-query";

export function useExamSearchQuery(body: SearchBody, options?: RowsQueryOptions<Exam>): UseQueryResult<SearchPage<Exam>, Error> {
  return useSearchQuery(EXAM_KEYS.SEARCH(body), examService.search, body, options);
}

/** One exam with its questions; `null` = nothing chosen yet (fetched only once an id is given). */
export function useExamQuery(id: string | null): UseQueryResult<Exam, Error> {
  return useQuery<Exam, Error>({ queryKey: EXAM_KEYS.DETAIL(id ?? ""), queryFn: () => examService.get(id!), enabled: !!id });
}

/** One exam's questions for the shared table: the exam comes as the `exam_id` parameter of the body
 *  (DataTable `params`) and goes into the path, not into the search body. */
export function useExamQuestionSearchQuery(body: SearchBody, options?: RowsQueryOptions<ExamQuestion>): UseQueryResult<SearchPage<ExamQuestion>, Error> {
  const { exam_id, ...rest } = body;
  const id = String(exam_id ?? "");
  return useSearchQuery(EXAM_KEYS.QUESTIONS(id, rest), (b) => examService.searchQuestions(id, b), rest as SearchBody, { ...options, enabled: !!id });
}

function useExamMutation<V, R = Exam>(fn: (v: V) => Promise<R>): UseMutationResult<R, Error, V> {
  const qc = useQueryClient();
  return useMutation<R, Error, V>({ mutationFn: fn, onSuccess: () => invalidate(qc, EXAM_KEYS.ALL) });
}

export const useCreateExamMutation = () => useExamMutation<CreateExamBody>(examService.create);

/** The numbers on the subject tabs: same body as the list minus paging and ordering, which do not move them. */
export function useExamFacetsQuery(body: ExamSearchBody): UseQueryResult<{ subjects: Record<string, number> }, Error> {
  const { sort, subject_id, ...rest } = body; // the scope in hand must not shrink the other tabs
  const facetsBody: ExamSearchBody = { ...rest, page: 1 };
  return useQuery<{ subjects: Record<string, number> }, Error>({ queryKey: EXAM_KEYS.FACETS(facetsBody), queryFn: () => examService.facets(facetsBody) });
}

export function useDeleteExamsMutation(): UseMutationResult<void, Error, string[]> {
  const qc = useQueryClient();
  return useMutation<void, Error, string[]>({
    mutationFn: async (ids) => {
      for (const id of ids) await examService.remove(id);
    },
    onSettled: () => invalidate(qc, EXAM_KEYS.ALL),
  });
}

export const useUpdateExamMutation = (id: string) => useExamMutation<UpdateExamBody>((body) => examService.update(id, body));
/** Fill the exam from its matrix; the answer says which rows fell short. */
export const useGenerateExamMutation = (id: string) => useExamMutation<BlueprintBody, BlueprintResult>((body) => examService.generate(id, body));
export const useAddExamQuestionsMutation = (id: string) => useExamMutation<string[]>((ids) => examService.addQuestions(id, { question_ids: ids }));
export const useRemoveExamQuestionMutation = (id: string) => useExamMutation<string>((qid) => examService.removeQuestion(id, qid));
export const useSwapExamQuestionMutation = (id: string) => useExamMutation<string>((qid) => examService.swap(id, qid));
export const useExamQuestionPointsMutation = (id: string) =>
  useExamMutation<{ questionId: string; points: number }>(({ questionId, points }) => examService.setPoints(id, questionId, { points }));
/** Save the new order of every question at once. */
export const useReorderExamMutation = (id: string) => useExamMutation<string[]>((ids) => examService.reorder(id, { question_ids: ids }));
