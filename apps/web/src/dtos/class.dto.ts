/** Create or edit a class: a year by id (or by code from old clients), a khối by id. */
export interface ClassBody {
  name: string;
  grade_id: string | null;
  school_year_id?: string;
  school_year?: string;
}
