import type { RunnerPaper } from "@/interfaces/attempt.interface";
import type { QuestionType } from "@/interfaces/question.interface";
import type { AssignmentState, ResultsPolicy } from "@/types/assignment.type";
import type { AttemptStatus } from "@/types/attempt.type";

/** An exam given to classes in a time window; `students` / `submitted` count its attempts. */
export interface Assignment {
  id: string;
  exam_id: string;
  title: string;
  open_at: string;
  close_at: string;
  duration_minutes: number;
  max_attempts: number;
  shuffle_questions: boolean;
  shuffle_options: boolean;
  results_policy: ResultsPolicy;
  students: number;
  submitted: number;
  classes: string[];
}

export interface AttemptBrief {
  id: string;
  status: AttemptStatus;
  started_at: string;
  deadline_at: string;
  submitted_at: string | null;
  score: number | null;
  max_score: number | null;
  score10: number | null;
  needs_grading: boolean;
}

/** One entry of `GET /me/assignments`. */
export interface MyAssignment {
  assignment: Assignment;
  state: AssignmentState;
  attempts: AttemptBrief[];
  attempts_left: number;
  /** the subject of the exam behind it, so the home screen can group by it; null when the exam has none */
  subject_id: string | null;
}

/** `GET /assignments/{id}/report`. */
export interface AssignmentReport {
  assignment_id: string;
  title: string;
  submitted: number;
  total_students: number;
  average: number | null;
  distribution: { from: number; to: number; count: number }[];
  students: { student_id: string; full_name: string; username: string; status: string; attempt_id: string | null; score10: number | null; needs_grading: boolean; tab_switches: number }[];
  questions: { question_id: string; position: number; type: QuestionType; stem: string; answered: number; ratio: number | null; top_wrong: { label: string; count: number } | null }[];
}

/** Answer of `POST /assignments/{id}/start`. */
export interface StartedAttempt {
  attempt_id: string;
}

/** `GET /assignments/{id}/paper`: the questions as a student sees them (no keys, no solutions) with no attempt
 *  behind them — what a trial run is sat from. */
export interface AssignmentPaper extends RunnerPaper {
  assignment_id: string;
  exam_id: string;
  max_score: number;
}
