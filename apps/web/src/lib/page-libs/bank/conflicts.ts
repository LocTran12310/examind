/**
 * The refusal the bank's "Môn" action can meet: a subject that would leave a question placed in another
 * subject's tree is refused whole, naming the questions and their topics (pickers-builder A-04, ADR-01 of
 * the API side). The teacher fixes the topic first; the bank never drops a placement by itself.
 */
import type { SubjectTopicConflict } from "@/interfaces/question.interface";
import { ApiError } from "@/lib/common/http";

export const SUBJECT_TOPIC_CONFLICT = "subject_topic_conflict";

function isConflict(x: unknown): x is SubjectTopicConflict {
  const c = x as SubjectTopicConflict;
  return !!c && typeof c.question_id === "string" && typeof c.topic_name === "string";
}

/** The conflicting questions of a refused bulk subject, or null when the error is something else. */
export function subjectTopicConflicts(error: unknown): SubjectTopicConflict[] | null {
  if (!(error instanceof ApiError) || error.code !== SUBJECT_TOPIC_CONFLICT) return null;
  const raw = (error.fields as Record<string, unknown> | undefined)?.conflicts;
  return Array.isArray(raw) ? raw.filter(isConflict) : [];
}
