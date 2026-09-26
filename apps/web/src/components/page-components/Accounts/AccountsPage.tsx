"use client";

import { ListLayout } from "@/components/common/ListLayout/ListLayout";
import { MasterDetail } from "@/components/common/MasterDetail/MasterDetail";
import { PageHeader } from "@/components/common/PageHeader/PageHeader";
import { DataTable } from "@/components/common/DataTable/DataTable";
import { MembershipTable } from "@/components/page-components/Orgs/MembershipTable/MembershipTable";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAccountsPage } from "@/hooks/page-hooks/accounts/use-accounts-page";
import { useAccountSearchQuery } from "@/hooks/react-query/use-query-account";

/** Every account of every organisation; select one to manage its organisations (school-years AC-14). */
export function AccountsPage() {
  const p = useAccountsPage();
  return (
    <ListLayout header={<PageHeader title="Tài khoản" description="Mọi tài khoản của mọi tổ chức. Chọn một tài khoản để gán vào tổ chức." />}>
      <MasterDetail
        id="accounts"
        master={<DataTable useRows={useAccountSearchQuery} columns={p.columns} getRowId={(a) => a.id} selectable={false} onRowActivate={p.setActive} activeRowId={p.active?.id} />}
        detail={
          p.active && (
            <Card className="flex h-full min-h-0 flex-col">
              <CardHeader>
                <CardTitle>Tổ chức của {p.active.full_name}</CardTitle>
                <CardDescription>
                  Đăng nhập: {p.active.home_org_code} / {p.active.username}
                </CardDescription>
              </CardHeader>
              <CardContent className="min-h-0 flex-1">
                <MembershipTable key={p.active.id} side={{ kind: "user", userId: p.active.id, userName: p.active.full_name }} />
              </CardContent>
            </Card>
          )
        }
      />
    </ListLayout>
  );
}
