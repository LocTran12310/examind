"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { ExternalLink } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import { FormDialog } from "@/components/app/FormDialog";
import { PageHeader } from "@/components/app/PageHeader";
import { DataTable } from "@/components/data-table/DataTable";
import { useTableQuery } from "@/components/data-table/useTableQuery";
import { ClassForm } from "@/components/org/ClassForms";
import { MemberManager } from "@/components/org/MemberManager";
import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { SchoolClass } from "@/lib/types";

export default function ClassesPage() {
  const tq = useTableQuery();
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<SchoolClass | null>(null);
  const [active, setActive] = useState<SchoolClass | null>(null);
  const [version, setVersion] = useState(0);
  const refresh = () => setVersion((v) => v + 1);

  const columns = useMemo<ColumnDef<SchoolClass, unknown>[]>(
    () => [
      { accessorKey: "name", header: "Lớp", cell: ({ row }) => <span className="font-medium">{row.original.name}</span>, meta: { filter: { kind: "text" }, sort: "name" } },
      { accessorKey: "grade", header: "Khối", meta: { filter: { kind: "number" }, sort: "grade", align: "right" } },
      { accessorKey: "school_year", header: "Năm học", meta: { filter: { kind: "text", placeholder: "2026-2027" }, sort: "school_year" } },
      { accessorKey: "member_count", header: "Sĩ số", meta: { sort: "member_count", align: "right" } },
    ],
    [],
  );

  return (
    <>
      <PageHeader title="Lớp học" description="Chọn một lớp để xem học sinh bên dưới." />
      <DataTable
        path="/classes"
        columns={columns}
        getRowId={(c) => c.id}
        reloadKey={version}
        onAdd={() => setCreating(true)}
        onEdit={setEditing}
        onDelete={async (rows) => {
          for (const c of rows) await api(`/classes/${c.id}`, { method: "DELETE" });
          if (rows.some((c) => c.id === active?.id)) setActive(null);
        }}
        deleteLabel={(rows) => `Xóa ${rows.length} lớp? Học sinh vẫn giữ tài khoản.`}
        onRowActivate={(c) => {
          setActive(c);
          tq.clear(["m.page", "m.full_name", "m.username", "m.sort"]);
        }}
        activeRowId={active?.id}
      />
      {active && (
        <Card className="mt-4">
          <CardHeader>
            <CardTitle>
              Chi tiết · Lớp {active.name} <span className="font-normal text-muted-foreground">({active.school_year})</span>
            </CardTitle>
            <CardAction>
              <Button variant="outline" size="sm" asChild>
                <Link href={`/org/classes/${active.id}`}>
                  <ExternalLink /> Mở trang lớp
                </Link>
              </Button>
            </CardAction>
          </CardHeader>
          <CardContent>
            <MemberManager classId={active.id} onChange={refresh} />
          </CardContent>
        </Card>
      )}
      <FormDialog open={creating} onOpenChange={setCreating} title="Tạo lớp">
        <ClassForm onDone={() => (setCreating(false), refresh())} />
      </FormDialog>
      <FormDialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)} title="Sửa lớp">
        {editing && <ClassForm klass={editing} onDone={() => (setEditing(null), refresh())} />}
      </FormDialog>
    </>
  );
}
