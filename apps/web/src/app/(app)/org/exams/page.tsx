"use client";

import { ListLayout } from "@/components/app/ListLayout";
import { MasterDetail } from "@/components/app/MasterDetail";
import type { ColumnDef } from "@tanstack/react-table";
import { ExternalLink } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { FormAlert } from "@/components/app/FormAlert";
import { FormDialog } from "@/components/app/FormDialog";
import { FormField } from "@/components/app/FormField";
import { PageHeader } from "@/components/app/PageHeader";
import { DataTable } from "@/components/data-table/DataTable";
import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { useMutation } from "@/lib/hooks";
import { ExamPreviewDialog, ExamQuestionsTable } from "@/components/exams/ExamDetail";
import { type Exam } from "@/lib/types";
import { formatDateTime } from "@/lib/datetime";

function NewExamForm() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const m = useMutation();
  return (
    <form
      className="grid gap-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const exam = await m.run(() => api<Exam>("/exams", { body: { title } }));
        if (exam) router.push(`/org/exams/${exam.id}`);
      }}
    >
      {m.message && <FormAlert>{m.message}</FormAlert>}
      <FormField label="Tên đề" error={m.fields.title}>
        <Input placeholder="Kiểm tra 15 phút – Hàm số bậc hai" value={title} onChange={(e) => setTitle(e.target.value)} required autoFocus />
      </FormField>
      <DialogFooter>
        <Button type="submit" disabled={m.busy}>
          Tạo và soạn đề
        </Button>
      </DialogFooter>
    </form>
  );
}

export default function ExamsPage() {
  const router = useRouter();
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
  return (
    <>
      <ListLayout header={<PageHeader title="Đề thi & giao bài" description="Tạo đề từ ngân hàng câu hỏi theo ma trận hoặc chọn tay. Chọn một đề để xem câu hỏi bên dưới." />}>
        <MasterDetail
          id="exams"
          master={
            <DataTable
        path="/exams"
        columns={columns}
        getRowId={(e) => e.id}
        onAdd={() => setCreating(true)}
        addLabel="Tạo đề"
        onEdit={(e) => router.push(`/org/exams/${e.id}`)}
        onDelete={async (rows) => {
          for (const e of rows) await api(`/exams/${e.id}`, { method: "DELETE" });
          if (rows.some((e) => e.id === active?.id)) setActive(null);
        }}
        deleteLabel={(rows) => `Xóa ${rows.length} đề thi?`}
        onRowActivate={setActive}
        activeRowId={active?.id}
      />
          }
          detail={active  && (
            <Card className="flex h-full min-h-0 flex-col gap-2 py-3">
          <CardHeader className="px-3">
            <CardTitle>Chi tiết · {active.title}</CardTitle>
            <CardAction>
              <Button variant="outline" size="sm" asChild>
                <Link href={`/org/exams/${active.id}`}>
                  <ExternalLink /> Soạn đề & giao bài
                </Link>
              </Button>
            </CardAction>
          </CardHeader>
          <CardContent className="min-h-0 flex-1 px-3">
            <ExamQuestionsTable examId={active.id} />
          </CardContent>
        </Card>
          )}
        />
      </ListLayout>
      <ExamPreviewDialog examId={preview} onClose={() => setPreview(null)} />
      <FormDialog open={creating} onOpenChange={setCreating} title="Tạo đề mới">
        <NewExamForm />
      </FormDialog>
    </>
  );
}
