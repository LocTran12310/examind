"use client";

import { ExternalLink, Upload } from "lucide-react";
import Link from "next/link";
import { FormDialog } from "@/components/app/FormDialog";
import { ListLayout } from "@/components/app/ListLayout";
import { PageHeader } from "@/components/app/PageHeader";
import { DataTable } from "@/components/common/DataTable/DataTable";
import { ClassForm } from "@/components/page-components/Classes/ClassForm/ClassForm";
import { MemberManager } from "@/components/page-components/Classes/MemberManager/MemberManager";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { CLASS_COLUMNS, GRADE_COLUMNS, LEVEL_COLUMNS, useStructurePage } from "@/hooks/page-hooks/structure/use-structure-page";
import { useClassSearchQuery } from "@/hooks/react-query/use-query-class";
import { useGradeSearchQuery, useSchoolLevelSearchQuery } from "@/hooks/react-query/use-query-structure";
import { GradeForm } from "./GradeForm/GradeForm";
import { LevelForm } from "./LevelForm/LevelForm";
import { StructureSplit } from "./StructureSplit/StructureSplit";
import { StructureTree } from "./StructureTree/StructureTree";

export function StructurePage() {
  const p = useStructurePage();
  const { admin, node, found } = p;

  let panel: React.ReactNode;
  if (!node) {
    panel = (
      <DataTable
        useRows={useSchoolLevelSearchQuery}
        prefix="l."
        columns={LEVEL_COLUMNS}
        getRowId={(r) => r.id}
        onAdd={admin ? () => p.setEditing({ kind: "level" }) : undefined}
        addLabel="Thêm cấp học"
        onEdit={admin ? (row) => p.setEditing({ kind: "level", row }) : undefined}
        onDelete={admin ? p.removeLevels : undefined}
        deleteLabel={(rows) => `Xóa ${rows.length} cấp học?`}
        onRowActivate={(r) => p.select({ kind: "level", id: r.id })}
      />
    );
  } else if (node.kind === "level" && found?.level) {
    panel = (
      <DataTable
        useRows={useGradeSearchQuery}
        prefix="g."
        params={p.levelParams}
        columns={GRADE_COLUMNS}
        getRowId={(r) => r.id}
        onAdd={admin ? () => p.setEditing({ kind: "grade" }) : undefined}
        addLabel="Thêm khối"
        onEdit={admin ? (row) => p.setEditing({ kind: "grade", row }) : undefined}
        onDelete={admin ? p.removeGrades : undefined}
        deleteLabel={(rows) => `Xóa ${rows.length} khối?`}
        onRowActivate={(r) => p.select({ kind: "grade", id: r.id })}
      />
    );
  } else if (node.kind === "grade" && found?.grade) {
    panel = (
      <DataTable
        useRows={useClassSearchQuery}
        prefix="c."
        params={p.classParams}
        columns={CLASS_COLUMNS}
        getRowId={(r) => r.id}
        onAdd={() => p.setEditing({ kind: "class" })}
        addLabel="Thêm lớp"
        onEdit={(row) => p.setEditing({ kind: "class", row })}
        onDelete={p.removeClasses}
        deleteLabel={(rows) => `Xóa ${rows.length} lớp? Học sinh vẫn giữ tài khoản.`}
        onRowActivate={(r) => p.select({ kind: "class", id: r.id })}
      />
    );
  } else if (node.kind === "class" && found?.klass) {
    panel = (
      <>
        <div className="mb-2 flex flex-wrap gap-2">
          <Button variant="outline" size="sm" asChild>
            <Link href={`/org/classes/${found.klass.id}`}>
              <ExternalLink /> Mở trang lớp
            </Link>
          </Button>
        </div>
        <MemberManager classId={found.klass.id} />
      </>
    );
  } else {
    panel = p.data ? <p className="text-sm text-muted-foreground">Không tìm thấy mục đã chọn.</p> : <Skeleton className="h-40" />;
  }

  const editing = p.editing;
  return (
    <>
      <ListLayout header={<PageHeader title="Cơ cấu trường" description={`Cấp học › Khối › Lớp › Học sinh${p.year ? " · " + p.year.name : ""}`} />}>
        <StructureSplit
          tree={p.data ? <StructureTree data={p.data} selected={node} onSelect={p.select} /> : <Skeleton className="h-60" />}
          title={p.title}
          crumbs={p.crumbs}
          action={
            node?.kind === "class" && (
              <Button variant="outline" size="sm" asChild>
                <Link href="/org/users/import">
                  <Upload /> Nhập học sinh từ file
                </Link>
              </Button>
            )
          }
        >
          {panel}
        </StructureSplit>
      </ListLayout>
      <FormDialog open={editing?.kind === "level"} onOpenChange={(o) => !o && p.closeEditing()} title={editing?.row ? "Sửa cấp học" : "Thêm cấp học"}>
        {editing?.kind === "level" && <LevelForm level={editing.row} onDone={p.closeEditing} />}
      </FormDialog>
      <FormDialog open={editing?.kind === "grade"} onOpenChange={(o) => !o && p.closeEditing()} title={editing?.row ? "Sửa khối" : "Thêm khối"}>
        {editing?.kind === "grade" && found?.level && <GradeForm grade={editing.row} levelId={found.level.id} onDone={p.closeEditing} />}
      </FormDialog>
      <FormDialog open={editing?.kind === "class"} onOpenChange={(o) => !o && p.closeEditing()} title={editing?.row ? "Sửa lớp" : "Thêm lớp"}>
        {editing?.kind === "class" && <ClassForm klass={editing.row} gradeId={found?.grade?.id} onDone={p.closeEditing} />}
      </FormDialog>
    </>
  );
}
