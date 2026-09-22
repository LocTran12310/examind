"use client";

import { ListLayout } from "@/components/app/ListLayout";
import { MasterDetail } from "@/components/app/MasterDetail";
import type { ColumnDef } from "@tanstack/react-table";
import { LogIn, Lock, LockOpen } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/app/ConfirmDialog";
import { FormDialog } from "@/components/app/FormDialog";
import { PageHeader } from "@/components/app/PageHeader";
import { ToneBadge } from "@/components/app/ToneBadge";
import { MembershipTable } from "@/components/admin/MembershipTable";
import { OrgCreateForm, OrgEditForm } from "@/components/admin/OrgForm";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DataTable } from "@/components/data-table/DataTable";
import { ToolbarButton } from "@/components/data-table/Toolbar";
import { useTableQuery } from "@/components/data-table/useTableQuery";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { api, ApiError } from "@/lib/api";
import type { Org } from "@/lib/types";

type Action = "suspend" | "activate";
const CONFIRM: Record<Action, string> = {
  suspend: "Khóa tổ chức? Người dùng của tổ chức sẽ không đăng nhập được.",
  activate: "Mở khóa tổ chức?",
};

function status(o: Org) {
  return (
    <span className="inline-flex gap-1">
      {o.deleted_at ? <ToneBadge tone="red">Đã xóa</ToneBadge> : o.status === "active" ? <ToneBadge tone="green">Hoạt động</ToneBadge> : <ToneBadge tone="amber">Tạm khóa</ToneBadge>}
      {o.is_system && <ToneBadge tone="blue">Hệ thống</ToneBadge>}
    </span>
  );
}

export default function OrgsPage() {
  const tq = useTableQuery();
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<Org | null>(null);
  const [pending, setPending] = useState<{ action: Action; orgs: Org[] } | null>(null);
  const [version, setVersion] = useState(0);
  const [active, setActive] = useState<Org | null>(null);
  const refresh = () => setVersion((v) => v + 1);
  const editable = (o: Org) => !o.is_system && !o.deleted_at;

  const columns = useMemo<ColumnDef<Org, unknown>[]>(
    () => [
      { accessorKey: "code", header: "Mã", cell: ({ row }) => <span className="font-mono">{row.original.code}</span>, meta: { filter: { kind: "text" }, sort: "code" } },
      { accessorKey: "name", header: "Tên tổ chức", meta: { filter: { kind: "text" }, sort: "name" } },
      {
        accessorKey: "status",
        header: "Trạng thái",
        cell: ({ row }) => status(row.original),
        meta: { filter: { kind: "select", options: [{ value: "active", label: "Hoạt động" }, { value: "suspended", label: "Tạm khóa" }] } },
      },
      { accessorKey: "user_count", header: "Người dùng", meta: { align: "right" } },
      { accessorKey: "created_at", header: "Ngày tạo", cell: ({ row }) => new Date(row.original.created_at).toLocaleDateString("vi-VN"), meta: { filter: { kind: "date" }, sort: "created_at" } },
    ],
    [],
  );

  async function enter(o: Org) {
    try {
      await api("/auth/switch-org", { body: { org_id: o.id } });
      window.location.assign(o.is_system ? "/admin/orgs" : "/org/users");
    } catch (e) {
      toast.error(e instanceof ApiError ? e.message : "Không vào được tổ chức");
    }
  }

  async function run(action: Action | "delete", orgs: Org[]) {
    try {
      for (const o of orgs.filter(editable)) {
        if (action === "delete") await api(`/admin/orgs/${o.id}`, { method: "DELETE" });
        else await api(`/admin/orgs/${o.id}/${action}`, { method: "POST" });
      }
      refresh();
    } catch (e) {
      toast.error(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
    }
  }

  return (
    <>
      <ListLayout header={<PageHeader
        title="Tổ chức"
        description="Chọn một tổ chức để quản lý thành viên bên dưới."
        actions={
          <div className="flex items-center gap-2">
            <Switch id="show-deleted" checked={tq.get("include_deleted") === "true"} onCheckedChange={(v) => tq.setFilter("include_deleted", v ? "true" : null)} />
            <Label htmlFor="show-deleted">Hiện tổ chức đã xóa</Label>
          </div>
        }
      />}>
        <MasterDetail
          id="orgs"
          master={
            <DataTable
        path="/admin/orgs"
        columns={columns}
        getRowId={(o) => o.id}
        reloadKey={version}
        onAdd={() => setCreating(true)}
        addLabel="Tạo tổ chức"
        onEdit={setEditing}
        onDelete={(orgs) => run("delete", orgs)}
        onRowActivate={(o) => setActive(o)}
        activeRowId={active?.id}
        deleteLabel={(orgs) => `Xóa ${orgs.filter(editable).length} tổ chức? Tổ chức sẽ bị ẩn và không đăng nhập được.`}
        actions={({ selected }) => (
          <>
            <ToolbarButton disabled={selected.length !== 1 || !!selected[0].deleted_at || selected[0].status !== "active"} onClick={() => void enter(selected[0])}>
              <LogIn /> Vào tổ chức
            </ToolbarButton>
            <ToolbarButton disabled={!selected.some((o) => editable(o) && o.status === "active")} onClick={() => setPending({ action: "suspend", orgs: selected })}>
              <Lock /> Khóa
            </ToolbarButton>
            <ToolbarButton disabled={!selected.some((o) => editable(o) && o.status !== "active")} onClick={() => setPending({ action: "activate", orgs: selected })}>
              <LockOpen /> Mở khóa
            </ToolbarButton>
          </>
        )}
      />
          }
          detail={active && !active.is_system  && (
            <Card className="min-h-full">
          <CardHeader>
            <CardTitle>Thành viên · {active.name}</CardTitle>
          </CardHeader>
          <CardContent>
            <MembershipTable key={active.id} side={{ kind: "org", orgId: active.id, orgName: active.name }} />
          </CardContent>
        </Card>
          )}
        />
      </ListLayout>
      <ConfirmDialog
        open={!!pending}
        onOpenChange={(o) => !o && setPending(null)}
        title={pending ? CONFIRM[pending.action] : ""}
        destructive={pending?.action === "suspend"}
        onConfirm={async () => {
          const p = pending!;
          setPending(null);
          await run(p.action, p.orgs);
        }}
      />
      <FormDialog open={creating} onOpenChange={(o) => (setCreating(o), o || refresh())} title="Tạo tổ chức">
        <OrgCreateForm onDone={() => (setCreating(false), refresh())} />
      </FormDialog>
      <FormDialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)} title="Sửa tổ chức">
        {editing && <OrgEditForm org={editing} onDone={() => (setEditing(null), refresh())} />}
      </FormDialog>
    </>
  );
}
