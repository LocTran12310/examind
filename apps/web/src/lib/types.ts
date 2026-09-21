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

export interface Org {
  id: string;
  code: string;
  name: string;
  status: "active" | "suspended";
  is_system: boolean;
  user_count: number;
  created_at: string;
  deleted_at: string | null;
}

export interface OrgCreated {
  org: Org;
  admin: { username: string; temp_password: string };
}

export interface User {
  id: string;
  username: string;
  full_name: string;
  email: string | null;
  role: Role;
  is_active: boolean;
  must_change_password: boolean;
  last_login_at: string | null;
  created_at: string;
  class_ids: string[];
}

export interface Credential {
  user_id: string;
  username: string;
  full_name: string;
  temp_password: string;
  role?: Role;
  class?: string;
}

export interface SchoolClass {
  id: string;
  name: string;
  grade: number | null;
  school_year: string;
  member_count: number;
  created_at: string;
}

export interface ClassDetail extends SchoolClass {
  members: User[];
}

export interface ImportRow {
  row: number;
  full_name: string;
  username: string;
  role: Role;
  class: string;
  errors: string[];
  generated_username: boolean;
}
