"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { ChevronDown, History, Lock, LockOpen, UserCog } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { FormAlert } from "@/components/app/FormAlert";
import { FormDialog } from "@/components/app/FormDialog";
import { FormField } from "@/components/app/FormField";
import { HistoryPanel } from "@/components/app/HistoryPanel";
import { OptionSelect } from "@/components/app/OptionSelect";
import { ToneBadge } from "@/components/app/ToneBadge";
import { DataTable } from "@/components/data-table/DataTable";
import { ToolbarButton } from "@/components/data-table/Toolbar";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";
import { useApi, useMutation } from "@/lib/hooks";
import { type Membership, type Org, type Page, ROLE_LABEL, type Role } from "@/lib/types";

const ROLES: Role[] = ["org_admin", "teacher", "student"];
const roleOptions = ROLES.map((r) => ({ value: r, label: ROLE_LABEL[r] }));

type Side = { kind: "org"; orgId: string; orgName: string } | { kind: "user"; userId: string; userName: string };

function AddForm({ side, onDone }: { side: Side; onDone: () => void }) {
  const [orgCode, setOrgCode] = useState("");
  const [username, setUsername] = useState("");
  const [orgId, setOrgId] = useState("");
  const [role, setRole] = useState<string>("teacher");
  const m = useMutation();
  const { data: orgs } = useApi<Page<Org>>(side.kind === "user" ? "/admin/orgs?page_size=all" : null);
  return (
    <form
      className="grid gap-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const r = await m.run(() =>
          side.kind === "org"
            ? api(`/admin/orgs/${side.orgId}/members`, { body: { org_code: orgCode, username, role } })
            : api(`/admin/users/${side.userId}/memberships`, { body: { org_id: orgId, role } }),
        );
        if (r) onDone();
      }}
    >
      {m.message && !Object.keys(m.fields).length && <FormAlert>{m.message}</FormAlert>}
      {side.kind === "org" ? (
        <div className="grid grid-cols-2 gap-4">
          <FormField label="Mã tổ chức gốc" error={m.fields.org_code}>
            <Input value={orgCode} onChange={(e) => setOrgCode(e.target.value)} placeholder="trungtama" required autoFocus />
          </FormField>
          <FormField label="Tên đăng nhập" error={m.fields.username}>
            <Input value={username} onChange={(e) => setUsername(e.target.value)} required />
          </FormField>
        </div>
      ) : (
        <FormField label="Tổ chức" error={m.fields.org_id}>
          {(f) => (
            <OptionSelect
              {...f}
              value={orgId}
              onValueChange={setOrgId}
              placeholder="Chọn tổ chức"
              options={(orgs?.items ?? []).filter((o) => !o.is_system && !o.deleted_at).map((o) => ({ value: o.id, label: `${o.name} (${o.code})` }))}
            />
          )}
        </FormField>
      )}
      <FormField label="Vai trò">{(f) => <OptionSelect {...f} value={role} onValueChange={setRole} options={roleOptions} />}</FormField>
      <DialogFooter>
        <Button type="submit" disabled={m.busy || (side.kind === "user" && !orgId)}>
          Thêm
        </Button>
      </DialogFooter>
    </form>
  );
}

/**
 * Memberships seen from one side: an org's members, or an account's organisations. Both call the same
 * membership service, so either screen shows what the other did (school-years ADR-04).
 */
export function MembershipTable({ side }: { side: Side }) {
  const [adding, setAdding] = useState(false);
  const [history, setHistory] = useState(false);
  const [version, setVersion] = useState(0);
  const refresh = () => setVersion((v) => v + 1);
  const path = side.kind === "org" ? `/admin/orgs/${side.orgId}/members` : `/admin/users/${side.userId}/memberships`;
  const url = (m: Membership) => (side.kind === "org" ? `/admin/orgs/${side.orgId}/members/${m.user_id}` : `/admin/users/${side.userId}/memberships/${m.org_id}`);

  async function patch(rows: Membership[], body: Record<string, unknown>) {
    try {
      for (const m of rows) await api(url(m), { method: "PATCH", body });
      refresh();
    } catch (e) {
      toast.error(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
    }
  }

  const columns = useMemo<ColumnDef<Membership, unknown>[]>(
    () => [
      ...(side.kind === "org"
        ? [
            { accessorKey: "full_name", header: "Họ tên", meta: { filter: { kind: "text" }, sort: "full_name" } } as ColumnDef<Membership, unknown>,
            { accessorKey: "username", header: "Tên đăng nhập", cell: ({ row }) => <span className="font-mono">{row.original.home_org_code}/{row.original.username}</span>, meta: { filter: { kind: "text" } } } as ColumnDef<Membership, unknown>,
          ]
        : [{ accessorKey: "org_name", header: "Tổ chức", cell: ({ row }) => `${row.original.org_name} (${row.original.org_code})`, meta: { filter: { kind: "text" } } } as ColumnDef<Membership, unknown>]),
      { accessorKey: "role", header: "Vai trò", cell: ({ row }) => ROLE_LABEL[row.original.role], meta: { filter: { kind: "select", options: roleOptions } } },
      {
        id: "status",
        header: "Trạng thái",
        cell: ({ row }) => (
          <span className="inline-flex gap-1">
            {row.original.is_home ? <ToneBadge tone="blue">Tổ chức gốc</ToneBadge> : null}
            {row.original.is_active ? <ToneBadge tone="green">Hoạt động</ToneBadge> : <ToneBadge tone="red">Đã khóa</ToneBadge>}
          </span>
        ),
      },
    ],
    [side.kind],
  );

  return (
    <>
      <DataTable<Membership>
        path={path}
        prefix="mb."
        columns={columns}
        getRowId={(m) => `${m.user_id}:${m.org_id}`}
        reloadKey={version}
        onAdd={() => setAdding(true)}
        addLabel={side.kind === "org" ? "Thêm tài khoản" : "Thêm vào tổ chức"}
        onDelete={async (rows) => {
          for (const m of rows.filter((m) => !m.is_home)) await api(url(m), { method: "DELETE" });
        }}
        deleteLabel={(rows) => `Gỡ ${rows.filter((m) => !m.is_home).length} thành viên? Tổ chức gốc không gỡ được.`}
        actions={({ selected }) => (
          <>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <ToolbarButton disabled={!selected.length}>
                  <UserCog /> Đổi vai trò <ChevronDown />
                </ToolbarButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                {ROLES.map((r) => (
                  <DropdownMenuItem key={r} onSelect={() => void patch(selected, { role: r })}>
                    {ROLE_LABEL[r]}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
            <ToolbarButton disabled={!selected.some((m) => !m.is_home && m.is_active)} onClick={() => void patch(selected.filter((m) => !m.is_home), { is_active: false })}>
              <Lock /> Khóa
            </ToolbarButton>
            <ToolbarButton disabled={!selected.some((m) => !m.is_active)} onClick={() => void patch(selected.filter((m) => !m.is_home), { is_active: true })}>
              <LockOpen /> Mở khóa
            </ToolbarButton>
            <ToolbarButton onClick={() => setHistory(true)}>
              <History /> Lịch sử
            </ToolbarButton>
          </>
        )}
        emptyText="Chưa có thành viên."
      />
      <FormDialog open={adding} onOpenChange={setAdding} title={side.kind === "org" ? `Thêm tài khoản vào ${side.orgName}` : `Thêm ${side.userName} vào tổ chức`}>
        <AddForm side={side} onDone={() => (setAdding(false), refresh())} />
      </FormDialog>
      <FormDialog open={history} onOpenChange={setHistory} title="Lịch sử" wide>
        {side.kind === "org" ? <HistoryPanel orgId={side.orgId} /> : <HistoryPanel related={side.userId} />}
      </FormDialog>
    </>
  );
}
