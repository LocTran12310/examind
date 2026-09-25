import {
  BarChart3,
  BookOpenCheck,
  Bot,
  Building2,
  CalendarRange,
  ClipboardList,
  FileStack,
  FileUp,
  GraduationCap,
  Library,
  ListChecks,
  ListTodo,
  type LucideIcon,
  Network,
  School,
  Settings2,
  Tags,
  TrendingUp,
  UserCog,
  Users,
} from "lucide-react";
import type { Role } from "@/interfaces/auth.interface";

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

/**
 * Roles nest, they are not disjoint sets (ADR-02): HS ⊂ GV ⊂ Admin. An item's `roles` therefore names the
 * *lowest* role allowed to see it, and everything above inherits it — a new item needs one role, not three.
 * `super_admin` stays outside the chain: it is a platform role granted through `isSuper`, and the items only a
 * platform admin may see name it on their own.
 */
const NESTED: Role[] = ["student", "teacher", "org_admin"];

/** The roles a role covers: itself plus everything below it in the chain. */
export function rolesUnder(role: Role): Role[] {
  const rank = NESTED.indexOf(role);
  return rank < 0 ? [role] : NESTED.slice(0, rank + 1);
}

/** "staff and above" — with nesting one role is enough, "teacher" already reaches an org admin. */
const STAFF: Role[] = ["teacher"];

export const NAV_GROUPS: NavGroup[] = [
  {
    label: "Đề & câu hỏi",
    items: [
      { href: "/org/documents", label: "Đề đã tải lên", roles: STAFF, icon: FileUp },
      { href: "/org/review", label: "Duyệt câu hỏi", roles: STAFF, icon: ListChecks },
      { href: "/org/review/untagged", label: "Chưa gắn chuyên đề", roles: STAFF, icon: ListTodo },
      { href: "/org/bank", label: "Ngân hàng câu hỏi", roles: STAFF, icon: Library },
      { href: "/org/exams", label: "Đề thi & giao bài", roles: STAFF, icon: FileStack },
    ],
  },
  {
    label: "Lớp & học sinh",
    items: [
      { href: "/org/school-years", label: "Năm học", roles: STAFF, icon: CalendarRange },
      { href: "/org/structure", label: "Cơ cấu trường", roles: STAFF, icon: School },
      { href: "/org/classes", label: "Lớp học", roles: STAFF, icon: GraduationCap },
      { href: "/org/users", label: "Người dùng", roles: STAFF, icon: Users },
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
  {
    label: "Hệ thống",
    items: [
      { href: "/admin/orgs", label: "Tổ chức", roles: ["super_admin"], icon: Building2 },
      { href: "/admin/users", label: "Tài khoản", roles: ["super_admin"], icon: UserCog },
    ],
  },
  {
    label: "Học tập",
    items: [
      { href: "/home", label: "Bài được giao", roles: ["student"], icon: ClipboardList },
      { href: "/me/stats", label: "Tiến độ của tôi", roles: ["student"], icon: TrendingUp },
    ],
  },
];

/** Items for the role in the active org, the roles below it included; a super admin keeps the "Hệ thống" items. */
export function groupsFor(role: Role, isSuper = false): NavGroup[] {
  const covers = rolesUnder(role);
  const can = (i: NavItem) => i.roles.some((r) => covers.includes(r)) || (isSuper && i.roles.includes("super_admin"));
  return NAV_GROUPS.map((g) => ({ ...g, items: g.items.filter(can) })).filter((g) => g.items.length);
}

export function navFor(role: Role, isSuper = false): NavItem[] {
  return groupsFor(role, isSuper).flatMap((g) => g.items);
}

/** The deepest nav item matching the path, so /org/exams/123 highlights "Đề thi". */
export function activeItem(role: Role, pathname: string, isSuper = false): NavItem | undefined {
  return navFor(role, isSuper)
    .filter((n) => pathname === n.href || pathname.startsWith(n.href + "/"))
    .sort((a, b) => b.href.length - a.href.length)[0];
}

export function homeFor(role: Role): string {
  return role === "super_admin" ? "/admin/orgs" : role === "student" ? "/home" : "/org/review";
}

export const APP_ICON = BookOpenCheck;
