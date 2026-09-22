import type { BlueprintRow, ExamSettings } from "@/interfaces/exam.interface";

export interface CreateExamBody {
  title: string;
}

/** `PATCH /exams/{id}`; `settings` is merged on the server (e.g. one type of `points_by_type`). */
export interface UpdateExamBody {
  title?: string;
  description?: string;
  settings?: { points_by_type?: Partial<ExamSettings["points_by_type"]>; scale_to?: number };
}

export interface BlueprintBody {
  rows: BlueprintRow[];
  seed?: number;
  replace?: boolean;
}

export interface ExamQuestionIdsBody {
  question_ids: string[];
}

export interface ExamQuestionPointsBody {
  points: number;
}
