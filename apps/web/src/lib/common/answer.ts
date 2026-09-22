import type { AttemptQuestion } from "@/interfaces/attempt.interface";
import type { AnswerResponse } from "@/types/attempt.type";

/** Whether a response counts as an answer (every true/false statement decided, text not blank). */
export function answered(q: AttemptQuestion, v: AnswerResponse): boolean {
  if (!v) return false;
  if (q.type === "mcq") return !!v.key;
  if (q.type === "true_false") return q.options.every((o) => typeof v[o.label] === "boolean");
  if (q.type === "short_answer") return !!String(v.value ?? "").trim();
  return !!String(v.text ?? "").trim();
}
