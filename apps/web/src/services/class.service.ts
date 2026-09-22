import type { ClassBody } from "@/dtos/class.dto";
import type { SearchBody } from "@/dtos/search.dto";
import type { ClassDetail, SchoolClass } from "@/interfaces/class.interface";
import type { SearchPage } from "@/interfaces/search-page.interface";
import type { ClassOverviewRow } from "@/lib/types";
import { http } from "@/lib/common/http";

export const classService = {
  search: (body: SearchBody) => http<SearchPage<SchoolClass>>("/classes/search", { body }),
  get: (id: string) => http<ClassDetail>(`/classes/${id}`),
  create: (body: ClassBody) => http<SchoolClass>("/classes", { body }),
  update: (id: string, body: ClassBody) => http<SchoolClass>(`/classes/${id}`, { method: "PATCH", body }),
  remove: (id: string) => http<void>(`/classes/${id}`, { method: "DELETE" }),
  addMembers: (id: string, userIds: string[]) => http<void>(`/classes/${id}/members`, { body: { user_ids: userIds } }),
  removeMember: (id: string, userId: string) => http<void>(`/classes/${id}/members/${userId}`, { method: "DELETE" }),
  /** Tình hình học tập: weakest topics and the latest personal review per student. */
  overview: (id: string) => http<ClassOverviewRow[]>(`/classes/${id}/overview`),
};
