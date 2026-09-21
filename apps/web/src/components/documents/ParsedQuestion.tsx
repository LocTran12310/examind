"use client";

import { QuestionView } from "@/components/question/QuestionView";
import { Badge } from "@/components/ui";
import type { ParsedQuestion as PQ } from "@/lib/types";

const PART = (p: string | null) => (p ? `Phần ${["", "I", "II", "III", "IV", "V"][Number(p)] ?? p} · ` : "");
const METHOD: Record<string, string> = { rule: "Quy tắc", llm: "AI", ocr: "OCR" };

export function ParsedQuestionCard({ q, threshold = 0.85 }: { q: PQ; threshold?: number }) {
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
      <QuestionView question={q} mode="review" solutionOpen={false} />
    </article>
  );
}
