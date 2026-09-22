import { useState } from "react";
import type { BlueprintRow, BlueprintShortfall } from "@/interfaces/exam.interface";
import type { QuestionType } from "@/interfaces/question.interface";
import { useExamAssignmentsQuery } from "@/hooks/react-query/use-query-assignment";
import { useClassOptionsQuery } from "@/hooks/react-query/use-query-class";
import {
  useAddExamQuestionsMutation,
  useExamQuery,
  useExamQuestionPointsMutation,
  useGenerateExamMutation,
  useRemoveExamQuestionMutation,
  useReorderExamMutation,
  useSwapExamQuestionMutation,
  useUpdateExamMutation,
} from "@/hooks/react-query/use-query-exam";
import { useQuestionSearchQuery } from "@/hooks/react-query/use-query-question";
import { useTagOptionsQuery } from "@/hooks/react-query/use-query-tag";
import { useTopicsQuery } from "@/hooks/react-query/use-query-topic";
import { ApiError } from "@/lib/common/http";

export type ExamPreviewMode = null | "exam" | "review";

/** The exam builder: matrix, questions (order, swap, remove, points), default points per type,
 *  adding from the bank, the preview and the assignments of this exam. Every change refreshes the exam. */
export function useExamDetailPage(id: string) {
  const { data: exam } = useExamQuery(id);
  // the matrix only offers the exam's subject (subject-scoped-bank A-07)
  const sid = exam?.subject_id || null;
  const { data: topics } = useTopicsQuery(sid, !!exam);
  const { data: tags } = useTagOptionsQuery(sid, !!exam);
  const { data: classes } = useClassOptionsQuery();
  const { data: assigned } = useExamAssignmentsQuery(id);
  const [shortfalls, setShortfalls] = useState<BlueprintShortfall[]>([]);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const { data: found } = useQuestionSearchQuery({ page: 1, limit: 10, q: query }, { enabled: !!query });
  const [preview, setPreview] = useState<ExamPreviewMode>(null);
  const [error, setError] = useState<string | null>(null);
  const [assigning, setAssigning] = useState(false);

  const generate = useGenerateExamMutation(id);
  const reorder = useReorderExamMutation(id);
  const swap = useSwapExamQuestionMutation(id);
  const remove = useRemoveExamQuestionMutation(id);
  const points = useExamQuestionPointsMutation(id);
  const update = useUpdateExamMutation(id);
  const add = useAddExamQuestionsMutation(id);

  async function run<R>(fn: () => Promise<R>): Promise<R | undefined> {
    setError(null);
    try {
      return await fn();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
      return undefined;
    }
  }

  const inExam = new Set(exam?.questions.map((q) => q.id) ?? []);

  return {
    exam,
    topics,
    tags,
    classes: classes ?? [],
    assigned: assigned ?? [],
    shortfalls,
    error,
    preview,
    setPreview,
    assigning,
    setAssigning,
    search,
    setSearch,
    found: found?.data ?? [],
    inExam,
    findInBank: () => setQuery(search),
    generate: (rows: BlueprintRow[]) =>
      void run(async () => {
        const r = await generate.mutateAsync({ rows });
        setShortfalls(r.shortfalls);
      }),
    saveOrder: async (order: string[]) => void (await run(() => reorder.mutateAsync(order))),
    swap: (qid: string) => void run(() => swap.mutateAsync(qid)),
    remove: (qid: string) => void run(() => remove.mutateAsync(qid)),
    setPoints: (qid: string, value: number) => void run(() => points.mutateAsync({ questionId: qid, points: value })),
    setTypePoints: (type: QuestionType, value: number) => void run(() => update.mutateAsync({ settings: { points_by_type: { [type]: value } } })),
    addQuestion: (qid: string) => void run(() => add.mutateAsync([qid])),
    // the new assignment shows up in "Đã giao" through the invalidated assignments query
    doneAssigning: () => setAssigning(false),
  };
}
