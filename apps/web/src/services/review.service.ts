import type { SearchBody } from "@/dtos/search.dto";
import type { AnswerKeyBody, ReviewActionBody, ReviewDocumentSearchBody, UpdateReviewDocumentBody } from "@/dtos/review.dto";
import type { ParsedQuestion } from "@/interfaces/question.interface";
import type { AnswerKeyResult, ApproveConfidentResult, ReviewDocument } from "@/interfaces/review.interface";
import type { SearchPage } from "@/interfaces/search-page.interface";
import { http } from "@/lib/common/http";

export const reviewService = {
  searchDocuments: (body: ReviewDocumentSearchBody) => http<SearchPage<ReviewDocument>>("/review/documents/search", { body }),
  /** Questions whose key the answers suggest is wrong (group "Nghi sai đáp án"). */
  searchFlagged: (body: SearchBody) => http<SearchPage<ParsedQuestion>>("/review/flagged/search", { body }),
  getDocument: (id: string) => http<ReviewDocument>(`/review/documents/${id}`),
  updateDocument: (id: string, body: UpdateReviewDocumentBody) => http<ReviewDocument>(`/review/documents/${id}`, { method: "PATCH", body }),
  /** The questions of a document that need a human, in review order. */
  queue: (id: string) => http<ParsedQuestion[]>(`/review/documents/${id}/queue`),
  action: (questionId: string, body: ReviewActionBody) => http<ParsedQuestion>(`/review/questions/${questionId}/action`, { body }),
  answerKey: (id: string, body: AnswerKeyBody) => http<AnswerKeyResult>(`/review/documents/${id}/answer-key`, { body }),
  approveConfident: (id: string) => http<ApproveConfidentResult>(`/review/documents/${id}/approve-confident`, { method: "POST" }),
};
