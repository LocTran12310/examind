import type { Role } from "@/interfaces/auth.interface";

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
  /** false when the account lives in another org and was added here */
  is_home?: boolean;
  home_org_code?: string | null;
}

/** A temporary password, shown once (create, reset, import). */
export interface Credential {
  user_id: string;
  username: string;
  full_name: string;
  temp_password: string;
  role?: Role;
  class?: string;
}

export interface UserCreated {
  user: User;
  temp_password: string;
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

/** `POST /users/import/preview`: every row of the file, checked. */
export interface ImportPreview {
  rows: ImportRow[];
  valid_count: number;
  error_count: number;
}

export interface ImportCommitted {
  created: Credential[];
}
