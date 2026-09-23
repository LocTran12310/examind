import type { DocumentQuestionState, ReviewState } from "@/interfaces/review.interface";

/** The one state a document shows in the list (review-ux ADR-01); the counts keep the breakdown. */
export const REVIEW_STATE_LABEL: Record<ReviewState, string> = { pending: "Cần xem", in_progress: "Đang duyệt", done: "Xong" };

export const REVIEW_STATE_OPTIONS = (Object.keys(REVIEW_STATE_LABEL) as ReviewState[]).map((value) => ({ value, label: REVIEW_STATE_LABEL[value] }));

/** What the queue calls the 5% sample (the API's group name) and what a teacher reads instead (ADR-03). */
export const SPOT_GROUP = "Kiểm tra ngẫu nhiên";
export const SPOT_LABEL = "Mẫu kiểm chứng";
export const SPOT_NOTE = "Mẫu kiểm chứng là 5% số câu hệ thống tự duyệt, rút ngẫu nhiên để bắt lỗi máy duyệt sai.";

/** The state filter above a document's queue; "pending" is what the keyboard queue works on. */
export const DOCUMENT_QUESTION_STATES: { value: DocumentQuestionState; label: string }[] = [
  { value: "pending", label: "Cần xem" },
  { value: "approved", label: "Đã duyệt" },
  { value: "rejected", label: "Đã loại" },
  { value: "duplicate", label: "Trùng" },
  { value: "all", label: "Tất cả" },
];

/** What a re-decision does, said in the button that takes it (review-ux AC-05). */
export const REDECIDE_ACTIONS: { status: "approved" | "rejected" | "needs_review"; label: string }[] = [
  { status: "approved", label: "Duyệt — chuyển sang Đã duyệt" },
  { status: "rejected", label: "Loại — chuyển sang Đã loại" },
  { status: "needs_review", label: "Trả lại — chuyển sang Cần xem" },
];
