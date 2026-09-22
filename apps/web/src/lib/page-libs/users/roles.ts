import { ROLE_LABEL } from "@/constants/role.constant";
import type { Role } from "@/interfaces/auth.interface";

/** The roles an account of `role` may give: org admins any org role, teachers students only. */
export function rolesManagedBy(role: Role): Role[] {
  return role === "org_admin" ? ["student", "teacher", "org_admin"] : ["student"];
}

export const roleOptions = (role: Role) => rolesManagedBy(role).map((r) => ({ value: r, label: ROLE_LABEL[r] }));
