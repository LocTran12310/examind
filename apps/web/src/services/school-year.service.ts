import type { CommitRolloverBody, CreateYearBody, UpdateYearBody, YearAction } from "@/dtos/school-year.dto";
import type { SearchBody } from "@/dtos/search.dto";
import type { RolloverPlan, RolloverResult, SchoolYear } from "@/interfaces/school-year.interface";
import type { SearchPage } from "@/interfaces/search-page.interface";
import { http } from "@/lib/common/http";

export const schoolYearService = {
  search: (body: SearchBody) => http<SearchPage<SchoolYear>>("/school-years/search", { body }),
  create: (body: CreateYearBody) => http<SchoolYear>("/school-years", { body }),
  update: (id: string, body: UpdateYearBody) => http<SchoolYear>(`/school-years/${id}`, { method: "PATCH", body }),
  /** activate (the previous active year is closed) · close · reopen */
  setStatus: (id: string, action: YearAction) => http<SchoolYear>(`/school-years/${id}/${action}`, { method: "POST" }),
  remove: (id: string) => http<void>(`/school-years/${id}`, { method: "DELETE" }),
  previewRollover: (id: string, targetCode: string | null) => http<RolloverPlan>(`/school-years/${id}/rollover/preview`, { body: { target_code: targetCode } }),
  commitRollover: (id: string, body: CommitRolloverBody) => http<RolloverResult>(`/school-years/${id}/rollover/commit`, { body }),
};
