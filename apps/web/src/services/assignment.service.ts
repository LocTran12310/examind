import type { CreateAssignmentBody } from "@/dtos/assignment.dto";
import type { SearchBody } from "@/dtos/search.dto";
import type { Assignment, AssignmentReport, MyAssignment, StartedAttempt } from "@/interfaces/assignment.interface";
import type { SearchPage } from "@/interfaces/search-page.interface";
import { http } from "@/lib/common/http";

export const assignmentService = {
  search: (body: SearchBody) => http<SearchPage<Assignment>>("/assignments/search", { body }),
  get: (id: string) => http<Assignment>(`/assignments/${id}`),
  create: (body: CreateAssignmentBody) => http<Assignment>("/assignments", { body }),
  remove: (id: string) => http<void>(`/assignments/${id}`, { method: "DELETE" }),
  report: (id: string) => http<AssignmentReport>(`/assignments/${id}/report`),
  /** The signed-in student's assignments with their attempts (a plain list). */
  mine: () => http<MyAssignment[]>("/me/assignments"),
  /** Start (or resume) an attempt. */
  start: (id: string) => http<StartedAttempt>(`/assignments/${id}/start`, { method: "POST" }),
};
