/** `POST /me/practice` */
export interface StartPracticeBody {
  count: number;
  subject_id?: string;
}

/** `POST /classes/{id}/adaptive-assignments` (times in UTC ISO). */
export interface ClassReviewBody {
  count: number;
  duration_minutes: number;
  open_at: string;
  close_at: string;
  title?: string;
}
