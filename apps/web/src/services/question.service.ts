import type { BulkQuestionsBody, QuestionBody, QuestionSearchBody, UpdateQuestionBody } from "@/dtos/question.dto";
import type { BankFacets, BulkResult, ParsedQuestion, Question, QuestionStats } from "@/interfaces/question.interface";
import type { SearchPage } from "@/interfaces/search-page.interface";
import { http } from "@/lib/common/http";

export const questionService = {
  search: (body: QuestionSearchBody) => http<SearchPage<ParsedQuestion>>("/questions/search", { body }),
  /** Counts per subject, topic, tag… for the same body (page, limit and sort are ignored). */
  facets: (body: QuestionSearchBody) => http<BankFacets>("/questions/facets", { body }),
  get: (id: string) => http<ParsedQuestion>(`/questions/${id}`),
  /** What the graded answers say about the question (tỉ lệ đúng, độ phân biệt, phương án đã chọn). */
  stats: (id: string) => http<QuestionStats>(`/questions/${id}/stats`),
  create: (body: QuestionBody) => http<ParsedQuestion>("/questions", { body }),
  update: (id: string, body: UpdateQuestionBody) => http<ParsedQuestion>(`/questions/${id}`, { method: "PATCH", body }),
  remove: (id: string) => http<void>(`/questions/${id}`, { method: "DELETE" }),
  bulk: (body: BulkQuestionsBody) => http<BulkResult>("/questions/bulk", { body }),
  /** A sample question to check rendering (formulas, images, solution). */
  demo: () => http<Question>("/questions/demo"),
};
