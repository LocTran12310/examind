import type { QuestionStatus, QuestionType } from "@/interfaces/question.interface";

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

/** value of the bank's subject meaning "questions without a subject" */
export const NO_SUBJECT = "none";
