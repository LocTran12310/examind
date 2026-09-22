"use client";

import { BackLink } from "@/components/common/BackLink/BackLink";
import { PageHeader } from "@/components/common/PageHeader/PageHeader";
import { Panel } from "@/components/common/Panel/Panel";
import { ToneBadge } from "@/components/common/ToneBadge/ToneBadge";
import { formValueOf, QuestionForm } from "@/components/common/QuestionForm/QuestionForm";
import { QuestionView } from "@/components/common/QuestionView/QuestionView";
import { Button } from "@/components/ui/button";
import { DIFFICULTY_LABEL, STATUS_LABEL } from "@/constants/question.constant";
import { useQuestionDetailPage } from "@/hooks/page-hooks/question-detail/use-question-detail-page";
import type { QuestionStatus } from "@/interfaces/question.interface";

export function QuestionDetailPage({ id }: { id: string }) {
  const p = useQuestionDetailPage(id);
  if (!p.ready || !p.question || !p.taxonomy || !p.topics || !p.tags) return null;
  const q = p.question;
  const primary = q.topics.find((t) => t.is_primary);
  return (
    <>
      <BackLink href="/org/bank">Ngân hàng câu hỏi</BackLink>
      <PageHeader
        title={q.number ? `Câu ${q.number}` : "Câu hỏi"}
        description={[primary?.name, q.difficulty ? DIFFICULTY_LABEL[q.difficulty] : null, q.grade ? `Lớp ${q.grade}` : null].filter(Boolean).join(" · ")}
        actions={
          <>
            <ToneBadge>{STATUS_LABEL[q.status as QuestionStatus] ?? q.status}</ToneBadge>
            {!p.editing && <Button onClick={() => p.setEditing(true)}>Sửa</Button>}
          </>
        }
      />
      {p.editing ? (
        <QuestionForm
          initial={formValueOf(q)}
          taxonomy={p.taxonomy}
          topics={p.topics}
          tags={p.tags}
          submitLabel="Lưu"
          onCancel={() => p.setEditing(false)}
          onSubmit={p.save}
        />
      ) : (
        <Panel className="max-w-3xl">
          <QuestionView question={q} mode="review" solutionOpen />
          {q.tags.length > 0 && <p className="mt-4 text-sm text-muted-foreground">{q.tags.map((t) => `#${t.name}`).join(" ")}</p>}
        </Panel>
      )}
    </>
  );
}
