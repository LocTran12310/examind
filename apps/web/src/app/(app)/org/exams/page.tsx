"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Alert, Button, Card, Empty, Input, PageHeader, Table, td, th } from "@/components/ui";
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
      <PageHeader title="Đề thi & giao bài" subtitle="Tạo đề từ ngân hàng câu hỏi theo ma trận hoặc chọn tay" />
      <Card className="mb-4">
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
          <Button variant="primary" type="submit">
            Tạo đề
          </Button>
        </form>
        {error && <div className="mt-2"><Alert>{error}</Alert></div>}
      </Card>
      {data && data.length === 0 && <Empty>Chưa có đề nào.</Empty>}
      {data && data.length > 0 && (
        <Table>
          <thead className="bg-gray-50">
            <tr>
              <th className={th}>Đề</th>
              <th className={th}>Số câu</th>
              <th className={th}>Tổng điểm</th>
              <th className={th}>Tạo lúc</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.map((e) => (
              <tr key={e.id}>
                <td className={td}>
                  <Link className="font-medium text-brand-700 hover:underline" href={`/org/exams/${e.id}`}>
                    {e.title}
                  </Link>
                </td>
                <td className={td}>{e.question_count}</td>
                <td className={td}>{e.total_points}</td>
                <td className={td}>{new Date(e.created_at).toLocaleDateString("vi-VN")}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </>
  );
}
