"use client";

import { useState } from "react";
import { TopicPicker } from "@/components/bank/TopicPicker";
import { QuestionView } from "@/components/question/QuestionView";
import { Alert, Badge, Button, Empty, Modal } from "@/components/ui";
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
    return <Empty>Đã xem hết các câu cần xem của đề này. 🎉</Empty>;
  }
  const primary = q.topics.find((t) => t.is_primary);

  return (
    <div className={showPage ? "grid gap-4 lg:grid-cols-2" : ""}>
      <section className="rounded-xl border border-gray-200 bg-white p-5" data-testid="queue-card">
        <header className="mb-3 flex flex-wrap items-center gap-2 text-sm">
          <span className="font-semibold" data-testid="counter">
            {index + 1}/{items.length}
          </span>
          <Badge tone={q.group === "Kiểm tra ngẫu nhiên" ? "blue" : "amber"}>{q.group}</Badge>
          <span className="text-gray-500">
            Câu {q.number}
            {q.part ? ` · Phần ${q.part}` : ""}
          </span>
          {done.has(q.id) && <Badge tone={q.status === "rejected" ? "red" : "green"}>{q.status === "rejected" ? "Đã loại" : "Đã xử lý"}</Badge>}
          {q.issues
            .filter((i) => i !== q.group && i !== "thiếu lời giải")
            .map((i) => (
              <Badge key={i} tone="red">
                {i}
              </Badge>
            ))}
        </header>
        {message && (
          <div className="mb-3">
            <Alert tone={message.tone}>{message.text}</Alert>
          </div>
        )}
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
        <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-gray-100 pt-3 text-sm">
          <span className="text-gray-500">Chuyên đề:</span>
          <button type="button" className="rounded bg-brand-50 px-2 py-0.5 text-brand-700" onClick={() => setPicking(true)} data-testid="topic-button">
            {primary ? primary.name : "Chọn chuyên đề"}
            {primary?.source && primary.source !== "manual" ? ` · gợi ý ${primary.score ? Math.round(primary.score * 100) + "%" : ""}` : ""}
          </button>
          <div className="ml-auto flex gap-2">
            <Button size="sm" onClick={() => setIndex((i) => Math.max(i - 1, 0))}>
              ← K
            </Button>
            <Button size="sm" variant="danger" onClick={() => void action("reject")}>
              Loại (X)
            </Button>
            {renderEditor && (
              <Button size="sm" onClick={() => setEditing(true)}>
                Sửa (E)
              </Button>
            )}
            <Button size="sm" variant="primary" onClick={() => void action("approve")}>
              Duyệt (Enter)
            </Button>
          </div>
        </div>
        <p className="mt-3 flex flex-wrap gap-3 text-xs text-gray-500" data-testid="legend">
          {LEGEND.map(([k, v]) => (
            <span key={k}>
              <kbd className="rounded border border-gray-300 px-1 font-mono">{k}</kbd> {v}
            </span>
          ))}
          <span>· còn {remaining} câu</span>
        </p>
      </section>
      {showPage && (
        <aside className="rounded-xl border border-gray-200 bg-white p-2" data-testid="source-page">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={`/api/documents/${doc.id}/pages/${q.page}.png`} alt={`Trang ${q.page} của đề gốc`} className="w-full" />
        </aside>
      )}
      <Modal open={picking} title="Chọn chuyên đề (T)" onClose={() => setPicking(false)}>
        <TopicPicker topics={topics} onPick={(t) => void pickTopic(t)} onClose={() => setPicking(false)} />
      </Modal>
    </div>
  );
}
