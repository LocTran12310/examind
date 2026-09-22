import { useAssignmentReportQuery } from "@/hooks/react-query/use-query-assignment";

/** Báo cáo bài giao: totals, score distribution, students and per-question stats. */
export function useAssignmentReportPage(id: string) {
  const { data } = useAssignmentReportQuery(id);
  return { report: data };
}
