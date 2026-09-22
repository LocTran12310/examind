export interface SchoolLevel {
  id: string;
  code: string;
  name: string;
  grade_from: number;
  grade_to: number;
  sort: number;
  grade_count: number;
}

export interface GradeRow {
  id: string;
  level: number;
  name: string;
  school_level_id: string | null;
  class_count: number;
}

export interface TreeClass {
  id: string;
  name: string;
  school_year: string;
  member_count: number;
}

export interface TreeGrade {
  id: string;
  level: number;
  name: string;
  class_count: number;
  student_count: number;
  classes: TreeClass[];
}

export interface TreeLevel {
  id: string;
  code: string;
  name: string;
  grade_from: number;
  grade_to: number;
  class_count: number;
  student_count: number;
  grades: TreeGrade[];
}

/** Cấp học › Khối › Lớp with counts (`GET /structure`). */
export interface Structure {
  levels: TreeLevel[];
  unassigned: TreeClass[];
}
