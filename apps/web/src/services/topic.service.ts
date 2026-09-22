import type { CreateTopicBody, UpdateTopicBody } from "@/dtos/topic.dto";
import type { Topic } from "@/interfaces/topic.interface";
import { http } from "@/lib/common/http";

export const topicService = {
  /** The whole tree (of one subject) as a flat list; the tree is not paged. */
  list: (subjectId?: string | null) => http<Topic[]>(subjectId ? `/topics?subject_id=${encodeURIComponent(subjectId)}` : "/topics"),
  create: (body: CreateTopicBody) => http<Topic>("/topics", { body }),
  update: (id: string, body: UpdateTopicBody) => http<Topic>(`/topics/${id}`, { method: "PATCH", body }),
  move: (id: string, parentId: string | null) => http<Topic>(`/topics/${id}/move`, { body: { parent_id: parentId } }),
  merge: (id: string, targetId: string) => http<Topic>(`/topics/${id}/merge`, { body: { target_id: targetId } }),
  remove: (id: string) => http<void>(`/topics/${id}`, { method: "DELETE" }),
};
