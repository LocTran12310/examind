import type { TagGroup } from "@/interfaces/tag.interface";

export const TAG_GROUP_LABEL: Record<TagGroup, string> = {
  method: "Phương pháp",
  skill: "Kỹ năng",
  source: "Nguồn đề",
  custom: "Khác",
};

export const TAG_GROUP_OPTIONS = Object.entries(TAG_GROUP_LABEL).map(([value, label]) => ({ value, label }));

/** value of the subject filter / picker meaning "shared by every subject" */
export const SHARED_SUBJECT = "shared";
