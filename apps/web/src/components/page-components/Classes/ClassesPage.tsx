"use client";

import { ExternalLink } from "lucide-react";
import Link from "next/link";
import { FormDialog } from "@/components/app/FormDialog";
import { ListLayout } from "@/components/app/ListLayout";
import { MasterDetail } from "@/components/app/MasterDetail";
import { PageHeader } from "@/components/app/PageHeader";
import { DataTable } from "@/components/common/DataTable/DataTable";
import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useClassesPage } from "@/hooks/page-hooks/classes/use-classes-page";
import { useClassSearchQuery } from "@/hooks/react-query/use-query-class";
import { ClassForm } from "./ClassForm/ClassForm";
import { MemberManager } from "./MemberManager/MemberManager";

export function ClassesPage() {
  const p = useClassesPage();
  return (
    <>
      <ListLayout header={<PageHeader title="Lớp học" description={`${p.year ? p.year.name + " · " : ""}Chọn một lớp để xem học sinh bên dưới.`} />}>
        <MasterDetail
          id="classes"
          master={
            <DataTable
              useRows={useClassSearchQuery}
              params={p.params}
              columns={p.columns}
              getRowId={(c) => c.id}
              onAdd={() => p.setCreating(true)}
              onEdit={p.setEditing}
              onDelete={p.removeClasses}
              deleteLabel={(rows) => `Xóa ${rows.length} lớp? Học sinh vẫn giữ tài khoản.`}
              onRowActivate={p.open}
              activeRowId={p.active?.id}
            />
          }
          detail={
            p.active && (
              <Card className="min-h-full">
                <CardHeader>
                  <CardTitle>
                    Chi tiết · Lớp {p.active.name} <span className="font-normal text-muted-foreground">({p.active.school_year})</span>
                  </CardTitle>
                  <CardAction>
                    <Button variant="outline" size="sm" asChild>
                      <Link href={`/org/classes/${p.active.id}`}>
                        <ExternalLink /> Mở trang lớp
                      </Link>
                    </Button>
                  </CardAction>
                </CardHeader>
                <CardContent>
                  <MemberManager classId={p.active.id} />
                </CardContent>
              </Card>
            )
          }
        />
      </ListLayout>
      <FormDialog open={p.creating} onOpenChange={p.setCreating} title="Tạo lớp">
        <ClassForm onDone={() => p.setCreating(false)} />
      </FormDialog>
      <FormDialog open={!!p.editing} onOpenChange={(o) => !o && p.setEditing(null)} title="Sửa lớp">
        {p.editing && <ClassForm klass={p.editing} onDone={() => p.setEditing(null)} />}
      </FormDialog>
    </>
  );
}
