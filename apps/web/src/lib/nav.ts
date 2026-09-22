import {
  BarChart3,
  BookOpenCheck,
  Bot,
  Building2,
  ClipboardList,
  FileStack,
  FileUp,
  GraduationCap,
  Library,
  ListChecks,
  type LucideIcon,
  Network,
  School,
  Settings2,
  Tags,
  TrendingUp,
  Users,
} from "lucide-react";
import type { Role } from "./types";

export interface NavItem {
  href: string;
  label: string;
  roles: Role[];
  icon: LucideIcon;
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
      { href: "/org/documents", label: "Đề đã tải lên", roles: STAFF, icon: FileUp },
      { href: "/org/review", label: "Duyệt câu hỏi", roles: STAFF, icon: ListChecks },
      { href: "/org/bank", label: "Ngân hàng câu hỏi", roles: STAFF, icon: Library },
      { href: "/org/exams", label: "Đề thi & giao bài", roles: STAFF, icon: FileStack },
    ],
  },
  {
    label: "Lớp & học sinh",
    items: [
      { href: "/org/structure", label: "Cơ cấu trường", roles: STAFF, icon: School },
      { href: "/org/users", label: "Người dùng", roles: STAFF, icon: Users },
      { href: "/org/classes", label: "Lớp học", roles: STAFF, icon: GraduationCap },
    ],
  },
  { label: "Báo cáo", items: [{ href: "/org/reports", label: "Kết quả theo chuyên đề", roles: STAFF, icon: BarChart3 }] },
  {
    label: "Cài đặt",
    items: [
      { href: "/org/topics", label: "Chuyên đề", roles: STAFF, icon: Network },
      { href: "/org/tags", label: "Tags", roles: STAFF, icon: Tags },
      { href: "/org/ai-models", label: "Model AI", roles: ["org_admin", "super_admin"], icon: Bot },
      { href: "/org/settings/ingestion", label: "Cấu hình tách đề", roles: ["org_admin"], icon: Settings2 },
    ],
  },
  { label: "Hệ thống", items: [{ href: "/admin/orgs", label: "Tổ chức", roles: ["super_admin"], icon: Building2 }] },
  {
    label: "Học tập",
    items: [
      { href: "/home", label: "Bài được giao", roles: ["student"], icon: ClipboardList },
      { href: "/me/stats", label: "Tiến độ của tôi", roles: ["student"], icon: TrendingUp },
    ],
  },
];

export function groupsFor(role: Role): NavGroup[] {
  return NAV_GROUPS.map((g) => ({ ...g, items: g.items.filter((i) => i.roles.includes(role)) })).filter((g) => g.items.length);
}

export function navFor(role: Role): NavItem[] {
  return groupsFor(role).flatMap((g) => g.items);
}

/** The deepest nav item matching the path, so /org/exams/123 highlights "Đề thi". */
export function activeItem(role: Role, pathname: string): NavItem | undefined {
  return navFor(role)
    .filter((n) => pathname === n.href || pathname.startsWith(n.href + "/"))
    .sort((a, b) => b.href.length - a.href.length)[0];
}

export function homeFor(role: Role): string {
  return role === "super_admin" ? "/admin/orgs" : role === "student" ? "/home" : "/org/review";
}

export const APP_ICON = BookOpenCheck;
