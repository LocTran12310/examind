import type { YearStatus } from "@/interfaces/school-year.interface";

export interface RecordYear {
  year: { id: string; code: string; status: YearStatus } | null;
  classes: { id: string; name: string; grade: number | null; status: string; status_label: string }[];
  answered: number;
  ratio: number | null;
  attempts: number;
  terms: Record<string, { answered: number; ratio: number | null }>;
  topics: { id: string; name: string; answered: number; ratio: number | null }[];
}

/** Hồ sơ học sinh (`GET /students/{id}/record`): one entry per school year, newest first. */
export interface StudentRecord {
  student: { id: string; username: string; full_name: string };
  years: RecordYear[];
}
