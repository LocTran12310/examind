import type { ColumnDef } from "@tanstack/react-table";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { useDeleteExamsMutation } from "@/hooks/react-query/use-query-exam";
import { useTaxonomyQuery } from "@/hooks/react-query/use-query-taxonomy";
import type { Exam } from "@/interfaces/exam.interface";
import { formatDateTime } from "@/lib/common/datetime";

/** Columns, the row chosen for the detail pane, the preview dialog (title click), create and delete of the exams page. */
export function useExamsPage() {
  const router = useRouter();
  const remove = useDeleteExamsMutation();
  const [creating, setCreating] = useState(false);
  const [active, setActive] = useState<Exam | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const { data: taxonomy } = useTaxonomyQuery();
  const subjects = useMemo(() => taxonomy?.subjects ?? [], [taxonomy]);

  const columns = useMemo<ColumnDef<Exam, unknown>[]>(
    () => [
      {
        accessorKey: "title",
        header: "Đề",
        // the title opens the whole exam in a dialog; the row itself shows its questions below
        cell: ({ row }) => (
          <Button
            type="button"
            variant="link"
            className="h-auto p-0 text-left font-medium whitespace-normal"
            onClick={(e) => {
              e.stopPropagation();
              setPreview(row.original.id);
            }}
          >
            {row.original.title}
          </Button>
        ),
        meta: { filter: { kind: "text" }, sort: "title" },
      },
      {
        // the exam carries a subject and the endpoint has always filtered by it; the list simply never showed it,
        // so a bank of two subjects would have been one undifferentiated pile of papers
        accessorKey: "subject_id",
        header: "Môn",
        cell: ({ row }) => subjects.find((s) => s.id === row.original.subject_id)?.name ?? <span className="text-muted-foreground">—</span>,
        meta: { filter: { kind: "select", options: subjects.map((s) => ({ value: s.id, label: s.name })) } },
      },
      { accessorKey: "grade", header: "Lớp", meta: { filter: { kind: "number" }, sort: "grade", align: "right" } },
      { accessorKey: "question_count", header: "Số câu", meta: { sort: "question_count", align: "right" } },
      { accessorKey: "total_points", header: "Tổng điểm", meta: { sort: "total_points", align: "right" } },
      { accessorKey: "created_at", header: "Tạo lúc", cell: ({ row }) => formatDateTime(row.original.created_at), meta: { filter: { kind: "date" }, sort: "created_at" } },
    ],
    [subjects],
  );

  return {
    columns,
    creating,
    setCreating,
    active,
    setActive,
    preview,
    closePreview: () => setPreview(null),
    edit: (e: Exam) => router.push(`/org/exams/${e.id}`),
    removeExams: async (rows: Exam[]) => {
      await remove.mutateAsync(rows.map((e) => e.id));
      if (rows.some((e) => e.id === active?.id)) setActive(null);
    },
  };
}
