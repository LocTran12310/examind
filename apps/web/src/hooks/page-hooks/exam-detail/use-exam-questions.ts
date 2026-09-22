import { useMemo, useState } from "react";
import type { ExamQuestion } from "@/interfaces/exam.interface";
import { movedTo, swapped } from "@/lib/page-libs/exam-detail/order";

/** The questions of the exam and a draft order (drag and drop, ↑/↓, "Đổi chỗ với"), saved once. */
export function useExamQuestions(questions: ExamQuestion[], onSaveOrder: (ids: string[]) => Promise<void> | void) {
  const [order, setOrder] = useState<string[] | null>(null);
  const [dragging, setDragging] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const byId = useMemo(() => new Map(questions.map((q) => [q.id, q])), [questions]);
  const original = questions.map((q) => q.id);
  const sectionOf = (id: string) => byId.get(id)?.section;
  return {
    order,
    list: order ? order.map((id) => byId.get(id)!).filter(Boolean) : [],
    original,
    changed: order ? order.filter((id, i) => id !== original[i]).length : 0,
    saving,
    dragging,
    setDragging,
    startOrdering: () => setOrder(original),
    cancel: () => setOrder(null),
    swap: (a: string, b: string) => order && setOrder(swapped(order, a, b)),
    /** drop `dragging` onto `target`, only inside one part */
    canDrop: (target: ExamQuestion) => !!dragging && sectionOf(dragging) === target.section,
    drop: (target: ExamQuestion) => {
      if (order && dragging && sectionOf(dragging) === target.section) setOrder(movedTo(order, dragging, target.id));
      setDragging(null);
    },
    save: async () => {
      if (!order) return;
      setSaving(true);
      try {
        await onSaveOrder(order);
        setOrder(null);
      } finally {
        setSaving(false);
      }
    },
  };
}
