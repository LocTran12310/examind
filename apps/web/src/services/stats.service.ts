import type { HeatmapParams, StatsParams } from "@/dtos/stats.dto";
import type { GroupStat, HeatmapData, TopicStat } from "@/interfaces/stats.interface";
import { http } from "@/lib/common/http";

/** Query string of the set values ("" and undefined are left out). */
function query(params: object): string {
  const s = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== null && v !== "") s.set(k, String(v));
  const out = s.toString();
  return out ? `?${out}` : "";
}

export const statsService = {
  topics: (params: StatsParams = {}) => http<TopicStat[]>(`/stats/topics${query(params)}`),
  groups: (by: string, params: StatsParams = {}) => http<GroupStat[]>(`/stats/groups${query({ by, ...params })}`),
  heatmap: (params: HeatmapParams) => http<HeatmapData>(`/stats/heatmap${query(params)}`),
};
