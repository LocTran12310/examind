/**
 * "Gán theo gợi ý" (pickers-builder AC-03, ADR-02): which pairs one request carries, and what the
 * teacher is told afterwards. Pure — the page hook feeds it the rows and the server's answer.
 */
import type { BulkTopicSkip } from "@/interfaces/question.interface";
import type { QueueRow } from "@/lib/page-libs/tagging-queue/rows";

export interface SuggestionPlan {
  pairs: { question_id: string; topic_id: string }[];
  /** selected questions the system has nothing to propose for: they are left untouched */
  noSuggestion: number;
}

/** Each row's own top suggestion; a row without one is counted, never sent. */
export function suggestionPairs(rows: QueueRow[]): SuggestionPlan {
  const pairs = rows.flatMap((r) => (r.suggestions[0] ? [{ question_id: r.q.id, topic_id: r.suggestions[0].topic_id }] : []));
  return { pairs, noSuggestion: rows.length - pairs.length };
}

/** What the click did, in one line: what took a topic, what had no suggestion, what the server refused. */
export function assignSummary(updated: number, noSuggestion: number, skipped: BulkTopicSkip[]): string {
  const parts = [`Đã gán chuyên đề cho ${updated} câu`];
  if (noSuggestion) parts.push(`${noSuggestion} câu chưa có gợi ý`);
  if (skipped.length) {
    const reasons = [...new Set(skipped.map((s) => s.message))];
    parts.push(`${skipped.length} câu bị bỏ qua (${reasons.join("; ")})`);
  }
  return parts.join(" · ");
}
