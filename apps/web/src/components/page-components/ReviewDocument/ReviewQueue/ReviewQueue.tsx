"use client";

import { EmptyState } from "@/components/app/EmptyState";
import { FormAlert } from "@/components/app/FormAlert";
import { FormDialog } from "@/components/app/FormDialog";
import { ToneBadge } from "@/components/app/ToneBadge";
import { QuestionView } from "@/components/common/QuestionView/QuestionView";
import { TopicPicker } from "@/components/common/TopicPicker/TopicPicker";
import { FlagPanel } from "@/components/page-components/ReviewDocument/FlagPanel/FlagPanel";
import { Button } from "@/components/ui/button";
import { Kbd } from "@/components/ui/kbd";
import { useReviewQueue } from "@/hooks/page-hooks/review-document/use-review-queue";
import type { SourceDocument } from "@/interfaces/document.interface";
import type { ParsedQuestion } from "@/interfaces/question.interface";
import type { Topic } from "@/interfaces/topic.interface";

const LEGEND: [string, string][] = [
  ["Enter", "duyệt + câu tiếp"],
  ["1–4", "chọn đáp án"],
  ["T", "chuyên đề"],
  ["E", "sửa"],
  ["X", "loại"],
  ["S", "bỏ qua"],
  ["J / K", "câu sau / trước"],
];

export interface EditorSlot {
  (props: { question: ParsedQuestion; onSaved: (q: ParsedQuestion) => void; onCancel: () => void }): React.ReactNode;
}

export function ReviewQueue({
  doc,
  initial,
  topics,
  renderEditor,
  onChange,
}: {
  doc: Pick<SourceDocument, "id" | "mime">;
  initial: ParsedQuestion[];
  topics: Topic[];
  renderEditor?: EditorSlot;
  onChange?: () => void;
}) {
  const r = useReviewQueue({ initial, hasEditor: !!renderEditor, onChange });
  const { q, items, index, done, remaining, message } = r;
  const showPage = q && q.page && (doc.mime === "application/pdf" || doc.mime.startsWith("image/"));

  if (!q || remaining === 0) {
    return <EmptyState>Đã xem hết các câu cần xem của đề này. 🎉</EmptyState>;
  }
  const primary = q.topics.find((t) => t.is_primary);

  return (
    <div className={showPage ? "grid gap-4 lg:grid-cols-2" : ""}>
      <section className="rounded-xl border border-border bg-card p-5" data-testid="queue-card">
        <header className="mb-3 flex flex-wrap items-center gap-2 text-sm">
          <span className="font-semibold" data-testid="counter">
            {index + 1}/{items.length}
          </span>
          <ToneBadge tone={q.group === "Kiểm tra ngẫu nhiên" ? "blue" : "amber"}>{q.group}</ToneBadge>
          <span className="text-muted-foreground">
            Câu {q.number}
            {q.part ? ` · Phần ${q.part}` : ""}
          </span>
          {done.has(q.id) && <ToneBadge tone={q.status === "rejected" ? "red" : "green"}>{q.status === "rejected" ? "Đã loại" : "Đã xử lý"}</ToneBadge>}
          {q.issues
            .filter((i) => i !== q.group && i !== "thiếu lời giải")
            .map((i) => (
              <ToneBadge key={i} tone="red">
                {i}
              </ToneBadge>
            ))}
        </header>
        {message && (
          <div className="mb-3">
            <FormAlert kind={message.tone === "red" ? "error" : "success"}>{message.text}</FormAlert>
          </div>
        )}
        {q.flag_evidence && !q.flag_evidence.dismissed && <FlagPanel ev={q.flag_evidence} />}
        {r.editing && renderEditor ? (
          renderEditor({ question: q, onSaved: r.saved, onCancel: () => r.setEditing(false) })
        ) : (
          <QuestionView
            question={q}
            mode="review"
            solutionOpen={false}
            onSelect={r.choosable ? r.setAnswer : undefined}
          />
        )}
        <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-border pt-3 text-sm">
          <span className="text-muted-foreground">Chuyên đề:</span>
          <Button type="button" size="xs" variant="secondary" className="bg-primary/10 font-normal text-primary hover:bg-primary/20" onClick={() => r.setPicking(true)} data-testid="topic-button">
            {primary ? primary.name : "Chọn chuyên đề"}
            {primary?.source && primary.source !== "manual" ? ` · gợi ý ${primary.score ? Math.round(primary.score * 100) + "%" : ""}` : ""}
          </Button>
          <div className="ml-auto flex gap-2">
            <Button variant="outline" size="sm" onClick={r.prev}>
              ← K
            </Button>
            <Button size="sm" variant="destructive" onClick={() => r.action("reject")}>
              Loại (X)
            </Button>
            {renderEditor && (
              <Button variant="outline" size="sm" onClick={() => r.setEditing(true)}>
                Sửa (E)
              </Button>
            )}
            <Button size="sm" onClick={() => r.action("approve")}>
              Duyệt (Enter)
            </Button>
          </div>
        </div>
        <p className="mt-3 flex flex-wrap gap-3 text-xs text-muted-foreground" data-testid="legend">
          {LEGEND.map(([k, v]) => (
            <span key={k}>
              <Kbd className="border border-input bg-transparent font-mono">{k}</Kbd> {v}
            </span>
          ))}
          <span>· còn {remaining} câu</span>
        </p>
      </section>
      {showPage && (
        <aside className="rounded-xl border border-border bg-card p-2" data-testid="source-page">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={`/api/documents/${doc.id}/pages/${q.page}.png`} alt={`Trang ${q.page} của đề gốc`} className="w-full" />
        </aside>
      )}
      <FormDialog open={r.picking} title="Chọn chuyên đề (T)" onOpenChange={(o) => !o && r.setPicking(false)}>
        <TopicPicker topics={topics} onPick={r.pickTopic} onClose={() => r.setPicking(false)} />
      </FormDialog>
    </div>
  );
}
