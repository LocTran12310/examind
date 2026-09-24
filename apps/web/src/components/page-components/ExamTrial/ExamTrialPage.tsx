"use client";

import { BackLink } from "@/components/common/BackLink/BackLink";
import { FormAlert } from "@/components/common/FormAlert/FormAlert";
import { PageHeader } from "@/components/common/PageHeader/PageHeader";
import { ResultView } from "@/components/page-components/AttemptResult/ResultView/ResultView";
import { Runner } from "@/components/page-components/ExamRunner/Runner/Runner";
import { useExamTrialPage } from "@/hooks/page-hooks/exam-trial/use-exam-trial-page";

/** Whoever set the exam sits it (AC-04, AC-05): the student's runner, then the student's result screen — and a line
 *  on the page at every step saying that none of it is recorded, because none of it is (exam-runner ADR-01). */
export function ExamTrialPage({ id }: { id: string }) {
  const p = useExamTrialPage(id);
  const back = <BackLink href={p.back}>Đề thi</BackLink>;
  if (p.error && !p.paper) return <>{back}<p className="text-sm text-destructive">{p.error}</p></>;
  if (!p.paper) return null;
  return (
    <>
      {back}
      <PageHeader title={p.paper.title} description="Chạy thử — làm như học sinh, nhưng không ghi lại gì" />
      {p.error && (
        <div className="mb-3">
          <FormAlert>{p.error}</FormAlert>
        </div>
      )}
      <FormAlert kind="info" className="mb-4">
        {p.result
          ? "Điểm của bản chạy thử, tính đúng như của học sinh. Không có lượt làm bài, điểm hay thống kê nào được ghi lại."
          : "Bản chạy thử: không có đồng hồ, không tự lưu, và không một lượt làm bài, điểm hay thống kê nào được ghi lại."}
      </FormAlert>
      {p.result ? <ResultView result={p.result} /> : <Runner view={p.paper} trial onFinished={p.graded} />}
    </>
  );
}
