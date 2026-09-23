"use client";

import { Panel } from "@/components/common/Panel/Panel";
import { ScoreBar } from "@/components/common/ScoreBar/ScoreBar";
import type { QuestionStats as Stats } from "@/interfaces/question.interface";

const MIN_OBSERVATIONS = 10;
const ROW = "grid grid-cols-[1fr_52px_64px] items-center gap-2 sm:grid-cols-[1fr_120px_52px_64px]";

const pct = (r: number | null) => (r === null ? "—" : `${Math.round(r * 100)}%`);

/** `45 giây`, `1 phút 20 giây`. */
export function duration(v: number | null): string {
  if (v === null) return "—";
  return v < 60 ? `${v} giây` : `${Math.floor(v / 60)} phút ${v % 60} giây`;
}

/** −1…1: how much better the strongest third of the attempts did than the weakest. */
const signed = (v: number | null) => (v === null ? "—" : `${v > 0 ? "+" : ""}${v.toFixed(2)}`);

/** One measure: its bar (only where a ratio makes one), its value and how many answers it was read from. */
function Row({ label, value, ratio, count }: { label: React.ReactNode; value: string; ratio: number | null; count: number }) {
  return (
    <li className={ROW}>
      <span className="truncate">{label}</span>
      <span className="hidden sm:block">{ratio === null ? null : <ScoreBar ratio={ratio} />}</span>
      <span className="text-right font-medium">{value}</span>
      <span className="text-right text-xs text-muted-foreground">{count} lượt</span>
    </li>
  );
}

/** Thống kê câu hỏi from the graded answers (learning-telemetry AC-03): nothing but the count until there is
 *  enough evidence. */
export function QuestionStats({ stats }: { stats: Stats }) {
  const n = stats.observations;
  return (
    <Panel className="max-w-3xl" data-testid="question-stats">
      <h2 className="mb-3 text-sm font-semibold">Thống kê từ bài làm</h2>
      {!stats.enough_data ? (
        <p className="text-sm text-muted-foreground">
          Chưa đủ dữ liệu — cần ít nhất {MIN_OBSERVATIONS} lượt trả lời (hiện có {n}).
        </p>
      ) : (
        <>
          <ul className="space-y-2 text-sm">
            <Row label="Tỉ lệ đúng" ratio={stats.correct_ratio ?? 0} value={pct(stats.correct_ratio)} count={n} />
            <Row label="Đúng ngay lần đầu" ratio={stats.first_attempt_ratio ?? 0} value={pct(stats.first_attempt_ratio)} count={n} />
            <Row label="Độ phân biệt" ratio={null} value={signed(stats.discrimination)} count={n} />
            <Row label="Thời gian trung vị" ratio={null} value={duration(stats.median_seconds)} count={n} />
          </ul>
          {stats.options.length > 0 && (
            <>
              <h3 className="mt-4 mb-2 text-sm font-medium">Phương án đã chọn</h3>
              <ul className="space-y-2 text-sm" data-testid="option-stats">
                {stats.options.map((o) => (
                  <Row
                    key={o.label}
                    label={
                      <>
                        {o.label}
                        {o.is_key && <span className="ml-1 text-green-600 dark:text-green-500">✓ đáp án</span>}
                      </>
                    }
                    ratio={o.ratio}
                    value={pct(o.ratio)}
                    count={o.chosen}
                  />
                ))}
              </ul>
            </>
          )}
        </>
      )}
    </Panel>
  );
}
