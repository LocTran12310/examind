"use client";

import { useExamRunnerPage } from "@/hooks/page-hooks/exam-runner/use-exam-runner-page";
import { Runner } from "./Runner/Runner";

export function ExamRunnerPage({ id }: { id: string }) {
  const p = useExamRunnerPage(id);
  if (p.error) return <p className="text-sm text-destructive">{p.error}</p>;
  if (!p.view) return null;
  return <Runner view={p.view} onFinished={p.finished} />;
}
