/** A topic of the report tree: points over max points of the answers in its subtree (`GET /stats/topics`). */
export interface TopicStat {
  id: string | null;
  parent_id: string | null;
  name: string;
  path: string;
  depth: number;
  level_kind: string;
  /** null for the "Chưa phân loại" row: it has no topic, so it has no subject to claim */
  subject_id: string | null;
  points: number;
  max_points: number;
  answered: number;
  ratio: number | null;
}

/** One question type, difficulty or tag (`GET /stats/groups`). */
export interface GroupStat {
  key: string;
  label: string;
  points: number;
  max_points: number;
  answered: number;
  ratio: number | null;
}

/** A class × the topics of one level (`GET /stats/heatmap`). */
export interface HeatmapData {
  columns: { id: string; name: string; path: string }[];
  rows: { student_id: string; full_name: string; username: string; cells: Record<string, { ratio: number | null; answered: number }> }[];
}
