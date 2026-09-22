import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import { STUDENT_KEYS } from "@/constants/react-query-key.constant";
import type { StudentRecord } from "@/interfaces/student-record.interface";
import { studentService } from "@/services/student.service";

export function useStudentRecordQuery(id: string): UseQueryResult<StudentRecord, Error> {
  return useQuery<StudentRecord, Error>({ queryKey: STUDENT_KEYS.RECORD(id), queryFn: () => studentService.record(id) });
}
