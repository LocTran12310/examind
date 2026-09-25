"use client";

import { EmptyState } from "@/components/common/EmptyState/EmptyState";
import { Panel } from "@/components/common/Panel/Panel";
import { ToneBadge } from "@/components/common/ToneBadge/ToneBadge";
import type { ClassSummary as Summary } from "@/interfaces/mastery.interface";

/** Cả lớp một chỗ: đã giao bao nhiêu, nộp bao nhiêu, trung bình mấy điểm, phổ điểm, và yếu ở đâu. */
export function ClassSummary({ data }: { data: Summary }) {
  // `average === null` nghĩa là chưa ai nộp, khác hẳn 0 (đã đo và bằng không) — nên hai trường hợp không dùng
  // chung một nhánh hiển thị, và lớp rỗng nói ra điều đó thay vì trưng một hàng số 0
  if (data.average === null) {
    return (
      <EmptyState>
        Chưa có bài nộp nào. Lớp đã được giao {data.assignments} bài; khi có học sinh nộp, điểm trung bình, phổ
        điểm và những chuyên đề lớp còn yếu sẽ hiện ở đây.
      </EmptyState>
    );
  }
  const most = Math.max(...data.distribution, 1);
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <Panel>
        <p className="text-sm text-muted-foreground">Bài giao</p>
        <p className="text-3xl font-semibold" data-testid="cs-assignments">{data.assignments}</p>
        <p className="mt-1 text-sm text-muted-foreground">{data.sittings} lượt đã nộp</p>
      </Panel>
      <Panel>
        <p className="text-sm text-muted-foreground">Điểm trung bình</p>
        <p className="text-3xl font-semibold" data-testid="cs-average">{data.average}</p>
        <p className="mt-1 text-sm text-muted-foreground">thang 10, theo tỉ lệ làm đúng</p>
      </Panel>
      <Panel>
        <p className="mb-2 text-sm text-muted-foreground">Phổ điểm</p>
        <div className="flex h-16 items-end gap-1" data-testid="cs-distribution">
          {data.distribution.map((n, i) => (
            <div key={i} className="flex-1 self-stretch" title={`${i}–${i + 1} điểm: ${n} lượt`}>
              <div className="mt-auto w-full rounded-t bg-primary/70" style={{ height: `${(n / most) * 100}%` }} />
            </div>
          ))}
        </div>
        <div className="mt-1 flex justify-between text-xs text-muted-foreground"><span>0</span><span>10</span></div>
      </Panel>
      <Panel className="lg:col-span-3">
        <h3 className="mb-2 font-medium">Chuyên đề lớp còn yếu (tỉ lệ thấp trước)</h3>
        {data.weakest.length === 0 ? (
          <p className="text-sm text-muted-foreground">Chưa đủ dữ liệu theo chuyên đề.</p>
        ) : (
          <ul className="flex flex-wrap gap-2" data-testid="cs-weakest">
            {data.weakest.map((w) => (
              <li key={w.name}>
                <ToneBadge tone={w.ratio < 0.5 ? "red" : "amber"}>
                  {w.name} {Math.round(w.ratio * 100)}% · {w.answered} lượt
                </ToneBadge>
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </div>
  );
}
