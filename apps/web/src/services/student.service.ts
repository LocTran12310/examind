import type { StudentRecord } from "@/interfaces/student-record.interface";
import { http } from "@/lib/common/http";

export const studentService = {
  record: (id: string) => http<StudentRecord>(`/students/${id}/record`),
};
