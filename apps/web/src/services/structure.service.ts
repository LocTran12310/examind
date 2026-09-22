import type { SearchBody } from "@/dtos/search.dto";
import type { GradeBody, LevelBody } from "@/dtos/structure.dto";
import type { SearchPage } from "@/interfaces/search-page.interface";
import type { GradeRow, SchoolLevel, Structure } from "@/interfaces/structure.interface";
import { http } from "@/lib/common/http";

export const structureService = {
  /** The Cấp học › Khối › Lớp tree for one year's classes (all years when `yearId` is empty). */
  tree: (yearId?: string | null) => http<Structure>(yearId ? `/structure?school_year_id=${encodeURIComponent(yearId)}` : "/structure"),
  searchLevels: (body: SearchBody) => http<SearchPage<SchoolLevel>>("/school-levels/search", { body }),
  createLevel: (body: LevelBody) => http<SchoolLevel>("/school-levels", { body }),
  updateLevel: (id: string, body: LevelBody) => http<SchoolLevel>(`/school-levels/${id}`, { method: "PATCH", body }),
  removeLevel: (id: string) => http<void>(`/school-levels/${id}`, { method: "DELETE" }),
  searchGrades: (body: SearchBody) => http<SearchPage<GradeRow>>("/grades/search", { body }),
  createGrade: (body: GradeBody) => http<GradeRow>("/grades", { body }),
  updateGrade: (id: string, body: GradeBody) => http<GradeRow>(`/grades/${id}`, { method: "PATCH", body }),
  removeGrade: (id: string) => http<void>(`/grades/${id}`, { method: "DELETE" }),
};
