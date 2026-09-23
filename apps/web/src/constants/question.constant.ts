import type { QuestionStatus, QuestionType, SuggestionSource } from "@/interfaces/question.interface";

export const STATUS_LABEL: Record<QuestionStatus, string> = {
  draft: "Nháp",
  auto_approved: "Tự duyệt",
  needs_review: "Cần xem",
  approved: "Đã duyệt",
  rejected: "Đã loại",
  duplicate: "Trùng",
  flagged: "Nghi sai đáp án",
};

export const DIFFICULTY_LABEL: Record<string, string> = { nb: "Nhận biết", th: "Thông hiểu", vd: "Vận dụng", vdc: "Vận dụng cao" };
export const TYPE_LABEL: Record<QuestionType, string> = { mcq: "Trắc nghiệm", true_false: "Đúng/Sai", short_answer: "Trả lời ngắn", essay: "Tự luận" };

/** where a suggested topic came from (topic-coverage AC-02) */
export const SUGGESTION_SOURCE_LABEL: Record<SuggestionSource, string> = { keyword: "Từ khóa", similar: "Tương tự", ai: "AI" };

/** value of the bank's subject meaning "questions without a subject" */
export const NO_SUBJECT = "none";
