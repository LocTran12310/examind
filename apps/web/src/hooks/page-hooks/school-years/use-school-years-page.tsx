import type { ColumnDef } from "@tanstack/react-table";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { useMe } from "@/hooks/common/use-me";
import { ToneBadge } from "@/components/app/ToneBadge";
import { YEAR_STATUS_LABEL, YEAR_STATUS_OPTIONS } from "@/constants/school-year.constant";
import type { YearAction } from "@/dtos/school-year.dto";
import { useYear } from "@/hooks/common/use-year";
import { useDeleteSchoolYearsMutation, useSchoolYearStatusMutation } from "@/hooks/react-query/use-query-school-year";
import type { SchoolYear } from "@/interfaces/school-year.interface";
import { ApiError } from "@/lib/common/http";
import { formatDate as d } from "@/lib/datetime";
import { nextYearCode } from "@/lib/page-libs/school-years/year-code";

const DONE: Record<YearAction, (code: string) => string> = {
  activate: (c) => `${c} là năm đang học`,
  close: (c) => `Đã khóa ${c}`,
  reopen: (c) => `Đã mở lại ${c}`,
};

/** Columns, dialogs and status changes of the School years page (org admins change, teachers read). */
export function useSchoolYearsPage() {
  const me = useMe();
  const admin = me.role === "org_admin";
  const { years } = useYear();
  const latest = [...years].sort((a, b) => b.code.localeCompare(a.code))[0]?.code;
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<SchoolYear | null>(null);
  const [history, setHistory] = useState<SchoolYear | null>(null);
  const [activating, setActivating] = useState<SchoolYear | null>(null);
  const status = useSchoolYearStatusMutation();
  const remove = useDeleteSchoolYearsMutation();

  const columns = useMemo<ColumnDef<SchoolYear, unknown>[]>(
    () => [
      { accessorKey: "code", header: "Năm học", cell: ({ row }) => <span className="font-medium">{row.original.code}</span>, meta: { filter: { kind: "text" }, sort: "code" } },
      { id: "dates", header: "Thời gian", cell: ({ row }) => `${d(row.original.start_date)} – ${d(row.original.end_date)}` },
      {
        id: "terms",
        header: "Học kỳ",
        cell: ({ row }) => (
          <div className="grid text-xs text-muted-foreground">
            {row.original.terms.map((t) => (
              <span key={t.code}>
                {t.name}: {d(t.start_date)} – {d(t.end_date)}
              </span>
            ))}
          </div>
        ),
      },
      {
        accessorKey: "status",
        header: "Trạng thái",
        cell: ({ row }) => <ToneBadge tone={row.original.status === "active" ? "green" : row.original.status === "closed" ? "gray" : "blue"}>{YEAR_STATUS_LABEL[row.original.status]}</ToneBadge>,
        meta: { filter: { kind: "select", options: YEAR_STATUS_OPTIONS }, sort: "status" },
      },
      { accessorKey: "class_count", header: "Số lớp", meta: { sort: "class_count", align: "right" } },
    ],
    [],
  );

  async function setStatus(y: SchoolYear, action: YearAction) {
    try {
      await status.mutateAsync({ id: y.id, action });
      toast.success(DONE[action](y.code));
    } catch (e) {
      toast.error(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
    }
  }

  return {
    admin,
    columns,
    suggestCode: nextYearCode(latest),
    creating,
    setCreating,
    editing,
    setEditing,
    history,
    setHistory,
    activating,
    setActivating,
    setStatus,
    confirmActivate: async () => {
      const y = activating!;
      setActivating(null);
      await setStatus(y, "activate");
    },
    removeYears: (rows: SchoolYear[]) => remove.mutateAsync(rows.map((y) => y.id)),
  };
}
