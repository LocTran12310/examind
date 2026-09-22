import type { ColumnDef } from "@tanstack/react-table";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { ToneBadge } from "@/components/app/ToneBadge";
import type { OrgAction } from "@/dtos/org.dto";
import { useSwitchOrg } from "@/hooks/common/use-switch-org";
import { useTableQuery } from "@/hooks/common/use-table-query";
import { useOrgActionMutation } from "@/hooks/react-query/use-query-org";
import type { Org } from "@/interfaces/org.interface";
import { ApiError } from "@/lib/common/http";
import { formatDate } from "@/lib/datetime";

type StatusAction = Exclude<OrgAction, "delete">;

const failed = (e: unknown, fallback = "Có lỗi xảy ra") => toast.error(e instanceof ApiError ? e.message : fallback);

function status(o: Org) {
  return (
    <span className="inline-flex gap-1">
      {o.deleted_at ? <ToneBadge tone="red">Đã xóa</ToneBadge> : o.status === "active" ? <ToneBadge tone="green">Hoạt động</ToneBadge> : <ToneBadge tone="amber">Tạm khóa</ToneBadge>}
      {o.is_system && <ToneBadge tone="blue">Hệ thống</ToneBadge>}
    </span>
  );
}

/** Columns, dialogs, status changes and "enter the org" of the super admin's Orgs page. */
export function useOrgsPage() {
  const tq = useTableQuery();
  const showDeleted = tq.get("include_deleted") === "true";
  const params = useMemo(() => ({ include_deleted: showDeleted || undefined }), [showDeleted]);
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<Org | null>(null);
  const [pending, setPending] = useState<{ action: StatusAction; orgs: Org[]; done?: () => void } | null>(null);
  const [active, setActive] = useState<Org | null>(null);
  const action = useOrgActionMutation();
  const { switchTo } = useSwitchOrg();
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
      { accessorKey: "created_at", header: "Ngày tạo", cell: ({ row }) => formatDate(row.original.created_at), meta: { filter: { kind: "date" }, sort: "created_at" } },
    ],
    [],
  );

  async function run(kind: OrgAction, orgs: Org[]) {
    try {
      await action.mutateAsync({ action: kind, ids: orgs.filter(editable).map((o) => o.id) });
    } catch (e) {
      failed(e);
    }
  }

  return {
    params,
    columns,
    editable,
    showDeleted,
    setShowDeleted: (v: boolean) => tq.setFilter("include_deleted", v ? "true" : null),
    creating,
    setCreating,
    editing,
    setEditing,
    pending,
    setPending,
    active,
    setActive,
    removeOrgs: (orgs: Org[]) => run("delete", orgs),
    confirmPending: async () => {
      const p = pending!;
      setPending(null);
      await run(p.action, p.orgs);
      p.done?.();
    },
    /** Work inside the org: the system org stays on this page, a tenant opens its users. */
    enter: async (o: Org) => {
      try {
        await switchTo(o.id, () => (o.is_system ? "/admin/orgs" : "/org/users"));
      } catch (e) {
        failed(e, "Không vào được tổ chức");
      }
    },
  };
}
