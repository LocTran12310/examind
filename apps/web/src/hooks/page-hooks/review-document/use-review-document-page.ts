import { useState } from "react";
import { useApproveConfidentMutation, useReviewDocumentQuery, useReviewQueueQuery } from "@/hooks/react-query/use-query-review";
import { useTopicsQuery } from "@/hooks/react-query/use-query-topic";

/** One document under review: its counts, the queue, the answer-key dialog and "approve confident". */
export function useReviewDocumentPage(id: string) {
  const info = useReviewDocumentQuery(id);
  const queue = useReviewQueueQuery(id);
  const subjectId = info.data?.document.meta.subject_id ?? null;
  const { data: topics } = useTopicsQuery(subjectId, !!info.data);
  const approve = useApproveConfidentMutation(id);
  const [pasting, setPasting] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  // the queue is a snapshot: a new version remounts it with the reloaded questions
  const [version, setVersion] = useState(0);
  const data = info.data;
  return {
    info: data,
    queue: queue.data,
    topics,
    confident: data ? data.counts.auto_approved - data.spot_pending : 0,
    pasting,
    setPasting,
    notice,
    version,
    approveConfident: async () => {
      const r = await approve.mutateAsync();
      setNotice(`Đã duyệt ${r.approved} câu tin cậy cao.`);
    },
    reloadInfo: () => void info.refetch(),
    answerKeyDone: async () => {
      setPasting(false);
      await Promise.all([info.refetch(), queue.refetch()]);
      setVersion((v) => v + 1);
    },
  };
}
