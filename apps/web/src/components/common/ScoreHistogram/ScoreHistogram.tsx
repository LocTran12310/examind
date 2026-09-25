"use client";

import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

export interface Bucket {
  from: number;
  to: number;
  count: number;
}

/** Phổ điểm: mười cột, mỗi cột một khoảng điểm.
 *
 * Vùng hover là **cả cột**, không phải riêng cái thanh. Bản trước đặt tooltip lên thanh, mà chiều cao thanh tỉ lệ
 * với số lượt — nên một khoảng điểm **không ai đạt** có thanh cao 0 và không cách nào rê chuột vào. Đúng những
 * khoảng trống ấy lại là thứ người dạy muốn hỏi nhất: "không em nào được 8–9 à?"
 */
export function ScoreHistogram({ buckets, total, testId = "distribution" }: { buckets: Bucket[]; total: number; testId?: string }) {
  const tallest = Math.max(1, ...buckets.map((b) => b.count));
  return (
    <TooltipProvider>
      <div className="flex h-20 items-stretch gap-1" data-testid={testId}>
        {buckets.map((b) => (
          <Tooltip key={b.from}>
            <TooltipTrigger asChild>
              <div className="flex flex-1 cursor-default flex-col justify-end rounded-sm hover:bg-muted/60" data-testid={`bucket-${b.from}`}>
                <div
                  className="w-full rounded-t bg-primary/70"
                  style={{ height: `${(b.count / tallest) * 100}%` }}
                  // a bucket nobody landed in still draws a hairline, so the column reads as "measured and empty"
                  // rather than as a gap where the chart forgot to render
                  data-empty={b.count === 0 ? "" : undefined}
                />
                <span className="pt-1 text-center text-[10px] text-muted-foreground/70">{b.from}</span>
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p className="font-medium">
                {b.from}–{b.to} điểm
              </p>
              <p>
                {b.count === 0 ? "Không có bài nào" : `${b.count} bài`}
                {total > 0 && b.count > 0 && ` · ${Math.round((b.count / total) * 100)}% của ${total} bài đã nộp`}
              </p>
            </TooltipContent>
          </Tooltip>
        ))}
      </div>
    </TooltipProvider>
  );
}
