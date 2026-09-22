"use client";

import { ListLayout } from "@/components/app/ListLayout";
import type { ColumnDef } from "@tanstack/react-table";
import { Download, KeyRound, Link2, Lock, LockOpen, Unlink, Upload } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { useMe } from "@/app/(app)/AppShell";
import { ConfirmDialog } from "@/components/app/ConfirmDialog";
import { FormDialog } from "@/components/app/FormDialog";
import { PageHeader } from "@/components/app/PageHeader";
import { ToneBadge } from "@/components/app/ToneBadge";
import { DataTable } from "@/components/data-table/DataTable";
import { ToolbarButton } from "@/components/common/DataTable/Toolbar";
import { useTableQuery } from "@/hooks/common/use-table-query";
import { LinkAccountForm } from "@/components/org/LinkAccountForm";
import { TempPassword, UserCreateForm, UserEditForm } from "@/components/org/UserForm";
import { api, ApiError } from "@/lib/api";
import { downloadText, toCsv } from "@/lib/csv";
import { fmt } from "@/lib/dates";
import { useApi } from "@/lib/hooks";
import { type Credential, type Page, ROLE_LABEL, type SchoolClass, type User } from "@/lib/types";

function status(u: User) {
  if (!u.is_active) return <ToneBadge tone="red">Đã khóa</ToneBadge>;
  if (u.must_change_password) return <ToneBadge tone="amber">Chờ đổi mật khẩu</ToneBadge>;
  return <ToneBadge tone="green">Hoạt động</ToneBadge>;
}

export default function UsersPage() {
  const me = useMe();
  const tq = useTableQuery();
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);
  const [resetFor, setResetFor] = useState<User | null>(null);
  const [reset, setReset] = useState<Credential | null>(null);
  const [linking, setLinking] = useState(false);
  const [unlinking, setUnlinking] = useState<User[] | null>(null);
  const [version, setVersion] = useState(0);
  const { data: classes } = useApi<Page<SchoolClass>>("/classes?page_size=all");
  const classById = useMemo(() => new Map(classes?.items.map((c) => [c.id, c]) ?? []), [classes]);
  const refresh = () => setVersion((v) => v + 1);

  const columns = useMemo<ColumnDef<User, unknown>[]>(
    () => [
      {
        accessorKey: "full_name",
        header: "Họ tên",
        cell: ({ row }) => (
          <span className="inline-flex items-center gap-2">
            {row.original.role === "student" ? (
              <Link href={`/org/students/${row.original.id}`} className="text-primary hover:underline">
                {row.original.full_name}
              </Link>
            ) : (
              row.original.full_name
            )}
            {row.original.is_home === false && <ToneBadge tone="blue">Từ {row.original.home_org_code}</ToneBadge>}
          </span>
        ),
        meta: { filter: { kind: "text" }, sort: "full_name" },
      },
      { accessorKey: "username", header: "Tên đăng nhập", cell: ({ row }) => <span className="font-mono">{row.original.username}</span>, meta: { filter: { kind: "text" }, sort: "username" } },
      ...(me.role === "org_admin"
        ? [
            {
              accessorKey: "role",
              header: "Vai trò",
              cell: ({ row }) => ROLE_LABEL[row.original.role],
              meta: { filter: { kind: "select", options: (["student", "teacher", "org_admin"] as const).map((r) => ({ value: r, label: ROLE_LABEL[r] })) }, sort: "role" },
            } satisfies ColumnDef<User, unknown>,
          ]
        : []),
      {
        id: "class_id",
        header: "Lớp",
        cell: ({ row }) => row.original.class_ids.map((id) => classById.get(id)?.name).filter(Boolean).join(", "),
        meta: { filter: { kind: "select", options: (classes?.items ?? []).map((c) => ({ value: c.id, label: `${c.name} (${c.school_year})` })) } },
      },
      { accessorKey: "is_active", header: "Trạng thái", cell: ({ row }) => status(row.original), meta: { filter: { kind: "select", options: [{ value: "true", label: "Hoạt động" }, { value: "false", label: "Đã khóa" }] } } },
      {
        accessorKey: "last_login_at",
        header: "Đăng nhập gần nhất",
        cell: ({ row }) => fmt(row.original.last_login_at),
        meta: { filter: { kind: "date" }, sort: "last_login_at" },
      },
    ],
    [me.role, classes, classById],
  );

  async function setActive(users: User[], active: boolean) {
    try {
      for (const u of users.filter((u) => u.id !== me.id)) await api(`/users/${u.id}`, { method: "PATCH", body: { is_active: active } });
      toast.success(active ? "Đã mở khóa" : "Đã khóa");
      refresh();
    } catch (e) {
      toast.error(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
    }
  }

  async function exportCsv() {
    const q = new URLSearchParams(tq.apiParams);
    q.set("page", "1");
    q.set("page_size", "all");
    const page = await api<Page<User>>(`/users?${q}`);
    const rows = page.items.map((u) => ({ full_name: u.full_name, username: u.username, email: u.email ?? "", role: ROLE_LABEL[u.role], classes: u.class_ids.map((id) => classById.get(id)?.name).join(" ") }));
    downloadText("nguoi-dung.csv", toCsv(rows, [["full_name", "Họ tên"], ["username", "Tên đăng nhập"], ["email", "Email"], ["role", "Vai trò"], ["classes", "Lớp"]]));
  }

  return (
    <>
      <ListLayout header={<PageHeader title={me.role === "teacher" ? "Học sinh" : "Người dùng"} />}>
        <DataTable
          path="/users"
          columns={columns}
          getRowId={(u) => u.id}
          reloadKey={version}
          onAdd={() => setCreating(true)}
          onEdit={setEditing}
          actions={({ selected }) => (
            <>
              <ToolbarButton disabled={selected.length !== 1 || selected[0].is_home === false} onClick={() => setResetFor(selected[0])}>
                <KeyRound /> Đặt lại mật khẩu
              </ToolbarButton>
              <ToolbarButton disabled={!selected.some((u) => u.is_active && u.id !== me.id)} onClick={() => void setActive(selected, false)}>
                <Lock /> Khóa
              </ToolbarButton>
              <ToolbarButton disabled={!selected.some((u) => !u.is_active)} onClick={() => void setActive(selected, true)}>
                <LockOpen /> Mở khóa
              </ToolbarButton>
              {me.role === "org_admin" && (
                <>
                  <ToolbarButton onClick={() => setLinking(true)}>
                    <Link2 /> Thêm tài khoản có sẵn
                  </ToolbarButton>
                  <ToolbarButton disabled={!selected.some((u) => u.is_home === false)} onClick={() => setUnlinking(selected.filter((u) => u.is_home === false))}>
                    <Unlink /> Gỡ khỏi tổ chức
                  </ToolbarButton>
                </>
              )}
              <ToolbarButton asChild>
                <Link href="/org/users/import">
                  <Upload /> Nhập khẩu
                </Link>
              </ToolbarButton>
              <ToolbarButton onClick={() => void exportCsv()}>
                <Download /> Xuất khẩu
              </ToolbarButton>
            </>
          )}
          emptyText="Chưa có tài khoản nào. Thêm từng người hoặc nhập từ file CSV/Excel."
        />
      </ListLayout>
      <FormDialog open={creating} onOpenChange={(o) => (setCreating(o), o || refresh())} title="Thêm tài khoản">
        <UserCreateForm myRole={me.role} orgCode={me.org.code} onDone={() => (setCreating(false), refresh())} />
      </FormDialog>
      <FormDialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)} title="Sửa tài khoản">
        {editing && <UserEditForm user={editing} myRole={me.role} onDone={() => (setEditing(null), refresh())} />}
      </FormDialog>
      <ConfirmDialog
        open={!!resetFor}
        onOpenChange={(o) => !o && setResetFor(null)}
        title={`Đặt lại mật khẩu cho ${resetFor?.full_name ?? ""}?`}
        description="Mật khẩu cũ và mọi phiên đăng nhập của người này sẽ bị hủy."
        confirmLabel="Đặt lại"
        onConfirm={async () => {
          const u = resetFor!;
          setResetFor(null);
          try {
            setReset(await api<Credential>(`/users/${u.id}/reset-password`, { method: "POST" }));
          } catch (e) {
            toast.error(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
          }
        }}
      />
      <FormDialog open={linking} onOpenChange={setLinking} title="Thêm tài khoản từ tổ chức khác">
        <LinkAccountForm
          onDone={(u) => {
            setLinking(false);
            toast.success(`Đã thêm ${u.full_name}`);
            refresh();
          }}
        />
      </FormDialog>
      <ConfirmDialog
        open={!!unlinking}
        onOpenChange={(o) => !o && setUnlinking(null)}
        destructive
        title={`Gỡ ${unlinking?.length ?? 0} tài khoản khỏi tổ chức?`}
        description="Tài khoản vẫn dùng được ở tổ chức gốc; họ sẽ rời các lớp của tổ chức này."
        confirmLabel="Gỡ"
        onConfirm={async () => {
          const rows = unlinking ?? [];
          setUnlinking(null);
          try {
            for (const u of rows) await api(`/users/${u.id}/membership`, { method: "DELETE" });
            refresh();
          } catch (e) {
            toast.error(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
          }
        }}
      />
      <FormDialog open={!!reset} onOpenChange={(o) => !o && setReset(null)} title="Đã đặt lại mật khẩu">
        {reset && <TempPassword username={reset.username} password={reset.temp_password} orgCode={me.org.code} />}
      </FormDialog>
    </>
  );
}
