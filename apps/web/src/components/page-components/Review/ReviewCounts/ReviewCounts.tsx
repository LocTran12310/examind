"use client";

import { ToneBadge, type Tone } from "@/components/common/ToneBadge/ToneBadge";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Progress as Bar } from "@/components/ui/progress";
import { REVIEW_STATE_LABEL, SPOT_LABEL, SPOT_NOTE } from "@/constants/review.constant";
import type { ReviewDocument, ReviewState } from "@/interfaces/review.interface";

const STATE_TONE: Record<ReviewState, Tone> = { pending: "amber", in_progress: "blue", done: "green" };

export function Progress({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-2">
      <Bar value={pct} className="w-28" aria-label="Tiến độ" />
      <span className="text-xs text-muted-foreground">{pct}%</span>
    </div>
  );
}

export function ReviewCounts({ r }: { r: ReviewDocument }) {
  return (
    <div className="flex flex-wrap gap-1">
      <ToneBadge tone="green">Tự duyệt {r.counts.auto_approved}</ToneBadge>
      <ToneBadge tone={r.counts.needs_review ? "amber" : "gray"}>Cần xem {r.counts.needs_review}</ToneBadge>
      {(r.counts.flagged ?? 0) > 0 && <ToneBadge tone="red">Nghi sai đáp án {r.counts.flagged}</ToneBadge>}
      {r.spot_pending > 0 && (
        <ToneBadge tone="blue">
          {SPOT_LABEL} {r.spot_pending}
        </ToneBadge>
      )}
      <ToneBadge>Đã duyệt {r.counts.approved}</ToneBadge>
      {r.counts.duplicate > 0 && <ToneBadge>Trùng {r.counts.duplicate}</ToneBadge>}
      {r.counts.rejected > 0 && <ToneBadge tone="red">Loại {r.counts.rejected}</ToneBadge>}
    </div>
  );
}

/** The one state of a document plus how many questions still wait; the six counts sit in a popover (ADR-01). */
export function ReviewStateCell({ r }: { r: ReviewDocument }) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <ToneBadge tone={STATE_TONE[r.review_state]}>{REVIEW_STATE_LABEL[r.review_state]}</ToneBadge>
      <span className="text-xs whitespace-nowrap text-muted-foreground">{r.pending > 0 ? `còn ${r.pending} câu` : "không còn câu nào"}</span>
      <Popover>
        <PopoverTrigger asChild>
          <Button type="button" variant="link" size="xs" className="px-0 text-xs" onClick={(e) => e.stopPropagation()}>
            Chi tiết
          </Button>
        </PopoverTrigger>
        <PopoverContent align="start" className="w-80 space-y-2">
          <ReviewCounts r={r} />
          <p className="text-xs text-muted-foreground">{SPOT_NOTE}</p>
        </PopoverContent>
      </Popover>
    </div>
  );
}
