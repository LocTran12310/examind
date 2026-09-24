import { useState } from "react";
import { useQuestionCountsQuery, useTopicCountsQuery } from "@/hooks/react-query/use-query-question";
import type { BlueprintRow } from "@/interfaces/exam.interface";
import type { Topic } from "@/interfaces/topic.interface";
import { rowPoolBody } from "@/lib/page-libs/exam-detail/blueprint";

/** Draft rows of the exam matrix, the row whose topic is being picked, and two counts per row: what its topic
 *  holds in the exam's subject (the facets, what the picker writes beside a topic — pickers-builder ADR-01) and
 *  what the row's own filters select (blueprint-truth ADR-01). The second is the one the generator will draw
 *  from; the first is what lets the row say that a topic is full but this row's type or difficulty is not.
 *  `onEdit` fires on every change so the page drops a refusal that no longer describes these rows. */
export function useBlueprintEditor(initial: BlueprintRow[], topics: Topic[], subjectId?: string | null, onEdit?: () => void) {
  const [rows, setRows] = useState<BlueprintRow[]>(initial.length ? initial : [{ type: "mcq", count: 10 }]);
  const [picking, setPicking] = useState<number | null>(null);
  // an exam without a subject of its own offers the whole tree, so the counts cover the whole bank
  const { data: counts } = useTopicCountsQuery(subjectId, true, true);
  // one count per row, re-asked whenever that row's topic, tag, type or difficulty changes (AC-02)
  const matching = useQuestionCountsQuery(rows.map((r) => rowPoolBody(subjectId, r)));
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
    /** questions in that row's topic whatever their type or difficulty, or null while there is none to show */
    held: (row: BlueprintRow) => (row.topic_id && counts ? (counts[row.topic_id] ?? 0) : null),
    /** questions this row's own filters select — the pool the generator will draw from (AC-01) */
    matching: (i: number) => matching[i] ?? null,
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
