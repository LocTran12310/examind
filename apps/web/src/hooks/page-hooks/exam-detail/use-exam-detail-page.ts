import { useState } from "react";
import type { BlueprintRefusal, BlueprintRow, BlueprintShortfall } from "@/interfaces/exam.interface";
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
import { emptyTopicRefusal } from "@/lib/page-libs/exam-detail/blueprint";

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
  const [refusal, setRefusal] = useState<BlueprintRefusal | null>(null);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const { data: found } = useQuestionSearchQuery({ page: 1, limit: 10, q: query }, { enabled: !!query });
  const [preview, setPreview] = useState<ExamPreviewMode>(null);
  const [error, setError] = useState<string | null>(null);
  const [assigning, setAssigning] = useState(false);
  const [swapping, setSwapping] = useState<string | null>(null);

  const generate = useGenerateExamMutation(id);
  const reorder = useReorderExamMutation(id);
  const swap = useSwapExamQuestionMutation(id);
  const remove = useRemoveExamQuestionMutation(id);
  const points = useExamQuestionPointsMutation(id);
  const update = useUpdateExamMutation(id);
  const add = useAddExamQuestionsMutation(id);

  /** `handled` may take an error the screen shows its own way (the empty-topic refusal). */
  async function run<R>(fn: () => Promise<R>, handled?: (e: unknown) => boolean): Promise<R | undefined> {
    setError(null);
    try {
      return await fn();
    } catch (e) {
      if (!handled?.(e)) setError(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
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
    refusal,
    clearRefusal: () => setRefusal(null),
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
    generate: (rows: BlueprintRow[]) => {
      setRefusal(null);
      void run(
        async () => {
          const r = await generate.mutateAsync({ rows });
          setShortfalls(r.shortfalls);
        },
        (e) => {
          // a row on an empty topic is refused by name: the matrix shows it, not the page's error line (AC-06)
          const r = emptyTopicRefusal(e);
          if (r) setRefusal(r);
          return !!r;
        },
      );
    },
    saveOrder: async (order: string[]) => void (await run(() => reorder.mutateAsync(order))),
    /** the question whose replacement is being chosen */
    swapping: exam?.questions.find((q) => q.id === swapping) ?? null,
    openSwap: (qid: string) => setSwapping(qid),
    closeSwap: () => setSwapping(null),
    /** the automatic replacement: the server picks from the same matrix row */
    autoSwap: () => {
      const qid = swapping;
      setSwapping(null);
      if (qid) void run(() => swap.mutateAsync(qid));
    },
    /** the teacher's own choice: the chosen question takes the place, the number and the points of the old
     *  one — added, the old one dropped, the order restored, then the points put back (ADR-03, AC-07) */
    chooseSwap: (newId: string) => {
      const old = exam?.questions.find((q) => q.id === swapping);
      if (!exam || !old || inExam.has(newId)) return;
      setSwapping(null);
      void run(async () => {
        const order = exam.questions.map((q) => (q.id === old.id ? newId : q.id));
        await add.mutateAsync([newId]);
        await remove.mutateAsync(old.id);
        await reorder.mutateAsync(order);
        if (old.points !== exam.settings.points_by_type[old.type]) await points.mutateAsync({ questionId: newId, points: old.points });
      });
    },
    remove: (qid: string) => void run(() => remove.mutateAsync(qid)),
    setPoints: (qid: string, value: number) => void run(() => points.mutateAsync({ questionId: qid, points: value })),
    setTypePoints: (type: QuestionType, value: number) => void run(() => update.mutateAsync({ settings: { points_by_type: { [type]: value } } })),
    addQuestion: (qid: string) => void run(() => add.mutateAsync([qid])),
    // the new assignment shows up in "Đã giao" through the invalidated assignments query
    doneAssigning: () => setAssigning(false),
  };
}
