import type { BulkQuestionsBody, BulkTopicsBody, QuestionBody, QuestionSearchBody, SuggestTopicsBody, UpdateQuestionBody } from "@/dtos/question.dto";
import type { BankFacets, BulkResult, BulkTopicsResult, ParsedQuestion, Question, QuestionStats, TopicSuggestions } from "@/interfaces/question.interface";
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
  /** One topic per question in one request — a page of the tagging queue at once (at most 200 pairs). */
  bulkTopics: (body: BulkTopicsBody) => http<BulkTopicsResult>("/questions/bulk/topics", { body }),
  /** Up to three topic candidates per question, computed on demand; at most 50 ids per request. */
  suggestTopics: (body: SuggestTopicsBody) => http<TopicSuggestions>("/questions/suggest-topics", { body }),
  /** A sample question to check rendering (formulas, images, solution). */
  demo: () => http<Question>("/questions/demo"),
};
