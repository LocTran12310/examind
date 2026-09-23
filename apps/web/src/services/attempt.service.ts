import type { GradeAnswerBody, SaveAnswerBody } from "@/dtos/attempt.dto";
import type { AttemptResult, AttemptView, GradeResult } from "@/interfaces/attempt.interface";
import { http } from "@/lib/common/http";

export const attemptService = {
  get: (id: string) => http<AttemptView>(`/attempts/${id}`),
  /** One answer plus the time it took; the answer is stored, the timing accumulated. */
  saveAnswer: (id: string, questionId: string, body: SaveAnswerBody) => http<unknown>(`/attempts/${id}/answers/${questionId}`, { method: "PUT", body }),
  submit: (id: string) => http<unknown>(`/attempts/${id}/submit`, { method: "POST" }),
  /** The student left the exam tab. */
  tabSwitch: (id: string) => http<unknown>(`/attempts/${id}/tab-switch`, { method: "POST" }),
  result: (id: string) => http<AttemptResult>(`/attempts/${id}/result`),
  grade: (id: string, questionId: string, body: GradeAnswerBody) => http<GradeResult>(`/attempts/${id}/answers/${questionId}/grade`, { method: "PATCH", body }),
};
