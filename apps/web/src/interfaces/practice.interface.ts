/** Why the questions of a personal review exam were chosen. */
export interface PlanGroup {
  reason: string;
  topic: string | null;
  count: number;
}

/** A personal practice attempt (`GET /me/practice`). */
export interface PracticeItem {
  attempt_id: string;
  title: string;
  status: "in_progress" | "submitted";
  started_at: string;
  submitted_at: string | null;
  score10: number | null;
  note: string | null;
  groups: PlanGroup[];
}

/** `POST /me/practice` */
export interface PracticeStarted {
  attempt_id: string;
  question_count: number;
  note: string | null;
  groups: PlanGroup[];
}
