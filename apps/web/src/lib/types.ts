export type Role = "super_admin" | "org_admin" | "teacher" | "student";

export interface OrgRef {
  id: string;
  code: string;
  name: string;
}

export interface Me {
  id: string;
  username: string;
  full_name: string;
  role: Role;
  must_change_password: boolean;
  org: OrgRef;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export const ROLE_LABEL: Record<Role, string> = {
  super_admin: "Quản trị hệ thống",
  org_admin: "Quản trị trung tâm",
  teacher: "Giáo viên",
  student: "Học sinh",
};
