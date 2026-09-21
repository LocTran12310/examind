"use client";

import Link from "next/link";
import { use, useState } from "react";
import { formValueOf, payloadOf, QuestionForm } from "@/components/bank/QuestionForm";
import { QuestionView } from "@/components/question/QuestionView";
import { Badge, Button, Card, PageHeader } from "@/components/ui";
import { api } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import { DIFFICULTY_LABEL, STATUS_LABEL, type ParsedQuestion, type QuestionStatus, type Tag, type Taxonomy, type Topic } from "@/lib/types";

export default function BankQuestionPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: q, setData } = useApi<ParsedQuestion>(`/questions/${id}`);
  const { data: taxonomy } = useApi<Taxonomy>("/taxonomy");
  const { data: topics } = useApi<Topic[]>("/topics");
  const { data: tags } = useApi<Tag[]>("/tags");
  const [editing, setEditing] = useState(false);
  if (!q || !taxonomy || !topics || !tags) return null;
  const primary = q.topics.find((t) => t.is_primary);
  return (
    <>
      <Link href="/org/bank" className="text-sm text-gray-500 hover:underline">
        ← Ngân hàng câu hỏi
      </Link>
      <PageHeader
        title={q.number ? `Câu ${q.number}` : "Câu hỏi"}
        subtitle={[primary?.name, q.difficulty ? DIFFICULTY_LABEL[q.difficulty] : null, q.grade ? `Lớp ${q.grade}` : null].filter(Boolean).join(" · ")}
        actions={
          <>
            <Badge>{STATUS_LABEL[q.status as QuestionStatus] ?? q.status}</Badge>
            {!editing && (
              <Button variant="primary" onClick={() => setEditing(true)}>
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
        <Card className="max-w-3xl">
          <QuestionView question={q} mode="review" solutionOpen />
          {q.tags.length > 0 && <p className="mt-4 text-sm text-gray-600">{q.tags.map((t) => `#${t.name}`).join(" ")}</p>}
        </Card>
      )}
    </>
  );
}
