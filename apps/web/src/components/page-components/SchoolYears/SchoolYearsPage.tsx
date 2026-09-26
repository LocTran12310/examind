"use client";

import { ArrowRightLeft, CheckCircle2, History, Lock, LockOpen } from "lucide-react";
import { useRouter } from "next/navigation";
import { ConfirmDialog } from "@/components/common/ConfirmDialog/ConfirmDialog";
import { FormDialog } from "@/components/common/FormDialog/FormDialog";
import { HistoryPanel } from "@/components/common/HistoryPanel/HistoryPanel";
import { ListLayout } from "@/components/common/ListLayout/ListLayout";
import { PageHeader } from "@/components/common/PageHeader/PageHeader";
import { DataTable } from "@/components/common/DataTable/DataTable";
import { ToolbarButton } from "@/components/common/DataTable/Toolbar";
import { useSchoolYearsPage } from "@/hooks/page-hooks/school-years/use-school-years-page";
import { useSchoolYearSearchQuery } from "@/hooks/react-query/use-query-school-year";
import { YearForm } from "./YearForm/YearForm";

export function SchoolYearsPage() {
  const p = useSchoolYearsPage();
  const router = useRouter();
  return (
    <>
      <ListLayout header={<PageHeader title="Năm học" description="Mỗi năm có Học kỳ 1 và Học kỳ 2. Năm đã khóa vẫn sửa được; mọi thay đổi được ghi vào lịch sử." />}>
        <DataTable
          useRows={useSchoolYearSearchQuery}
          columns={p.columns}
          getRowId={(y) => y.id}
          onAdd={p.admin ? () => p.setCreating(true) : undefined}
          addLabel="Thêm năm học"
          onEdit={p.admin ? p.setEditing : undefined}
          onDelete={p.admin ? p.removeYears : undefined}
          deleteLabel={(rows) => `Xóa ${rows.length} năm học? Chỉ xóa được năm chưa có lớp.`}
          actions={({ selected }) => {
            const one = selected.length === 1 ? selected[0] : null;
            return (
              p.admin && (
                <>
                  <ToolbarButton disabled={!one || one.status === "active"} onClick={() => one && p.setActivating(one)}>
                    <CheckCircle2 /> Đặt làm năm đang học
                  </ToolbarButton>
                  <ToolbarButton disabled={!one || one.status === "closed"} onClick={() => one && void p.setStatus(one, "close")}>
                    <Lock /> Khóa
                  </ToolbarButton>
                  <ToolbarButton disabled={!one || one.status !== "closed"} onClick={() => one && void p.setStatus(one, "reopen")}>
                    <LockOpen /> Mở lại
                  </ToolbarButton>
                  <ToolbarButton disabled={!one} onClick={() => one && router.push(`/org/school-years/${one.id}/rollover`)}>
                    <ArrowRightLeft /> Chuyển năm học
                  </ToolbarButton>
                  <ToolbarButton disabled={!one} onClick={() => one && p.setHistory(one)}>
                    <History /> Lịch sử
                  </ToolbarButton>
                </>
              )
            );
          }}
        />
      </ListLayout>
      <ConfirmDialog
        open={!!p.activating}
        onOpenChange={(o) => !o && p.setActivating(null)}
        title={`Đặt ${p.activating?.code ?? ""} làm năm đang học?`}
        description="Năm đang học hiện tại sẽ được khóa (vẫn sửa được, có ghi lịch sử)."
        onConfirm={p.confirmActivate}
      />
      <FormDialog open={p.creating} onOpenChange={p.setCreating} title="Thêm năm học">
        <YearForm suggest={p.suggestCode} onDone={() => p.setCreating(false)} />
      </FormDialog>
      <FormDialog open={!!p.editing} onOpenChange={(o) => !o && p.setEditing(null)} title={`Sửa ${p.editing?.code ?? ""}`}>
        {p.editing && <YearForm year={p.editing} onDone={() => p.setEditing(null)} />}
      </FormDialog>
      <FormDialog open={!!p.history} onOpenChange={(o) => !o && p.setHistory(null)} title={`Lịch sử · ${p.history?.code ?? ""}`} wide tall>
        {p.history && <HistoryPanel targetId={p.history.id} />}
      </FormDialog>
    </>
  );
}
