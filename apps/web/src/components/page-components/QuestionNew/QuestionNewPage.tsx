"use client";

import { PageHeader } from "@/components/app/PageHeader";
import { QuestionForm } from "@/components/common/QuestionForm/QuestionForm";
import { useQuestionNewPage } from "@/hooks/page-hooks/question-new/use-question-new-page";

export function QuestionNewPage() {
  const p = useQuestionNewPage();
  if (!p.taxonomy || !p.topics || !p.tags || !p.initial) return null;
  return (
    <>
      <PageHeader title="Thêm câu hỏi" description="Dán hoặc kéo thả ảnh trực tiếp vào ô đề bài / lời giải" />
      <QuestionForm initial={p.initial} taxonomy={p.taxonomy} topics={p.topics} tags={p.tags} submitLabel="Tạo câu hỏi" onCancel={p.cancel} onSubmit={p.save} />
    </>
  );
}
