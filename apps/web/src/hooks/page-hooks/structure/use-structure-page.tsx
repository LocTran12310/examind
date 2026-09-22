import type { ColumnDef } from "@tanstack/react-table";
import { useMemo, useState } from "react";
import { useMe } from "@/hooks/common/use-me";
import { nodeKey, type NodeRef, parseNode } from "@/lib/page-libs/structure/node";
import { useTableQuery } from "@/hooks/common/use-table-query";
import { useYear } from "@/hooks/common/use-year";
import { useDeleteClassesMutation } from "@/hooks/react-query/use-query-class";
import { useDeleteGradesMutation, useDeleteLevelsMutation, useStructureQuery } from "@/hooks/react-query/use-query-structure";
import type { SchoolClass } from "@/interfaces/class.interface";
import type { GradeRow, SchoolLevel } from "@/interfaces/structure.interface";

export const LEVEL_COLUMNS: ColumnDef<SchoolLevel, unknown>[] = [
  { accessorKey: "name", header: "Cấp học", cell: ({ row }) => <span className="font-medium">{row.original.name}</span>, meta: { filter: { kind: "text" }, sort: "name" } },
  { accessorKey: "code", header: "Mã", cell: ({ row }) => <span className="font-mono">{row.original.code}</span>, meta: { sort: "code" } },
  { id: "range", header: "Khối", cell: ({ row }) => `${row.original.grade_from}–${row.original.grade_to}`, meta: { align: "right" } },
  { accessorKey: "grade_count", header: "Số khối", meta: { sort: "grade_count", align: "right" } },
];
export const GRADE_COLUMNS: ColumnDef<GradeRow, unknown>[] = [
  { accessorKey: "name", header: "Khối", cell: ({ row }) => <span className="font-medium">{row.original.name}</span>, meta: { filter: { kind: "text" } } },
  { accessorKey: "level", header: "Số", meta: { sort: "level", align: "right" } },
  { accessorKey: "class_count", header: "Số lớp", meta: { sort: "class_count", align: "right" } },
];
export const CLASS_COLUMNS: ColumnDef<SchoolClass, unknown>[] = [
  { accessorKey: "name", header: "Lớp", cell: ({ row }) => <span className="font-medium">{row.original.name}</span>, meta: { filter: { kind: "text" }, sort: "name" } },
  { accessorKey: "school_year", header: "Năm học", meta: { filter: { kind: "text", placeholder: "2026-2027" }, sort: "school_year" } },
  { accessorKey: "member_count", header: "Sĩ số", meta: { sort: "member_count", align: "right" } },
];

export type StructureEditing = { kind: "level"; row?: SchoolLevel } | { kind: "grade"; row?: GradeRow } | { kind: "class"; row?: SchoolClass } | null;

/** Tree node in the URL (`node=grade:<id>`), the tree of the header year, dialogs and deletes. */
export function useStructurePage() {
  const me = useMe();
  const admin = me.role === "org_admin";
  const tq = useTableQuery();
  const node = parseNode(tq.get("node"));
  const { year } = useYear();
  const { data } = useStructureQuery(year?.id ?? null);
  const [editing, setEditing] = useState<StructureEditing>(null);
  const removeLevels = useDeleteLevelsMutation();
  const removeGrades = useDeleteGradesMutation();
  const removeClasses = useDeleteClassesMutation();

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

  const gradeId = found?.grade?.id;
  const levelParams = useMemo(() => ({ school_level_id: found?.level?.id }), [found?.level?.id]);
  const classParams = useMemo(() => ({ grade_id: gradeId, school_year_id: year?.id }), [gradeId, year?.id]);
  const title = !node ? "Cấp học" : found?.klass ? `Lớp ${found.klass.name}` : found?.grade ? found.grade.name : found?.level?.name ?? "";
  const crumbs =
    node?.kind === "level"
      ? `Khối ${found?.level?.grade_from}–${found?.level?.grade_to}`
      : [found?.level?.name, node?.kind === "class" ? found?.grade?.name : undefined].filter(Boolean).join(" › ");

  return {
    admin,
    year,
    data,
    node,
    found,
    select,
    levelParams,
    classParams,
    title,
    crumbs,
    editing,
    setEditing,
    closeEditing: () => setEditing(null),
    removeLevels: (rows: SchoolLevel[]) => removeLevels.mutateAsync(rows.map((r) => r.id)),
    removeGrades: (rows: GradeRow[]) => removeGrades.mutateAsync(rows.map((r) => r.id)),
    removeClasses: (rows: SchoolClass[]) => removeClasses.mutateAsync(rows.map((r) => r.id)),
  };
}
