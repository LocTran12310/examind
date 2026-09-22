import type { ColumnDef } from "@tanstack/react-table";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { useDeleteExamsMutation } from "@/hooks/react-query/use-query-exam";
import type { Exam } from "@/interfaces/exam.interface";
import { formatDateTime } from "@/lib/datetime";

/** Columns, the row chosen for the detail pane, the preview dialog (title click), create and delete of the exams page. */
export function useExamsPage() {
  const router = useRouter();
  const remove = useDeleteExamsMutation();
  const [creating, setCreating] = useState(false);
  const [active, setActive] = useState<Exam | null>(null);
  const [preview, setPreview] = useState<string | null>(null);

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
      { accessorKey: "grade", header: "Lớp", meta: { filter: { kind: "number" }, sort: "grade", align: "right" } },
      { accessorKey: "question_count", header: "Số câu", meta: { sort: "question_count", align: "right" } },
      { accessorKey: "total_points", header: "Tổng điểm", meta: { sort: "total_points", align: "right" } },
      { accessorKey: "created_at", header: "Tạo lúc", cell: ({ row }) => formatDateTime(row.original.created_at), meta: { filter: { kind: "date" }, sort: "created_at" } },
    ],
    [],
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
