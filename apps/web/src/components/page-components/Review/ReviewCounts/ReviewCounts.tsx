"use client";

import { ToneBadge } from "@/components/app/ToneBadge";
import { Progress as Bar } from "@/components/ui/progress";
import type { ReviewDocument } from "@/interfaces/review.interface";

export function Progress({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-2">
      <Bar value={pct} className="w-28" aria-label="Tiến độ" />
      <span className="text-xs text-muted-foreground">{pct}%</span>
    </div>
  );
}

/** Questions still waiting for a human: needs review, spot checks and suspect keys. */
export const pendingOf = (r: ReviewDocument) => r.counts.needs_review + r.spot_pending + (r.counts.flagged ?? 0);

export function ReviewCounts({ r }: { r: ReviewDocument }) {
  return (
    <div className="flex flex-wrap gap-1">
      <ToneBadge tone="green">Tự duyệt {r.counts.auto_approved}</ToneBadge>
      <ToneBadge tone={r.counts.needs_review ? "amber" : "gray"}>Cần xem {r.counts.needs_review}</ToneBadge>
      {(r.counts.flagged ?? 0) > 0 && <ToneBadge tone="red">Nghi sai đáp án {r.counts.flagged}</ToneBadge>}
      {r.spot_pending > 0 && <ToneBadge tone="blue">Kiểm tra ngẫu nhiên {r.spot_pending}</ToneBadge>}
      <ToneBadge>Đã duyệt {r.counts.approved}</ToneBadge>
      {r.counts.duplicate > 0 && <ToneBadge>Trùng {r.counts.duplicate}</ToneBadge>}
      {r.counts.rejected > 0 && <ToneBadge tone="red">Loại {r.counts.rejected}</ToneBadge>}
    </div>
  );
}
