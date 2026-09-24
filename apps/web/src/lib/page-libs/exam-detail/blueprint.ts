import type { QuestionSearchBody } from "@/dtos/question.dto";
import type { BlueprintRefusal, BlueprintRow } from "@/interfaces/exam.interface";
import { ApiError } from "@/lib/common/http";

/** The search body that counts exactly what one matrix row can draw from (blueprint-truth ADR-01): the exam's
 *  subject, the row's own topic subtree, tag, question type and difficulty, usable questions only — the same
 *  filter `POST /exams/{id}/blueprint` hands to the pool, so the number on the row and the number the generator
 *  finds cannot drift. Only `total` is read, hence `limit: 1`; a row with no topic has no number to show. */
export function rowPoolBody(subjectId: string | null | undefined, row: BlueprintRow): QuestionSearchBody | null {
  if (!row.topic_id) return null;
  return {
    page: 1, limit: 1, status: "usable", topic_id: row.topic_id,
    ...(subjectId ? { subject_id: subjectId } : {}),
    ...(row.tag_id ? { tag_ids: [row.tag_id] } : {}),
    ...(row.type ? { type: row.type } : {}),
    ...(row.difficulty ? { difficulty: row.difficulty } : {}),
  };
}

/** The 422 `empty_topic` of `POST /exams/{id}/blueprint` as the row it names (pickers-builder AC-06);
 *  anything else is not this refusal and is reported as a plain error. */
export function emptyTopicRefusal(e: unknown): BlueprintRefusal | null {
  if (!(e instanceof ApiError) || e.code !== "empty_topic") return null;
  const f = (e.fields ?? {}) as Record<string, unknown>;
  return {
    row: Number(f.row ?? 0),
    topic_id: String(f.topic_id ?? ""),
    topic_name: String(f.topic_name ?? ""),
    question_count: Number(f.question_count ?? 0),
    message: e.message,
  };
}
