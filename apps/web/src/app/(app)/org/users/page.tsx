"use client";

import Link from "next/link";
import { useState } from "react";
import { useMe } from "@/app/(app)/AppShell";
import { TempPassword, UserCreateForm, UserEditForm } from "@/components/org/UserForm";
import { UserTable } from "@/components/org/UserTable";
import { Alert, Button, Empty, Input, Modal, PageHeader, Select } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { qs, useApi } from "@/lib/hooks";
import { type Credential, type Page, type SchoolClass, type User } from "@/lib/types";

export default function UsersPage() {
  const me = useMe();
  const [q, setQ] = useState("");
  const [role, setRole] = useState("");
  const [classId, setClassId] = useState("");
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);
  const [reset, setReset] = useState<Credential | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { data, reload } = useApi<Page<User>>(`/users${qs({ q, role, class_id: classId, page_size: 200 })}`);
  const { data: classes } = useApi<SchoolClass[]>("/classes");
  const className = (id: string) => classes?.find((c) => c.id === id)?.name ?? "";

  async function act(fn: () => Promise<unknown>) {
    setError(null);
    try {
      await fn();
      await reload();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
    }
  }

  return (
    <>
      <PageHeader
        title={me.role === "teacher" ? "Học sinh" : "Người dùng"}
        subtitle={data ? `${data.total} tài khoản` : undefined}
        actions={
          <>
            <Link href="/org/users/import">
              <Button>Nhập từ file</Button>
            </Link>
            <Button variant="primary" onClick={() => setCreating(true)}>
              Thêm tài khoản
            </Button>
          </>
        }
      />
      <div className="mb-4 flex flex-wrap gap-3">
        <Input placeholder="Tìm theo tên hoặc tên đăng nhập" className="max-w-xs" value={q} onChange={(e) => setQ(e.target.value)} />
        {me.role === "org_admin" && (
          <Select value={role} onChange={(e) => setRole(e.target.value)} aria-label="Vai trò">
            <option value="">Tất cả vai trò</option>
            <option value="student">Học sinh</option>
            <option value="teacher">Giáo viên</option>
            <option value="org_admin">Quản trị</option>
          </Select>
        )}
        <Select value={classId} onChange={(e) => setClassId(e.target.value)} aria-label="Lớp">
          <option value="">Tất cả lớp</option>
          {classes?.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name} ({c.school_year})
            </option>
          ))}
        </Select>
      </div>
      {error && <div className="mb-3"><Alert>{error}</Alert></div>}
      {data && data.items.length === 0 ? (
        <Empty>Chưa có tài khoản nào. Thêm từng người hoặc nhập từ file CSV/Excel.</Empty>
      ) : (
        data && (
          <UserTable
            users={data.items}
            meId={me.id}
            className={className}
            onEdit={setEditing}
            onReset={(u) =>
              window.confirm(`Đặt lại mật khẩu cho ${u.full_name}?`) &&
              act(async () => setReset(await api<Credential>(`/users/${u.id}/reset-password`, { method: "POST" })))
            }
            onToggle={(u) => act(() => api(`/users/${u.id}`, { method: "PATCH", body: { is_active: !u.is_active } }))}
          />
        )
      )}
      <Modal open={creating} title="Thêm tài khoản" onClose={() => (setCreating(false), void reload())}>
        <UserCreateForm myRole={me.role} orgCode={me.org.code} onDone={() => (setCreating(false), void reload())} />
      </Modal>
      <Modal open={!!editing} title="Sửa tài khoản" onClose={() => setEditing(null)}>
        {editing && <UserEditForm user={editing} myRole={me.role} onDone={() => (setEditing(null), void reload())} />}
      </Modal>
      <Modal open={!!reset} title="Đã đặt lại mật khẩu" onClose={() => setReset(null)}>
        {reset && <TempPassword username={reset.username} password={reset.temp_password} orgCode={me.org.code} />}
      </Modal>
    </>
  );
}
