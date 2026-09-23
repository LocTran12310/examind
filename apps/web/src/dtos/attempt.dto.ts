import type { AnswerResponse } from "@/types/attempt.type";

/** `PUT /attempts/{id}/answers/{qid}`; the seconds are what the question was on screen since the last save
 *  (the server accumulates and clamps them) and `first_seen_at` is ISO UTC. */
export interface SaveAnswerBody {
  response: AnswerResponse;
  seconds_spent?: number;
  first_seen_at?: string;
}

export interface GradeAnswerBody {
  points: number;
  comment: string | null;
}
