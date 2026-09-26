/** A topic of a student's mastery: leaves are tracked, parents rolled up (`GET /me/mastery`). */
export interface MasteryRow {
  topic_id: string;
  parent_id: string | null;
  name: string;
  path: string;
  depth: number;
  /** the subject this topic belongs to, so a reader can narrow to one without asking the taxonomy again */
  subject_id: string | null;
  mastery: number | null;
  answers: number;
  tracked: boolean;
  /** Enough answers to say anything about the topic; otherwise it reads "chưa đủ dữ liệu". */
  enough_data: boolean;
  /** Weak by the one server-side rule (learning-telemetry AC-05) — the UI never re-derives it. */
  weak: boolean;
}

/** The newest personal review paper of one student, plus `total` — how many that student has been given in all.
 *  `total` is what keeps the cell from implying the newest one is the only one (exam-labels ADR-02). */
export interface ClassReviewRef {
  assignment_id: string;
  title: string;
  status: string;
  open_at: string;
  close_at: string;
  total: number;
}

/** One student of a class: weakest topics and the latest personal review (`GET /classes/{id}/overview`). */
export interface ClassOverviewRow {
  student_id: string;
  full_name: string;
  username: string;
  weakest: { name: string; mastery: number; answers: number }[];
  review: ClassReviewRef | null;
}

/** Cả lớp trong một lời gọi (class-overview-and-subjects AC-03). `average` là `null` khi chưa ai nộp — khác hẳn
 * 0, vốn có nghĩa là đã đo và bằng không. */
export interface ClassSummary {
  assignments: number;
  sittings: number;
  average: number | null;
  distribution: number[];
  weakest: { name: string; ratio: number; answered: number }[];
}
