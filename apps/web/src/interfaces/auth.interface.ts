export type Role = "super_admin" | "org_admin" | "teacher" | "student";

export interface OrgRef {
  id: string;
  code: string;
  name: string;
}

/** `GET /auth/me`: the signed-in user in the org they are working in. */
export interface Me {
  id: string;
  username: string;
  full_name: string;
  /** role in the active org */
  role: Role;
  must_change_password: boolean;
  /** the org the user is working in (header selector) */
  org: OrgRef;
  home_org?: OrgRef;
  is_super?: boolean;
}

/** `GET /me/orgs`: an org the user belongs to (every org for a super admin). */
export interface MyOrg extends OrgRef {
  role: Role;
  is_home: boolean;
}
