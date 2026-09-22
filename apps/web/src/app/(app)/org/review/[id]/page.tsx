"use client";

import { BackLink } from "@/components/app/BackLink";
import { use, useState } from "react";
import { AnswerKeyDialog } from "@/components/review/AnswerKeyDialog";
import { QuestionEditor } from "@/components/review/QuestionEditor";
import { ReviewQueue } from "@/components/review/ReviewQueue";
import { FormAlert } from "@/components/app/FormAlert";
import { Button } from "@/components/ui/button";
import { FormDialog } from "@/components/app/FormDialog";
import { PageHeader } from "@/components/app/PageHeader";
import { api } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type { ParsedQuestion, ReviewDocument, Topic } from "@/lib/types";

export default function ReviewDocumentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: info, reload } = useApi<ReviewDocument>(`/review/documents/${id}`);
  const { data: queue, reload: reloadQueue } = useApi<ParsedQuestion[]>(`/review/documents/${id}/queue`);
  const { data: topics } = useApi<Topic[]>(info?.document.meta.subject_id ? `/topics?subject_id=${info.document.meta.subject_id}` : "/topics");
  const [pasting, setPasting] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [version, setVersion] = useState(0);
  if (!info || !queue || !topics) return null;
  const confident = info.counts.auto_approved - info.spot_pending;

  return (
    <>
      <BackLink href="/org/review">Duyệt câu hỏi</BackLink>
      <PageHeader
        title={info.document.filename}
        description={`Tự duyệt ${info.counts.auto_approved} · Cần xem ${info.counts.needs_review} · Đã duyệt ${info.counts.approved}`}
        actions={
          <>
            <Button variant="outline" onClick={() => setPasting(true)}>Dán đáp án</Button>
            {confident > 0 && (
              <Button variant="outline"
                onClick={async () => {
                  const r = await api<{ approved: number }>(`/review/documents/${id}/approve-confident`, { method: "POST" });
                  setNotice(`Đã duyệt ${r.approved} câu tin cậy cao.`);
                  void reload();
                }}
              >
                Duyệt tất cả câu tin cậy cao ({confident})
              </Button>
            )}
          </>
        }
      />
      {notice && <div className="mb-3"><FormAlert kind="success">{notice}</FormAlert></div>}
      <ReviewQueue
        key={version}
        doc={info.document}
        initial={queue}
        topics={topics}
        onChange={reload}
        renderEditor={(p) => <QuestionEditor {...p} />}
      />
      <FormDialog open={pasting} title="Dán bảng đáp án" onOpenChange={(o) => !o && setPasting(false)}>
        <AnswerKeyDialog
          docId={id}
          onDone={async () => {
            setPasting(false);
            await Promise.all([reload(), reloadQueue()]);
            setVersion((v) => v + 1);
          }}
        />
      </FormDialog>
    </>
  );
}
