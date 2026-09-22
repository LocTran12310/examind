"use client";

import { QuestionView } from "@/components/question/QuestionView";
import { ToneBadge } from "@/components/app/ToneBadge";
import type { ParsedQuestion as PQ } from "@/lib/types";

const PART = (p: string | null) => (p ? `Phần ${["", "I", "II", "III", "IV", "V"][Number(p)] ?? p} · ` : "");
const METHOD: Record<string, string> = { rule: "Quy tắc", llm: "AI", ocr: "OCR" };

export function metaChips(q: PQ, subjectName?: string, semesterName?: string): string[] {
  return [subjectName, q.grade ? `Lớp ${q.grade}` : null, semesterName, q.exam_kind].filter(Boolean) as string[];
}

export function ParsedQuestionCard({ q, threshold = 0.85, meta = [] }: { q: PQ; threshold?: number; meta?: string[] }) {
  const primary = q.topics.find((t) => t.is_primary) ?? q.topics[0];
  const ok = (q.confidence ?? 0) >= threshold;
  const shownIssues = q.issues.filter((i) => i !== "thiếu lời giải" || !q.solution);
  return (
    <article className="rounded-xl border border-border bg-card p-4" data-testid={`pq-${q.part ?? ""}-${q.number}`}>
      <header className="mb-3 flex flex-wrap items-center gap-2 text-sm">
        <span className="font-semibold">
          {PART(q.part)}Câu {q.number}
        </span>
        <ToneBadge tone={ok ? "green" : "amber"}>Tin cậy {Math.round((q.confidence ?? 0) * 100)}%</ToneBadge>
        {q.parse_method && <ToneBadge tone={q.parse_method === "llm" ? "blue" : "gray"}>{METHOD[q.parse_method] ?? q.parse_method}{q.parse_model ? ` · ${q.parse_model}` : ""}</ToneBadge>}
        {shownIssues.map((i) => (
          <ToneBadge key={i} tone={i === "thiếu lời giải" ? "gray" : "red"}>
            {i}
          </ToneBadge>
        ))}
      </header>
      <div className="mb-3 flex flex-wrap gap-2 text-xs" data-testid="chips">
        {meta.length > 0 && <span className="rounded bg-muted px-2 py-0.5 text-foreground/80">{meta.join(" · ")}</span>}
        {q.tags.map((t) => (
          <span key={t.id} className="rounded bg-muted px-2 py-0.5 text-foreground/80">
            #{t.name}
          </span>
        ))}
        {primary ? (
          <span className="rounded bg-primary/10 px-2 py-0.5 text-primary" data-testid="topic-chip">
            Chuyên đề: {primary.name}
            {primary.score !== null && ` · ${Math.round(primary.score * 100)}%`}
            {primary.source === "ai" ? " · AI" : primary.source === "auto" ? " · gợi ý" : ""}
          </span>
        ) : (
          <span className="rounded bg-amber-500/10 px-2 py-0.5 text-amber-800 dark:text-amber-400">Chưa có chuyên đề</span>
        )}
      </div>
      <QuestionView question={q} mode="review" solutionOpen={false} />
    </article>
  );
}
