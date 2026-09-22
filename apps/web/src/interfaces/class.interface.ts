import type { User } from "@/lib/types";

export interface SchoolClass {
  id: string;
  name: string;
  grade: number | null;
  grade_id?: string | null;
  school_year_id?: string | null;
  school_year: string;
  member_count: number;
  created_at: string;
}

export interface ClassDetail extends SchoolClass {
  members: User[];
}
