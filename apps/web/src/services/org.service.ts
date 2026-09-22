import type { CreateOrgBody, UpdateOrgBody } from "@/dtos/org.dto";
import type { SearchBody } from "@/dtos/search.dto";
import type { Org, OrgCreated } from "@/interfaces/org.interface";
import type { SearchPage } from "@/interfaces/search-page.interface";
import { http } from "@/lib/common/http";

/** Organisations (super admin). */
export const orgService = {
  /** `include_deleted: true` also lists soft-deleted orgs. */
  search: (body: SearchBody) => http<SearchPage<Org>>("/admin/orgs/search", { body }),
  get: (id: string) => http<Org>(`/admin/orgs/${id}`),
  create: (body: CreateOrgBody) => http<OrgCreated>("/admin/orgs", { body }),
  update: (id: string, body: UpdateOrgBody) => http<Org>(`/admin/orgs/${id}`, { method: "PATCH", body }),
  remove: (id: string, hard = false) => http<void>(`/admin/orgs/${id}${hard ? "?hard=true" : ""}`, { method: "DELETE" }),
  suspend: (id: string) => http<Org>(`/admin/orgs/${id}/suspend`, { method: "POST" }),
  activate: (id: string) => http<Org>(`/admin/orgs/${id}/activate`, { method: "POST" }),
};
