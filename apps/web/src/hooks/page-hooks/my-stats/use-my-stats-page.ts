import { useMe } from "@/hooks/common/use-me";
import { usePracticeHistoryQuery, useMyMasteryQuery } from "@/hooks/react-query/use-query-practice";
import { useGroupStatsQuery, useTopicStatsQuery } from "@/hooks/react-query/use-query-stats";

/** "Tiến độ của tôi": the caller's own answers per topic and type, mastery, and practice history.
 *  Roles nest, so staff reach this page too and read their own — empty, because nobody assigns them work.
 *  `canPractise` is the one thing that does not nest: starting a practice run writes a real attempt and real
 *  answer facts, and a teacher's practice would land in the organisation's numbers as if a student had sat it. */
export function useMyStatsPage() {
  const me = useMe();
  // scoped to the caller on purpose. The stats endpoints narrow to a student automatically and otherwise answer
  // for the whole organisation — which is what /org/reports wants and the exact opposite of what a page called
  // "của tôi" may show. Staff reach this page now that roles nest, so the scope has to be said out loud.
  const mine = { student_id: me.id };
  const { data: topics } = useTopicStatsQuery(mine);
  const { data: types } = useGroupStatsQuery("type", mine);
  const { data: mastery } = useMyMasteryQuery();
  const { data: practice } = usePracticeHistoryQuery();
  return { ready: !!(topics && types && mastery), canPractise: me.role === "student",
           topics: topics ?? [], types: types ?? [], mastery: mastery ?? [], practice };
}
