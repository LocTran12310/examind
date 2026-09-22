/** Query of `GET /stats/topics` and `/stats/groups`: the whole org (or the student's own answers) unless narrowed. */
export interface StatsParams {
  class_id?: string;
  school_year_id?: string;
  term_code?: string;
  student_id?: string;
  assignment_id?: string;
  subject_id?: string;
}

/** Query of `GET /stats/heatmap`. */
export interface HeatmapParams {
  class_id: string;
  level: string;
  term_code?: string;
  subject_id?: string;
}
