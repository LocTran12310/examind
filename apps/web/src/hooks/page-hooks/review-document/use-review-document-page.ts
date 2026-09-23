import { useMemo, useState } from "react";
import { toast } from "sonner";
import { payloadOf, type QuestionFormValue } from "@/components/common/QuestionForm/QuestionForm";
import { STATUS_LABEL } from "@/constants/question.constant";
import { useTableQuery } from "@/hooks/common/use-table-query";
import { useBulkUpdateQuestionsMutation, useTopicCountsQuery, useUpdateQuestionMutation } from "@/hooks/react-query/use-query-question";
import { useApproveConfidentMutation, useDocumentQuestionsSearchQuery, useReviewDocumentQuery, useReviewQueueQuery } from "@/hooks/react-query/use-query-review";
import { useTagOptionsQuery } from "@/hooks/react-query/use-query-tag";
import { useTaxonomyQuery } from "@/hooks/react-query/use-query-taxonomy";
import { useTopicsQuery } from "@/hooks/react-query/use-query-topic";
import type { DocumentQuestionState } from "@/interfaces/review.interface";
import type { QuestionStatus } from "@/interfaces/question.interface";
import { ApiError } from "@/lib/common/http";

const DEFAULT_STATE: DocumentQuestionState = "pending";

/** One document under review: the state filter, the keyboard queue, the questions of any other state,
 *  their editing and re-decision, the answer-key dialog and "approve confident". */
export function useReviewDocumentPage(id: string) {
  const tq = useTableQuery();
  const state = (tq.get("state") || DEFAULT_STATE) as DocumentQuestionState;
  const info = useReviewDocumentQuery(id);
  const queue = useReviewQueueQuery(id);
  const subjectId = info.data?.document.meta.subject_id ?? null;
  const { data: topics } = useTopicsQuery(subjectId, !!info.data);
  const { data: taxonomy } = useTaxonomyQuery();
  const { data: topicCounts } = useTopicCountsQuery(subjectId);
  const { data: tags } = useTagOptionsQuery(subjectId ?? "shared", !!info.data);
  const approve = useApproveConfidentMutation(id);
  const { mutateAsync: redecideQuestions } = useBulkUpdateQuestionsMutation();
  const { mutateAsync: updateQuestion } = useUpdateQuestionMutation();
  const [pasting, setPasting] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  // the queue is a snapshot: a new version remounts it with the reloaded questions
  const [version, setVersion] = useState(0);
  // the decided states are read from the search endpoint; the keyboard queue keeps its own endpoint
  const body = useMemo(() => ({ page: tq.page, limit: tq.pageSize, state }), [tq.page, tq.pageSize, state]);
  const list = useDocumentQuestionsSearchQuery(id, body, { enabled: state !== DEFAULT_STATE });
  const data = info.data;

  async function run(fn: () => Promise<unknown>) {
    try {
      await fn();
      return true;
    } catch (e) {
      toast.error(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
      return false;
    }
  }

  return {
    info: data,
    queue: queue.data,
    topics,
    topicCounts,
    taxonomy,
    tags,
    state,
    setState: (v: DocumentQuestionState) => {
      setEditingId(null);
      setNotice(null);
      tq.setFilter("state", v === DEFAULT_STATE ? null : v);
    },
    list: list.data,
    listLoading: list.isFetching,
    page: tq.page,
    pageSize: tq.pageSize,
    setPage: tq.setPage,
    confident: data ? data.counts.auto_approved - data.spot_pending : 0,
    pasting,
    setPasting,
    notice,
    version,
    editingId,
    setEditingId,
    approveConfident: async () => {
      const r = await approve.mutateAsync();
      setNotice(`Đã duyệt ${r.approved} câu tin cậy cao.`);
    },
    /** Re-deciding is the same command that decided first (ADR-02); the counts and the state follow. */
    redecide: async (questionId: string, status: QuestionStatus) => {
      const ok = await run(() => redecideQuestions({ ids: [questionId], set: { status } }));
      if (!ok) return;
      setNotice(`Đã chuyển câu hỏi sang "${STATUS_LABEL[status]}".`);
      setVersion((v) => v + 1);
    },
    saveQuestion: async (questionId: string, v: QuestionFormValue) => {
      await updateQuestion({ id: questionId, body: payloadOf(v) });
      setEditingId(null);
      setNotice("Đã lưu câu hỏi.");
      setVersion((x) => x + 1);
    },
    reloadInfo: () => void info.refetch(),
    answerKeyDone: async () => {
      setPasting(false);
      await Promise.all([info.refetch(), queue.refetch()]);
      setVersion((v) => v + 1);
    },
  };
}
