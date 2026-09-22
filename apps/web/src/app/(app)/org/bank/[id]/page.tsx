"use client";

import { BackLink } from "@/components/app/BackLink";
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
// eslint-disable-next-line no-restricted-imports -- screen moves to a page hook in its own slice
import { useTagOptionsQuery } from "@/hooks/react-query/use-query-tag";

export default function BankQuestionPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: q, setData } = useApi<ParsedQuestion>(`/questions/${id}`);
  const { data: taxonomy } = useApi<Taxonomy>("/taxonomy");
  // a question with a subject only offers that subject's topics and tags (subject-scoped-bank, ui-polish A-04)
  const sid = q?.subject_id;
  const { data: topics } = useApi<Topic[]>(q ? (sid ? `/topics?subject_id=${sid}` : "/topics") : null);
  const { data: tags } = useTagOptionsQuery(sid || null, !!q);
  const [editing, setEditing] = useState(false);
  if (!q || !taxonomy || !topics || !tags) return null;
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
