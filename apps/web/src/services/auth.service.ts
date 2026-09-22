import type { ChangePasswordBody, LoginBody } from "@/dtos/auth.dto";
import type { Me, MyOrg } from "@/interfaces/auth.interface";
import { http } from "@/lib/common/http";

export const authService = {
  login: (body: LoginBody) => http<Me>("/auth/login", { body }),
  logout: () => http<void>("/auth/logout", { method: "POST" }),
  /** New access cookie from the refresh cookie (the server layout found none). */
  refresh: () => http<void>("/auth/refresh", { method: "POST" }),
  me: () => http<Me>("/auth/me"),
  switchOrg: (orgId: string) => http<Me>("/auth/switch-org", { body: { org_id: orgId } }),
  changePassword: (body: ChangePasswordBody) => http<void>("/auth/change-password", { body }),
  /** The orgs of the header selector (a plain list, every org for a super admin). */
  myOrgs: () => http<MyOrg[]>("/me/orgs"),
};
