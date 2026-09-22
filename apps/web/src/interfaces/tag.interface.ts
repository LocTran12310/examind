export type TagGroup = "method" | "skill" | "source" | "custom";

export interface Tag {
  id: string;
  group: TagGroup;
  name: string;
  /** null = shared by every subject */
  subject_id?: string | null;
}
