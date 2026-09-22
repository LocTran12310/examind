"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { useMemo, useState } from "react";
import { MembershipTable } from "@/components/admin/MembershipTable";
import { PageHeader } from "@/components/app/PageHeader";
import { ToneBadge } from "@/components/app/ToneBadge";
import { DataTable } from "@/components/data-table/DataTable";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { Account } from "@/lib/types";

/** Every account of every organisation; select one to manage its organisations (school-years AC-14). */
export default function AccountsPage() {
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
  return (
    <>
      <PageHeader title="Tài khoản" description="Mọi tài khoản của mọi tổ chức. Chọn một tài khoản để gán vào tổ chức." />
      <DataTable path="/admin/users" columns={columns} getRowId={(a) => a.id} selectable={false} onRowActivate={setActive} activeRowId={active?.id} />
      {active && (
        <Card className="mt-4">
          <CardHeader>
            <CardTitle>Tổ chức của {active.full_name}</CardTitle>
            <CardDescription>
              Đăng nhập: {active.home_org_code} / {active.username}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <MembershipTable key={active.id} side={{ kind: "user", userId: active.id, userName: active.full_name }} />
          </CardContent>
        </Card>
      )}
    </>
  );
}
