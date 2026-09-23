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

/** What one change of the bank was, in the teacher's words: the `action` naming a batch in "Thay đổi gần đây"
 *  (bulk-safety AC-03). A batch that wrote several kinds of event is named by the coarsest of them, so "Sửa
 *  hàng loạt" already covers the chuyên đề and tag it placed on the way. */
export const REVIEW_ACTION_LABEL: Record<string, string> = {
  bulk: "Sửa hàng loạt",
  undo: "Hoàn tác",
  topic: "Đặt chuyên đề",
  tag: "Đặt tag",
  edit: "Sửa câu hỏi",
  answer: "Sửa đáp án",
  approve: "Duyệt",
  reject: "Loại",
  restore: "Trả lại để xem",
  skip: "Bỏ qua",
  triage: "Phân loại tự động",
  spot_ok: "Kiểm tra mẫu: đạt",
  spot_fail: "Kiểm tra mẫu: không đạt",
};

/** What a change moved: the snapshot field names of a review event, as the bank's own screens name them. */
export const EVENT_FIELD_LABEL: Record<string, string> = {
  status: "Duyệt",
  difficulty: "Mức độ",
  grade: "Lớp",
  subject_id: "Môn",
  topics: "Chuyên đề",
  primary_topic: "Chuyên đề chính",
  tags: "Tag",
  answer: "Đáp án",
  confidence: "Độ tin cậy",
  issues: "Cảnh báo",
};
