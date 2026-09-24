import type { ResultsPolicy } from "@/types/assignment.type";
import type { AnswerResponse } from "@/types/attempt.type";

/** `POST /assignments`; times are ISO UTC. */
export interface CreateAssignmentBody {
  exam_id: string;
  title: string;
  open_at: string;
  close_at: string;
  duration_minutes: number;
  max_attempts: number;
  shuffle_questions: boolean;
  shuffle_options: boolean;
  results_policy: ResultsPolicy;
  class_ids: string[];
}

/** `POST /assignments/{id}/trial`: the answers of a trial run keyed by question id, in the shapes an attempt saves.
 *  An empty map is a valid (blank) trial run. */
export interface TrialBody {
  responses: Record<string, AnswerResponse>;
}
