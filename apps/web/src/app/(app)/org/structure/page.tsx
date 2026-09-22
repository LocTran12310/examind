"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { ExternalLink, Upload } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import { useMe } from "@/app/(app)/AppShell";
import { FormDialog } from "@/components/app/FormDialog";
import { PageHeader } from "@/components/app/PageHeader";
import { DataTable } from "@/components/data-table/DataTable";
import { useTableQuery } from "@/components/data-table/useTableQuery";
import { ClassForm } from "@/components/org/ClassForms";
import { MemberManager } from "@/components/org/MemberManager";
import { GradeForm, LevelForm } from "@/components/structure/StructureForms";
import { nodeKey, type NodeRef, parseNode, StructureTree } from "@/components/structure/StructureTree";
import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { useYear } from "@/components/app/YearContext";
import { useApi } from "@/lib/hooks";
import type { GradeRow, SchoolClass, SchoolLevel, Structure } from "@/lib/types";

const levelCols: ColumnDef<SchoolLevel, unknown>[] = [
  { accessorKey: "name", header: "Cấp học", cell: ({ row }) => <span className="font-medium">{row.original.name}</span>, meta: { filter: { kind: "text" }, sort: "name" } },
  { accessorKey: "code", header: "Mã", cell: ({ row }) => <span className="font-mono">{row.original.code}</span>, meta: { sort: "code" } },
  { id: "range", header: "Khối", cell: ({ row }) => `${row.original.grade_from}–${row.original.grade_to}`, meta: { align: "right" } },
  { accessorKey: "grade_count", header: "Số khối", meta: { sort: "grade_count", align: "right" } },
];
const gradeCols: ColumnDef<GradeRow, unknown>[] = [
  { accessorKey: "name", header: "Khối", cell: ({ row }) => <span className="font-medium">{row.original.name}</span>, meta: { filter: { kind: "text" } } },
  { accessorKey: "level", header: "Số", meta: { sort: "level", align: "right" } },
  { accessorKey: "class_count", header: "Số lớp", meta: { sort: "class_count", align: "right" } },
];
const classCols: ColumnDef<SchoolClass, unknown>[] = [
  { accessorKey: "name", header: "Lớp", cell: ({ row }) => <span className="font-medium">{row.original.name}</span>, meta: { filter: { kind: "text" }, sort: "name" } },
  { accessorKey: "school_year", header: "Năm học", meta: { filter: { kind: "text", placeholder: "2026-2027" }, sort: "school_year" } },
  { accessorKey: "member_count", header: "Sĩ số", meta: { sort: "member_count", align: "right" } },
];

type Editing = { kind: "level"; row?: SchoolLevel } | { kind: "grade"; row?: GradeRow } | { kind: "class"; row?: SchoolClass } | null;

export default function StructurePage() {
  const me = useMe();
  const admin = me.role === "org_admin";
  const tq = useTableQuery();
  const node = parseNode(tq.get("node"));
  const { year } = useYear();
  const { data, reload } = useApi<Structure>(year ? `/structure?school_year_id=${year.id}` : "/structure");
  const [editing, setEditing] = useState<Editing>(null);
  const [version, setVersion] = useState(0);
  const changed = () => {
    setVersion((v) => v + 1);
    void reload();
  };
  const select = (n: NodeRef) => {
    // a new node starts with clean table params
    const drop = ["l.", "g.", "c.", "m."];
    const changes: Record<string, string | null> = { node: nodeKey(n) || null };
    new URLSearchParams(window.location.search).forEach((_, k) => drop.some((p) => k.startsWith(p)) && (changes[k] = null));
    tq.setFilters(changes);
  };

  const found = useMemo(() => {
    if (!data || !node) return null;
    for (const lv of data.levels) {
      if (node.kind === "level" && lv.id === node.id) return { level: lv };
      for (const g of lv.grades) {
        if (node.kind === "grade" && g.id === node.id) return { level: lv, grade: g };
        const c = g.classes.find((c) => node.kind === "class" && c.id === node.id);
        if (c) return { level: lv, grade: g, klass: c };
      }
    }
    const c = data.unassigned.find((c) => node.kind === "class" && c.id === node.id);
    return c ? { klass: c } : null;
  }, [data, node]);

  let panel: React.ReactNode;
  if (!node) {
    panel = (
      <DataTable<SchoolLevel>
        path="/school-levels"
        prefix="l."
        columns={levelCols}
        getRowId={(r) => r.id}
        reloadKey={version}
        onAdd={admin ? () => setEditing({ kind: "level" }) : undefined}
        addLabel="Thêm cấp học"
        onEdit={admin ? (row) => setEditing({ kind: "level", row }) : undefined}
        onDelete={admin ? async (rows) => { for (const r of rows) await api(`/school-levels/${r.id}`, { method: "DELETE" }); changed(); } : undefined}
        deleteLabel={(rows) => `Xóa ${rows.length} cấp học?`}
        onRowActivate={(r) => select({ kind: "level", id: r.id })}
      />
    );
  } else if (node.kind === "level" && found?.level) {
    const levelId = found.level.id;
    panel = (
      <DataTable<GradeRow>
        path="/grades"
        prefix="g."
        params={{ school_level_id: levelId }}
        columns={gradeCols}
        getRowId={(r) => r.id}
        reloadKey={version}
        onAdd={admin ? () => setEditing({ kind: "grade" }) : undefined}
        addLabel="Thêm khối"
        onEdit={admin ? (row) => setEditing({ kind: "grade", row }) : undefined}
        onDelete={admin ? async (rows) => { for (const r of rows) await api(`/grades/${r.id}`, { method: "DELETE" }); changed(); } : undefined}
        deleteLabel={(rows) => `Xóa ${rows.length} khối?`}
        onRowActivate={(r) => select({ kind: "grade", id: r.id })}
      />
    );
  } else if (node.kind === "grade" && found?.grade) {
    panel = (
      <DataTable<SchoolClass>
        path="/classes"
        prefix="c."
        params={{ grade_id: found.grade.id, school_year_id: year?.id }}
        columns={classCols}
        getRowId={(r) => r.id}
        reloadKey={version}
        onAdd={() => setEditing({ kind: "class" })}
        addLabel="Thêm lớp"
        onEdit={(row) => setEditing({ kind: "class", row })}
        onDelete={async (rows) => { for (const r of rows) await api(`/classes/${r.id}`, { method: "DELETE" }); changed(); }}
        deleteLabel={(rows) => `Xóa ${rows.length} lớp? Học sinh vẫn giữ tài khoản.`}
        onRowActivate={(r) => select({ kind: "class", id: r.id })}
      />
    );
  } else if (node.kind === "class" && found?.klass) {
    panel = (
      <>
        <div className="mb-2 flex flex-wrap gap-2">
          <Button variant="outline" size="sm" asChild>
            <Link href={`/org/classes/${found.klass.id}`}>
              <ExternalLink /> Mở trang lớp
            </Link>
          </Button>
        </div>
        <MemberManager classId={found.klass.id} onChange={changed} />
      </>
    );
  } else {
    panel = data ? <p className="text-sm text-muted-foreground">Không tìm thấy mục đã chọn.</p> : <Skeleton className="h-40" />;
  }

  const title = !node ? "Cấp học" : found?.klass ? `Lớp ${found.klass.name}` : found?.grade ? found.grade.name : found?.level?.name ?? "";
  const crumbs = node?.kind === "level" ? `Khối ${found?.level?.grade_from}–${found?.level?.grade_to}` : [found?.level?.name, node?.kind === "class" ? found?.grade?.name : undefined].filter(Boolean).join(" › ");

  return (
    <>
      <PageHeader title="Cơ cấu trường" description={`Cấp học › Khối › Lớp › Học sinh${year ? " · " + year.name : ""}`} />
      <div className="grid gap-4 lg:grid-cols-[23rem_1fr]">
        <Card className="h-fit">
          <CardContent>{data ? <StructureTree data={data} selected={node} onSelect={select} /> : <Skeleton className="h-60" />}</CardContent>
        </Card>
        <Card className="min-w-0">
          <CardHeader>
            <CardTitle>{title}</CardTitle>
            {crumbs && <CardDescription>{crumbs}</CardDescription>}
            {node?.kind === "class" && (
              <CardAction>
                <Button variant="outline" size="sm" asChild>
                  <Link href="/org/users/import">
                    <Upload /> Nhập học sinh từ file
                  </Link>
                </Button>
              </CardAction>
            )}
          </CardHeader>
          <CardContent>{panel}</CardContent>
        </Card>
      </div>
      <FormDialog open={editing?.kind === "level"} onOpenChange={(o) => !o && setEditing(null)} title={editing?.row ? "Sửa cấp học" : "Thêm cấp học"}>
        {editing?.kind === "level" && <LevelForm level={editing.row} onDone={() => (setEditing(null), changed())} />}
      </FormDialog>
      <FormDialog open={editing?.kind === "grade"} onOpenChange={(o) => !o && setEditing(null)} title={editing?.row ? "Sửa khối" : "Thêm khối"}>
        {editing?.kind === "grade" && found?.level && <GradeForm grade={editing.row} levelId={found.level.id} onDone={() => (setEditing(null), changed())} />}
      </FormDialog>
      <FormDialog open={editing?.kind === "class"} onOpenChange={(o) => !o && setEditing(null)} title={editing?.row ? "Sửa lớp" : "Thêm lớp"}>
        {editing?.kind === "class" && <ClassForm klass={editing.row} gradeId={found?.grade?.id} onDone={() => (setEditing(null), changed())} />}
      </FormDialog>
    </>
  );
}
