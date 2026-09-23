"use client";

import { BackLink } from "@/components/common/BackLink/BackLink";
import { PageHeader } from "@/components/common/PageHeader/PageHeader";
import { QuestionForm } from "@/components/common/QuestionForm/QuestionForm";
import { useQuestionNewPage } from "@/hooks/page-hooks/question-new/use-question-new-page";

export function QuestionNewPage() {
  const p = useQuestionNewPage();
  if (!p.taxonomy || !p.topics || !p.tags || !p.initial) return null;
  return (
    <>
      <BackLink href="/org/bank">Ngân hàng câu hỏi</BackLink>
      <PageHeader title="Thêm câu hỏi" description="Dán hoặc kéo thả ảnh trực tiếp vào ô đề bài / lời giải" />
      <QuestionForm initial={p.initial} taxonomy={p.taxonomy} topics={p.topics} tags={p.tags} submitLabel="Tạo câu hỏi" onCancel={p.cancel} onSubmit={p.save} />
    </>
  );
}
