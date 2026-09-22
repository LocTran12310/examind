import type { ColumnDef } from "@tanstack/react-table";
import { useMemo, useState } from "react";
import { useTableQuery } from "@/hooks/common/use-table-query";
import { useYear } from "@/hooks/common/use-year";
import { useDeleteClassesMutation } from "@/hooks/react-query/use-query-class";
import type { SchoolClass } from "@/interfaces/class.interface";

/** Columns, dialogs and the selected class of the Classes page; the list follows the header year. */
export function useClassesPage() {
  const tq = useTableQuery();
  const { year } = useYear();
  const params = useMemo(() => ({ school_year_id: year?.id }), [year?.id]);
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<SchoolClass | null>(null);
  const [active, setActive] = useState<SchoolClass | null>(null);
  const remove = useDeleteClassesMutation();
  const columns = useMemo<ColumnDef<SchoolClass, unknown>[]>(
    () => [
      { accessorKey: "name", header: "Lớp", cell: ({ row }) => <span className="font-medium">{row.original.name}</span>, meta: { filter: { kind: "text" }, sort: "name" } },
      { accessorKey: "grade", header: "Khối", meta: { filter: { kind: "number" }, sort: "grade", align: "right" } },
      { accessorKey: "school_year", header: "Năm học", meta: { filter: { kind: "text", placeholder: "2026-2027" }, sort: "school_year" } },
      { accessorKey: "member_count", header: "Sĩ số", meta: { sort: "member_count", align: "right" } },
    ],
    [],
  );
  return {
    year,
    params,
    columns,
    creating,
    setCreating,
    editing,
    setEditing,
    active,
    open: (c: SchoolClass) => {
      setActive(c);
      tq.clear(["m.page", "m.full_name", "m.username", "m.sort"]);
    },
    removeClasses: async (rows: SchoolClass[]) => {
      await remove.mutateAsync(rows.map((c) => c.id));
      if (rows.some((c) => c.id === active?.id)) setActive(null);
    },
  };
}
