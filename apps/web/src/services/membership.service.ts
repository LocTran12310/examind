import type { AddMemberBody, AddMembershipBody, UpdateMembershipBody } from "@/dtos/org.dto";
import type { SearchBody } from "@/dtos/search.dto";
import type { Membership } from "@/interfaces/org.interface";
import type { SearchPage } from "@/interfaces/search-page.interface";
import { http } from "@/lib/common/http";

/** One side of a membership: an org's members (`org_id`) or an account's orgs (`user_id`). */
export type MembershipSide = { org_id: string } | { user_id: string };

const base = (side: MembershipSide) => ("org_id" in side ? `/admin/orgs/${side.org_id}/members` : `/admin/users/${side.user_id}/memberships`);
const one = (side: MembershipSide, m: Membership) => `${base(side)}/${"org_id" in side ? m.user_id : m.org_id}`;

/** Memberships seen from either side; both call the same membership rules on the server (school-years ADR-04). */
export const membershipService = {
  /** The side travels in the body (`org_id` or `user_id`, like any resource parameter) and picks the path. */
  search: ({ org_id, user_id, ...body }: SearchBody) =>
    http<SearchPage<Membership>>(`${base(org_id ? { org_id: String(org_id) } : { user_id: String(user_id) })}/search`, { body }),
  add: (side: MembershipSide, body: AddMemberBody | AddMembershipBody) => http<Membership>(base(side), { body }),
  update: (side: MembershipSide, m: Membership, body: UpdateMembershipBody) => http<Membership>(one(side, m), { method: "PATCH", body }),
  remove: (side: MembershipSide, m: Membership) => http<void>(one(side, m), { method: "DELETE" }),
};
