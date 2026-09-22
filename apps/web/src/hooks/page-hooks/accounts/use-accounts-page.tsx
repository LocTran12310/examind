import type { ColumnDef } from "@tanstack/react-table";
import { useMemo, useState } from "react";
import { ToneBadge } from "@/components/app/ToneBadge";
import type { Account } from "@/interfaces/org.interface";

/** Columns and the selected account of the super admin's Accounts page. */
export function useAccountsPage() {
  const [active, setActive] = useState<Account | null>(null);
  const columns = useMemo<ColumnDef<Account, unknown>[]>(
    () => [
      { accessorKey: "full_name", header: "Họ tên", meta: { filter: { kind: "text" }, sort: "full_name" } },
      { accessorKey: "username", header: "Tên đăng nhập", cell: ({ row }) => <span className="font-mono">{row.original.username}</span>, meta: { filter: { kind: "text" }, sort: "username" } },
      { accessorKey: "home_org_code", header: "Tổ chức gốc", cell: ({ row }) => `${row.original.home_org_name} (${row.original.home_org_code})`, meta: { filter: { kind: "text" }, sort: "home_org_code" } },
      { accessorKey: "org_count", header: "Số tổ chức", meta: { sort: "org_count", align: "right" } },
      {
        accessorKey: "is_active",
        header: "Trạng thái",
        cell: ({ row }) => (row.original.is_active ? <ToneBadge tone="green">Hoạt động</ToneBadge> : <ToneBadge tone="red">Đã khóa</ToneBadge>),
        meta: { filter: { kind: "select", options: [{ value: "true", label: "Hoạt động" }, { value: "false", label: "Đã khóa" }] } },
      },
    ],
    [],
  );
  return { columns, active, setActive };
}
