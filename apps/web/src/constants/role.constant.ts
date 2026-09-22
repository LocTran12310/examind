import type { Role } from "@/interfaces/auth.interface";

export const ROLE_LABEL: Record<Role, string> = {
  super_admin: "Quản trị hệ thống",
  org_admin: "Quản trị trung tâm",
  teacher: "Giáo viên",
  student: "Học sinh",
};

/** Roles a membership can have (an org admin, teacher or student of that org). */
export const MEMBER_ROLES: Role[] = ["org_admin", "teacher", "student"];
export const MEMBER_ROLE_OPTIONS = MEMBER_ROLES.map((r) => ({ value: r, label: ROLE_LABEL[r] }));
