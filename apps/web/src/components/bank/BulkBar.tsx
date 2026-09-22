"use client";

import { Check, ChevronDown, Gauge, Network, Tag as TagIcon, Trash2, X } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/app/ConfirmDialog";
import { FormDialog } from "@/components/app/FormDialog";
import { ToolbarButton } from "@/components/data-table/Toolbar";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { api, ApiError } from "@/lib/api";
import { DIFFICULTY_LABEL, type Tag, type Topic } from "@/lib/types";
import { TopicPicker } from "./TopicPicker";

/** Bulk actions for the selected questions, rendered inside the table toolbar. */
export function BulkActions({ ids, topics, tags, onDone, onClear }: { ids: string[]; topics: Topic[]; tags: Tag[]; onDone: () => void; onClear: () => void }) {
  const [picking, setPicking] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const none = ids.length === 0;

  async function apply(set: Record<string, unknown>, label: string) {
    try {
      const r = await api<{ updated: number }>("/questions/bulk", { body: { ids, set } });
      toast.success(`${label}: ${r.updated} câu`);
      onDone();
    } catch (e) {
      toast.error(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
    }
  }

  async function remove() {
    let failed = 0;
    for (const id of ids) await api(`/questions/${id}`, { method: "DELETE" }).catch(() => failed++);
    if (failed) toast.error(`${failed} câu không xóa được (đang dùng trong đề)`);
    else toast.success(`Đã xóa ${ids.length} câu`);
    onClear();
    onDone();
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <ToolbarButton disabled={none}>
            <Gauge /> Mức độ <ChevronDown />
          </ToolbarButton>
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          {Object.entries(DIFFICULTY_LABEL).map(([k, v]) => (
            <DropdownMenuItem key={k} onSelect={() => void apply({ difficulty: k }, `Đã đặt mức độ ${v}`)}>
              {v}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
      <ToolbarButton disabled={none} onClick={() => setPicking(true)}>
        <Network /> Chuyên đề
      </ToolbarButton>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <ToolbarButton disabled={none || !tags.length}>
            <TagIcon /> Thêm tag <ChevronDown />
          </ToolbarButton>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="max-h-72 overflow-y-auto">
          {tags.map((t) => (
            <DropdownMenuItem key={t.id} onSelect={() => void apply({ add_tag_ids: [t.id] }, `Đã thêm tag ${t.name}`)}>
              {t.name}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
      <ToolbarButton disabled={none} onClick={() => void apply({ status: "approved" }, "Đã duyệt")}>
        <Check /> Duyệt
      </ToolbarButton>
      <ToolbarButton disabled={none} onClick={() => void apply({ status: "rejected" }, "Đã loại")}>
        <X /> Loại
      </ToolbarButton>
      <ToolbarButton disabled={none} onClick={() => setConfirming(true)}>
        <Trash2 /> Xóa
      </ToolbarButton>
      <ConfirmDialog
        open={confirming}
        onOpenChange={setConfirming}
        destructive
        title={`Xóa vĩnh viễn ${ids.length} câu hỏi?`}
        description="Câu đang dùng trong đề thi sẽ không bị xóa."
        confirmLabel="Xóa"
        onConfirm={async () => {
          setConfirming(false);
          await remove();
        }}
      />
      <FormDialog open={picking} title="Đặt chuyên đề cho các câu đã chọn" onOpenChange={setPicking}>
        <TopicPicker
          topics={topics}
          onPick={(t) => {
            setPicking(false);
            void apply({ primary_topic_id: t.id }, `Đã đặt chuyên đề ${t.name}`);
          }}
          onClose={() => setPicking(false)}
        />
      </FormDialog>
    </>
  );
}
