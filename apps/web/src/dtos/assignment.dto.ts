import type { ResultsPolicy } from "@/types/assignment.type";

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
