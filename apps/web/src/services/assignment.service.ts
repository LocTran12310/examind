import type { CreateAssignmentBody, TrialBody } from "@/dtos/assignment.dto";
import type { SearchBody } from "@/dtos/search.dto";
import type { Assignment, AssignmentPaper, AssignmentReport, MyAssignment, StartedAttempt } from "@/interfaces/assignment.interface";
import type { AttemptResult } from "@/interfaces/attempt.interface";
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
  /** The paper with no attempt behind it — what a trial run is sat from. */
  paper: (id: string) => http<AssignmentPaper>(`/assignments/${id}/paper`),
  /** A trial run graded in memory, in the shape of an attempt's result; nothing is written (exam-runner ADR-01). */
  trial: (id: string, body: TrialBody) => http<AttemptResult>(`/assignments/${id}/trial`, { body }),
};
