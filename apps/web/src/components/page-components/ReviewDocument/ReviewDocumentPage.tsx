"use client";

import { BackLink } from "@/components/common/BackLink/BackLink";
import { FormAlert } from "@/components/common/FormAlert/FormAlert";
import { FormDialog } from "@/components/common/FormDialog/FormDialog";
import { PageHeader } from "@/components/common/PageHeader/PageHeader";
import { AnswerKeyDialog } from "@/components/page-components/ReviewDocument/AnswerKeyDialog/AnswerKeyDialog";
import { QuestionEditor } from "@/components/page-components/ReviewDocument/QuestionEditor/QuestionEditor";
import { ReviewQueue } from "@/components/page-components/ReviewDocument/ReviewQueue/ReviewQueue";
import { Button } from "@/components/ui/button";
import { useReviewDocumentPage } from "@/hooks/page-hooks/review-document/use-review-document-page";

export function ReviewDocumentPage({ id }: { id: string }) {
  const p = useReviewDocumentPage(id);
  if (!p.info || !p.queue || !p.topics) return null;
  const { info } = p;
  return (
    <>
      <BackLink href="/org/review">Duyệt câu hỏi</BackLink>
      <PageHeader
        title={info.document.filename}
        description={`Tự duyệt ${info.counts.auto_approved} · Cần xem ${info.counts.needs_review} · Đã duyệt ${info.counts.approved}`}
        actions={
          <>
            <Button variant="outline" onClick={() => p.setPasting(true)}>Dán đáp án</Button>
            {p.confident > 0 && (
              <Button variant="outline" onClick={() => void p.approveConfident()}>
                Duyệt tất cả câu tin cậy cao ({p.confident})
              </Button>
            )}
          </>
        }
      />
      {p.notice && <div className="mb-3"><FormAlert kind="success">{p.notice}</FormAlert></div>}
      <ReviewQueue key={p.version} doc={info.document} initial={p.queue} topics={p.topics} onChange={p.reloadInfo} renderEditor={(e) => <QuestionEditor {...e} />} />
      <FormDialog open={p.pasting} title="Dán bảng đáp án" onOpenChange={(o) => !o && p.setPasting(false)}>
        <AnswerKeyDialog docId={id} onDone={() => void p.answerKeyDone()} />
      </FormDialog>
    </>
  );
}
