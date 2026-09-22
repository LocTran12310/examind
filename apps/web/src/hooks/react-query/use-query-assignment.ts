import { useMutation, useQuery, useQueryClient, type UseMutationResult, type UseQueryResult } from "@tanstack/react-query";
import { ASSIGNMENT_KEYS, ATTEMPT_KEYS } from "@/constants/react-query-key.constant";
import type { CreateAssignmentBody } from "@/dtos/assignment.dto";
import type { SearchBody } from "@/dtos/search.dto";
import type { Assignment, AssignmentReport, MyAssignment, StartedAttempt } from "@/interfaces/assignment.interface";
import type { RowsQueryOptions, SearchPage } from "@/interfaces/search-page.interface";
import { invalidate } from "@/lib/common/query-client";
import { LIMIT_ALL } from "@/lib/common/search-body";
import { assignmentService } from "@/services/assignment.service";
import { useSearchQuery } from "./use-search-query";

export function useAssignmentSearchQuery(body: SearchBody, options?: RowsQueryOptions<Assignment>): UseQueryResult<SearchPage<Assignment>, Error> {
  return useSearchQuery(ASSIGNMENT_KEYS.SEARCH(body), assignmentService.search, body, options);
}

/** Every assignment of one exam (the "Đã giao" list of the exam page). */
export function useExamAssignmentsQuery(examId: string): UseQueryResult<Assignment[], Error> {
  const body: SearchBody = { page: 1, limit: LIMIT_ALL, filters: { exam_id: { value: examId } } };
  return useQuery<Assignment[], Error>({
    queryKey: ASSIGNMENT_KEYS.SEARCH(body),
    queryFn: async () => (await assignmentService.search(body)).data,
  });
}

export function useAssignmentReportQuery(id: string): UseQueryResult<AssignmentReport, Error> {
  return useQuery<AssignmentReport, Error>({ queryKey: ASSIGNMENT_KEYS.REPORT(id), queryFn: () => assignmentService.report(id) });
}

/** The signed-in student's assignments. */
export function useMyAssignmentsQuery(): UseQueryResult<MyAssignment[], Error> {
  return useQuery<MyAssignment[], Error>({ queryKey: ASSIGNMENT_KEYS.MINE, queryFn: assignmentService.mine });
}

export function useCreateAssignmentMutation(): UseMutationResult<Assignment, Error, CreateAssignmentBody> {
  const qc = useQueryClient();
  return useMutation<Assignment, Error, CreateAssignmentBody>({
    mutationFn: assignmentService.create,
    onSuccess: () => invalidate(qc, ASSIGNMENT_KEYS.ALL),
  });
}

/** Start or resume an attempt: the student's list and the attempts change. */
export function useStartAssignmentMutation(): UseMutationResult<StartedAttempt, Error, string> {
  const qc = useQueryClient();
  return useMutation<StartedAttempt, Error, string>({
    mutationFn: assignmentService.start,
    onSuccess: () => invalidate(qc, ASSIGNMENT_KEYS.ALL, ATTEMPT_KEYS.ALL),
  });
}
