"use client";

import Link from "next/link";
import { Markdown } from "@/components/common/Markdown/Markdown";
import { ToneBadge } from "@/components/common/ToneBadge/ToneBadge";
import { Checkbox } from "@/components/ui/checkbox";
import { DIFFICULTY_LABEL, STATUS_LABEL, TYPE_LABEL } from "@/constants/question.constant";
import type { ParsedQuestion, QuestionStatus } from "@/interfaces/question.interface";

export function QuestionRow({ q, selected, onToggle }: { q: ParsedQuestion; selected: boolean; onToggle: () => void }) {
  const primary = q.topics.find((t) => t.is_primary);
  return (
    <li className="flex gap-3 border-b px-3 py-3 last:border-0 hover:bg-muted/40" data-testid={`bank-${q.id}`}>
      <Checkbox aria-label="Chọn câu" checked={selected} onCheckedChange={onToggle} className="mt-1" />
      <div className="min-w-0 flex-1">
        <Link href={`/org/bank/${q.id}`} className="block hover:text-primary">
          <div className="line-clamp-3 text-sm">
            <Markdown>{q.stem}</Markdown>
          </div>
        </Link>
        <div className="mt-1 flex flex-wrap gap-1 text-xs">
          <ToneBadge>{TYPE_LABEL[q.type]}</ToneBadge>
          {q.difficulty && <ToneBadge tone="blue">{DIFFICULTY_LABEL[q.difficulty] ?? q.difficulty}</ToneBadge>}
          {q.grade && <ToneBadge>Lớp {q.grade}</ToneBadge>}
          <ToneBadge tone={q.status === "approved" || q.status === "auto_approved" ? "green" : q.status === "rejected" ? "red" : "amber"}>
            {STATUS_LABEL[q.status as QuestionStatus] ?? q.status}
          </ToneBadge>
          {primary && <ToneBadge tone="blue" className="h-auto whitespace-normal">{primary.name}</ToneBadge>}
          {q.tags.map((t) => (
            <ToneBadge key={t.id} className="font-normal">
              #{t.name}
            </ToneBadge>
          ))}
        </div>
      </div>
    </li>
  );
}
