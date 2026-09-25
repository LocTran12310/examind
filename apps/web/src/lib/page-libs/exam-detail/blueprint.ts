import { DIFFICULTY_LABEL, TYPE_LABEL } from "@/constants/question.constant";
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

/** What a row narrows its topic down to, in the words of its own two selects. */
function rowFilterLabel(row: BlueprintRow): string {
  return [row.type ? TYPE_LABEL[row.type] : null, row.difficulty ? DIFFICULTY_LABEL[row.difficulty] : null].filter(Boolean).join(" · ");
}

/** Why a row cannot be filled, said with both numbers it has (AC-03): what its topic holds altogether and what
 *  its own filters leave of that. A teacher who only reads "thiếu 3 câu" cannot tell the two cases apart —
 *  a topic that is simply short, and a full topic whose questions are of another type. Without both numbers
 *  (a row on a tag, a count still on its way) it stays the bare sentence it has always been. */
export function shortfallReason(row: BlueprintRow, held: number | null, matching: number | null, missing: number): string {
  if (held === null || matching === null || held === 0) return `thiếu ${missing} câu`;
  if (matching >= held) return `Chuyên đề chỉ có ${held} câu dùng được — thiếu ${missing} câu.`;
  return `Chuyên đề có ${held} câu dùng được, nhưng chỉ ${matching} câu là “${rowFilterLabel(row)}” — thiếu ${missing} câu.`;
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
