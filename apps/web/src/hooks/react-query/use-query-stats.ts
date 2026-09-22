import { keepPreviousData, useQuery, type UseQueryResult } from "@tanstack/react-query";
import { STATS_KEYS } from "@/constants/react-query-key.constant";
import type { HeatmapParams, StatsParams } from "@/dtos/stats.dto";
import type { GroupStat, HeatmapData, TopicStat } from "@/interfaces/stats.interface";
import { statsService } from "@/services/stats.service";

/** Per topic (the report tree); `enabled` false = the tab is not shown. The last answer stays while the next loads. */
export function useTopicStatsQuery(params: StatsParams = {}, enabled = true): UseQueryResult<TopicStat[], Error> {
  return useQuery<TopicStat[], Error>({ queryKey: STATS_KEYS.TOPICS(params), queryFn: () => statsService.topics(params), enabled, placeholderData: keepPreviousData });
}

/** Per question type, difficulty or tag. */
export function useGroupStatsQuery(by: string, params: StatsParams = {}, enabled = true): UseQueryResult<GroupStat[], Error> {
  return useQuery<GroupStat[], Error>({ queryKey: STATS_KEYS.GROUPS(by, params), queryFn: () => statsService.groups(by, params), enabled, placeholderData: keepPreviousData });
}

/** A class × topics of one level; needs a class. */
export function useHeatmapQuery(params: HeatmapParams | null): UseQueryResult<HeatmapData, Error> {
  return useQuery<HeatmapData, Error>({
    queryKey: STATS_KEYS.HEATMAP(params),
    queryFn: () => statsService.heatmap(params as HeatmapParams),
    enabled: !!params,
    placeholderData: keepPreviousData,
  });
}
