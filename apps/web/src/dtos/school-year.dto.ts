import type { RolloverAction } from "@/interfaces/school-year.interface";

export interface TermBody {
  code: "hk1" | "hk2";
  start_date: string;
  end_date: string;
}

export interface UpdateYearBody {
  name: string | null;
  start_date: string | null;
  end_date: string | null;
  terms?: TermBody[];
}

export interface CreateYearBody extends UpdateYearBody {
  code: string;
}

export type YearAction = "activate" | "close" | "reopen";

export interface CommitRolloverBody {
  target_code: string;
  activate_target: boolean;
  classes: { source_class_id: string; target_name: string | null; students: { user_id: string; action: RolloverAction }[] }[];
}
