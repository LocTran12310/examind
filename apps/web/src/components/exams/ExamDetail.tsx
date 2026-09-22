"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { ExternalLink } from "lucide-react";
import Link from "next/link";
import { useMemo } from "react";
import { FormDialog } from "@/components/app/FormDialog";
import { DataTable } from "@/components/data-table/DataTable";
import { Markdown } from "@/components/question/Markdown";
import { QuestionView } from "@/components/question/QuestionView";
import { Button } from "@/components/ui/button";
import { useApi } from "@/lib/hooks";
import { type Exam, type ExamQuestion, TYPE_LABEL } from "@/lib/types";

const SECTION_LABEL: Record<string, string> = { I: "Phần I", II: "Phần II", III: "Phần III", IV: "Phần IV" };

/** One exam's questions in the shared server-side table (no toolbar); fetched only when an exam is chosen. */
export function ExamQuestionsTable({ examId }: { examId: string }) {
  const columns = useMemo<ColumnDef<ExamQuestion, unknown>[]>(
    () => [
      { accessorKey: "position", header: "#", meta: { sort: "position", align: "right", className: "w-12" } },
      {
        accessorKey: "stem",
        header: "Câu hỏi",
        // rendered: formulas, emphasis and pictures, not raw markdown
        cell: ({ row }) => <Markdown className="line-clamp-4 max-w-4xl text-sm [&_img]:max-h-40">{row.original.stem}</Markdown>,
        meta: { filter: { kind: "text", placeholder: "Tìm trong đề bài…" } },
      },
      {
        accessorKey: "section",
        header: "Phần",
        cell: ({ row }) => SECTION_LABEL[row.original.section] ?? row.original.section,
        meta: { filter: { kind: "select", options: Object.entries(SECTION_LABEL).map(([value, label]) => ({ value, label })) }, sort: "section", className: "w-24" },
      },
      {
        accessorKey: "type",
        header: "Loại",
        cell: ({ row }) => TYPE_LABEL[row.original.type],
        meta: { filter: { kind: "select", options: Object.entries(TYPE_LABEL).map(([value, label]) => ({ value, label })) }, className: "w-32" },
      },
      { accessorKey: "points", header: "Điểm", meta: { sort: "points", align: "right", className: "w-16" } },
    ],
    [],
  );
  return <DataTable key={examId} path={`/exams/${examId}/questions`} prefix="q." columns={columns} getRowId={(q) => q.id} selectable={false} toolbar={false} emptyText="Đề chưa có câu hỏi." />;
}

/** The whole exam as students will read it (formulas, pictures, answers, solutions) — fetched on open. */
export function ExamPreviewDialog({ examId, onClose }: { examId: string | null; onClose: () => void }) {
  const { data } = useApi<Exam>(examId ? `/exams/${examId}` : null);
  const exam = data && data.id === examId ? data : null;
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
