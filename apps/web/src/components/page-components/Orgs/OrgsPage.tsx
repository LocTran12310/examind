"use client";

import { LogIn, Lock, LockOpen } from "lucide-react";
import { ConfirmDialog } from "@/components/common/ConfirmDialog/ConfirmDialog";
import { FormDialog } from "@/components/common/FormDialog/FormDialog";
import { ListLayout } from "@/components/common/ListLayout/ListLayout";
import { MasterDetail } from "@/components/common/MasterDetail/MasterDetail";
import { PageHeader } from "@/components/common/PageHeader/PageHeader";
import { DataTable } from "@/components/common/DataTable/DataTable";
import { ToolbarButton } from "@/components/common/DataTable/Toolbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { ORG_ACTION_CONFIRM } from "@/constants/org.constant";
import { useOrgsPage } from "@/hooks/page-hooks/orgs/use-orgs-page";
import { useOrgSearchQuery } from "@/hooks/react-query/use-query-org";
import { MembershipTable } from "./MembershipTable/MembershipTable";
import { OrgCreateForm, OrgEditForm } from "./OrgForm/OrgForm";

export function OrgsPage() {
  const p = useOrgsPage();
  return (
    <>
      <ListLayout
        header={
          <PageHeader
            title="Tổ chức"
            description="Chọn một tổ chức để quản lý thành viên bên dưới."
            actions={
              <div className="flex items-center gap-2">
                <Switch id="show-deleted" checked={p.showDeleted} onCheckedChange={p.setShowDeleted} />
                <Label htmlFor="show-deleted">Hiện tổ chức đã xóa</Label>
              </div>
            }
          />
        }
      >
        <MasterDetail
          id="orgs"
          master={
            <DataTable
              useRows={useOrgSearchQuery}
              params={p.params}
              columns={p.columns}
              getRowId={(o) => o.id}
              onAdd={() => p.setCreating(true)}
              addLabel="Tạo tổ chức"
              onEdit={p.setEditing}
              onDelete={p.removeOrgs}
              onRowActivate={p.setActive}
              activeRowId={p.active?.id}
              deleteLabel={(orgs) => `Xóa ${orgs.filter(p.editable).length} tổ chức? Tổ chức sẽ bị ẩn và không đăng nhập được.`}
              actions={({ selected, clearSelection }) => (
                <>
                  <ToolbarButton disabled={selected.length !== 1 || !!selected[0].deleted_at || selected[0].status !== "active"} onClick={() => void p.enter(selected[0])}>
                    <LogIn /> Vào tổ chức
                  </ToolbarButton>
                  <ToolbarButton disabled={!selected.some((o) => p.editable(o) && o.status === "active")} onClick={() => p.setPending({ action: "suspend", orgs: selected, done: clearSelection })}>
                    <Lock /> Khóa
                  </ToolbarButton>
                  <ToolbarButton disabled={!selected.some((o) => p.editable(o) && o.status !== "active")} onClick={() => p.setPending({ action: "activate", orgs: selected, done: clearSelection })}>
                    <LockOpen /> Mở khóa
                  </ToolbarButton>
                </>
              )}
            />
          }
          detail={
            p.active &&
            !p.active.is_system && (
              <Card className="flex h-full min-h-0 flex-col">
                <CardHeader>
                  <CardTitle>Thành viên · {p.active.name}</CardTitle>
                </CardHeader>
                <CardContent className="min-h-0 flex-1">
                  <MembershipTable key={p.active.id} side={{ kind: "org", orgId: p.active.id, orgName: p.active.name }} />
                </CardContent>
              </Card>
            )
          }
        />
      </ListLayout>
      <ConfirmDialog
        open={!!p.pending}
        onOpenChange={(o) => !o && p.setPending(null)}
        title={p.pending ? ORG_ACTION_CONFIRM[p.pending.action] : ""}
        destructive={p.pending?.action === "suspend"}
        onConfirm={p.confirmPending}
      />
      <FormDialog open={p.creating} onOpenChange={p.setCreating} title="Tạo tổ chức">
        <OrgCreateForm onDone={() => p.setCreating(false)} />
      </FormDialog>
      <FormDialog open={!!p.editing} onOpenChange={(o) => !o && p.setEditing(null)} title="Sửa tổ chức">
        {p.editing && <OrgEditForm org={p.editing} onDone={() => p.setEditing(null)} />}
      </FormDialog>
    </>
  );
}
