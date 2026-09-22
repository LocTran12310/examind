export interface LevelBody {
  code: string;
  name: string;
  grade_from: number;
  grade_to: number;
}

export interface GradeBody {
  level: number;
  name: string | null;
  school_level_id: string;
}
