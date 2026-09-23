/**
 * The tagging queue's rows: what one untagged question shows (topic-coverage AC-01) and how a
 * suggested topic is labelled. Pure — the page hook feeds it what the queries answered.
 */
import type { SourceDocument } from "@/interfaces/document.interface";
import type { ParsedQuestion, SuggestionSource, TopicSuggestion } from "@/interfaces/question.interface";
import type { Taxonomy } from "@/interfaces/taxonomy.interface";
import type { Topic } from "@/interfaces/topic.interface";
import { formatDate } from "@/lib/common/datetime";
import { topicLabel } from "@/lib/common/topic-tree";

export interface QueueSuggestion {
  topic_id: string;
  label: string;
  score: number;
  source: SuggestionSource;
}

export interface QueueRow {
  q: ParsedQuestion;
  subject: string;
  document: string;
  /** when the source document was uploaded; a question carries no date of its own */
  date: string;
  suggestions: QueueSuggestion[];
}

export interface QueueContext {
  suggestions: Record<string, TopicSuggestion[]>;
  topicsById: Map<string, Topic>;
  documents: Map<string, SourceDocument>;
  taxonomy?: Taxonomy;
}

/** A suggested topic as a teacher reads it: the chain of names when the tree is loaded, else what the API sent. */
export function suggestionLabel(s: TopicSuggestion, topicsById: Map<string, Topic>): string {
  const t = topicsById.get(s.topic_id);
  return t ? topicLabel(t, topicsById) : s.path || s.name;
}

export function queueRows(items: ParsedQuestion[], ctx: QueueContext): QueueRow[] {
  return items.map((q) => {
    const doc = q.source_document_id ? ctx.documents.get(q.source_document_id) : undefined;
    return {
      q,
      subject: ctx.taxonomy?.subjects.find((s) => s.id === q.subject_id)?.name ?? "Chưa phân môn",
      document: doc?.filename ?? "—",
      date: doc ? formatDate(doc.created_at) : "—",
      suggestions: (ctx.suggestions[q.id] ?? []).map((s) => ({ topic_id: s.topic_id, label: suggestionLabel(s, ctx.topicsById), score: s.score, source: s.source })),
    };
  });
}
