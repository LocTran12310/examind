"use client";

import { ChevronDown, History, Lock, LockOpen, UserCog } from "lucide-react";
import { FormAlert } from "@/components/common/FormAlert/FormAlert";
import { FormDialog } from "@/components/common/FormDialog/FormDialog";
import { FormField } from "@/components/common/FormField/FormField";
import { HistoryPanel } from "@/components/common/HistoryPanel/HistoryPanel";
import { OptionSelect } from "@/components/common/OptionSelect/OptionSelect";
import { DataTable } from "@/components/common/DataTable/DataTable";
import { ToolbarButton } from "@/components/common/DataTable/Toolbar";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { MEMBER_ROLE_OPTIONS, MEMBER_ROLES, ROLE_LABEL } from "@/constants/role.constant";
import { type MembershipTableSide, useMembershipAddForm, useMembershipTable } from "@/hooks/page-hooks/orgs/use-membership-table";
import { useMembershipSearchQuery } from "@/hooks/react-query/use-query-membership";
import type { Membership } from "@/interfaces/org.interface";

function AddForm({ side, onDone }: { side: MembershipTableSide; onDone: () => void }) {
  const f = useMembershipAddForm(side, onDone);
  return (
    <form
      className="grid gap-4"
      onSubmit={(e) => {
        e.preventDefault();
        f.submit();
      }}
    >
      {f.message && !Object.keys(f.fields).length && <FormAlert>{f.message}</FormAlert>}
      {side.kind === "org" ? (
        <div className="grid grid-cols-2 gap-4">
          <FormField label="Mã tổ chức gốc" error={f.fields.org_code}>
            <Input value={f.orgCode} onChange={(e) => f.setOrgCode(e.target.value)} placeholder="trungtama" required autoFocus />
          </FormField>
          <FormField label="Tên đăng nhập" error={f.fields.username}>
            <Input value={f.username} onChange={(e) => f.setUsername(e.target.value)} required />
          </FormField>
        </div>
      ) : (
        <FormField label="Tổ chức" error={f.fields.org_id}>
          {(p) => <OptionSelect {...p} value={f.orgId} onValueChange={f.setOrgId} placeholder="Chọn tổ chức" options={f.orgOptions} />}
        </FormField>
      )}
      <FormField label="Vai trò">{(p) => <OptionSelect {...p} value={f.role} onValueChange={f.setRole} options={MEMBER_ROLE_OPTIONS} />}</FormField>
      <DialogFooter>
        <Button type="submit" disabled={f.busy || (side.kind === "user" && !f.orgId)}>
          Thêm
        </Button>
      </DialogFooter>
    </form>
  );
}

/**
 * Memberships seen from one side: an org's members, or an account's organisations. Both call the same
 * membership service, so either screen shows what the other did (school-years ADR-04).
 */
export function MembershipTable({ side }: { side: MembershipTableSide }) {
  const t = useMembershipTable(side);
  return (
    <>
      <DataTable<Membership>
        useRows={useMembershipSearchQuery}
        params={t.params}
        prefix="mb."
        columns={t.columns}
        getRowId={(m) => `${m.user_id}:${m.org_id}`}
        onAdd={() => t.setAdding(true)}
        addLabel={side.kind === "org" ? "Thêm tài khoản" : "Thêm vào tổ chức"}
        onDelete={t.removeRows}
        deleteLabel={(rows) => `Gỡ ${rows.filter((m) => !m.is_home).length} thành viên? Tổ chức gốc không gỡ được.`}
        actions={({ selected, clearSelection }) => (
          <>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <ToolbarButton disabled={!selected.length}>
                  <UserCog /> Đổi vai trò <ChevronDown />
                </ToolbarButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                {MEMBER_ROLES.map((r) => (
                  <DropdownMenuItem key={r} onSelect={() => void t.setRole(selected, r).then(clearSelection)}>
                    {ROLE_LABEL[r]}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
            <ToolbarButton disabled={!selected.some((m) => !m.is_home && m.is_active)} onClick={() => void t.lock(selected).then(clearSelection)}>
              <Lock /> Khóa
            </ToolbarButton>
            <ToolbarButton disabled={!selected.some((m) => !m.is_active)} onClick={() => void t.unlock(selected).then(clearSelection)}>
              <LockOpen /> Mở khóa
            </ToolbarButton>
            <ToolbarButton onClick={() => t.setHistory(true)}>
              <History /> Lịch sử
            </ToolbarButton>
          </>
        )}
        emptyText="Chưa có thành viên."
      />
      <FormDialog open={t.adding} onOpenChange={t.setAdding} title={side.kind === "org" ? `Thêm tài khoản vào ${side.orgName}` : `Thêm ${side.userName} vào tổ chức`}>
        <AddForm side={side} onDone={() => t.setAdding(false)} />
      </FormDialog>
      <FormDialog open={t.history} onOpenChange={t.setHistory} title="Lịch sử" wide>
        {side.kind === "org" ? <HistoryPanel orgId={side.orgId} /> : <HistoryPanel related={side.userId} />}
      </FormDialog>
    </>
  );
}
