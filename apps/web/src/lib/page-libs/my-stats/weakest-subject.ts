import type { TopicStat } from "@/interfaces/stats.interface";

/** The subject this student is furthest behind in, or null when nothing says.
 *
 *  Read off the rows the progress page already has, so nothing extra is fetched: points over max points per
 *  subject, lowest first. A subject nobody has answered anything in cannot be "weakest" — it is unmeasured, and
 *  unmeasured is not the same as weak (the rule the mastery bands are built on). */
export function weakestSubject(rows: TopicStat[]): string | null {
  const totals = new Map<string, { got: number; max: number }>();
  for (const r of rows) {
    if (!r.subject_id || !r.answered) continue;
    const t = totals.get(r.subject_id) ?? { got: 0, max: 0 };
    totals.set(r.subject_id, { got: t.got + r.points, max: t.max + r.max_points });
  }
  let worst: string | null = null;
  let lowest = Infinity;
  for (const [id, t] of totals) {
    if (!t.max) continue;
    const ratio = t.got / t.max;
    if (ratio < lowest) [worst, lowest] = [id, ratio];
  }
  return worst;
}
