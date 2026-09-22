"use client";

import { useRouter } from "next/navigation";
import { formValueOf, payloadOf, QuestionForm } from "@/components/bank/QuestionForm";
import { PageHeader } from "@/components/app/PageHeader";
import { api } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type { Page, ParsedQuestion, Tag, Taxonomy, Topic } from "@/lib/types";

export default function NewQuestionPage() {
  const router = useRouter();
  const { data: taxonomy } = useApi<Taxonomy>("/taxonomy");
  const { data: topics } = useApi<Topic[]>("/topics");
  const { data: tagsPage } = useApi<Page<Tag>>("/tags?page_size=all");
  const tags = tagsPage?.items;
  if (!taxonomy || !topics || !tags) return null;
  const initial = { ...formValueOf(), subject_id: taxonomy.subjects.find((s) => s.code === "toan")?.id ?? null };
  return (
    <>
      <PageHeader title="Thêm câu hỏi" description="Dán hoặc kéo thả ảnh trực tiếp vào ô đề bài / lời giải" />
      <QuestionForm
        initial={initial}
        taxonomy={taxonomy}
        topics={topics}
        tags={tags}
        submitLabel="Tạo câu hỏi"
        onCancel={() => router.push("/org/bank")}
        onSubmit={async (v) => {
          const q = await api<ParsedQuestion>("/questions", { body: payloadOf(v) });
          router.push(`/org/bank/${q.id}`);
        }}
      />
    </>
  );
}
