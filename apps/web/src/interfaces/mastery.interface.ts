/** A topic of a student's mastery: leaves are tracked, parents rolled up (`GET /me/mastery`). */
export interface MasteryRow {
  topic_id: string;
  parent_id: string | null;
  name: string;
  path: string;
  depth: number;
  mastery: number | null;
  answers: number;
  tracked: boolean;
}

/** One student of a class: weakest topics and the latest personal review (`GET /classes/{id}/overview`). */
export interface ClassOverviewRow {
  student_id: string;
  full_name: string;
  username: string;
  weakest: { name: string; mastery: number; answers: number }[];
  review: { assignment_id: string; title: string; status: string } | null;
}
