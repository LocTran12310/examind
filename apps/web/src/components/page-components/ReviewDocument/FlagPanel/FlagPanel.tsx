"use client";

import type { FlagEvidence } from "@/interfaces/question.interface";

/** Why the key is suspected wrong: the share of each option and what the strongest students chose. */
export function FlagPanel({ ev }: { ev: FlagEvidence }) {
  const total = Object.values(ev.option_counts).reduce((a, b) => a + b, 0) || 1;
  return (
    <div className="mb-3 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive" data-testid="flag-panel">
      <div className="font-medium">Nghi sai đáp án: {ev.reason}</div>
      <div className="mt-2 flex flex-wrap gap-3">
        {Object.entries(ev.option_counts)
          .sort()
          .map(([label, n]) => (
            <span key={label}>
              {label}: {Math.round((n / total) * 100)}%{label === ev.key ? " (đáp án hiện tại)" : ""}
            </span>
          ))}
      </div>
      <div className="mt-1 text-xs">
        {ev.answers} lượt trả lời · nhóm giỏi ({ev.top_quartile.size} em) chọn {ev.top_quartile.choice} {Math.round(ev.top_quartile.share * 100)}%. Sửa đáp án (1–4) rồi Enter, hoặc Enter để giữ nguyên.
      </div>
    </div>
  );
}
