"use client";

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
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import { useApi, useMutation } from "@/lib/hooks";
import { type Exam, TYPE_LABEL } from "@/lib/types";

const plain = (md: string) => md.replace(/!\[[^\]]*\]\([^)]*\)/g, "[hình]").replace(/\$([^$]*)\$/g, "$1").replace(/\s+/g, " ").trim();

function ExamDetail({ id }: { id: string }) {
  const { data } = useApi<Exam>(`/exams/${id}`);
  if (!data) return <p className="text-sm text-muted-foreground">Đang tải…</p>;
  if (!data.questions.length) return <p className="text-sm text-muted-foreground">Đề chưa có câu hỏi.</p>;
  return (
    <div className="rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">#</TableHead>
            <TableHead>Câu hỏi</TableHead>
            <TableHead>Loại</TableHead>
            <TableHead className="text-right">Điểm</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.questions.map((q) => (
            <TableRow key={q.id}>
              <TableCell className="tabular-nums">{q.position}</TableCell>
              <TableCell className="max-w-xl truncate">{plain(q.stem)}</TableCell>
              <TableCell>{TYPE_LABEL[q.type]}</TableCell>
              <TableCell className="text-right tabular-nums">{q.points}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

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
  const columns = useMemo<ColumnDef<Exam, unknown>[]>(
    () => [
      { accessorKey: "title", header: "Đề", cell: ({ row }) => <span className="font-medium">{row.original.title}</span>, meta: { filter: { kind: "text" }, sort: "title" } },
      { accessorKey: "grade", header: "Lớp", meta: { filter: { kind: "number" }, sort: "grade", align: "right" } },
      { accessorKey: "question_count", header: "Số câu", meta: { sort: "question_count", align: "right" } },
      { accessorKey: "total_points", header: "Tổng điểm", meta: { sort: "total_points", align: "right" } },
      { accessorKey: "created_at", header: "Tạo lúc", cell: ({ row }) => new Date(row.original.created_at).toLocaleDateString("vi-VN"), meta: { filter: { kind: "date" }, sort: "created_at" } },
    ],
    [],
  );
  return (
    <>
      <PageHeader title="Đề thi & giao bài" description="Tạo đề từ ngân hàng câu hỏi theo ma trận hoặc chọn tay. Chọn một đề để xem câu hỏi bên dưới." />
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
      {active && (
        <Card className="mt-4">
          <CardHeader>
            <CardTitle>Chi tiết · {active.title}</CardTitle>
            <CardAction>
              <Button variant="outline" size="sm" asChild>
                <Link href={`/org/exams/${active.id}`}>
                  <ExternalLink /> Soạn đề & giao bài
                </Link>
              </Button>
            </CardAction>
          </CardHeader>
          <CardContent>
            <ExamDetail id={active.id} />
          </CardContent>
        </Card>
      )}
      <FormDialog open={creating} onOpenChange={setCreating} title="Tạo đề mới">
        <NewExamForm />
      </FormDialog>
    </>
  );
}
