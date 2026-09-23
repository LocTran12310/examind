"use client";

import { Pagination } from "@/components/common/DataTable/Pagination";
import { EmptyState } from "@/components/common/EmptyState/EmptyState";
import { QuestionForm, formValueOf, type QuestionFormValue } from "@/components/common/QuestionForm/QuestionForm";
import { QuestionView } from "@/components/common/QuestionView/QuestionView";
import { ToneBadge, type Tone } from "@/components/common/ToneBadge/ToneBadge";
import { Button } from "@/components/ui/button";
import { STATUS_LABEL } from "@/constants/question.constant";
import { REDECIDE_ACTIONS, SPOT_LABEL } from "@/constants/review.constant";
import type { ParsedQuestion, QuestionStatus } from "@/interfaces/question.interface";
import type { SearchPage } from "@/interfaces/search-page.interface";
import type { Tag } from "@/interfaces/tag.interface";
import type { Taxonomy } from "@/interfaces/taxonomy.interface";
import type { Topic } from "@/interfaces/topic.interface";

const STATUS_TONE: Record<string, Tone> = { approved: "green", auto_approved: "green", needs_review: "amber", flagged: "red", rejected: "red", duplicate: "gray", draft: "gray" };

/** The document's questions in a decided state: each row names its state and can be read, corrected
 *  and decided again (AC-04, AC-05). The pending queue keeps its own keyboard screen. */
export function QuestionList({
  page,
  pageNo,
  pageSize,
  onPage,
  editingId,
  onEdit,
  onSave,
  onDecide,
  taxonomy,
  topics,
  tags,
}: {
  page?: SearchPage<ParsedQuestion>;
  pageNo: number;
  pageSize: number;
  onPage: (p: number) => void;
  editingId: string | null;
  onEdit: (id: string | null) => void;
  onSave: (id: string, v: QuestionFormValue) => Promise<void>;
  onDecide: (id: string, status: QuestionStatus) => void;
  taxonomy?: Taxonomy;
  topics?: Topic[];
  tags?: Tag[];
}) {
  if (!page) return null;
  if (page.data.length === 0) return <EmptyState>Không có câu nào ở trạng thái này.</EmptyState>;
  const editable = !!(taxonomy && topics && tags);

  return (
    <div className="space-y-4" data-testid="question-list">
      {page.data.map((q) => (
        <section key={q.id} className="rounded-xl border border-border bg-card p-5" data-testid={`question-${q.id}`}>
          <header className="mb-3 flex flex-wrap items-center gap-2 text-sm">
            <span className="text-muted-foreground">
              Câu {q.number}
              {q.part ? ` · Phần ${q.part}` : ""}
            </span>
            <ToneBadge tone={STATUS_TONE[q.status] ?? "gray"}>{STATUS_LABEL[q.status as QuestionStatus] ?? q.status}</ToneBadge>
            {q.spot_check && <ToneBadge tone="blue">{SPOT_LABEL}</ToneBadge>}
          </header>
          {editingId === q.id && editable ? (
            <QuestionForm
              initial={formValueOf(q)}
              taxonomy={taxonomy}
              topics={topics}
              tags={tags}
              submitLabel="Lưu câu hỏi"
              onSubmit={(v) => onSave(q.id, v)}
              onCancel={() => onEdit(null)}
            />
          ) : (
            <QuestionView question={q} mode="review" solutionOpen={false} />
          )}
          <div className="mt-4 flex flex-wrap items-center justify-end gap-2 border-t border-border pt-3">
            {editingId !== q.id && (
              <Button variant="outline" size="sm" disabled={!editable} data-testid="edit-question" onClick={() => onEdit(q.id)}>
                Sửa nội dung câu hỏi
              </Button>
            )}
            {REDECIDE_ACTIONS.filter((a) => a.status !== q.status).map((a) => (
              <Button
                key={a.status}
                size="sm"
                data-testid={`decide-${a.status}`}
                variant={a.status === "approved" ? "default" : a.status === "rejected" ? "destructive" : "outline"}
                onClick={() => onDecide(q.id, a.status)}
              >
                {a.label}
              </Button>
            ))}
          </div>
        </section>
      ))}
      <Pagination page={pageNo} pageSize={pageSize} total={page.total} onPage={onPage} />
    </div>
  );
}
