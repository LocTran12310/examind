import type { ColumnDef } from "@tanstack/react-table";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { useDeleteExamsMutation, useExamFacetsQuery } from "@/hooks/react-query/use-query-exam";
import { useTaxonomyQuery } from "@/hooks/react-query/use-query-taxonomy";
import { useTableQuery } from "@/hooks/common/use-table-query";
import { toSearchBody } from "@/lib/common/search-body";
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
  // the same URL this page's table already reads, so the tab and the table cannot disagree about the scope
  const tq = useTableQuery();
  const subject = tq.apiParams.get("subject_id") ?? "";
  const params = useMemo(() => ({ subject_id: subject }), [subject]);
  // the numbers on the tabs: the rest of the search, without the scope in hand (a tab says what it would show)
  const { data: facets } = useExamFacetsQuery(toSearchBody(tq.apiParams, { title: "text", grade: "number", created_at: "date" }));

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
        // the column says which subject a paper is for; narrowing by subject is the tabs' job, and two ways to
        // say the same thing is two ways for them to disagree
        cell: ({ row }) => subjects.find((s) => s.id === row.original.subject_id)?.name ?? <span className="text-muted-foreground">—</span>,
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
    subjects,
    subject,
    params,
    facets,
    chooseSubject: (id: string) => tq.setFilters({ subject_id: id }),
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
