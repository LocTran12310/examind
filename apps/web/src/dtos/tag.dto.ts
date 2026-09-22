import type { TagGroup } from "@/interfaces/tag.interface";

export interface CreateTagBody {
  group: TagGroup;
  name: string;
  subject_id: string | null;
}

export type UpdateTagBody = Partial<CreateTagBody>;
