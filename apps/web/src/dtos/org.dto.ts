export interface CreateOrgBody {
  code: string;
  name: string;
  admin_username: string;
}

export interface UpdateOrgBody {
  code?: string;
  name?: string;
}

/** Status changes and removal applied to several orgs from the toolbar. */
export type OrgAction = "suspend" | "activate" | "delete";

/** An org side: add an account by its home org code + username. */
export interface AddMemberBody {
  org_code: string;
  username: string;
  role: string;
}

/** An account side: add the account to an org. */
export interface AddMembershipBody {
  org_id: string;
  role: string;
}

export interface UpdateMembershipBody {
  role?: string;
  is_active?: boolean;
}
