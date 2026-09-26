import type { BlueprintBody, CreateExamBody, ExamQuestionIdsBody, ExamQuestionPointsBody, ExamSearchBody, UpdateExamBody } from "@/dtos/exam.dto";
import type { SearchBody } from "@/dtos/search.dto";
import type { BlueprintResult, Exam, ExamQuestion } from "@/interfaces/exam.interface";
import type { SearchPage } from "@/interfaces/search-page.interface";
import { http } from "@/lib/common/http";

export const examService = {
  /** The list never embeds questions (`questions: []`). */
  search: (body: SearchBody) => http<SearchPage<Exam>>("/exams/search", { body }),
  /** How many exams each subject holds under the rest of the search — the numbers on the subject tabs. */
  facets: (body: ExamSearchBody) => http<{ subjects: Record<string, number> }>("/exams/facets", { body }),
  get: (id: string) => http<Exam>(`/exams/${id}`),
  create: (body: CreateExamBody) => http<Exam>("/exams", { body }),
  update: (id: string, body: UpdateExamBody) => http<Exam>(`/exams/${id}`, { method: "PATCH", body }),
  remove: (id: string) => http<void>(`/exams/${id}`, { method: "DELETE" }),
  /** One exam's questions, paged and filtered (default order by position). */
  searchQuestions: (id: string, body: SearchBody) => http<SearchPage<ExamQuestion>>(`/exams/${id}/questions/search`, { body }),
  generate: (id: string, body: BlueprintBody) => http<BlueprintResult>(`/exams/${id}/blueprint`, { body }),
  addQuestions: (id: string, body: ExamQuestionIdsBody) => http<Exam>(`/exams/${id}/questions`, { body }),
  removeQuestion: (id: string, questionId: string) => http<Exam>(`/exams/${id}/questions/${questionId}`, { method: "DELETE" }),
  setPoints: (id: string, questionId: string, body: ExamQuestionPointsBody) => http<Exam>(`/exams/${id}/questions/${questionId}`, { method: "PATCH", body }),
  /** Replace a question with another one of the same matrix row. */
  swap: (id: string, questionId: string) => http<Exam>(`/exams/${id}/questions/${questionId}/swap`, { method: "POST" }),
  reorder: (id: string, body: ExamQuestionIdsBody) => http<Exam>(`/exams/${id}/order`, { method: "PUT", body }),
};
