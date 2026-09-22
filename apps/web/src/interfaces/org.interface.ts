import type { Role } from "@/interfaces/auth.interface";

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

/** An account's place in one org, seen from the org (members) or from the account (memberships). */
export interface Membership {
  user_id: string;
  username: string;
  full_name: string;
  home_org_code: string;
  org_id: string;
  org_code: string;
  org_name: string;
  role: Role;
  is_active: boolean;
  is_home: boolean;
}

/** An account of any org (super admin's Tài khoản page). */
export interface Account {
  id: string;
  username: string;
  full_name: string;
  home_org_code: string;
  home_org_name: string;
  is_active: boolean;
  org_count: number;
}
