export type YearStatus = "planning" | "active" | "closed";

export interface SchoolTerm {
  code: "hk1" | "hk2";
  name: string;
  start_date: string;
  end_date: string;
}

export interface SchoolYear {
  id: string;
  code: string;
  name: string;
  start_date: string;
  end_date: string;
  status: YearStatus;
  terms: SchoolTerm[];
  class_count: number;
}

export type RolloverAction = "promote" | "retain" | "transfer" | "graduate";

export interface RolloverStudent {
  user_id: string;
  full_name: string;
  username: string;
  current_status: string;
  action: RolloverAction;
}

export interface RolloverClass {
  source_class_id: string;
  source_name: string;
  grade: number | null;
  graduating: boolean;
  target_name: string | null;
  target_grade: number | null;
  target_exists: boolean;
  students: RolloverStudent[];
}

/** Answer of `POST /school-years/{id}/rollover/preview`. */
export interface RolloverPlan {
  source_year: { id: string; code: string; status: string };
  target_code: string;
  target_year_id: string | null;
  top_grade: number;
  classes: RolloverClass[];
}

/** Answer of `POST /school-years/{id}/rollover/commit`. */
export interface RolloverResult {
  target_year_id: string;
  target_code: string;
  classes_created: string[];
  promote: number;
  retain: number;
  transfer: number;
  graduate: number;
}
