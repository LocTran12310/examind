/**
 * Bank filters kept in the URL (subject-scoped-bank). One place for their keys, chip labels and
 * how each one is removed, shared by the sheet, the chips and the subject tabs.
 */
import { topicLabel } from "@/lib/common/topic-tree";
import { DIFFICULTY_LABEL, STATUS_LABEL, TYPE_LABEL } from "@/constants/question.constant";
import type { QuestionSearchBody } from "@/dtos/question.dto";
import type { Tag } from "@/interfaces/tag.interface";
import type { Taxonomy } from "@/interfaces/taxonomy.interface";
import type { Topic } from "@/interfaces/topic.interface";
import { toSearchBody } from "@/lib/common/search-body";
import { periodLabel } from "@/lib/common/exam-period";

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

/** Bank parameters of the URL, sent at the top of the search body; lists are comma separated in the URL. */
const PARAMS: Record<string, "text" | "number" | "list"> = {
  subject_id: "text",
  grade: "number",
  semester_code: "text",
  exam_kind: "text",
  type: "text",
  difficulty: "text",
  status: "text",
  topic_id: "text",
  topic_ids: "list",
  tag_ids: "list",
  document_id: "text",
  school_year: "text",
};

/** The bank URL (page, page_size, q and the bank parameters) → body of `POST /questions/search`; empty ones are left out. */
export function bankSearchBody(params: URLSearchParams): QuestionSearchBody {
  const body: QuestionSearchBody = toSearchBody(params, {});
  for (const [key, kind] of Object.entries(PARAMS)) {
    const value = params.get(key) ?? "";
    if (!value) continue;
    if (kind === "list") {
      const ids = list(value);
      if (ids.length) body[key] = ids;
    } else if (kind === "number") {
      if (Number.isFinite(Number(value))) body[key] = Number(value);
    } else body[key] = value;
  }
  return body;
}
