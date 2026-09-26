import type { SearchBody } from "@/dtos/search.dto";
import type { BlueprintRow, ExamSettings } from "@/interfaces/exam.interface";

/** `POST /exams/search` and `/exams/facets`: the subject the list is scoped to rides at the top of the body —
 *  an id, or "none" for the exams nobody gave a subject. */
export interface ExamSearchBody extends SearchBody {
  subject_id?: string | null;
}

export interface CreateExamBody {
  title: string;
  /** the exam's own subject: what its matrix and pickers are scoped to. Optional — a draft may not know yet. */
  subject_id?: string | null;
  /** the grade the paper is for (10/11/12), not a class */
  grade?: number | null;
}

/** `PATCH /exams/{id}`; `settings` is merged on the server (e.g. one type of `points_by_type`). */
export interface UpdateExamBody {
  title?: string;
  subject_id?: string | null;
  grade?: number | null;
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
