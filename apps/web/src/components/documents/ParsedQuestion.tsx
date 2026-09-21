"use client";

import { QuestionView } from "@/components/question/QuestionView";
import { Badge } from "@/components/ui";
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
    <article className="rounded-xl border border-gray-200 bg-white p-4" data-testid={`pq-${q.part ?? ""}-${q.number}`}>
      <header className="mb-3 flex flex-wrap items-center gap-2 text-sm">
        <span className="font-semibold">
          {PART(q.part)}Câu {q.number}
        </span>
        <Badge tone={ok ? "green" : "amber"}>Tin cậy {Math.round((q.confidence ?? 0) * 100)}%</Badge>
        {q.parse_method && <Badge tone={q.parse_method === "llm" ? "blue" : "gray"}>{METHOD[q.parse_method] ?? q.parse_method}{q.parse_model ? ` · ${q.parse_model}` : ""}</Badge>}
        {shownIssues.map((i) => (
          <Badge key={i} tone={i === "thiếu lời giải" ? "gray" : "red"}>
            {i}
          </Badge>
        ))}
      </header>
      <div className="mb-3 flex flex-wrap gap-2 text-xs" data-testid="chips">
        {meta.length > 0 && <span className="rounded bg-gray-100 px-2 py-0.5 text-gray-700">{meta.join(" · ")}</span>}
        {q.tags.map((t) => (
          <span key={t.id} className="rounded bg-gray-100 px-2 py-0.5 text-gray-700">
            #{t.name}
          </span>
        ))}
        {primary ? (
          <span className="rounded bg-brand-50 px-2 py-0.5 text-brand-700" data-testid="topic-chip">
            Chuyên đề: {primary.name}
            {primary.score !== null && ` · ${Math.round(primary.score * 100)}%`}
            {primary.source === "ai" ? " · AI" : primary.source === "auto" ? " · gợi ý" : ""}
          </span>
        ) : (
          <span className="rounded bg-amber-50 px-2 py-0.5 text-amber-800">Chưa có chuyên đề</span>
        )}
      </div>
      <QuestionView question={q} mode="review" solutionOpen={false} />
    </article>
  );
}
