import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { answered } from "@/lib/common/answer";
import { useSaveAnswerMutation, useSubmitAttemptMutation, useTabSwitchMutation } from "@/hooks/react-query/use-query-attempt";
import { useQuestionTimer } from "@/hooks/page-hooks/exam-runner/use-question-timer";
import type { AttemptQuestion, RunnerPaper } from "@/interfaces/attempt.interface";
import { ApiError } from "@/lib/common/http";
import type { AnswerResponse } from "@/types/attempt.type";

const SAVE_DEBOUNCE = 500;
const RETRY_EVERY = 3000;

/**
 * The exam while it is open: answers kept here and autosaved after a short pause (unsaved ones retried),
 * a countdown on the server clock (`server_now` sets the offset) that submits at zero, and every
 * switch away from the tab reported. An answer refused because the attempt closed ends the exam.
 * Each save carries the seconds the question was on screen since the last one (learning-telemetry ADR-01).
 *
 * `trial` is the second mode, and it exists because the person who set the exam sits the same screen with nothing
 * behind it (exam-runner ADR-01): no attempt to save an answer to, no deadline to count down to, nobody to report a
 * tab switch for, nothing to submit. Everything a student's runner is — the questions, the navigator, both view
 * modes, the unanswered count — is the same code; `trial` only keeps the four server calls from happening and hands
 * the answers to `onFinished`, which is the only place a trial run's grade can come from.
 */
export function useExamRunner(view: RunnerPaper, onFinished: (answers: Record<string, AnswerResponse>) => void, trial = false) {
  const [answers, setAnswers] = useState<Record<string, AnswerResponse>>(() => Object.fromEntries(view.questions.map((q) => [q.id, q.response])));
  const [index, setIndex] = useState(0);
  const [pending, setPending] = useState<Record<string, AnswerResponse>>({});
  const [confirming, setConfirming] = useState(false);
  const [closed, setClosed] = useState(!!view.status && view.status !== "in_progress");
  const [error, setError] = useState<string | null>(null);
  const offset = useMemo(() => (view.server_now ? new Date(view.server_now).getTime() - Date.now() : 0), [view.server_now]);
  const deadline = view.deadline_at ? new Date(view.deadline_at).getTime() : 0;
  /** Milliseconds to the deadline, or null in a trial run: there is no deadline, so there is nothing to show. */
  const [left, setLeft] = useState<number | null>(() => (trial ? null : deadline - (Date.now() + offset)));
  const timers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});
  const q: AttemptQuestion = view.questions[index];
  // a trial run has no attempt id; these three are built with one that is never used, because nothing below fires
  const { mutateAsync: saveAnswer } = useSaveAnswerMutation(view.id ?? "");
  const { mutateAsync: submit } = useSubmitAttemptMutation(view.id ?? "");
  const { mutateAsync: reportTabSwitch } = useTabSwitchMutation(view.id ?? "");
  const timer = useQuestionTimer(q.id, !closed && !trial);
  /** The option an mcq currently holds; whole-paper mode needs it per question, not only for the current one. */
  const keyOf = (x: AttemptQuestion) => (x.type === "mcq" ? (((answers[x.id] ?? {}) as { key?: string }).key ?? null) : null);

  const finish = useCallback(async () => {
    setClosed(true);
    timer.close();
    if (!trial) await submit().catch(() => undefined);
    onFinished(answers);
  }, [trial, submit, onFinished, timer, answers]);

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
          onFinished(answers);
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
    [saveAnswer, onFinished, timer, answers],
  );

  /** `questionId` is how whole-paper mode answers a question other than the one the navigator points at. */
  function change(value: AnswerResponse, questionId?: string) {
    if (closed) return;
    const qid = questionId ?? q.id;
    // the question just touched becomes the current one, so the timer, the navigator and a switch back to
    // one-question mode all follow the student instead of the last arrow they pressed
    if (qid !== q.id) setIndex(view.questions.findIndex((x) => x.id === qid));
    setAnswers((a) => ({ ...a, [qid]: value }));
    if (trial) return; // nothing to save it to, so nothing is ever pending
    setPending((p) => ({ ...p, [qid]: value }));
    clearTimeout(timers.current[qid]);
    timers.current[qid] = setTimeout(() => void flush(qid, value), SAVE_DEBOUNCE);
  }

  // countdown from the server clock
  useEffect(() => {
    if (trial) return;
    const t = setInterval(() => setLeft(deadline - (Date.now() + offset)), 500);
    return () => clearInterval(t);
  }, [trial, deadline, offset]);
  useEffect(() => {
    if (left !== null && left <= 0 && !closed) void finish();
  }, [left, closed, finish]);

  // retry unsaved answers
  useEffect(() => {
    if (trial) return;
    const t = setInterval(() => {
      for (const [qid, v] of Object.entries(pending)) void flush(qid, v);
    }, RETRY_EVERY);
    return () => clearInterval(t);
  }, [trial, pending, flush]);

  // count tab switches
  useEffect(() => {
    if (trial) return;
    const onHide = () => {
      if (document.visibilityState === "hidden" && !closed) void reportTabSwitch().catch(() => undefined);
    };
    document.addEventListener("visibilitychange", onHide);
    return () => document.removeEventListener("visibilitychange", onHide);
  }, [trial, reportTabSwitch, closed]);

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
    keyOf,
    unanswered: view.questions.filter((x) => !answered(x, answers[x.id])).length,
    unsaved: Object.keys(pending).length,
    selected: keyOf(q),
    /** "Nộp bài" confirmed: save what is still pending, then submit. */
    submitNow: async () => {
      setConfirming(false);
      for (const [qid, v] of Object.entries(pending)) await flush(qid, v);
      await finish();
    },
  };
}
