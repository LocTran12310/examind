"use client";

import { useState } from "react";
import { Alert, Button, Modal, Select } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { DIFFICULTY_LABEL, type Tag, type Topic } from "@/lib/types";
import { TopicPicker } from "./TopicPicker";

export function BulkBar({ ids, topics, tags, onDone, onClear }: { ids: string[]; topics: Topic[]; tags: Tag[]; onDone: () => void; onClear: () => void }) {
  const [picking, setPicking] = useState(false);
  const [message, setMessage] = useState<{ tone: "red" | "green"; text: string } | null>(null);
  if (!ids.length) return null;

  async function apply(set: Record<string, unknown>, label: string) {
    setMessage(null);
    try {
      const r = await api<{ updated: number }>("/questions/bulk", { body: { ids, set } });
      setMessage({ tone: "green", text: `${label}: ${r.updated} câu` });
      onDone();
    } catch (e) {
      setMessage({ tone: "red", text: e instanceof ApiError ? e.message : "Có lỗi xảy ra" });
    }
  }

  async function remove() {
    if (!window.confirm(`Xóa vĩnh viễn ${ids.length} câu hỏi?`)) return;
    setMessage(null);
    let failed = 0;
    for (const id of ids) {
      await api(`/questions/${id}`, { method: "DELETE" }).catch(() => failed++);
    }
    setMessage(failed ? { tone: "red", text: `${failed} câu không xóa được (đang dùng trong đề)` } : { tone: "green", text: `Đã xóa ${ids.length} câu` });
    onClear();
    onDone();
  }

  return (
    <div className="sticky top-0 z-10 mb-3 space-y-2 rounded-xl border border-brand-100 bg-brand-50 p-3" data-testid="bulk-bar">
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <span className="font-medium">Đã chọn {ids.length}</span>
        <Select aria-label="Đặt mức độ" value="" onChange={(e) => e.target.value && void apply({ difficulty: e.target.value }, "Đã đặt mức độ")}>
          <option value="">Đặt mức độ…</option>
          {Object.entries(DIFFICULTY_LABEL).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </Select>
        <Button size="sm" onClick={() => setPicking(true)}>
          Đặt chuyên đề…
        </Button>
        <Select aria-label="Thêm tag" value="" onChange={(e) => e.target.value && void apply({ add_tag_ids: [e.target.value] }, "Đã thêm tag")}>
          <option value="">Thêm tag…</option>
          {tags.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </Select>
        <Button size="sm" onClick={() => void apply({ status: "approved" }, "Đã duyệt")}>
          Duyệt
        </Button>
        <Button size="sm" onClick={() => void apply({ status: "rejected" }, "Đã loại")}>
          Loại
        </Button>
        <Button size="sm" variant="danger" onClick={() => void remove()}>
          Xóa
        </Button>
        <Button size="sm" variant="ghost" onClick={onClear}>
          Bỏ chọn
        </Button>
      </div>
      {message && <Alert tone={message.tone}>{message.text}</Alert>}
      <Modal open={picking} title="Đặt chuyên đề cho các câu đã chọn" onClose={() => setPicking(false)}>
        <TopicPicker
          topics={topics}
          onPick={(t) => {
            setPicking(false);
            void apply({ primary_topic_id: t.id }, `Đã đặt chuyên đề ${t.name}`);
          }}
          onClose={() => setPicking(false)}
        />
      </Modal>
    </div>
  );
}
