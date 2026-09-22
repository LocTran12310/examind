"use client";

import { useState } from "react";
import { TopicPicker } from "@/components/bank/TopicPicker";
import { QuestionView } from "@/components/question/QuestionView";
import { FormAlert } from "@/components/app/FormAlert";
import { ToneBadge } from "@/components/app/ToneBadge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/app/EmptyState";
import { FormDialog } from "@/components/app/FormDialog";
import { api, ApiError } from "@/lib/api";
import type { ParsedQuestion, SourceDocument, Topic } from "@/lib/types";
import { useHotkeys } from "./useHotkeys";

const LEGEND: [string, string][] = [
  ["Enter", "duyệt + câu tiếp"],
  ["1–4", "chọn đáp án"],
  ["T", "chuyên đề"],
  ["E", "sửa"],
  ["X", "loại"],
  ["S", "bỏ qua"],
  ["J / K", "câu sau / trước"],
];

export function FlagPanel({ ev }: { ev: NonNullable<ParsedQuestion["flag_evidence"]> }) {
  const total = Object.values(ev.option_counts).reduce((a, b) => a + b, 0) || 1;
  return (
    <div className="mb-3 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-red-900" data-testid="flag-panel">
      <div className="font-medium">Nghi sai đáp án: {ev.reason}</div>
      <div className="mt-2 flex flex-wrap gap-3">
        {Object.entries(ev.option_counts)
          .sort()
          .map(([label, n]) => (
            <span key={label}>
              {label}: {Math.round((n / total) * 100)}%{label === ev.key ? " (đáp án hiện tại)" : ""}
            </span>
          ))}
      </div>
      <div className="mt-1 text-xs">
        {ev.answers} lượt trả lời · nhóm giỏi ({ev.top_quartile.size} em) chọn {ev.top_quartile.choice} {Math.round(ev.top_quartile.share * 100)}%. Sửa đáp án (1–4) rồi Enter, hoặc Enter để giữ nguyên.
      </div>
    </div>
  );
}

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
  const [items, setItems] = useState(initial);
  const [done, setDone] = useState<Set<string>>(new Set());
  const [index, setIndex] = useState(0);
  const [message, setMessage] = useState<{ tone: "red" | "green"; text: string } | null>(null);
  const [picking, setPicking] = useState(false);
  const [editing, setEditing] = useState(false);
  const q = items[index];
  const remaining = items.filter((x) => !done.has(x.id)).length;
  const showPage = q && q.page && (doc.mime === "application/pdf" || doc.mime.startsWith("image/"));

  function replace(updated: ParsedQuestion) {
    setItems((xs) => xs.map((x) => (x.id === updated.id ? { ...x, ...updated, group: x.group } : x)));
  }

  function next(from = index) {
    const after = items.findIndex((x, i) => i > from && !done.has(x.id));
    if (after >= 0) setIndex(after);
  }

  async function run<T>(fn: () => Promise<T>): Promise<T | undefined> {
    setMessage(null);
    try {
      return await fn();
    } catch (e) {
      setMessage({ tone: "red", text: e instanceof ApiError ? e.message : "Có lỗi xảy ra" });
      return undefined;
    }
  }

  async function action(kind: "approve" | "reject" | "skip") {
    if (!q) return;
    const r = await run(() => api<ParsedQuestion>(`/review/questions/${q.id}/action`, { body: { action: kind } }));
    if (!r) return;
    replace(r);
    if (kind !== "skip") setDone((s) => new Set(s).add(q.id));
    onChange?.();
    next();
  }

  async function setAnswer(label: string) {
    if (!q) return;
    const previous = q;
    let answer: Record<string, unknown>;
    if (q.type === "true_false") {
      const cur = (q.answer ?? {}) as Record<string, boolean | null>;
      answer = Object.fromEntries(q.options.map((o) => [o.label, o.label === label ? !(cur[o.label] ?? false) : (cur[o.label] ?? false)]));
    } else {
      answer = { key: label };
    }
    replace({ ...q, answer: answer as ParsedQuestion["answer"] }); // optimistic
    const r = await run(() => api<ParsedQuestion>(`/questions/${q.id}`, { method: "PATCH", body: { answer } }));
    if (r) replace(r);
    else replace(previous);
  }

  async function pickTopic(t: Topic) {
    if (!q) return;
    setPicking(false);
    const r = await run(() => api<ParsedQuestion>(`/questions/${q.id}`, { method: "PATCH", body: { primary_topic_id: t.id } }));
    if (r) replace(r);
  }

  const labelFor = (n: number) => (q?.type === "true_false" ? "abcd" : "ABCD")[n - 1];
  useHotkeys(
    {
      Enter: () => void action("approve"),
      x: () => void action("reject"),
      s: () => void action("skip"),
      j: () => setIndex((i) => Math.min(i + 1, items.length - 1)),
      k: () => setIndex((i) => Math.max(i - 1, 0)),
      t: () => setPicking(true),
      e: () => renderEditor && setEditing(true),
      "1": () => q && ["mcq", "true_false"].includes(q.type) && void setAnswer(labelFor(1)),
      "2": () => q && ["mcq", "true_false"].includes(q.type) && void setAnswer(labelFor(2)),
      "3": () => q && ["mcq", "true_false"].includes(q.type) && void setAnswer(labelFor(3)),
      "4": () => q && ["mcq", "true_false"].includes(q.type) && void setAnswer(labelFor(4)),
    },
    !picking && !editing,
  );

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
        {editing && renderEditor ? (
          renderEditor({
            question: q,
            onSaved: (r) => {
              replace(r);
              setEditing(false);
            },
            onCancel: () => setEditing(false),
          })
        ) : (
          <QuestionView
            question={q}
            mode="review"
            solutionOpen={false}
            onSelect={["mcq", "true_false"].includes(q.type) ? (label) => void setAnswer(label) : undefined}
          />
        )}
        <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-border pt-3 text-sm">
          <span className="text-muted-foreground">Chuyên đề:</span>
          <button type="button" className="rounded bg-primary/10 px-2 py-0.5 text-primary" onClick={() => setPicking(true)} data-testid="topic-button">
            {primary ? primary.name : "Chọn chuyên đề"}
            {primary?.source && primary.source !== "manual" ? ` · gợi ý ${primary.score ? Math.round(primary.score * 100) + "%" : ""}` : ""}
          </button>
          <div className="ml-auto flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setIndex((i) => Math.max(i - 1, 0))}>
              ← K
            </Button>
            <Button size="sm" variant="destructive" onClick={() => void action("reject")}>
              Loại (X)
            </Button>
            {renderEditor && (
              <Button variant="outline" size="sm" onClick={() => setEditing(true)}>
                Sửa (E)
              </Button>
            )}
            <Button size="sm" onClick={() => void action("approve")}>
              Duyệt (Enter)
            </Button>
          </div>
        </div>
        <p className="mt-3 flex flex-wrap gap-3 text-xs text-muted-foreground" data-testid="legend">
          {LEGEND.map(([k, v]) => (
            <span key={k}>
              <kbd className="rounded border border-input px-1 font-mono">{k}</kbd> {v}
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
      <FormDialog open={picking} title="Chọn chuyên đề (T)" onOpenChange={(o) => !o && setPicking(false)}>
        <TopicPicker topics={topics} onPick={(t) => void pickTopic(t)} onClose={() => setPicking(false)} />
      </FormDialog>
    </div>
  );
}
