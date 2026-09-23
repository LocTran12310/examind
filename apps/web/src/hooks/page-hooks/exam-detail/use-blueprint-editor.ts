import { useState } from "react";
import { useTopicCountsQuery } from "@/hooks/react-query/use-query-question";
import type { BlueprintRow } from "@/interfaces/exam.interface";
import type { Topic } from "@/interfaces/topic.interface";

/** Draft rows of the exam matrix, the row whose topic is being picked, and how many questions each topic holds
 *  in the exam's subject — the number the row and the picker show, from the facets (pickers-builder ADR-01).
 *  `onEdit` fires on every change so the page drops a refusal that no longer describes these rows. */
export function useBlueprintEditor(initial: BlueprintRow[], topics: Topic[], subjectId?: string | null, onEdit?: () => void) {
  const [rows, setRows] = useState<BlueprintRow[]>(initial.length ? initial : [{ type: "mcq", count: 10 }]);
  const [picking, setPicking] = useState<number | null>(null);
  // an exam without a subject of its own offers the whole tree, so the counts cover the whole bank
  const { data: counts } = useTopicCountsQuery(subjectId, true, true);
  const byId = new Map(topics.map((t) => [t.id, t]));
  const change = (next: BlueprintRow[]) => {
    setRows(next);
    onEdit?.();
  };
  const set = (i: number, patch: Partial<BlueprintRow>) => change(rows.map((r, j) => (j === i ? { ...r, ...patch } : r)));
  return {
    rows,
    byId,
    counts,
    set,
    picking,
    setPicking,
    /** questions in that row's topic, or null while there is no topic or no count to show */
    held: (row: BlueprintRow) => (row.topic_id && counts ? (counts[row.topic_id] ?? 0) : null),
    total: rows.reduce((n, r) => n + (r.count || 0), 0),
    invalid: rows.some((r) => !(r.topic_id || r.tag_id) || !r.count),
    addRow: () => change([...rows, { type: "mcq", count: 5 }]),
    removeRow: (i: number) => change(rows.filter((_, j) => j !== i)),
    pick: (topicId: string) => {
      if (picking !== null) set(picking, { topic_id: topicId });
      setPicking(null);
    },
  };
}
