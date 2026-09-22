"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { FormAlert } from "@/components/app/FormAlert";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/app/Panel";
import { EmptyState } from "@/components/app/EmptyState";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/app/PageHeader";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api, ApiError } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type { Exam } from "@/lib/types";

export default function ExamsPage() {
  const router = useRouter();
  const { data } = useApi<Exam[]>("/exams");
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  return (
    <>
      <PageHeader title="Đề thi & giao bài" description="Tạo đề từ ngân hàng câu hỏi theo ma trận hoặc chọn tay" />
      <Panel className="mb-4">
        <form
          className="flex gap-2"
          onSubmit={async (e) => {
            e.preventDefault();
            try {
              const exam = await api<Exam>("/exams", { body: { title } });
              router.push(`/org/exams/${exam.id}`);
            } catch (err) {
              setError(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
            }
          }}
        >
          <Input placeholder="Tên đề mới, ví dụ: Kiểm tra 15 phút – Hàm số bậc hai" value={title} onChange={(e) => setTitle(e.target.value)} required />
          <Button type="submit">
            Tạo đề
          </Button>
        </form>
        {error && <div className="mt-2"><FormAlert>{error}</FormAlert></div>}
      </Panel>
      {data && data.length === 0 && <EmptyState>Chưa có đề nào.</EmptyState>}
      {data && data.length > 0 && (
        <div className="rounded-lg border bg-card">
<Table>
          <TableHeader>
            <TableRow>
              <TableHead>Đề</TableHead>
              <TableHead>Số câu</TableHead>
              <TableHead>Tổng điểm</TableHead>
              <TableHead>Tạo lúc</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((e) => (
              <TableRow key={e.id}>
                <TableCell>
                  <Link className="font-medium text-primary hover:underline" href={`/org/exams/${e.id}`}>
                    {e.title}
                  </Link>
                </TableCell>
                <TableCell>{e.question_count}</TableCell>
                <TableCell>{e.total_points}</TableCell>
                <TableCell>{new Date(e.created_at).toLocaleDateString("vi-VN")}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
</div>
      )}
    </>
  );
}
