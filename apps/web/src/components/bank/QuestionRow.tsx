"use client";

import Link from "next/link";
import { Markdown } from "@/components/question/Markdown";
import { Badge } from "@/components/ui";
import { DIFFICULTY_LABEL, STATUS_LABEL, TYPE_LABEL, type ParsedQuestion, type QuestionStatus } from "@/lib/types";

export function QuestionRow({ q, selected, onToggle }: { q: ParsedQuestion; selected: boolean; onToggle: () => void }) {
  const primary = q.topics.find((t) => t.is_primary);
  return (
    <li className="flex gap-3 border-b border-gray-100 px-3 py-3 last:border-0" data-testid={`bank-${q.id}`}>
      <input type="checkbox" aria-label="Chọn câu" checked={selected} onChange={onToggle} className="mt-1" />
      <div className="min-w-0 flex-1">
        <Link href={`/org/bank/${q.id}`} className="block hover:text-brand-700">
          <div className="line-clamp-3 text-sm">
            <Markdown>{q.stem}</Markdown>
          </div>
        </Link>
        <div className="mt-1 flex flex-wrap gap-1 text-xs">
          <Badge>{TYPE_LABEL[q.type]}</Badge>
          {q.difficulty && <Badge tone="blue">{DIFFICULTY_LABEL[q.difficulty] ?? q.difficulty}</Badge>}
          {q.grade && <Badge>Lớp {q.grade}</Badge>}
          <Badge tone={q.status === "approved" || q.status === "auto_approved" ? "green" : q.status === "rejected" ? "red" : "amber"}>
            {STATUS_LABEL[q.status as QuestionStatus] ?? q.status}
          </Badge>
          {primary && <span className="rounded bg-brand-50 px-2 py-0.5 text-brand-700">{primary.name}</span>}
          {q.tags.map((t) => (
            <span key={t.id} className="rounded bg-gray-100 px-2 py-0.5 text-gray-600">
              #{t.name}
            </span>
          ))}
        </div>
      </div>
    </li>
  );
}
