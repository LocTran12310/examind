import type { BlueprintRefusal } from "@/interfaces/exam.interface";
import { ApiError } from "@/lib/common/http";

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
