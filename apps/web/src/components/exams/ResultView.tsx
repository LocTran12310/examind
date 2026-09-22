"use client";

import { cn } from "@/lib/utils";
import { Markdown } from "@/components/question/Markdown";
import { QuestionView } from "@/components/question/QuestionView";
import { FormAlert } from "@/components/app/FormAlert";
import { ToneBadge } from "@/components/app/ToneBadge";
import { Panel } from "@/components/app/Panel";
import { fmt } from "@/lib/dates";
import type { AttemptResult, ResultQuestion } from "@/lib/types";
import { EssayGrader } from "./EssayGrader";

export function Bar({ ratio }: { ratio: number }) {
  const pct = Math.round(ratio * 100);
  return (
    <div className="h-2 w-full overflow-hidden rounded bg-muted">
      <div className={cn("h-2", pct >= 80 ? "bg-green-500" : pct >= 50 ? "bg-amber-400" : "bg-red-400")} style={{ width: `${pct}%` }} />
    </div>
  );
}

function YourAnswer({ q }: { q: ResultQuestion }) {
  const r = q.response ?? {};
  if (q.type === "true_false") {
    return (
      <table className="mt-2 text-sm" data-testid="tf-result">
        <tbody>
          {q.options.map((o) => {
            const mine = r[o.label];
            const key = (q.answer ?? {})[o.label];
            return (
              <tr key={o.label}>
                <td className="pr-3 font-semibold">{o.label})</td>
                <td className={cn("pr-3", mine === key ? "text-emerald-700 dark:text-emerald-400" : "text-destructive")}>Bạn: {mine === undefined ? "—" : mine ? "Đúng" : "Sai"}</td>
                <td className="text-muted-foreground">Đáp án: {key ? "Đúng" : "Sai"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    );
  }
  if (q.type === "short_answer") return <p className={cn("mt-2 text-sm", q.is_correct ? "text-emerald-700 dark:text-emerald-400" : "text-destructive")}>Bạn trả lời: {String(r.value ?? "—")}</p>;
  if (q.type === "essay")
    return (
      <div className="mt-2 rounded-lg bg-muted/50 p-3 text-sm">
        <div className="mb-1 font-medium">Bài làm</div>
        <Markdown>{String(r.text ?? "(bỏ trống)")}</Markdown>
      </div>
    );
  return null;
}

export function ResultView({ result, staff, onChange }: { result: AttemptResult; staff?: boolean; onChange?: () => void }) {
  if (result.hidden) {
    return (
      <Panel className="max-w-xl">
        <h2 className="text-lg font-semibold">{result.title}</h2>
        {result.score10 !== undefined && <p className="mt-2 text-3xl font-semibold text-primary">{result.score10} điểm</p>}
        <FormAlert kind="info">
          {result.reason === "after_close"
            ? `Đáp án và lời giải sẽ hiện sau khi đóng bài (${fmt(result.available_at)}).`
            : result.reason === "never"
              ? "Giáo viên chỉ cho xem điểm của bài này."
              : "Bài chưa nộp."}
        </FormAlert>
      </Panel>
    );
  }
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        <Panel>
          <div className="text-sm text-muted-foreground">Điểm</div>
          <div className="text-3xl font-semibold text-primary" data-testid="score10">
            {result.score10}
          </div>
          <div className="text-sm text-muted-foreground">
            {result.score} / {result.max_score} điểm thô{result.needs_grading ? " · đang chấm tự luận" : ""}
          </div>
          {staff && result.tab_switches > 0 && <ToneBadge tone="amber">Rời tab {result.tab_switches} lần</ToneBadge>}
        </Panel>
        <Panel>
          <div className="mb-2 text-sm text-muted-foreground">Theo phần</div>
          {result.sections?.map((s) => (
            <div key={s.section} className="mb-1 text-sm">
              <div className="flex justify-between">
                <span>Phần {s.section}</span>
                <span>
                  {Math.round(s.points * 100) / 100}/{s.max_points}
                </span>
              </div>
              <Bar ratio={s.max_points ? s.points / s.max_points : 0} />
            </div>
          ))}
        </Panel>
        <Panel>
          <div className="mb-2 text-sm text-muted-foreground">Theo chuyên đề (yếu nhất trước)</div>
          {result.topics?.slice(0, 6).map((t) => (
            <div key={t.topic} className="mb-1 text-sm" data-testid="topic-row">
              <div className="flex justify-between gap-2">
                <span className="truncate">{t.topic}</span>
                <span>{t.max_points ? Math.round((t.points / t.max_points) * 100) : 0}%</span>
              </div>
              <Bar ratio={t.max_points ? t.points / t.max_points : 0} />
            </div>
          ))}
        </Panel>
      </div>
      <div className="space-y-4">
        {result.questions?.map((q, i) => (
          <article key={q.id} className="rounded-xl border border-border bg-card p-4" data-testid={`rq-${i + 1}`}>
            <div className="mb-2 flex items-center gap-2 text-sm">
              <ToneBadge tone={q.points === null ? "amber" : q.is_correct ? "green" : q.points ? "blue" : "red"}>
                {q.points === null ? "Chờ chấm" : `${Math.round(q.points * 100) / 100}/${q.max_points}`}
              </ToneBadge>
            </div>
            <QuestionView question={q} mode="result" number={i + 1} selected={q.type === "mcq" ? ((q.response ?? {}).key as string) ?? null : null} solutionOpen={!q.is_correct} />
            <YourAnswer q={q} />
            {q.comment && <FormAlert kind="info">Nhận xét: {q.comment}</FormAlert>}
            {staff && q.type === "essay" && (
              <EssayGrader attemptId={result.id} questionId={q.id} max={q.max_points} points={q.points} comment={q.comment} onSaved={() => onChange?.()} />
            )}
          </article>
        ))}
      </div>
    </div>
  );
}
