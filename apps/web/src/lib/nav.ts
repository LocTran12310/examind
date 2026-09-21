import type { Role } from "./types";

export interface NavItem {
  href: string;
  label: string;
  roles: Role[];
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}

const STAFF: Role[] = ["org_admin", "teacher"];

export const NAV_GROUPS: NavGroup[] = [
  {
    label: "Đề & câu hỏi",
    items: [
      { href: "/org/documents", label: "Đề đã tải lên", roles: STAFF },
      { href: "/org/review", label: "Duyệt câu hỏi", roles: STAFF },
      { href: "/org/bank", label: "Ngân hàng câu hỏi", roles: STAFF },
      { href: "/org/exams", label: "Đề thi & giao bài", roles: STAFF },
    ],
  },
  {
    label: "Lớp & học sinh",
    items: [
      { href: "/org/users", label: "Người dùng", roles: STAFF },
      { href: "/org/classes", label: "Lớp học", roles: STAFF },
    ],
  },
  { label: "Báo cáo", items: [{ href: "/org/reports", label: "Kết quả theo chuyên đề", roles: STAFF }] },
  {
    label: "Cài đặt",
    items: [
      { href: "/org/topics", label: "Chuyên đề", roles: STAFF },
      { href: "/org/tags", label: "Tags", roles: STAFF },
      { href: "/org/ai-models", label: "Model AI", roles: ["org_admin", "super_admin"] },
      { href: "/org/settings/ingestion", label: "Cấu hình tách đề", roles: ["org_admin"] },
    ],
  },
  { label: "Hệ thống", items: [{ href: "/admin/orgs", label: "Tổ chức", roles: ["super_admin"] }] },
  {
    label: "Học tập",
    items: [
      { href: "/home", label: "Bài được giao", roles: ["student"] },
      { href: "/me/stats", label: "Tiến độ của tôi", roles: ["student"] },
    ],
  },
];

export function groupsFor(role: Role): NavGroup[] {
  return NAV_GROUPS.map((g) => ({ ...g, items: g.items.filter((i) => i.roles.includes(role)) })).filter((g) => g.items.length);
}

export function navFor(role: Role): NavItem[] {
  return groupsFor(role).flatMap((g) => g.items);
}

export function homeFor(role: Role): string {
  return role === "super_admin" ? "/admin/orgs" : role === "student" ? "/home" : "/org/review";
}
