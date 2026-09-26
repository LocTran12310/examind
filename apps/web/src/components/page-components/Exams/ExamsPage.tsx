"use client";

import { ExternalLink } from "lucide-react";
import Link from "next/link";
import { FormDialog } from "@/components/common/FormDialog/FormDialog";
import { ListLayout } from "@/components/common/ListLayout/ListLayout";
import { MasterDetail } from "@/components/common/MasterDetail/MasterDetail";
import { PageHeader } from "@/components/common/PageHeader/PageHeader";
import { DataTable } from "@/components/common/DataTable/DataTable";
import { SubjectTabs } from "@/components/common/SubjectTabs/SubjectTabs";
import { ExamPreviewDialog } from "@/components/page-components/ExamDetail/ExamPreviewDialog/ExamPreviewDialog";
import { ExamQuestionsTable } from "@/components/page-components/ExamDetail/ExamQuestionsTable/ExamQuestionsTable";
import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useExamsPage } from "@/hooks/page-hooks/exams/use-exams-page";
import { useExamSearchQuery } from "@/hooks/react-query/use-query-exam";
import { NewExamForm } from "./NewExamForm/NewExamForm";

export function ExamsPage() {
  const p = useExamsPage();
  return (
    <>
      <ListLayout header={<PageHeader title="Đề thi & giao bài" description="Tạo đề từ ngân hàng câu hỏi theo ma trận hoặc chọn tay. Chọn một đề để xem câu hỏi bên dưới." />}>
        <MasterDetail
          id="exams"
          master={
            <div className="flex h-full min-h-0 flex-col gap-2">
              {/* the scope sits above the table, not in a column: it is what the list is *about*, and the
                  numbers on it say what each tab would show */}
              <SubjectTabs subjects={p.subjects} counts={p.facets?.subjects} value={p.subject} onChange={p.chooseSubject} allLabel="Tất cả" />
              <DataTable
              useRows={useExamSearchQuery}
              params={p.params}
              columns={p.columns}
              getRowId={(e) => e.id}
              onAdd={() => p.setCreating(true)}
              addLabel="Tạo đề"
              onEdit={p.edit}
              onDelete={p.removeExams}
              deleteLabel={(rows) => `Xóa ${rows.length} đề thi?`}
              onRowActivate={p.setActive}
              activeRowId={p.active?.id}
              />
            </div>
          }
          detail={
            p.active && (
              <Card className="flex h-full min-h-0 flex-col gap-2 py-3">
                <CardHeader className="px-3">
                  <CardTitle>Chi tiết · {p.active.title}</CardTitle>
                  <CardAction>
                    <Button variant="outline" size="sm" asChild>
                      <Link href={`/org/exams/${p.active.id}`}>
                        <ExternalLink /> Soạn đề & giao bài
                      </Link>
                    </Button>
                  </CardAction>
                </CardHeader>
                <CardContent className="min-h-0 flex-1 px-3">
                  <ExamQuestionsTable examId={p.active.id} />
                </CardContent>
              </Card>
            )
          }
        />
      </ListLayout>
      <ExamPreviewDialog examId={p.preview} onClose={p.closePreview} />
      <FormDialog open={p.creating} onOpenChange={p.setCreating} title="Tạo đề mới">
        <NewExamForm />
      </FormDialog>
    </>
  );
}
