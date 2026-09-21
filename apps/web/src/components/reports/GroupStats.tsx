"use client";

import { Bar } from "@/components/exams/ResultView";
import { DIFFICULTY_LABEL, TYPE_LABEL, type GroupStat, type QuestionType } from "@/lib/types";

export function groupLabel(by: string, g: GroupStat): string {
  if (by === "type") return TYPE_LABEL[g.key as QuestionType] ?? g.label;
  if (by === "difficulty") return DIFFICULTY_LABEL[g.key] ?? "Chưa gán mức độ";
  return g.label;
}

export function GroupStats({ by, rows }: { by: string; rows: GroupStat[] }) {
  if (!rows.length) return <p className="text-sm text-gray-500">Chưa có dữ liệu.</p>;
  return (
    <ul className="space-y-2" data-testid={`groups-${by}`}>
      {rows.map((g) => (
        <li key={g.key} className="grid grid-cols-[1fr_140px_48px_60px] items-center gap-2 text-sm">
          <span className="truncate">{groupLabel(by, g)}</span>
          <Bar ratio={g.ratio ?? 0} />
          <span className="text-right font-medium">{g.ratio === null ? "—" : `${Math.round(g.ratio * 100)}%`}</span>
          <span className="text-right text-xs text-gray-500">{g.answered} lượt</span>
        </li>
      ))}
    </ul>
  );
}
