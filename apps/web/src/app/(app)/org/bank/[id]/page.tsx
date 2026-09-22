"use client";

import Link from "next/link";
import { use, useState } from "react";
import { formValueOf, payloadOf, QuestionForm } from "@/components/bank/QuestionForm";
import { QuestionView } from "@/components/question/QuestionView";
import { ToneBadge } from "@/components/app/ToneBadge";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/app/Panel";
import { PageHeader } from "@/components/app/PageHeader";
import { api } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import { DIFFICULTY_LABEL, STATUS_LABEL, type ParsedQuestion, type QuestionStatus, type Page, type Tag, type Taxonomy, type Topic } from "@/lib/types";

export default function BankQuestionPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: q, setData } = useApi<ParsedQuestion>(`/questions/${id}`);
  const { data: taxonomy } = useApi<Taxonomy>("/taxonomy");
  const { data: topics } = useApi<Topic[]>("/topics");
  const { data: tagsPage } = useApi<Page<Tag>>("/tags?page_size=all");
  const tags = tagsPage?.items;
  const [editing, setEditing] = useState(false);
  if (!q || !taxonomy || !topics || !tags) return null;
  const primary = q.topics.find((t) => t.is_primary);
  return (
    <>
      <Link href="/org/bank" className="text-sm text-muted-foreground hover:underline">
        ← Ngân hàng câu hỏi
      </Link>
      <PageHeader
        title={q.number ? `Câu ${q.number}` : "Câu hỏi"}
        description={[primary?.name, q.difficulty ? DIFFICULTY_LABEL[q.difficulty] : null, q.grade ? `Lớp ${q.grade}` : null].filter(Boolean).join(" · ")}
        actions={
          <>
            <ToneBadge>{STATUS_LABEL[q.status as QuestionStatus] ?? q.status}</ToneBadge>
            {!editing && (
              <Button onClick={() => setEditing(true)}>
                Sửa
              </Button>
            )}
          </>
        }
      />
      {editing ? (
        <QuestionForm
          initial={formValueOf(q)}
          taxonomy={taxonomy}
          topics={topics}
          tags={tags}
          submitLabel="Lưu"
          onCancel={() => setEditing(false)}
          onSubmit={async (v) => {
            setData(await api<ParsedQuestion>(`/questions/${id}`, { method: "PATCH", body: payloadOf(v) }));
            setEditing(false);
          }}
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
