export interface Taxonomy {
  subjects: { id: string; code: string; name: string }[];
  grades: { id: string; level: number; name: string; school_level_id?: string | null; school_level_name?: string | null }[];
  semesters: { id: string; code: string; name: string }[];
}
