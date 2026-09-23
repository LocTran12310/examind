import { useMemo } from "react";
import type { Exam } from "@/interfaces/exam.interface";
import { examWeighting, type Weighting } from "@/lib/page-libs/exam-detail/weighting";

/** The weighting of the exam as shown by the strip: per part, the raw total and the scaled one. */
export function useExamWeighting(exam: Pick<Exam, "questions" | "settings">): Weighting {
  return useMemo(() => examWeighting(exam), [exam]);
}
