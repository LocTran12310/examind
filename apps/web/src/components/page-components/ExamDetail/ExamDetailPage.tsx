"use client";

import { BackLink } from "@/components/app/BackLink";
import { FormAlert } from "@/components/app/FormAlert";
import { FormDialog } from "@/components/app/FormDialog";
import { PageHeader } from "@/components/app/PageHeader";
import { Panel } from "@/components/app/Panel";
import { QuestionView } from "@/components/common/QuestionView/QuestionView";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { useExamDetailPage } from "@/hooks/page-hooks/exam-detail/use-exam-detail-page";
import { AssignDialog } from "./AssignDialog/AssignDialog";
import { AssignedList } from "./AssignedList/AssignedList";
import { BankSearch } from "./BankSearch/BankSearch";
import { BlueprintEditor } from "./BlueprintEditor/BlueprintEditor";
import { ExamQuestions } from "./ExamQuestions/ExamQuestions";
import { PointsByType } from "./PointsByType/PointsByType";

export function ExamDetailPage({ id }: { id: string }) {
  const p = useExamDetailPage(id);
  if (!p.exam || !p.topics || !p.tags) return null;
  const exam = p.exam;

  return (
    <>
      <BackLink href="/org/exams">Đề thi</BackLink>
      <PageHeader
        title={exam.title}
        description={`${exam.question_count} câu · tổng ${exam.total_points} điểm (quy về thang ${exam.settings.scale_to})`}
        actions={
          <>
            <Button variant="outline" onClick={() => p.setPreview("exam")} disabled={!exam.question_count}>
              Xem trước
            </Button>
            <Button onClick={() => p.setAssigning(true)} disabled={!exam.question_count}>
              Giao bài
            </Button>
          </>
        }
      />
      {p.error && (
        <div className="mb-3">
          <FormAlert>{p.error}</FormAlert>
        </div>
      )}
      <div className="grid gap-6 xl:grid-cols-[3fr_2fr]">
        <div className="space-y-4">
          <Panel>
            <h2 className="mb-3 font-medium">Ma trận đề</h2>
            <BlueprintEditor initial={exam.blueprint} topics={p.topics} tags={p.tags} shortfalls={p.shortfalls} onGenerate={p.generate} />
          </Panel>
          <Panel>
            <h2 className="mb-2 font-medium">Câu hỏi trong đề</h2>
            {exam.questions.length === 0 ? (
              <p className="text-sm text-muted-foreground">Chưa có câu nào — tạo theo ma trận hoặc thêm từ ngân hàng.</p>
            ) : (
              <ExamQuestions questions={exam.questions} onSaveOrder={p.saveOrder} onSwap={p.swap} onRemove={p.remove} onPoints={p.setPoints} />
            )}
          </Panel>
        </div>
        <div className="space-y-4">
          <AssignedList assigned={p.assigned} />
          <PointsByType settings={exam.settings} onChange={p.setTypePoints} />
          <BankSearch search={p.search} onSearchChange={p.setSearch} onFind={p.findInBank} found={p.found} inExam={p.inExam} onAdd={p.addQuestion} />
        </div>
      </div>
      <FormDialog open={p.assigning} title="Giao bài" wide onOpenChange={(o) => !o && p.setAssigning(false)}>
        {p.assigning && <AssignDialog examId={id} title={exam.title} classes={p.classes} onDone={p.doneAssigning} />}
      </FormDialog>
      <FormDialog open={!!p.preview} title="Xem trước đề" wide onOpenChange={(o) => !o && p.setPreview(null)}>
        <div className="mb-4 flex items-center gap-2 text-sm">
          <Checkbox id="preview-answers" checked={p.preview === "review"} onCheckedChange={(v) => p.setPreview(v === true ? "review" : "exam")} />
          <Label htmlFor="preview-answers" className="font-normal">
            Hiện đáp án và lời giải
          </Label>
        </div>
        <div className="space-y-6" data-testid="exam-preview">
          {exam.questions.map((q) => (
            <QuestionView key={q.id} question={q} mode={p.preview === "review" ? "review" : "exam"} number={q.position} />
          ))}
        </div>
      </FormDialog>
    </>
  );
}
