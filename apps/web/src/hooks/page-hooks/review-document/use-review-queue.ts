import { useState } from "react";
import { useHotkeys } from "@/hooks/common/use-hotkeys";
import { useUpdateQuestionMutation } from "@/hooks/react-query/use-query-question";
import { useReviewActionMutation } from "@/hooks/react-query/use-query-review";
import type { ParsedQuestion } from "@/interfaces/question.interface";
import type { ReviewAction } from "@/interfaces/review.interface";
import type { Topic } from "@/interfaces/topic.interface";
import { ApiError } from "@/lib/common/http";

/** The review queue of one document: the current question, keyboard shortcuts, answer / topic / approve.
 *  The queue is a snapshot (`initial`): handled questions stay in place, marked, and are skipped by "next". */
export function useReviewQueue({ initial, hasEditor, onChange }: { initial: ParsedQuestion[]; hasEditor: boolean; onChange?: () => void }) {
  const [items, setItems] = useState(initial);
  const [done, setDone] = useState<Set<string>>(new Set());
  const [index, setIndex] = useState(0);
  const [message, setMessage] = useState<{ tone: "red" | "green"; text: string } | null>(null);
  const [picking, setPicking] = useState(false);
  const [editing, setEditing] = useState(false);
  const { mutateAsync: review } = useReviewActionMutation();
  const { mutateAsync: update } = useUpdateQuestionMutation();
  const q = items[index];
  const remaining = items.filter((x) => !done.has(x.id)).length;

  function replace(updated: ParsedQuestion) {
    setItems((xs) => xs.map((x) => (x.id === updated.id ? { ...x, ...updated, group: x.group } : x)));
  }

  function next(from = index) {
    const after = items.findIndex((x, i) => i > from && !done.has(x.id));
    if (after >= 0) setIndex(after);
  }

  async function run<T>(fn: () => Promise<T>): Promise<T | undefined> {
    setMessage(null);
    try {
      return await fn();
    } catch (e) {
      setMessage({ tone: "red", text: e instanceof ApiError ? e.message : "Có lỗi xảy ra" });
      return undefined;
    }
  }

  async function action(kind: ReviewAction) {
    if (!q) return;
    const r = await run(() => review({ questionId: q.id, action: kind }));
    if (!r) return;
    replace(r);
    if (kind !== "skip") setDone((s) => new Set(s).add(q.id));
    onChange?.();
    next();
  }

  async function setAnswer(label: string) {
    if (!q) return;
    const previous = q;
    let answer: Record<string, unknown>;
    if (q.type === "true_false") {
      const cur = (q.answer ?? {}) as Record<string, boolean | null>;
      answer = Object.fromEntries(q.options.map((o) => [o.label, o.label === label ? !(cur[o.label] ?? false) : (cur[o.label] ?? false)]));
    } else {
      answer = { key: label };
    }
    replace({ ...q, answer: answer as ParsedQuestion["answer"] }); // optimistic
    const r = await run(() => update({ id: q.id, body: { answer } }));
    if (r) replace(r);
    else replace(previous);
  }

  async function pickTopic(t: Topic) {
    if (!q) return;
    setPicking(false);
    const r = await run(() => update({ id: q.id, body: { primary_topic_id: t.id } }));
    if (r) replace(r);
  }

  /** A teacher sets the level. The answer carries `difficulty_source: "manual"` back, so the card stops offering
   * the machine's guess without the hook having to decide that for itself. */
  async function pickDifficulty(level: string) {
    if (!q) return;
    const r = await run(() => update({ id: q.id, body: { difficulty: level } }));
    if (r) replace(r);
  }

  const choosable = !!q && ["mcq", "true_false"].includes(q.type);
  const labelFor = (n: number) => (q?.type === "true_false" ? "abcd" : "ABCD")[n - 1];
  const prev = () => setIndex((i) => Math.max(i - 1, 0));
  useHotkeys(
    {
      Enter: () => void action("approve"),
      x: () => void action("reject"),
      s: () => void action("skip"),
      j: () => setIndex((i) => Math.min(i + 1, items.length - 1)),
      k: prev,
      t: () => setPicking(true),
      e: () => hasEditor && setEditing(true),
      "1": () => choosable && void setAnswer(labelFor(1)),
      "2": () => choosable && void setAnswer(labelFor(2)),
      "3": () => choosable && void setAnswer(labelFor(3)),
      "4": () => choosable && void setAnswer(labelFor(4)),
    },
    !picking && !editing,
  );

  return {
    items,
    q,
    index,
    done,
    remaining,
    message,
    picking,
    setPicking,
    editing,
    setEditing,
    choosable,
    prev,
    action: (kind: ReviewAction) => void action(kind),
    setAnswer: (label: string) => void setAnswer(label),
    pickTopic: (t: Topic) => void pickTopic(t),
    pickDifficulty: (level: string) => void pickDifficulty(level),
    saved: (r: ParsedQuestion) => {
      replace(r);
      setEditing(false);
    },
  };
}
