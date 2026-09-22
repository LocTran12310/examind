import { useState } from "react";
import type { BlueprintRow } from "@/interfaces/exam.interface";
import type { Topic } from "@/interfaces/topic.interface";

/** Draft rows of the exam matrix and the row whose topic is being picked. */
export function useBlueprintEditor(initial: BlueprintRow[], topics: Topic[]) {
  const [rows, setRows] = useState<BlueprintRow[]>(initial.length ? initial : [{ type: "mcq", count: 10 }]);
  const [picking, setPicking] = useState<number | null>(null);
  const byId = new Map(topics.map((t) => [t.id, t]));
  const set = (i: number, patch: Partial<BlueprintRow>) => setRows(rows.map((r, j) => (j === i ? { ...r, ...patch } : r)));
  return {
    rows,
    byId,
    set,
    picking,
    setPicking,
    total: rows.reduce((n, r) => n + (r.count || 0), 0),
    invalid: rows.some((r) => !(r.topic_id || r.tag_id) || !r.count),
    addRow: () => setRows([...rows, { type: "mcq", count: 5 }]),
    removeRow: (i: number) => setRows(rows.filter((_, j) => j !== i)),
    pick: (topicId: string) => {
      if (picking !== null) set(picking, { topic_id: topicId });
      setPicking(null);
    },
  };
}
