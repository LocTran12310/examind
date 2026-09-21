import type { Role } from "./types";

export interface NavItem {
  href: string;
  label: string;
  roles: Role[];
}

export const NAV: NavItem[] = [
  { href: "/admin/orgs", label: "Tổ chức", roles: ["super_admin"] },
  { href: "/org/users", label: "Người dùng", roles: ["org_admin", "teacher"] },
  { href: "/org/classes", label: "Lớp học", roles: ["org_admin", "teacher"] },
  { href: "/org/topics", label: "Chuyên đề", roles: ["org_admin", "teacher"] },
  { href: "/org/tags", label: "Tags", roles: ["org_admin", "teacher"] },
];

export function navFor(role: Role): NavItem[] {
  return NAV.filter((n) => n.roles.includes(role));
}

export function homeFor(role: Role): string {
  return role === "super_admin" ? "/admin/orgs" : role === "student" ? "/home" : "/org/users";
}
