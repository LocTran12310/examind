"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { DataTable } from "@/components/common/DataTable/DataTable";
import { Markdown } from "@/components/common/Markdown/Markdown";
import { SECTION_LABEL, SECTION_OPTIONS } from "@/constants/exam.constant";
import { TYPE_LABEL } from "@/constants/question.constant";
import { useExamQuestionsTable } from "@/hooks/page-hooks/exam-detail/use-exam-questions-table";
import { useExamQuestionSearchQuery } from "@/hooks/react-query/use-query-exam";
import type { ExamQuestion } from "@/interfaces/exam.interface";

const COLUMNS: ColumnDef<ExamQuestion, unknown>[] = [
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
    meta: { filter: { kind: "select", options: SECTION_OPTIONS }, sort: "section", className: "w-24" },
  },
  {
    accessorKey: "type",
    header: "Loại",
    cell: ({ row }) => TYPE_LABEL[row.original.type],
    meta: { filter: { kind: "select", options: Object.entries(TYPE_LABEL).map(([value, label]) => ({ value, label })) }, className: "w-32" },
  },
  { accessorKey: "points", header: "Điểm", meta: { sort: "points", align: "right", className: "w-16" } },
];

/** One exam's questions in the shared server-side table (no toolbar); fetched only when an exam is chosen. */
export function ExamQuestionsTable({ examId }: { examId: string }) {
  const { params } = useExamQuestionsTable(examId);
  return (
    <DataTable
      key={examId}
      useRows={useExamQuestionSearchQuery}
      params={params}
      prefix="q."
      columns={COLUMNS}
      getRowId={(q) => q.id}
      selectable={false}
      toolbar={false}
      emptyText="Đề chưa có câu hỏi."
    />
  );
}
