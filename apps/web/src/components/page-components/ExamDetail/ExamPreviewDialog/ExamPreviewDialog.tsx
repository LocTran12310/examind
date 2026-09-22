"use client";

import { ExternalLink } from "lucide-react";
import Link from "next/link";
import { FormDialog } from "@/components/app/FormDialog";
import { QuestionView } from "@/components/common/QuestionView/QuestionView";
import { Button } from "@/components/ui/button";
import { SECTION_LABEL } from "@/constants/exam.constant";
import { TYPE_LABEL } from "@/constants/question.constant";
import { useExamPreview } from "@/hooks/page-hooks/exam-detail/use-exam-preview";

/** The whole exam as students will read it (formulas, pictures, answers, solutions) — fetched on open. */
export function ExamPreviewDialog({ examId, onClose }: { examId: string | null; onClose: () => void }) {
  const { exam } = useExamPreview(examId);
  let section = "";
  return (
    <FormDialog open={!!examId} onOpenChange={(o) => !o && onClose()} title={exam?.title ?? "Đề thi"} description={exam ? `${exam.question_count} câu · ${exam.total_points} điểm` : undefined} wide>
      {!exam ? (
        <p className="text-sm text-muted-foreground">Đang tải…</p>
      ) : (
        <div className="grid gap-3">
          <div className="flex justify-end">
            <Button variant="outline" size="sm" asChild>
              <Link href={`/org/exams/${exam.id}`}>
                <ExternalLink /> Soạn đề & giao bài
              </Link>
            </Button>
          </div>
          {!exam.questions.length && <p className="text-sm text-muted-foreground">Đề chưa có câu hỏi.</p>}
          {exam.questions.map((q) => {
            const head = q.section !== section ? ((section = q.section), <h3 className="mt-2 text-sm font-semibold">{SECTION_LABEL[q.section] ?? q.section}</h3>) : null;
            return (
              <div key={q.id} className="grid gap-1">
                {head}
                <div className="rounded-lg border p-3" data-testid={`preview-q-${q.position}`}>
                  <p className="mb-1 text-xs text-muted-foreground">
                    Câu {q.position} · {TYPE_LABEL[q.type]} · {q.points} điểm
                  </p>
                  <QuestionView question={q} mode="review" />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </FormDialog>
  );
}
