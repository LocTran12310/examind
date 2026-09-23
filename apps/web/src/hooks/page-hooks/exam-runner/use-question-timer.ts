import { useCallback, useEffect, useMemo, useRef } from "react";

interface Tracked {
  /** Milliseconds on screen the server has not been told about yet. */
  unreported: number;
  firstSeen: string;
}

export interface QuestionTimer {
  /** The whole seconds measured for a question since its last save, and when the runner first showed it. */
  take: (questionId: string) => { seconds: number; firstSeenAt: string | undefined };
  /** Those seconds reached the server: only what is left waits for the next save. */
  reported: (questionId: string, seconds: number) => void;
  /** End the running interval (the exam is over). */
  close: () => void;
}

/**
 * How long each question is on screen (learning-telemetry ADR-01): an interval opens when the runner shows a
 * question and closes when it switches, when the tab is hidden and when the exam ends; coming back to a question
 * adds to what it already has. Measuring only — the server clamps the numbers.
 */
export function useQuestionTimer(questionId: string, running: boolean): QuestionTimer {
  const seen = useRef<Record<string, Tracked>>({});
  const open = useRef<{ id: string; at: number } | null>(null);

  const fold = useCallback(() => {
    const cur = open.current;
    if (!cur) return;
    const at = Date.now();
    const tracked = seen.current[cur.id];
    if (tracked) tracked.unreported += at - cur.at;
    open.current = { id: cur.id, at };
  }, []);

  const close = useCallback(() => {
    fold();
    open.current = null;
  }, [fold]);

  const start = useCallback(
    (id: string) => {
      close();
      seen.current[id] = seen.current[id] ?? { unreported: 0, firstSeen: new Date().toISOString() };
      open.current = { id, at: Date.now() };
    },
    [close],
  );

  // the question on screen while the exam runs
  useEffect(() => {
    if (!running) {
      close();
      return;
    }
    start(questionId);
    return close;
  }, [questionId, running, start, close]);

  // a hidden tab is not time on the question
  useEffect(() => {
    const onVisibility = () => {
      if (document.visibilityState === "hidden") close();
      else if (running) start(questionId);
    };
    document.addEventListener("visibilitychange", onVisibility);
    return () => document.removeEventListener("visibilitychange", onVisibility);
  }, [questionId, running, start, close]);

  return useMemo(
    () => ({
      take: (id: string) => {
        fold();
        const tracked = seen.current[id];
        return { seconds: Math.floor((tracked?.unreported ?? 0) / 1000), firstSeenAt: tracked?.firstSeen };
      },
      reported: (id: string, seconds: number) => {
        const tracked = seen.current[id];
        if (tracked) tracked.unreported = Math.max(0, tracked.unreported - seconds * 1000);
      },
      close,
    }),
    [fold, close],
  );
}
