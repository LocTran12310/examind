import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { answered } from "@/lib/common/answer";
import { useSaveAnswerMutation, useSubmitAttemptMutation, useTabSwitchMutation } from "@/hooks/react-query/use-query-attempt";
import { useQuestionTimer } from "@/hooks/page-hooks/exam-runner/use-question-timer";
import type { AttemptQuestion, AttemptView } from "@/interfaces/attempt.interface";
import { ApiError } from "@/lib/common/http";
import type { AnswerResponse } from "@/types/attempt.type";

const SAVE_DEBOUNCE = 500;
const RETRY_EVERY = 3000;

/**
 * The exam while it is open: answers kept here and autosaved after a short pause (unsaved ones retried),
 * a countdown on the server clock (`server_now` sets the offset) that submits at zero, and every
 * switch away from the tab reported. An answer refused because the attempt closed ends the exam.
 * Each save carries the seconds the question was on screen since the last one (learning-telemetry ADR-01).
 */
export function useExamRunner(view: AttemptView, onFinished: () => void) {
  const [answers, setAnswers] = useState<Record<string, AnswerResponse>>(() => Object.fromEntries(view.questions.map((q) => [q.id, q.response])));
  const [index, setIndex] = useState(0);
  const [pending, setPending] = useState<Record<string, AnswerResponse>>({});
  const [confirming, setConfirming] = useState(false);
  const [closed, setClosed] = useState(view.status !== "in_progress");
  const [error, setError] = useState<string | null>(null);
  const offset = useMemo(() => new Date(view.server_now).getTime() - Date.now(), [view.server_now]);
  const deadline = new Date(view.deadline_at).getTime();
  const [left, setLeft] = useState(() => deadline - (Date.now() + offset));
  const timers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});
  const q: AttemptQuestion = view.questions[index];
  const { mutateAsync: saveAnswer } = useSaveAnswerMutation(view.id);
  const { mutateAsync: submit } = useSubmitAttemptMutation(view.id);
  const { mutateAsync: reportTabSwitch } = useTabSwitchMutation(view.id);
  const timer = useQuestionTimer(q.id, !closed);

  const finish = useCallback(async () => {
    setClosed(true);
    timer.close();
    await submit().catch(() => undefined);
    onFinished();
  }, [submit, onFinished, timer]);

  const flush = useCallback(
    async (qid: string, value: AnswerResponse) => {
      const { seconds, firstSeenAt } = timer.take(qid);
      try {
        await saveAnswer({ questionId: qid, body: { response: value, seconds_spent: seconds, first_seen_at: firstSeenAt } });
        timer.reported(qid, seconds);
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
    [saveAnswer, onFinished, timer],
  );

  function change(value: AnswerResponse) {
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
      if (document.visibilityState === "hidden" && !closed) void reportTabSwitch().catch(() => undefined);
    };
    document.addEventListener("visibilitychange", onHide);
    return () => document.removeEventListener("visibilitychange", onHide);
  }, [reportTabSwitch, closed]);

  return {
    q,
    index,
    setIndex,
    answers,
    left,
    closed,
    error,
    confirming,
    setConfirming,
    change,
    unanswered: view.questions.filter((x) => !answered(x, answers[x.id])).length,
    unsaved: Object.keys(pending).length,
    selected: q.type === "mcq" ? (((answers[q.id] ?? {}) as { key?: string }).key ?? null) : null,
    /** "Nộp bài" confirmed: save what is still pending, then submit. */
    submitNow: async () => {
      setConfirming(false);
      for (const [qid, v] of Object.entries(pending)) await flush(qid, v);
      await finish();
    },
  };
}
