import type { ClassReviewBody, StartPracticeBody } from "@/dtos/practice.dto";
import type { MasteryRow } from "@/interfaces/mastery.interface";
import type { PracticeItem, PracticeStarted } from "@/interfaces/practice.interface";
import { http } from "@/lib/common/http";

/** Mastery and personal review exams (analytics). */
export const practiceService = {
  myMastery: () => http<MasteryRow[]>("/me/mastery"),
  start: (body: StartPracticeBody) => http<PracticeStarted>("/me/practice", { body }),
  history: () => http<PracticeItem[]>("/me/practice"),
  assignClass: (classId: string, body: ClassReviewBody) => http<{ created: number }>(`/classes/${classId}/adaptive-assignments`, { body }),
};
