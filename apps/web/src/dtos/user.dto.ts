import type { Role } from "@/interfaces/auth.interface";
import type { ImportRow } from "@/interfaces/user.interface";

export interface CreateUserBody {
  full_name: string;
  /** null = generated from the name */
  username: string | null;
  role: Role;
}

export interface UpdateUserBody {
  full_name?: string;
  email?: string;
  role?: Role;
  is_active?: boolean;
}

/** Add an account of another org (its home org code + username) with a role here. */
export interface LinkUserBody {
  org_code: string;
  username: string;
  role: string;
}

export interface ImportCommitBody {
  rows: ImportRow[];
}
