"use client";

import { cn } from "@/lib/utils";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { QuestionView } from "@/components/question/QuestionView";
import { FormAlert } from "@/components/app/FormAlert";
import { ToneBadge } from "@/components/app/ToneBadge";
import { Button } from "@/components/ui/button";
import { FormDialog } from "@/components/app/FormDialog";
import { api, ApiError } from "@/lib/api";
import type { AttemptQuestion, AttemptView } from "@/lib/types";
import { AnswerInput, answered } from "./AnswerInput";

type Resp = Record<string, unknown> | null;
const SAVE_DEBOUNCE = 500;
const RETRY_EVERY = 3000;

export function formatLeft(ms: number): string {
  const s = Math.max(0, Math.floor(ms / 1000));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  const pad = (n: number) => String(n).padStart(2, "0");
  return h ? `${h}:${pad(m)}:${pad(sec)}` : `${pad(m)}:${pad(sec)}`;
}

export function ExamRunner({ view, onFinished }: { view: AttemptView; onFinished: () => void }) {
  const [answers, setAnswers] = useState<Record<string, Resp>>(() => Object.fromEntries(view.questions.map((q) => [q.id, q.response])));
  const [index, setIndex] = useState(0);
  const [pending, setPending] = useState<Record<string, Resp>>({});
  const [confirming, setConfirming] = useState(false);
  const [closed, setClosed] = useState(view.status !== "in_progress");
  const [error, setError] = useState<string | null>(null);
  const offset = useMemo(() => new Date(view.server_now).getTime() - Date.now(), [view.server_now]);
  const deadline = new Date(view.deadline_at).getTime();
  const [left, setLeft] = useState(() => deadline - (Date.now() + offset));
  const timers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});
  const q: AttemptQuestion = view.questions[index];

  const finish = useCallback(async () => {
    setClosed(true);
    await api(`/attempts/${view.id}/submit`, { method: "POST" }).catch(() => undefined);
    onFinished();
  }, [view.id, onFinished]);

  const flush = useCallback(
    async (qid: string, value: Resp) => {
      try {
        await api(`/attempts/${view.id}/answers/${qid}`, { method: "PUT", body: { response: value } });
        setPending((p) => {
          if (p[qid] !== value) return p;
          const n = { ...p };
          delete n[qid];
          return n;
        });
      } catch (e) {
        if (e instanceof ApiError && e.code === "attempt_closed") {
          setClosed(true);
          onFinished();
        } else if (e instanceof ApiError && e.status === 422) {
          setError(e.message);
          setPending((p) => {
            const n = { ...p };
            delete n[qid];
            return n;
          });
        }
        // network errors: keep pending, the retry loop picks it up
      }
    },
    [view.id, onFinished],
  );

  function change(value: Resp) {
    if (closed) return;
    setAnswers((a) => ({ ...a, [q.id]: value }));
    setPending((p) => ({ ...p, [q.id]: value }));
    clearTimeout(timers.current[q.id]);
    const qid = q.id;
    timers.current[qid] = setTimeout(() => void flush(qid, value), SAVE_DEBOUNCE);
  }

  // countdown from the server clock
  useEffect(() => {
    const t = setInterval(() => setLeft(deadline - (Date.now() + offset)), 500);
    return () => clearInterval(t);
  }, [deadline, offset]);
  useEffect(() => {
    if (left <= 0 && !closed) void finish();
  }, [left, closed, finish]);

  // retry unsaved answers
  useEffect(() => {
    const t = setInterval(() => {
      for (const [qid, v] of Object.entries(pending)) void flush(qid, v);
    }, RETRY_EVERY);
    return () => clearInterval(t);
  }, [pending, flush]);

  // count tab switches
  useEffect(() => {
    const onHide = () => {
      if (document.visibilityState === "hidden" && !closed) void api(`/attempts/${view.id}/tab-switch`, { method: "POST" }).catch(() => undefined);
    };
    document.addEventListener("visibilitychange", onHide);
    return () => document.removeEventListener("visibilitychange", onHide);
  }, [view.id, closed]);

  const unanswered = view.questions.filter((x) => !answered(x, answers[x.id])).length;
  const unsaved = Object.keys(pending).length;
  const selected = q.type === "mcq" ? ((answers[q.id] ?? {}) as { key?: string }).key ?? null : null;

  return (
    <div className="mx-auto max-w-5xl">
      <div className="sticky top-0 z-10 -mx-4 mb-4 flex flex-wrap items-center gap-3 border-b border-border bg-card/95 px-4 py-2 backdrop-blur">
        <span className="min-w-0 flex-1 truncate font-medium">{view.title}</span>
        <span className={cn("font-mono text-lg", left < 60_000 ? "text-destructive" : "text-foreground")} data-testid="timer">
          {formatLeft(left)}
        </span>
        {unsaved > 0 ? <ToneBadge tone="amber">Chưa lưu {unsaved}</ToneBadge> : <ToneBadge tone="green">Đã lưu</ToneBadge>}
        <Button onClick={() => setConfirming(true)} disabled={closed}>
          Nộp bài
        </Button>
      </div>
      {error && <div className="mb-3"><FormAlert>{error}</FormAlert></div>}
      <div className="grid gap-4 md:grid-cols-[1fr_220px]">
        <section className="rounded-xl border border-border bg-card p-4 sm:p-6" data-testid="exam-question">
          <div className="mb-2 text-xs text-muted-foreground">
            Phần {q.section} · {q.points} điểm
          </div>
          <QuestionView
            question={q}
            mode="exam"
            number={q.number}
            selected={selected}
            onSelect={q.type === "mcq" && !closed ? (label) => change({ key: label }) : undefined}
          />
          <AnswerInput q={q} value={answers[q.id]} onChange={change} />
          <div className="mt-6 flex justify-between">
            <Button variant="outline" disabled={index === 0} onClick={() => setIndex(index - 1)}>
              ← Câu trước
            </Button>
            <Button variant="outline" disabled={index === view.questions.length - 1} onClick={() => setIndex(index + 1)}>
              Câu sau →
            </Button>
          </div>
        </section>
        <aside className="rounded-xl border border-border bg-card p-3">
          <div className="mb-2 text-xs text-muted-foreground">Bảng câu · còn {unanswered} câu chưa làm</div>
          <div className="grid grid-cols-6 gap-1 md:grid-cols-5" data-testid="navigator">
            {view.questions.map((x, i) => (
              <button
                key={x.id}
                type="button"
                aria-label={`Câu ${x.number}`}
                aria-current={i === index ? "true" : undefined}
                onClick={() => setIndex(i)}
                className={cn(
                  "rounded py-1 text-sm",
                  i === index && "ring-2 ring-ring",
                  answered(x, answers[x.id]) ? "bg-primary text-white" : "border border-input",
                )}
              >
                {x.number}
              </button>
            ))}
          </div>
        </aside>
      </div>
      <FormDialog open={confirming} title="Nộp bài?" onOpenChange={(o) => !o && setConfirming(false)}>
        <p className="mb-4 text-sm">
          {unanswered ? `Bạn còn ${unanswered} câu chưa làm. ` : ""}Sau khi nộp sẽ không sửa được nữa.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => setConfirming(false)}>Làm tiếp</Button>
          <Button
           
            onClick={async () => {
              setConfirming(false);
              for (const [qid, v] of Object.entries(pending)) await flush(qid, v);
              await finish();
            }}
          >
            Nộp bài
          </Button>
        </div>
      </FormDialog>
    </div>
  );
}
