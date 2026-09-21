import type { Role } from "./types";

export interface NavItem {
  href: string;
  label: string;
  roles: Role[];
}

export const NAV: NavItem[] = [
  { href: "/admin/orgs", label: "Tổ chức", roles: ["super_admin"] },
  { href: "/org/documents", label: "Đề đã tải lên", roles: ["org_admin", "teacher"] },
  { href: "/org/users", label: "Người dùng", roles: ["org_admin", "teacher"] },
  { href: "/org/classes", label: "Lớp học", roles: ["org_admin", "teacher"] },
  { href: "/org/topics", label: "Chuyên đề", roles: ["org_admin", "teacher"] },
  { href: "/org/tags", label: "Tags", roles: ["org_admin", "teacher"] },
  { href: "/org/ai-models", label: "Model AI", roles: ["org_admin", "super_admin"] },
  { href: "/org/settings/ingestion", label: "Cấu hình tách đề", roles: ["org_admin"] },
];

export function navFor(role: Role): NavItem[] {
  return NAV.filter((n) => n.roles.includes(role));
}

export function homeFor(role: Role): string {
  return role === "super_admin" ? "/admin/orgs" : role === "student" ? "/home" : "/org/users";
}
