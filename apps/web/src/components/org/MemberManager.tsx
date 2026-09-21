"use client";

import { useState } from "react";
import { Alert, Button, Card, Empty, Input, Table, td, th } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { qs, useApi } from "@/lib/hooks";
import type { ClassDetail, Page, User } from "@/lib/types";

export function MemberManager({ detail, onChange }: { detail: ClassDetail; onChange: () => void }) {
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);
  const { data: candidates } = useApi<Page<User>>(q.length >= 2 ? `/users${qs({ q, role: "student", page_size: 20 })}` : null);
  const memberIds = new Set(detail.members.map((m) => m.id));

  async function run(fn: () => Promise<unknown>) {
    setError(null);
    try {
      await fn();
      onChange();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
    }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
      <div>
        {error && <div className="mb-3"><Alert>{error}</Alert></div>}
        {detail.members.length === 0 ? (
          <Empty>Lớp chưa có học sinh.</Empty>
        ) : (
          <Table>
            <thead className="bg-gray-50">
              <tr>
                <th className={th}>Họ tên</th>
                <th className={th}>Tên đăng nhập</th>
                <th className={th} />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {detail.members.map((m) => (
                <tr key={m.id} data-testid={`member-${m.username}`}>
                  <td className={td}>{m.full_name}</td>
                  <td className={`${td} font-mono`}>{m.username}</td>
                  <td className={`${td} text-right`}>
                    <Button size="sm" variant="danger" onClick={() => run(() => api(`/classes/${detail.id}/members/${m.id}`, { method: "DELETE" }))}>
                      Xóa khỏi lớp
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </div>
      <Card>
        <h2 className="mb-2 font-medium">Thêm học sinh</h2>
        <Input placeholder="Tìm tên hoặc tên đăng nhập" value={q} onChange={(e) => setQ(e.target.value)} />
        <ul className="mt-3 divide-y divide-gray-100">
          {candidates?.items
            .filter((u) => !memberIds.has(u.id))
            .map((u) => (
              <li key={u.id} className="flex items-center justify-between py-2 text-sm">
                <span>
                  {u.full_name} <span className="font-mono text-gray-500">{u.username}</span>
                </span>
                <Button size="sm" onClick={() => run(() => api(`/classes/${detail.id}/members`, { body: { user_ids: [u.id] } }))}>
                  Thêm
                </Button>
              </li>
            ))}
        </ul>
      </Card>
    </div>
  );
}
