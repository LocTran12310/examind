import type { AnswerResponse } from "@/types/attempt.type";

export interface SaveAnswerBody {
  response: AnswerResponse;
}

export interface GradeAnswerBody {
  points: number;
  comment: string | null;
}
