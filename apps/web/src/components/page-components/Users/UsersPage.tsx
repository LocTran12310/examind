"use client";

import { Download, KeyRound, Link2, Lock, LockOpen, Unlink, Upload } from "lucide-react";
import Link from "next/link";
import { ConfirmDialog } from "@/components/app/ConfirmDialog";
import { FormDialog } from "@/components/app/FormDialog";
import { ListLayout } from "@/components/app/ListLayout";
import { PageHeader } from "@/components/app/PageHeader";
import { DataTable } from "@/components/common/DataTable/DataTable";
import { ToolbarButton } from "@/components/common/DataTable/Toolbar";
import { useUsersPage } from "@/hooks/page-hooks/users/use-users-page";
import { useUserSearchQuery } from "@/hooks/react-query/use-query-user";
import { LinkAccountForm } from "./LinkAccountForm/LinkAccountForm";
import { TempPassword } from "./TempPassword/TempPassword";
import { UserCreateForm, UserEditForm } from "./UserForm/UserForm";

export function UsersPage() {
  const p = useUsersPage();
  const { me } = p;
  return (
    <>
      <ListLayout header={<PageHeader title={me.role === "teacher" ? "Học sinh" : "Người dùng"} />}>
        <DataTable
          useRows={useUserSearchQuery}
          columns={p.columns}
          getRowId={(u) => u.id}
          onAdd={() => p.setCreating(true)}
          onEdit={p.setEditing}
          actions={({ selected, clearSelection }) => (
            <>
              <ToolbarButton disabled={selected.length !== 1 || selected[0].is_home === false} onClick={() => p.setResetFor(selected[0])}>
                <KeyRound /> Đặt lại mật khẩu
              </ToolbarButton>
              <ToolbarButton disabled={!selected.some((u) => u.is_active && u.id !== me.id)} onClick={() => void p.lock(selected).then(clearSelection)}>
                <Lock /> Khóa
              </ToolbarButton>
              <ToolbarButton disabled={!selected.some((u) => !u.is_active)} onClick={() => void p.unlock(selected).then(clearSelection)}>
                <LockOpen /> Mở khóa
              </ToolbarButton>
              {me.role === "org_admin" && (
                <>
                  <ToolbarButton onClick={() => p.setLinking(true)}>
                    <Link2 /> Thêm tài khoản có sẵn
                  </ToolbarButton>
                  <ToolbarButton disabled={!selected.some((u) => u.is_home === false)} onClick={() => p.setUnlinking(selected.filter((u) => u.is_home === false))}>
                    <Unlink /> Gỡ khỏi tổ chức
                  </ToolbarButton>
                </>
              )}
              <ToolbarButton asChild>
                <Link href="/org/users/import">
                  <Upload /> Nhập khẩu
                </Link>
              </ToolbarButton>
              <ToolbarButton onClick={() => void p.exportCsv()}>
                <Download /> Xuất khẩu
              </ToolbarButton>
            </>
          )}
          emptyText="Chưa có tài khoản nào. Thêm từng người hoặc nhập từ file CSV/Excel."
        />
      </ListLayout>
      <FormDialog open={p.creating} onOpenChange={p.setCreating} title="Thêm tài khoản">
        <UserCreateForm myRole={me.role} orgCode={me.org.code} onDone={() => p.setCreating(false)} />
      </FormDialog>
      <FormDialog open={!!p.editing} onOpenChange={(o) => !o && p.setEditing(null)} title="Sửa tài khoản">
        {p.editing && <UserEditForm user={p.editing} myRole={me.role} onDone={() => p.setEditing(null)} />}
      </FormDialog>
      <ConfirmDialog
        open={!!p.resetFor}
        onOpenChange={(o) => !o && p.setResetFor(null)}
        title={`Đặt lại mật khẩu cho ${p.resetFor?.full_name ?? ""}?`}
        description="Mật khẩu cũ và mọi phiên đăng nhập của người này sẽ bị hủy."
        confirmLabel="Đặt lại"
        onConfirm={p.confirmReset}
      />
      <FormDialog open={p.linking} onOpenChange={p.setLinking} title="Thêm tài khoản từ tổ chức khác">
        <LinkAccountForm onDone={p.linked} />
      </FormDialog>
      <ConfirmDialog
        open={!!p.unlinking}
        onOpenChange={(o) => !o && p.setUnlinking(null)}
        destructive
        title={`Gỡ ${p.unlinking?.length ?? 0} tài khoản khỏi tổ chức?`}
        description="Tài khoản vẫn dùng được ở tổ chức gốc; họ sẽ rời các lớp của tổ chức này."
        confirmLabel="Gỡ"
        onConfirm={p.confirmUnlink}
      />
      <FormDialog open={!!p.reset} onOpenChange={(o) => !o && p.setReset(null)} title="Đã đặt lại mật khẩu">
        {p.reset && <TempPassword username={p.reset.username} password={p.reset.temp_password} orgCode={me.org.code} />}
      </FormDialog>
    </>
  );
}
