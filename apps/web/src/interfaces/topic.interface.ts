export type LevelKind = "strand" | "topic" | "subtopic" | "type";

/** A node of the knowledge tree; `path` is the chain of stable labels from its strand. */
export interface Topic {
  id: string;
  subject_id: string;
  parent_id: string | null;
  name: string;
  level_kind: LevelKind;
  grade: number | null;
  path: string;
  depth: number;
  sort: number;
  child_count: number;
}
