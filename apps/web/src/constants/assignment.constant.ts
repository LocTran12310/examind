import type { ResultsPolicy } from "@/types/assignment.type";

export const RESULTS_POLICY_OPTIONS: { value: ResultsPolicy; label: string }[] = [
  { value: "after_submit", label: "Ngay sau khi nộp" },
  { value: "after_close", label: "Sau khi đóng bài" },
  { value: "never", label: "Chỉ xem điểm" },
];

/** Status of a student in an assignment report. */
export const REPORT_STATUS_LABEL: Record<string, string> = { submitted: "Đã nộp", in_progress: "Đang làm", not_started: "Chưa làm" };
