import type { GradeAnswerBody, SaveAnswerBody } from "@/dtos/attempt.dto";
import type { SearchBody } from "@/dtos/search.dto";
import type { AttemptHistoryRow, AttemptResult, AttemptView, GradeResult } from "@/interfaces/attempt.interface";
import type { SearchPage } from "@/interfaces/search-page.interface";
import { http } from "@/lib/common/http";

export const attemptService = {
  /** Lượt làm bài, mới nhất trước. Phạm vi do phiên quyết: học sinh chỉ đọc được của chính mình. */
  search: (body: SearchBody) => http<SearchPage<AttemptHistoryRow>>("/attempts/search", { method: "POST", body }),
  get: (id: string) => http<AttemptView>(`/attempts/${id}`),
  /** One answer plus the time it took; the answer is stored, the timing accumulated. */
  saveAnswer: (id: string, questionId: string, body: SaveAnswerBody) => http<unknown>(`/attempts/${id}/answers/${questionId}`, { method: "PUT", body }),
  submit: (id: string) => http<unknown>(`/attempts/${id}/submit`, { method: "POST" }),
  /** The student left the exam tab. */
  tabSwitch: (id: string) => http<unknown>(`/attempts/${id}/tab-switch`, { method: "POST" }),
  result: (id: string) => http<AttemptResult>(`/attempts/${id}/result`),
  grade: (id: string, questionId: string, body: GradeAnswerBody) => http<GradeResult>(`/attempts/${id}/answers/${questionId}/grade`, { method: "PATCH", body }),
};
