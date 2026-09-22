"use client";

import { useState } from "react";
import { FormAlert } from "@/components/app/FormAlert";
import { Button } from "@/components/ui/button";
import { FormDialog } from "@/components/app/FormDialog";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
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
    <div className="sticky top-0 z-10 mb-3 space-y-2 rounded-xl border border-primary/20 bg-primary/10 p-3" data-testid="bulk-bar">
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <span className="font-medium">Đã chọn {ids.length}</span>
        <NativeSelect aria-label="Đặt mức độ" value="" onChange={(e) => e.target.value && void apply({ difficulty: e.target.value }, "Đã đặt mức độ")}>
          <NativeSelectOption value="">Đặt mức độ…</NativeSelectOption>
          {Object.entries(DIFFICULTY_LABEL).map(([k, v]) => (
            <NativeSelectOption key={k} value={k}>
              {v}
            </NativeSelectOption>
          ))}
        </NativeSelect>
        <Button variant="outline" size="sm" onClick={() => setPicking(true)}>
          Đặt chuyên đề…
        </Button>
        <NativeSelect aria-label="Thêm tag" value="" onChange={(e) => e.target.value && void apply({ add_tag_ids: [e.target.value] }, "Đã thêm tag")}>
          <NativeSelectOption value="">Thêm tag…</NativeSelectOption>
          {tags.map((t) => (
            <NativeSelectOption key={t.id} value={t.id}>
              {t.name}
            </NativeSelectOption>
          ))}
        </NativeSelect>
        <Button variant="outline" size="sm" onClick={() => void apply({ status: "approved" }, "Đã duyệt")}>
          Duyệt
        </Button>
        <Button variant="outline" size="sm" onClick={() => void apply({ status: "rejected" }, "Đã loại")}>
          Loại
        </Button>
        <Button size="sm" variant="destructive" onClick={() => void remove()}>
          Xóa
        </Button>
        <Button size="sm" variant="ghost" onClick={onClear}>
          Bỏ chọn
        </Button>
      </div>
      {message && <FormAlert kind={message.tone === "red" ? "error" : "success"}>{message.text}</FormAlert>}
      <FormDialog open={picking} title="Đặt chuyên đề cho các câu đã chọn" onOpenChange={(o) => !o && setPicking(false)}>
        <TopicPicker
          topics={topics}
          onPick={(t) => {
            setPicking(false);
            void apply({ primary_topic_id: t.id }, `Đã đặt chuyên đề ${t.name}`);
          }}
          onClose={() => setPicking(false)}
        />
      </FormDialog>
    </div>
  );
}
