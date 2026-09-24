import type { ParsedQuestion, Question } from "@/interfaces/question.interface";
import type { AnswerResponse, AttemptStatus } from "@/types/attempt.type";

export interface AttemptQuestion extends Question {
  number: number;
  section: string;
  points: number;
  response: AnswerResponse;
}

/** What the runner works on. An attempt fills in the whole of it; a trial run's paper has a title and questions and
 *  nothing else — no attempt to save to, no deadline, no server clock (exam-runner ADR-01). */
export interface RunnerPaper {
  id?: string;
  status?: AttemptStatus;
  deadline_at?: string;
  server_now?: string;
  title: string;
  questions: AttemptQuestion[];
}

/** `GET /attempts/{id}`: what the runner needs; `server_now` sets the countdown on the server clock. */
export interface AttemptView extends RunnerPaper {
  id: string;
  title: string;
  status: AttemptStatus;
  started_at: string;
  deadline_at: string;
  submitted_at: string | null;
  server_now: string;
  tab_switches: number;
  student: { id: string; full_name: string; username: string };
  assignment_id: string | null;
  questions: AttemptQuestion[];
}

export interface ResultQuestion extends ParsedQuestion {
  section: string;
  response: AnswerResponse;
  points: number | null;
  max_points: number;
  is_correct: boolean | null;
  comment: string | null;
}

/** `GET /attempts/{id}/result`; `hidden` with a `reason` when the policy keeps answers back.
 *  `id` is null for a trial run: it is graded in memory and there is no attempt to point at (exam-runner ADR-01). */
export interface AttemptResult {
  id: string | null;
  title: string;
  status: string;
  submitted_at: string | null;
  needs_grading: boolean;
  tab_switches: number;
  hidden: boolean;
  reason?: string;
  available_at?: string | null;
  score?: number;
  max_score?: number;
  score10?: number;
  questions?: ResultQuestion[];
  sections?: { section: string; points: number; max_points: number }[];
  topics?: { topic: string; points: number; max_points: number; count: number }[];
}

/** Answer of `PATCH /attempts/{id}/answers/{qid}/grade`. */
export interface GradeResult {
  score: number;
  needs_grading: boolean;
}
