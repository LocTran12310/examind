import { usePracticeHistoryQuery, useMyMasteryQuery } from "@/hooks/react-query/use-query-practice";
import { useGroupStatsQuery, useTopicStatsQuery } from "@/hooks/react-query/use-query-stats";

/** "Tiến độ của tôi": the student's own answers per topic and type, mastery, and practice history. */
export function useMyStatsPage() {
  const { data: topics } = useTopicStatsQuery();
  const { data: types } = useGroupStatsQuery("type");
  const { data: mastery } = useMyMasteryQuery();
  const { data: practice } = usePracticeHistoryQuery();
  return { ready: !!(topics && types && mastery), topics: topics ?? [], types: types ?? [], mastery: mastery ?? [], practice };
}
