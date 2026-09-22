"use client";

import { ListLayout } from "@/components/app/ListLayout";
import type { ColumnDef } from "@tanstack/react-table";
import { ArrowRightLeft, CheckCircle2, History, Lock, LockOpen } from "lucide-react";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { useMe } from "@/app/(app)/AppShell";
import { ConfirmDialog } from "@/components/app/ConfirmDialog";
import { FormDialog } from "@/components/app/FormDialog";
import { HistoryPanel } from "@/components/app/HistoryPanel";
import { PageHeader } from "@/components/app/PageHeader";
import { ToneBadge } from "@/components/app/ToneBadge";
import { useYear } from "@/components/app/YearContext";
import { DataTable } from "@/components/data-table/DataTable";
import { ToolbarButton } from "@/components/data-table/Toolbar";
import { nextYearCode, YearForm } from "@/components/years/YearForm";
import { api, ApiError } from "@/lib/api";
import { type SchoolYear, YEAR_STATUS_LABEL } from "@/lib/types";
import { formatDate } from "@/lib/datetime";

const d = (s: string) => formatDate(s);

export default function SchoolYearsPage() {
  const me = useMe();
  const admin = me.role === "org_admin";
  const router = useRouter();
  const { years, reload: reloadYears } = useYear();
  const latest = [...years].sort((a, b) => b.code.localeCompare(a.code))[0]?.code;
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<SchoolYear | null>(null);
  const [history, setHistory] = useState<SchoolYear | null>(null);
  const [activating, setActivating] = useState<SchoolYear | null>(null);
  const [version, setVersion] = useState(0);
  const changed = () => {
    setVersion((v) => v + 1);
    void reloadYears();
  };

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
        meta: { filter: { kind: "select", options: Object.entries(YEAR_STATUS_LABEL).map(([value, label]) => ({ value, label })) }, sort: "status" },
      },
      { accessorKey: "class_count", header: "Số lớp", meta: { sort: "class_count", align: "right" } },
    ],
    [],
  );

  async function setStatus(y: SchoolYear, action: "activate" | "close" | "reopen") {
    try {
      await api(`/school-years/${y.id}/${action}`, { method: "POST" });
      toast.success(action === "activate" ? `${y.code} là năm đang học` : action === "close" ? `Đã khóa ${y.code}` : `Đã mở lại ${y.code}`);
      changed();
    } catch (e) {
      toast.error(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
    }
  }

  return (
    <>
      <ListLayout header={<PageHeader title="Năm học" description="Mỗi năm có Học kỳ 1 và Học kỳ 2. Năm đã khóa vẫn sửa được; mọi thay đổi được ghi vào lịch sử." />}>
        <DataTable<SchoolYear>
          path="/school-years"
          columns={columns}
          getRowId={(y) => y.id}
          reloadKey={version}
          onAdd={admin ? () => setCreating(true) : undefined}
          addLabel="Thêm năm học"
          onEdit={admin ? setEditing : undefined}
          onDelete={admin ? async (rows) => { for (const y of rows) await api(`/school-years/${y.id}`, { method: "DELETE" }); changed(); } : undefined}
          deleteLabel={(rows) => `Xóa ${rows.length} năm học? Chỉ xóa được năm chưa có lớp.`}
          actions={({ selected }) => {
            const one = selected.length === 1 ? selected[0] : null;
            return (
              <>
                {admin && (
                  <>
                    <ToolbarButton disabled={!one || one.status === "active"} onClick={() => one && setActivating(one)}>
                      <CheckCircle2 /> Đặt làm năm đang học
                    </ToolbarButton>
                    <ToolbarButton disabled={!one || one.status === "closed"} onClick={() => one && void setStatus(one, "close")}>
                      <Lock /> Khóa
                    </ToolbarButton>
                    <ToolbarButton disabled={!one || one.status !== "closed"} onClick={() => one && void setStatus(one, "reopen")}>
                      <LockOpen /> Mở lại
                    </ToolbarButton>
                    <ToolbarButton disabled={!one} onClick={() => one && router.push(`/org/school-years/${one.id}/rollover`)}>
                      <ArrowRightLeft /> Chuyển năm học
                    </ToolbarButton>
                  </>
                )}
                {admin && (
                  <ToolbarButton disabled={!one} onClick={() => one && setHistory(one)}>
                    <History /> Lịch sử
                  </ToolbarButton>
                )}
              </>
            );
          }}
        />
      </ListLayout>
      <ConfirmDialog
        open={!!activating}
        onOpenChange={(o) => !o && setActivating(null)}
        title={`Đặt ${activating?.code ?? ""} làm năm đang học?`}
        description="Năm đang học hiện tại sẽ được khóa (vẫn sửa được, có ghi lịch sử)."
        onConfirm={async () => {
          const y = activating!;
          setActivating(null);
          await setStatus(y, "activate");
        }}
      />
      <FormDialog open={creating} onOpenChange={setCreating} title="Thêm năm học">
        <YearForm suggest={nextYearCode(latest)} onDone={() => (setCreating(false), changed())} />
      </FormDialog>
      <FormDialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)} title={`Sửa ${editing?.code ?? ""}`}>
        {editing && <YearForm year={editing} onDone={() => (setEditing(null), changed())} />}
      </FormDialog>
      <FormDialog open={!!history} onOpenChange={(o) => !o && setHistory(null)} title={`Lịch sử · ${history?.code ?? ""}`} wide>
        {history && <HistoryPanel targetId={history.id} />}
      </FormDialog>
    </>
  );
}
