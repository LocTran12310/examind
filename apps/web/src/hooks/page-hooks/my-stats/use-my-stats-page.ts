import { useMemo, useState } from "react";
import { useMe } from "@/hooks/common/use-me";
import { useTaxonomyQuery } from "@/hooks/react-query/use-query-taxonomy";
import { usePracticeHistoryQuery, useMyMasteryQuery } from "@/hooks/react-query/use-query-practice";
import { useGroupStatsQuery, useTopicStatsQuery } from "@/hooks/react-query/use-query-stats";
import { weakestSubject } from "@/lib/page-libs/my-stats/weakest-subject";

/** "Tiến độ của tôi": the caller's own answers per topic and type, mastery, and practice history.
 *  Roles nest, so staff reach this page too and read their own — empty, because nobody assigns them work.
 *  `canPractise` is the one thing that does not nest: starting a practice run writes a real attempt and real
 *  answer facts, and a teacher's practice would land in the organisation's numbers as if a student had sat it. */
export function useMyStatsPage() {
  const me = useMe();
  // scoped to the caller on purpose. The stats endpoints narrow to a student automatically and otherwise answer
  // for the whole organisation — which is what /org/reports wants and the exact opposite of what a page called
  // "của tôi" may show. Staff reach this page now that roles nest, so the scope has to be said out loud.
  // one scope for the whole page (ADR-03): a picker that narrowed only half of it would let a reader choose
  // "Toán" and then read a number of every subject with nothing on screen saying so
  const [subjectId, setSubjectId] = useState("");
  const mine = useMemo(() => ({ student_id: me.id, ...(subjectId ? { subject_id: subjectId } : {}) }), [me.id, subjectId]);
  const { data: taxonomy } = useTaxonomyQuery();
  const { data: topics } = useTopicStatsQuery(mine);
  const { data: types } = useGroupStatsQuery("type", mine);
  const { data: mastery } = useMyMasteryQuery();
  const { data: practice } = usePracticeHistoryQuery();
  // these two lists are short and carry their own subject, so they are narrowed here rather than re-fetched.
  // A row with no subject (a practice run from before exams recorded one) belongs to no subject and is left out
  // of a narrowed view rather than claimed by it (A-08).
  const ofSubject = <T extends { subject_id: string | null }>(rows: T[]) => (subjectId ? rows.filter((r) => r.subject_id === subjectId) : rows);
  return { ready: !!(topics && types && mastery), canPractise: me.role === "student",
           subjectId, setSubjectId,
           subjectOptions: (taxonomy?.subjects ?? []).map((s) => ({ value: s.id, label: s.name })),
           // named only while showing every subject: with one picked there is nothing to tell apart (F23 ADR-04)
           subjectNames: subjectId ? undefined : new Map((taxonomy?.subjects ?? []).map((s) => [s.id, s.name])),
           // the subject step of "Tạo đề ôn tập" opens here: these rows already say where the student is
           // furthest behind, so nothing extra is fetched to preselect it (A-03)
           weakestSubject: weakestSubject(topics ?? []),
           topics: topics ?? [], types: types ?? [], mastery: ofSubject(mastery ?? []), practice: practice && ofSubject(practice) };
}
