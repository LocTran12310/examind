import type { ParsedQuestion, QuestionType } from "@/interfaces/question.interface";

/** One row of the exam matrix: a topic or a tag, an optional question type and difficulty, and a count.
 *
 *  `type` is optional because the endpoint has always treated it that way (`row.get("type") or None` — a row
 *  without one draws from every type). Declaring it required here made such a row — the seeded exams have
 *  them — render as a blank select nobody could read or reproduce. */
export interface BlueprintRow {
  topic_id?: string | null;
  tag_id?: string | null;
  type?: QuestionType | null;
  difficulty?: string | null;
  count: number;
}

/** A question inside an exam (a parsed question plus its place and points). */
export interface ExamQuestion extends ParsedQuestion {
  position: number;
  section: string;
  points: number;
  row: number | null;
}

export interface ExamSettings {
  points_by_type: Record<QuestionType, number>;
  scale_to: number;
}

/** An exam; the list (`POST /exams/search`) always sends `questions: []`. */
export interface Exam {
  id: string;
  title: string;
  subject_id: string | null;
  grade: number | null;
  description: string;
  settings: ExamSettings;
  blueprint: BlueprintRow[];
  source: string;
  question_count: number;
  total_points: number;
  created_at: string;
  questions: ExamQuestion[];
}

/** A matrix row that did not find enough questions. */
export interface BlueprintShortfall {
  row: number;
  missing: number;
}

/** A matrix row `POST /exams/{id}/blueprint` refused: its topic holds no usable question
 *  (422 `empty_topic`; pickers-builder A-05, AC-06). */
export interface BlueprintRefusal {
  row: number;
  topic_id: string;
  topic_name: string;
  question_count: number;
  message: string;
}

/** Answer of `POST /exams/{id}/blueprint`. */
export interface BlueprintResult {
  added: number;
  shortfalls: BlueprintShortfall[];
  exam: Exam;
}
