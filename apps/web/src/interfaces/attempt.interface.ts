import type { ParsedQuestion, Question } from "@/interfaces/question.interface";
import type { AnswerResponse, AttemptStatus } from "@/types/attempt.type";

export interface AttemptQuestion extends Question {
  number: number;
  section: string;
  points: number;
  response: AnswerResponse;
}

/** `GET /attempts/{id}`: what the runner needs; `server_now` sets the countdown on the server clock. */
export interface AttemptView {
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

/** `GET /attempts/{id}/result`; `hidden` with a `reason` when the policy keeps answers back. */
export interface AttemptResult {
  id: string;
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
