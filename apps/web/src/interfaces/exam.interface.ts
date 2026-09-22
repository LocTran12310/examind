import type { ParsedQuestion, QuestionType } from "@/interfaces/question.interface";

/** One row of the exam matrix: a topic or a tag, a question type, an optional difficulty and a count. */
export interface BlueprintRow {
  topic_id?: string | null;
  tag_id?: string | null;
  type: QuestionType;
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

/** Answer of `POST /exams/{id}/blueprint`. */
export interface BlueprintResult {
  added: number;
  shortfalls: BlueprintShortfall[];
  exam: Exam;
}
