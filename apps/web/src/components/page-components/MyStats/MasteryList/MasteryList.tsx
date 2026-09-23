"use client";

import { ScoreBar } from "@/components/common/ScoreBar/ScoreBar";
import type { MasteryRow } from "@/interfaces/mastery.interface";

/** The band a topic is in. "Cần ôn" is the server's weak rule, never a threshold of our own (AC-05). */
export function level(row: Pick<MasteryRow, "mastery" | "enough_data" | "weak">): string {
  if (!row.enough_data) return "Chưa đủ dữ liệu";
  if (row.weak) return "Cần ôn";
  return (row.mastery ?? 0) >= 0.8 ? "Vững" : "Khá";
}

export function MasteryList({ rows, limit }: { rows: MasteryRow[]; limit?: number }) {
  const tracked = rows.filter((r) => r.tracked && r.mastery !== null).sort((a, b) => (a.mastery ?? 0) - (b.mastery ?? 0));
  const shown = limit ? tracked.slice(0, limit) : tracked;
  if (!shown.length) return <p className="text-sm text-muted-foreground">Chưa đủ dữ liệu — làm thêm bài để hệ thống hiểu bạn.</p>;
  return (
    <ul className="space-y-2" data-testid="mastery">
      {shown.map((r) => (
        <li key={r.topic_id} className="grid grid-cols-[1fr_120px_56px_96px] items-center gap-2 text-sm">
          <span className="truncate" title={r.path}>
            {r.name}
          </span>
          <ScoreBar ratio={r.mastery ?? 0} />
          <span className="text-right font-medium">{Math.round((r.mastery ?? 0) * 100)}%</span>
          <span className="text-right text-xs text-muted-foreground">{level(r)}</span>
        </li>
      ))}
    </ul>
  );
}
