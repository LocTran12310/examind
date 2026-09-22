/**
 * Bank filters kept in the URL (subject-scoped-bank). One place for their keys, chip labels and
 * how each one is removed, shared by the sheet, the chips and the subject tabs.
 */
import { periodLabel } from "@/lib/exam-period";
import { DIFFICULTY_LABEL, STATUS_LABEL, TYPE_LABEL, type Tag, type Taxonomy, type Topic } from "@/lib/types";
import { topicLabel } from "./TopicPicker";

export type BankQuery = Record<string, string>;
export type Changes = Record<string, string | null>;

/** Filters that only make sense inside one subject — dropped when the subject changes (AC-02). */
export const SUBJECT_SCOPED = ["topic_ids", "topic_id", "tag_ids"] as const;

/** Keys the sheet edits (search and subject live outside it). */
export const SHEET_KEYS = ["topic_ids", "topic_id", "type", "difficulty", "grade", "semester_code", "exam_kind", "school_year", "tag_ids", "status"] as const;

export const list = (v?: string) => (v ?? "").split(",").filter(Boolean);

export interface Chip {
  key: string;
  label: string;
  /** URL changes that remove just this chip */
  remove: Changes;
}

export function chips(value: BankQuery, ctx: { taxonomy: Taxonomy; topics: Topic[]; tags: Tag[] }): Chip[] {
  const out: Chip[] = [];
  const byTopic = new Map(ctx.topics.map((t) => [t.id, t]));
  const topicIds = list(value.topic_ids ?? value.topic_id).filter((id) => byTopic.has(id));
  for (const id of topicIds) {
    const rest = topicIds.filter((x) => x !== id);
    out.push({ key: `topic:${id}`, label: topicLabel(byTopic.get(id)!, byTopic), remove: { topic_ids: rest.length ? rest.join(",") : null, topic_id: null } });
  }
  if (value.type) out.push({ key: "type", label: TYPE_LABEL[value.type as keyof typeof TYPE_LABEL] ?? value.type, remove: { type: null } });
  if (value.difficulty) out.push({ key: "difficulty", label: DIFFICULTY_LABEL[value.difficulty] ?? value.difficulty, remove: { difficulty: null } });
  if (value.grade) {
    const g = ctx.taxonomy.grades.find((x) => String(x.level) === value.grade);
    out.push({ key: "grade", label: g?.name ?? `Lớp ${value.grade}`, remove: { grade: null } });
  }
  if (value.semester_code || value.exam_kind)
    out.push({ key: "period", label: periodLabel(value.semester_code, value.exam_kind), remove: { semester_code: null, exam_kind: null } });
  if (value.school_year) out.push({ key: "school_year", label: `Năm học ${value.school_year}`, remove: { school_year: null } });
  const byTag = new Map(ctx.tags.map((t) => [t.id, t]));
  const tagIds = list(value.tag_ids);
  for (const id of tagIds) {
    const t = byTag.get(id);
    const rest = tagIds.filter((x) => x !== id);
    out.push({ key: `tag:${id}`, label: t ? (t.group === "source" ? t.name : `#${t.name}`) : "Tag", remove: { tag_ids: rest.length ? rest.join(",") : null } });
  }
  if (value.status && value.status !== "usable")
    out.push({ key: "status", label: value.status === "all" ? "Mọi trạng thái" : (STATUS_LABEL as Record<string, string>)[value.status] ?? value.status, remove: { status: null } });
  return out;
}

/** Every sheet filter cleared (subject and search stay). */
export const clearAll: Changes = Object.fromEntries(SHEET_KEYS.map((k) => [k, null]));
